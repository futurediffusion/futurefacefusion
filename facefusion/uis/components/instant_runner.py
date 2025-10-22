from copy import deepcopy
from time import sleep
from typing import List, Optional, Tuple

import gradio

from facefusion import process_manager, state_manager, wording
from facefusion.batch_helper import compose_batch_output_path
from facefusion.args import collect_step_args
from facefusion.core import process_step
from facefusion.filesystem import is_directory, is_image, is_video
from facefusion.jobs import job_helper, job_manager, job_runner, job_store
from facefusion.temp_helper import clear_temp_directory
from facefusion.types import Args, UiWorkflow
from facefusion.uis.core import get_ui_component
from facefusion.uis.ui_helper import suggest_output_path

INSTANT_RUNNER_WRAPPER : Optional[gradio.Row] = None
INSTANT_RUNNER_START_BUTTON : Optional[gradio.Button] = None
INSTANT_RUNNER_STOP_BUTTON : Optional[gradio.Button] = None
INSTANT_RUNNER_CLEAR_BUTTON : Optional[gradio.Button] = None


def render() -> None:
    global INSTANT_RUNNER_WRAPPER
    global INSTANT_RUNNER_START_BUTTON
    global INSTANT_RUNNER_STOP_BUTTON
    global INSTANT_RUNNER_CLEAR_BUTTON

    if job_manager.init_jobs(state_manager.get_item('jobs_path')):
        is_instant_runner = state_manager.get_item('ui_workflow') == 'instant_runner'

        with gradio.Row(visible = is_instant_runner) as INSTANT_RUNNER_WRAPPER:
            INSTANT_RUNNER_START_BUTTON = gradio.Button(
                value = wording.get('uis.start_button'),
                variant = 'primary',
                size = 'sm'
            )
            INSTANT_RUNNER_STOP_BUTTON = gradio.Button(
                value = wording.get('uis.stop_button'),
                variant = 'primary',
                size = 'sm',
                visible = False
            )
            INSTANT_RUNNER_CLEAR_BUTTON = gradio.Button(
                value = wording.get('uis.clear_button'),
                size = 'sm'
            )


def listen() -> None:
    output_image = get_ui_component('output_image')
    output_video = get_ui_component('output_video')
    ui_workflow_dropdown = get_ui_component('ui_workflow_dropdown')

    if output_image and output_video:
        INSTANT_RUNNER_START_BUTTON.click(start, outputs = [ INSTANT_RUNNER_START_BUTTON, INSTANT_RUNNER_STOP_BUTTON ])
        INSTANT_RUNNER_START_BUTTON.click(run, outputs = [ INSTANT_RUNNER_START_BUTTON, INSTANT_RUNNER_STOP_BUTTON, output_image, output_video ])
        INSTANT_RUNNER_STOP_BUTTON.click(stop, outputs = [ INSTANT_RUNNER_START_BUTTON, INSTANT_RUNNER_STOP_BUTTON, output_image, output_video ])
        INSTANT_RUNNER_CLEAR_BUTTON.click(clear, outputs = [ output_image, output_video ])
    if ui_workflow_dropdown:
        ui_workflow_dropdown.change(remote_update, inputs = ui_workflow_dropdown, outputs = INSTANT_RUNNER_WRAPPER)


def remote_update(ui_workflow : UiWorkflow) -> gradio.Row:
    is_instant_runner = ui_workflow == 'instant_runner'

    return gradio.Row(visible = is_instant_runner)


def start() -> Tuple[gradio.Button, gradio.Button]:
    while not process_manager.is_processing():
        sleep(0.5)
    return gradio.Button(visible = False), gradio.Button(visible = True)


def run() -> Tuple[gradio.Button, gradio.Button, gradio.Image, gradio.Video]:
    step_args = collect_step_args()
    target_paths: List[str] = step_args.get('target_paths') or []
    output_path = step_args.get('output_path')
    display_output_path: Optional[str] = step_args.get('output_path')

    if output_path and len(target_paths) <= 1 and is_directory(output_path):
        suggested_output_path = suggest_output_path(output_path, state_manager.get_item('target_path'))
        if suggested_output_path:
            step_args['output_path'] = suggested_output_path
            display_output_path = suggested_output_path

    if job_manager.init_jobs(state_manager.get_item('jobs_path')):
        create_and_run_job(step_args)
        if len(target_paths) > 1:
            display_output_path = resolve_batch_preview_output_path(output_path, target_paths)
        else:
            display_output_path = step_args.get('output_path')
        step_args['output_path'] = output_path
        state_manager.set_item('output_path', output_path)

    if display_output_path and is_image(display_output_path):
        return (
            gradio.Button(visible = True),
            gradio.Button(visible = False),
            gradio.Image(value = display_output_path, visible = True),
            gradio.Video(value = None, visible = False)
        )
    if display_output_path and is_video(display_output_path):
        return (
            gradio.Button(visible = True),
            gradio.Button(visible = False),
            gradio.Image(value = None, visible = False),
            gradio.Video(value = display_output_path, visible = True)
        )
    return (
        gradio.Button(visible = True),
        gradio.Button(visible = False),
        gradio.Image(value = None),
        gradio.Video(value = None)
    )


def resolve_batch_preview_output_path(base_output_path: Optional[str], target_paths: List[str]) -> Optional[str]:
    if not base_output_path:
        return None

    total = len(target_paths)
    for index, target_path in enumerate(target_paths):
        candidate_path = compose_batch_output_path(base_output_path, target_path, index, total)
        if is_image(candidate_path) or is_video(candidate_path):
            return candidate_path
    return None


def create_and_run_job(step_args : Args) -> bool:
    for key in job_store.get_job_keys():
        state_manager.sync_item(key) #type:ignore[arg-type]

    target_paths : List[str] = step_args.get('target_paths') or []

    if len(target_paths) > 1:
        return create_and_run_batch_job(step_args, target_paths)

    return create_and_run_single_job(step_args, target_paths)


def create_and_run_single_job(step_args : Args, target_paths : List[str]) -> bool:
    job_id = job_helper.suggest_job_id('ui')
    normalized_step_args = deepcopy(step_args)
    target_path = normalized_step_args.get('target_path')

    if target_path:
        normalized_step_args['target_paths'] = [ target_path ]
    else:
        normalized_step_args['target_paths'] = target_paths

    return job_manager.create_job(job_id) and job_manager.add_step(job_id, normalized_step_args) and job_manager.submit_job(job_id) and job_runner.run_job(job_id, process_step)


def create_and_run_batch_job(step_args : Args, target_paths : List[str]) -> bool:
    job_id = job_helper.suggest_job_id('ui')
    base_output_path = step_args.get('output_path')

    if not job_manager.create_job(job_id):
        return False

    for index, target_path in enumerate(target_paths):
        batch_step_args = deepcopy(step_args)
        batch_step_args['target_path'] = target_path
        batch_step_args['target_paths'] = [ target_path ]
        batch_step_args['output_path'] = compose_batch_output_path(base_output_path, target_path, index, len(target_paths))

        if not job_manager.add_step(job_id, batch_step_args):
            return False

    return job_manager.submit_job(job_id) and job_runner.run_job(job_id, process_step)


def stop() -> Tuple[gradio.Button, gradio.Button, gradio.Image, gradio.Video]:
    process_manager.stop()
    return gradio.Button(visible = True), gradio.Button(visible = False), gradio.Image(value = None), gradio.Video(value = None)


def clear() -> Tuple[gradio.Image, gradio.Video]:
    while process_manager.is_processing():
        sleep(0.5)
    if state_manager.get_item('target_path'):
        clear_temp_directory(state_manager.get_item('target_path'))
    return gradio.Image(value = None), gradio.Video(value = None)

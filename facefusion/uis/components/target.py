from typing import List, Optional, Tuple, Union

import gradio

from facefusion import state_manager, wording
from facefusion.face_store import clear_static_faces
from facefusion.filesystem import is_image, is_video
from facefusion.uis.core import register_ui_component
from facefusion.uis.types import ComponentOptions, File

TARGET_FILE : Optional[gradio.File] = None
TARGET_IMAGE : Optional[gradio.Image] = None
TARGET_VIDEO : Optional[gradio.Video] = None


def render() -> None:
    global TARGET_FILE
    global TARGET_IMAGE
    global TARGET_VIDEO

    target_paths : List[str] = state_manager.get_item('target_paths') or []
    target_path = state_manager.get_item('target_path')

    if not target_path and target_paths:
        target_path = target_paths[0]
        state_manager.set_item('target_path', target_path)

    is_target_image = is_image(target_path)
    is_target_video = is_video(target_path)
    TARGET_FILE = gradio.File(
        label = wording.get('uis.target_file'),
        file_count = 'multiple'
    )
    target_image_options : ComponentOptions = {
        'show_label': False,
        'visible': False
    }
    target_video_options : ComponentOptions = {
        'show_label': False,
        'visible': False
    }
    if is_target_image and target_path:
        target_image_options['value'] = target_path
        target_image_options['visible'] = True
    if is_target_video and target_path:
        target_video_options['value'] = target_path
        target_video_options['visible'] = True
    TARGET_IMAGE = gradio.Image(**target_image_options)
    TARGET_VIDEO = gradio.Video(**target_video_options)
    register_ui_component('target_image', TARGET_IMAGE)
    register_ui_component('target_video', TARGET_VIDEO)


def listen() -> None:
    TARGET_FILE.change(update, inputs = TARGET_FILE, outputs = [ TARGET_IMAGE, TARGET_VIDEO ])


def update(file_input : Union[File, List[File]]) -> Tuple[gradio.Image, gradio.Video]:
    clear_static_faces()

    files : List[File] = []

    if isinstance(file_input, list):
        files = [ uploaded_file for uploaded_file in file_input if uploaded_file ]
    elif file_input:
        files = [ file_input ]

    image_paths = [ uploaded_file.name for uploaded_file in files if is_image(uploaded_file.name) ]
    video_paths = [ uploaded_file.name for uploaded_file in files if is_video(uploaded_file.name) ]

    if video_paths:
        state_manager.set_item('target_path', video_paths[0])
        state_manager.clear_item('target_paths')
        return gradio.Image(value = None, visible = False), gradio.Video(value = video_paths[0], visible = True)

    if image_paths:
        state_manager.set_item('target_path', image_paths[0])
        state_manager.set_item('target_paths', image_paths)
        return gradio.Image(value = image_paths[0], visible = True), gradio.Video(value = None, visible = False)

    state_manager.clear_item('target_path')
    state_manager.clear_item('target_paths')
    return gradio.Image(value = None, visible = False), gradio.Video(value = None, visible = False)

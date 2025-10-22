import os

from facefusion import logger
from facefusion.jobs import job_helper, job_manager
from facefusion.types import JobOutputSet, JobStep, ProcessStep


def run_job(job_id : str, process_step : ProcessStep) -> bool:
    queued_job_ids = job_manager.find_job_ids('queued')

    if job_id in queued_job_ids:
        if run_steps(job_id, process_step) and finalize_steps(job_id):
            clean_steps(job_id)
            return job_manager.move_job_file(job_id, 'completed')
        clean_steps(job_id)
        job_manager.move_job_file(job_id, 'failed')
    return False


def run_jobs(process_step : ProcessStep, halt_on_error : bool) -> bool:
    queued_job_ids = job_manager.find_job_ids('queued')
    has_error = False

    if queued_job_ids:
        for job_id in queued_job_ids:
            if not run_job(job_id, process_step):
                has_error = True
                if halt_on_error:
                    return False
        return not has_error
    return False


def retry_job(job_id : str, process_step : ProcessStep) -> bool:
    failed_job_ids = job_manager.find_job_ids('failed')

    if job_id in failed_job_ids:
        return job_manager.set_steps_status(job_id, 'queued') and job_manager.move_job_file(job_id, 'queued') and run_job(job_id, process_step)
    return False


def retry_jobs(process_step : ProcessStep, halt_on_error : bool) -> bool:
    failed_job_ids = job_manager.find_job_ids('failed')
    has_error = False

    if failed_job_ids:
        for job_id in failed_job_ids:
            if not retry_job(job_id, process_step):
                has_error = True
                if halt_on_error:
                    return False
        return not has_error
    return False


def run_step(job_id: str, step_index: int, step: JobStep, process_step: ProcessStep) -> bool:
    step_args = step.get('args') or {}
    output_path = step_args.get('output_path')

    logger.info(f'[BATCH DEBUG] Starting step {step_index} with output_path: {output_path}', __name__)

    if not job_manager.set_step_status(job_id, step_index, 'started'):
        logger.error('[BATCH DEBUG] Failed to set step status to started', __name__)
        return False

    if not process_step(job_id, step_index, step_args):
        logger.error('[BATCH DEBUG] Process step failed', __name__)
        job_manager.set_step_status(job_id, step_index, 'failed')
        return False

    if not output_path:
        logger.error(f'[BATCH DEBUG] No output path defined for step {step_index}', __name__)
        job_manager.set_step_status(job_id, step_index, 'failed')
        return False

    if not os.path.exists(output_path):
        logger.error(f'[BATCH DEBUG] Output file NOT FOUND after processing: {output_path}', __name__)
        output_dir = os.path.dirname(output_path)
        if output_dir and os.path.exists(output_dir):
            files_in_dir = os.listdir(output_dir)
            logger.error(f'[BATCH DEBUG] Files in output directory: {files_in_dir}', __name__)
        job_manager.set_step_status(job_id, step_index, 'failed')
        return False

    logger.debug(f'[BATCH DEBUG] Forcing cleanup after step {step_index}', __name__)

    import gc

    gc.collect()

    target_path = step_args.get('target_path')
    if target_path:
        from facefusion.temp_helper import clear_temp_directory

        logger.debug(f'[BATCH DEBUG] Clearing temp directory for step {step_index}: {target_path}', __name__)
        clear_temp_directory(target_path)

    file_size = os.path.getsize(output_path)
    logger.info(f'[BATCH DEBUG] SUCCESS! Output file exists: {output_path} ({file_size} bytes)', __name__)

    return job_manager.set_step_status(job_id, step_index, 'completed')


def run_steps(job_id : str, process_step : ProcessStep) -> bool:
    steps = job_manager.get_steps(job_id)

    if steps:
        for index, step in enumerate(steps):
            if not run_step(job_id, index, step, process_step):
                return False
        return True
    return False


def finalize_steps(job_id: str) -> bool:
    logger.info('[BATCH DEBUG] Finalize steps - files already in final locations', __name__)
    return True


def clean_steps(job_id: str) -> bool:
    logger.info('[BATCH DEBUG] Clean steps - skipping (files are final outputs)', __name__)
    return True


def collect_output_set(job_id : str) -> JobOutputSet:
    steps = job_manager.get_steps(job_id)
    job_output_set : JobOutputSet = {}

    for index, step in enumerate(steps):
        output_path = step.get('args').get('output_path')

        if output_path:
            step_output_path = job_helper.get_step_output_path(job_id, index, output_path)
            if step_output_path:
                job_output_set.setdefault(output_path, []).append(step_output_path)
    return job_output_set

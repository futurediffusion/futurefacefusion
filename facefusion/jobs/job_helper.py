import os
from datetime import datetime
from typing import Optional

from facefusion.filesystem import get_file_extension, get_file_name


def get_step_output_path(job_id: str, step_index: int, output_path: str) -> Optional[str]:
    """
    SIMPLIFIED: Return the output_path as-is without modifications.
    This prevents batch jobs from getting renamed with job_id suffixes.
    """
    # Simply return the original output_path
    return output_path


def suggest_job_id(job_prefix: str = 'job') -> str:
    return job_prefix + '-' + datetime.now().strftime('%Y-%m-%d-%H-%M-%S')

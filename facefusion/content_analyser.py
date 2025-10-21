from functools import lru_cache
from typing import List, Tuple

from facefusion import state_manager
from facefusion.common_helper import is_macos
from facefusion.execution import has_execution_provider
from facefusion.types import Detection, DownloadScope, DownloadSet, ExecutionProvider, Fps, InferencePool, ModelSet, VisionFrame

STREAM_COUNTER = 0


@lru_cache()
def create_static_model_set(download_scope : DownloadScope) -> ModelSet:
        return {}


def get_inference_pool() -> InferencePool:
        return {}


def clear_inference_pool() -> None:
        return None


def resolve_execution_providers() -> List[ExecutionProvider]:
	if is_macos() and has_execution_provider('coreml'):
		return [ 'cpu' ]
	return state_manager.get_item('execution_providers')


def collect_model_downloads() -> Tuple[DownloadSet, DownloadSet]:
        return {}, {}


def pre_check() -> bool:
        return True


def analyse_stream(vision_frame : VisionFrame, video_fps : Fps) -> bool:
        return False


def analyse_frame(vision_frame : VisionFrame) -> bool:
        return False


@lru_cache()
def analyse_image(image_path : str) -> bool:
        return False


@lru_cache()
def analyse_video(video_path : str, trim_frame_start : int, trim_frame_end : int) -> bool:
        return False


def detect_nsfw(vision_frame : VisionFrame) -> bool:
        return False


def detect_with_nsfw_1(vision_frame : VisionFrame) -> bool:
        return False


def detect_with_nsfw_2(vision_frame : VisionFrame) -> bool:
        return False


def detect_with_nsfw_3(vision_frame : VisionFrame) -> bool:
        return False


def forward_nsfw(vision_frame : VisionFrame, model_name : str) -> Detection:
        return []


def prepare_detect_frame(temp_vision_frame : VisionFrame, model_name : str) -> VisionFrame:
        return temp_vision_frame

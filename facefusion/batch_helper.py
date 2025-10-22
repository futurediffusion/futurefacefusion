from pathlib import Path
from typing import Optional

from facefusion.filesystem import is_directory


def compose_batch_output_path(base_output_path: Optional[str], target_path: str, index: int, total: int) -> str:
    import logging

    target_path_obj = Path(target_path)
    target_suffix = target_path_obj.suffix or ''
    target_stem = target_path_obj.stem or f'target-{index:03d}'

    logger = logging.getLogger(__name__)
    logger.debug(f'Composing batch output path - base: {base_output_path}, target: {target_path}, index: {index}, total: {total}')

    if base_output_path:
        base_path = Path(base_output_path)
        base_suffix = base_path.suffix
        base_stem = base_path.stem or target_stem

        if is_directory(base_output_path) or (not base_suffix and not base_path.exists()):
            directory_path = base_path
            suffix = target_suffix or base_suffix
            batch_suffix = f'-{index:03d}' if total > 1 else ''
            file_name = f"{target_stem}-faceswap{batch_suffix}{suffix}"
            result = str(directory_path / file_name)
            logger.debug(f'Generated output path (directory): {result}')
            return result

        suffix = base_suffix or target_suffix
        if total == 1:
            if suffix and not base_suffix:
                result = str(base_path.with_suffix(suffix))
                logger.debug(f'Generated output path (single with suffix): {result}')
                return result
            result = str(base_path)
            logger.debug(f'Generated output path (single): {result}')
            return result

        batch_suffix = f"-faceswap-{index:03d}"
        if suffix:
            file_name = f"{base_stem}{batch_suffix}{suffix}"
        else:
            file_name = f"{base_stem}{batch_suffix}"
        result = str(base_path.with_name(file_name))
        logger.debug(f'Generated output path (batch): {result}')
        return result

    batch_suffix = f"-faceswap-{index:03d}"
    file_name = f"{target_stem}{batch_suffix}{target_suffix}" if target_suffix else f"{target_stem}{batch_suffix}"
    result = str(target_path_obj.with_name(file_name))
    logger.debug(f'Generated output path (default): {result}')
    return result

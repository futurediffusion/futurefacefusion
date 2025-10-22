from pathlib import Path

import pytest

instant_runner = pytest.importorskip(
    'facefusion.uis.components.instant_runner',
    reason = 'gradio is required for UI instant runner tests'
)

compose_batch_output_path = instant_runner.compose_batch_output_path


def test_compose_batch_output_path_uses_nonexistent_directory(tmp_path) -> None:
    base_output_directory = tmp_path / 'batch_outputs'
    target_path = tmp_path / 'example.png'

    result = compose_batch_output_path(str(base_output_directory), str(target_path), 0, 2)

    result_path = Path(result)
    assert result_path.parent == base_output_directory
    assert result_path.suffix == target_path.suffix
    assert result_path.name.startswith('example-faceswap-0')


def test_compose_batch_output_path_for_file_target(tmp_path) -> None:
    base_output_file = tmp_path / 'result.jpg'
    target_path = tmp_path / 'example.png'

    result = compose_batch_output_path(str(base_output_file), str(target_path), 1, 3)

    assert result == str(base_output_file.with_name('result-faceswap-001.jpg'))

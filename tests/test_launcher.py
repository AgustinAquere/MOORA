from pathlib import Path

import launcher


def _requirements(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "requirements.txt"
    path.write_text(text, encoding="utf-8")
    return path


def test_read_requirements_ignores_comments_and_options(tmp_path):
    path = _requirements(tmp_path, "# comentario\n\nnumpy>=1.0  # nota\n--index-url https://x\n-r otro.txt\npandas\n")
    assert launcher.read_requirements(path) == ["numpy>=1.0", "pandas"]


def test_installed_requirements_are_not_reported(tmp_path):
    path = _requirements(tmp_path, "numpy>=1.0\npytest\n")
    assert launcher.missing_requirements(path) == []


def test_missing_package_is_reported(tmp_path):
    path = _requirements(tmp_path, "numpy\npaquete-que-no-existe-moora\n")
    assert launcher.missing_requirements(path) == ["paquete-que-no-existe-moora (no instalado)"]


def test_outdated_version_is_reported(tmp_path):
    path = _requirements(tmp_path, "numpy>=999\n")
    (item,) = launcher.missing_requirements(path)
    assert item.startswith("numpy>=999 (instalado ")


def test_requirement_with_false_marker_is_skipped(tmp_path):
    path = _requirements(tmp_path, 'paquete-que-no-existe-moora; python_version < "3.0"\n')
    assert launcher.missing_requirements(path) == []


def test_project_requirements_are_satisfied():
    assert launcher.missing_requirements() == []

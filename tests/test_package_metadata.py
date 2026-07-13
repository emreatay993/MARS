from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10
    import tomli as tomllib


def test_corex_compatible_runtime_dependencies_are_declared() -> None:
    pyproject = tomllib.loads(
        (Path(__file__).parents[1] / "pyproject.toml").read_text(encoding="utf-8")
    )

    assert pyproject["project"]["requires-python"] == ">=3.10,<3.13"
    assert pyproject["project"]["dependencies"] == [
        "ansys-dpf-core>=0.16,<0.17",
        "numba>=0.65.1",
        "numpy>=2.0",
        "pandas>=2.3",
        "psutil>=5.9",
    ]

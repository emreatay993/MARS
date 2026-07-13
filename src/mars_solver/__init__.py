"""Public API for the Qt-free MARS runtime."""

__version__ = "1.0.0"

from .headless_runtime import MarsEvent, MarsJob, MarsRunResult, run_job

__all__ = ["MarsEvent", "MarsJob", "MarsRunResult", "run_job", "__version__"]

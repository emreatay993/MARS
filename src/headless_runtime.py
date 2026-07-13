"""Compatibility launcher for source checkouts; prefer :mod:`mars_solver`."""

from mars_solver.headless_runtime import *  # noqa: F401,F403
from mars_solver.headless_runtime import (
    MarsCliError,
    MarsJobValidationError,
    __all__,
    cli_main,
)


if __name__ == "__main__":
    raise SystemExit(cli_main())

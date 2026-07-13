"""Run the MARS batch command through ``python -m mars_solver``."""

from .headless_runtime import cli_main

raise SystemExit(cli_main())

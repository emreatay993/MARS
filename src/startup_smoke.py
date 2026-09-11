"""Opt-in GUI startup protocol, imported before Qt/controller imports in smoke mode.

The external runner captures failures before this module, including bootloader
failures. This report supplies Python phases and tracebacks, not bootstrap logs.
"""
import argparse
import json
import os
from pathlib import Path
import sys
import traceback


class StartupSmoke:
    def __init__(self, report_path):
        self.path = Path(report_path).absolute()
        self.failed = False
        self.event_loop_ran = False
        self.app = None
        self._original_hook = sys.excepthook
        self.report = {
            "protocol": "mars-startup-v1", "status": "starting", "phase": "python-entry",
            "pid": os.getpid(), "executable": sys.executable, "phases": [],
        }
        self.phase("python-entry")
        sys.excepthook = self._exception_hook

    def phase(self, phase):
        self.report["phase"] = phase
        self.report["phases"].append(phase)
        self._write()

    def _write(self):
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        temporary.write_text(json.dumps(self.report, indent=2), encoding="utf-8")
        temporary.replace(self.path)

    def _exception_hook(self, exc_type, exc, tb):
        self.failed = True
        self.report.update(status="failed", traceback="".join(traceback.format_exception(exc_type, exc, tb)))
        self._write()
        if sys.stderr is not None:
            traceback.print_exception(exc_type, exc, tb, file=sys.stderr)
        if self.app is not None:
            self.app.exit(1)

    def run_event_loop(self, app, window):
        from PyQt5.QtCore import QTimer

        self.app = app
        self.phase("controller-created")

        def finish():
            if app.activeModalWidget() is not None:
                self._exception_hook(RuntimeError, RuntimeError("Unexpected modal dialog during startup"), None)
                return
            if self.failed:
                app.exit(1)
                return
            self.event_loop_ran = True
            self.phase("event-loop-running")
            window.close()
            app.quit()

        QTimer.singleShot(500, finish)
        code = app.exec_()
        if self.failed or not self.event_loop_ran or code != 0:
            if not self.failed:
                self._exception_hook(RuntimeError, RuntimeError(f"GUI event loop ended before readiness (exit {code})"), None)
            return code or 1
        self.report["status"] = "ready"
        self.phase("event-loop-complete")
        return 0

    def run(self, launch):
        try:
            code = launch(self)
            if self.failed or self.report["status"] != "ready":
                return code or 1
            return code
        except BaseException:
            self._exception_hook(*sys.exc_info())
            return 1
        finally:
            sys.excepthook = self._original_hook


def run_smoke(argv, launch):
    parser = argparse.ArgumentParser(description="Bounded GUI startup check")
    parser.add_argument("--smoke-test", action="store_true", required=True)
    parser.add_argument("--smoke-report", required=True)
    options = parser.parse_args(argv)
    return StartupSmoke(options.smoke_report).run(launch)

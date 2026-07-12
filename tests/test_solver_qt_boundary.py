"""The numerical solver and computation facade must remain importable without Qt."""

import subprocess
import sys
from pathlib import Path


def test_solver_and_computation_import_without_pyqt():
    src_dir = Path(__file__).resolve().parents[1] / "src"
    script = f"""
import builtins
import sys

real_import = builtins.__import__

def import_without_qt(name, *args, **kwargs):
    if name == "PyQt5" or name.startswith("PyQt5."):
        raise AssertionError(f"unexpected Qt import: {{name}}")
    return real_import(name, *args, **kwargs)

builtins.__import__ = import_without_qt
sys.path.insert(0, {str(src_dir)!r})
import solver.engine
import core.computation
"""

    completed = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr


def test_solver_thread_forwards_progress_on_main_thread(monkeypatch):
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")

    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
    from PyQt5.QtCore import QCoreApplication, QEventLoop, QObject, QThread, QTimer, pyqtSlot
    from ui.handlers.analysis_handler import SolverThread

    app = QCoreApplication.instance() or QCoreApplication([])
    main_thread = QThread.currentThread()
    received = []
    errors = []

    class Receiver(QObject):
        @pyqtSlot(int)
        def receive(self, value):
            received.append((value, QThread.currentThread() is main_thread))

    class FakeHandler:
        def _configure_analysis_engine(self):
            pass

        def _execute_analysis(self, _config, progress_callback=None):
            progress_callback(42)
            return None

    receiver = Receiver()
    thread = SolverThread(FakeHandler(), None)
    loop = QEventLoop()
    thread.progress.connect(receiver.receive)
    thread.finished.connect(lambda *_args: loop.quit())
    thread.error.connect(lambda message: (errors.append(message), loop.quit()))
    QTimer.singleShot(5000, loop.quit)
    thread.start()
    loop.exec_()
    thread.wait()

    assert app is not None
    assert errors == []
    assert received == [(42, True)]

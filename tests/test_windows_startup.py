"""Focused Windows build/packaged-runner contracts; no dependency installs/builds.

Run with: python -m unittest discover -s tests -p test_windows_startup.py -v
Real venv probes use stdlib venv without pip. Tiny C# executables exercise actual
Windows process exits/stalls/redirection rather than mocking Start-Process.
"""
import hashlib
import ctypes
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
import venv

ROOT = Path(__file__).resolve().parents[1]
SUPPORT = ROOT / "scripts/windows"
SHELLS = [path for name in ("powershell.exe", "pwsh.exe") if (path := shutil.which(name))]


def ps_quote(value):
    return "'" + str(value).replace("'", "''") + "'"


@unittest.skipUnless(os.name == "nt", "Windows process contracts")
class WindowsStartupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(prefix="mars startup contracts ")
        cls.area = Path(cls.temporary.name)
        cls.fixture = cls.area / "fixture.exe"
        code = f"Add-Type -TypeDefinition (Get-Content -Raw -LiteralPath {ps_quote(ROOT / 'tests/windows_native_fixture.cs')}) -OutputAssembly {ps_quote(cls.fixture)} -OutputType ConsoleApplication"
        result = subprocess.run([SHELLS[0], "-NoProfile", "-Command", code], capture_output=True, text=True)
        if result.returncode:
            raise AssertionError(result.stdout + result.stderr)

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def setUp(self):
        self.case = Path(tempfile.mkdtemp(dir=self.area))
        self.repo = self.case / "checkout with spaces"
        self.repo.mkdir()
        shutil.copy2(ROOT / "build.ps1", self.repo)
        shutil.copy2(ROOT / "build.bat", self.repo)
        shutil.copytree(SUPPORT, self.repo / "scripts/windows")
        self.environment = os.environ.copy()
        for name in ("VIRTUAL_ENV", "CONDA_PREFIX", "MARS_TEST_MODE", "MARS_TEST_EXIT", "MARS_TEST_VERSION", "MARS_TEST_BITS"):
            self.environment.pop(name, None)
        self.calls = self.case / "native-calls.txt"
        self.environment["MARS_TEST_CALLS"] = str(self.calls)

    def run_ps(self, shell, script, *args, pause=False, env=None):
        command = [shell, "-NoProfile", "-File", str(script), *map(str, args)]
        if not pause:
            command.append("-NoPause")
        return subprocess.run(command, input="\n", capture_output=True, text=True, errors="replace",
                              timeout=25, cwd=self.case, env=env or self.environment)

    def fake_environment(self, **overrides):
        prefix = self.repo / "build/release environment 312"
        (prefix / "Scripts").mkdir(parents=True, exist_ok=True)
        shutil.copy2(self.fixture, prefix / "Scripts/python.exe")
        environment = self.environment.copy()
        environment.update(VIRTUAL_ENV=str(prefix), PATH=str(prefix / "Scripts") + os.pathsep + environment["PATH"])
        environment.update(overrides)
        return prefix, environment

    def package(self):
        package = self.case / "relocated package with spaces"
        package.mkdir()
        for name in ("diagnose.ps1", "diagnose.bat", "windows_common.ps1"):
            shutil.copy2(SUPPORT / name, package)
        shutil.copy2(self.fixture, package / "diagnostic.exe")
        (package / "package.json").write_text(json.dumps({"diagnosticExecutable": "diagnostic.exe", "startupExecutables": ["diagnostic.exe"]}))
        self.write_inventory(package, ["diagnostic.exe"])
        return package

    def write_inventory(self, package, names):
        records = [{"path": name, "sha256": hashlib.sha256((package / name).read_bytes()).hexdigest()} for name in names]
        (package / "runtime-inventory.json").write_text(json.dumps({"files": records}))

    def test_no_environment_rejected_before_dependencies_with_final_pause(self):
        for shell in SHELLS:
            with self.subTest(shell=shell):
                result = self.run_ps(shell, self.repo / "build.ps1", pause=True)
                self.assertNotEqual(result.returncode, 0, result.stdout)
                self.assertIn("No active environment", result.stdout)
                self.assertIn("Press Enter", result.stdout)
                self.assertFalse(self.calls.exists())

    def test_early_argument_errors_and_no_pause(self):
        for shell in SHELLS:
            for arguments in (("-BadOption",), ("-PackageDir",), ("-PackageDir", "somewhere")):
                with self.subTest(shell=shell, args=arguments):
                    result = self.run_ps(shell, self.repo / "build.ps1", *arguments)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertNotIn("Press Enter", result.stdout)
                    self.assertIn("[FAILED]", result.stdout)

    def test_wrong_python_or_architecture_precedes_dependency_writes(self):
        for shell in SHELLS:
            for overrides in ({"MARS_TEST_VERSION": "3,11,9"}, {"MARS_TEST_BITS": "32"}):
                with self.subTest(shell=shell, overrides=overrides):
                    _, environment = self.fake_environment(**overrides)
                    result = self.run_ps(shell, self.repo / "build.ps1", env=environment)
                    self.assertNotEqual(result.returncode, 0, result.stdout)
                    self.assertIn("Python 3.12 x64", result.stdout)
                    self.assertNotIn("-m pip", self.calls.read_text())

    def test_native_nonzero_and_stderr_warning_preserved(self):
        for shell in SHELLS:
            with self.subTest(shell=shell):
                prefix, environment = self.fake_environment()
                sibling = self.repo / "build/keep.txt"
                sibling.write_text("keep")
                configuration = json.loads((SUPPORT / "package.json").read_text())
                work = self.repo / ("build/pyinstaller-" + configuration["name"])
                work.mkdir(exist_ok=True)
                (work / "stale.txt").write_text("old")
                result = self.run_ps(shell, self.repo / "build.ps1", "-Clean", env=environment)
                self.assertEqual(result.returncode, 23, result.stdout + result.stderr)
                self.assertIn("harmless interpreter warning", result.stdout)
                self.assertIn("fixture stderr", result.stdout)
                self.assertTrue((prefix / "Scripts/python.exe").exists())
                self.assertTrue(sibling.exists())
                self.assertFalse((work / "stale.txt").exists())
                self.assertTrue(list((self.repo / "build/logs").rglob("dependencies.stderr.log")))

    def test_actual_arbitrary_venv_names_and_mismatched_path(self):
        for name in ("not-a-default-env", "release environment 312"):
            prefix = self.case / name
            venv.EnvBuilder(with_pip=False).create(prefix)
            for shell in SHELLS:
                with self.subTest(shell=shell, name=name):
                    environment = self.environment.copy()
                    environment.update(VIRTUAL_ENV=str(prefix), PATH=str(prefix / "Scripts") + os.pathsep + environment["PATH"])
                    code = f"$ErrorActionPreference='Stop'; . {ps_quote(SUPPORT / 'windows_common.ps1')}; Get-ActiveBuildPython {ps_quote(self.repo)} {ps_quote(self.case)} | ConvertTo-Json"
                    result = subprocess.run([shell, "-NoProfile", "-Command", code], env=environment, capture_output=True, text=True, timeout=20)
                    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                    self.assertIn(str(prefix), result.stdout)
                    environment["VIRTUAL_ENV"] = str(self.repo)
                    result = self.run_ps(shell, self.repo / "build.ps1", env=environment)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn("does not match", result.stdout)

    def test_clean_refuses_environment_overlap_and_junction(self):
        _, environment = self.fake_environment()
        config = json.loads((SUPPORT / "package.json").read_text())
        target = self.repo / ("build/pyinstaller-" + config["name"])
        for shell in SHELLS:
            code = f"$ErrorActionPreference='Stop'; . {ps_quote(SUPPORT / 'windows_common.ps1')}; Assert-BuildTarget {ps_quote(target)} {ps_quote(target)} {ps_quote(target / 'active env')}"
            result = subprocess.run([shell, "-NoProfile", "-Command", code], capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
        destination = self.case / "do not delete"
        destination.mkdir()
        (destination / "sentinel").write_text("preserved")
        code = f"New-Item -ItemType Junction -Path {ps_quote(target)} -Target {ps_quote(destination)}"
        subprocess.run([SHELLS[0], "-NoProfile", "-Command", code], check=True, capture_output=True)
        try:
            result = self.run_ps(SHELLS[0], self.repo / "build.ps1", "-Clean", env=environment)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("reparse", result.stdout)
            self.assertEqual((destination / "sentinel").read_text(), "preserved")
        finally:
            # Delete only the test-created junction itself, never recurse through it.
            os.rmdir(target)

    def test_packaged_protocol_success_failure_stall_and_pre_python(self):
        package = self.package()
        for shell in SHELLS:
            for mode, expected in (("success", 0), ("failure", 7), ("stall", 1), ("pre-python", 1), ("no-report", 1), ("wrong-pid", 1)):
                with self.subTest(shell=shell, mode=mode):
                    environment = dict(self.environment, MARS_TEST_MODE=mode)
                    result = self.run_ps(shell, package / "diagnose.ps1", "-TimeoutSeconds", "2", "-LogRoot", self.case / "logs", env=environment)
                    self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
                    self.assertIn("fixture stderr", result.stdout)
                    self.assertNotIn("Press Enter", result.stdout)
                    if mode == "pre-python":
                        self.assertIn("Failed to start embedded python interpreter!", result.stdout)
                    if mode == "stall":
                        self.assertIn("timed out", result.stdout)

    def test_children_cannot_escape_job_or_hold_output_drain(self):
        package = self.package()
        unrelated = subprocess.Popen([str(self.fixture), "--hold-output"], stdout=subprocess.DEVNULL,
                                     stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW)
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.OpenProcess.restype = ctypes.c_void_p
        kernel.OpenProcess.argtypes = [ctypes.c_uint32, ctypes.c_int, ctypes.c_uint32]
        kernel.WaitForSingleObject.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
        kernel.CloseHandle.argtypes = [ctypes.c_void_p]
        try:
            for shell in SHELLS:
                for mode in ("early-child", "ready-child"):
                    for attempt in range(2):
                        with self.subTest(shell=shell, mode=mode, attempt=attempt):
                            pid_file = self.case / "child pid.txt"
                            environment = dict(self.environment, MARS_TEST_MODE=mode, MARS_TEST_CHILD_FILE=str(pid_file))
                            started = time.monotonic()
                            result = self.run_ps(shell, package / "diagnose.ps1", "-TimeoutSeconds", "2", "-LogRoot", self.case / "logs", env=environment)
                            self.assertEqual(result.returncode, 1 if mode == "early-child" else 0, result.stdout + result.stderr)
                            self.assertLess(time.monotonic() - started, 8, result.stdout)
                            handle = kernel.OpenProcess(0x100000, False, int(pid_file.read_text()))
                            if handle:
                                try:
                                    self.assertEqual(kernel.WaitForSingleObject(handle, 2000), 0, "Escaped child remains alive")
                                finally:
                                    kernel.CloseHandle(handle)
                            self.assertIsNone(unrelated.poll(), "Unrelated same-name process was stopped")
        finally:
            unrelated.terminate()
            unrelated.wait(timeout=5)

    def test_all_configured_launchers_must_acknowledge_before_build_passes(self):
        package = self.package()
        shutil.copy2(self.fixture, package / "windowed.exe")
        (package / "package.json").write_text(json.dumps({
            "diagnosticExecutable": "diagnostic.exe",
            "startupExecutables": ["diagnostic.exe", "windowed.exe"],
        }))
        self.write_inventory(package, ["diagnostic.exe", "windowed.exe"])
        for shell in SHELLS:
            for mode, expected in (("success", 0), ("failure", 7), ("no-report", 1)):
                with self.subTest(shell=shell, windowed_mode=mode):
                    environment = dict(self.environment, MARS_TEST_MODE="success", MARS_TEST_WINDOWED_MODE=mode)
                    result = self.run_ps(shell, self.repo / "build.ps1", "-SmokeOnly", "-PackageDir", package, env=environment)
                    self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
                    self.assertIn("Startup acknowledged: " + str(package / "diagnostic.exe"), result.stdout)
                    self.assertIn("windowed.stderr.log", result.stdout)
                    self.assertIn("windowed.smoke-report.json", result.stdout)
                    console_reports = list((self.repo / "build/logs").rglob("smoke-report.json"))
                    self.assertTrue(console_reports)
                    self.assertTrue(all(json.loads(path.read_text())["status"] == "ready" for path in console_reports))
                    if mode == "success":
                        self.assertIn("PASS: every startup executable", result.stdout)
                    else:
                        self.assertNotIn("PASS: every startup executable", result.stdout)

    def test_repository_startup_list_excludes_batch_cli(self):
        configuration = json.loads((SUPPORT / "package.json").read_text())
        expected = ["MARSDiagnostics.exe", "MARS.exe"] if configuration["name"] == "MARS" else ["MARS-SC.exe"]
        self.assertEqual(configuration["startupExecutables"], expected)
        self.assertEqual(configuration.get("batchExecutable"), "MARSBatch.exe" if configuration["name"] == "MARS" else None)

    def test_batch_help_is_an_additional_exit_code_gate(self):
        package = self.package()
        shutil.copy2(self.fixture, package / "batch.exe")
        (package / "package.json").write_text(json.dumps({
            "diagnosticExecutable": "diagnostic.exe", "startupExecutables": ["diagnostic.exe"],
            "batchExecutable": "batch.exe",
        }))
        self.write_inventory(package, ["diagnostic.exe", "batch.exe"])
        for shell in SHELLS:
            for code in (0, 19):
                with self.subTest(shell=shell, batch_exit=code):
                    environment = dict(self.environment, MARS_TEST_MODE="success", MARS_TEST_EXIT=str(code))
                    result = self.run_ps(shell, self.repo / "build.ps1", "-SmokeOnly", "-PackageDir", package, env=environment)
                    self.assertEqual(result.returncode, code, result.stdout + result.stderr)
                    self.assertIn("Startup acknowledged:", result.stdout)
                    self.assertIn("batch-help.stderr.log", result.stdout)
                    self.assertIn("--help", self.calls.read_text().splitlines())
                    if code == 0:
                        self.assertIn("Batch --help passed:", result.stdout)
                    else:
                        self.assertNotIn("PASS: every startup executable", result.stdout)

    def test_relative_paths_follow_powershell_location(self):
        package = self.package()
        for shell in SHELLS:
            with self.subTest(shell=shell):
                code = (
                    f"Set-Location -LiteralPath {ps_quote(self.case)}; "
                    f"& {ps_quote(package / 'diagnose.ps1')} -PackageDir {ps_quote(package.name)} "
                    "-LogRoot '.\\relative logs' -NoPause"
                )
                result = subprocess.run([shell, "-NoProfile", "-Command", code], cwd=self.repo,
                                        env=self.environment, capture_output=True, text=True, timeout=20)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertIn(str(self.case / "relative logs"), result.stdout)
                self.assertFalse((self.repo / "relative logs").exists())

    def test_missing_or_corrupt_runtime_still_launches_console(self):
        package = self.package()
        internal = package / "_internal"
        internal.mkdir()
        library = internal / "base_library.zip"
        library.write_bytes(b"original zip fixture")
        self.write_inventory(package, ["diagnostic.exe", "_internal/base_library.zip"])
        for corrupt in (False, True):
            if corrupt:
                library.write_bytes(b"corrupt")
            else:
                library.unlink()
            result = self.run_ps(SHELLS[0], package / "diagnose.ps1", "-LogRoot", self.case / "logs", env=dict(self.environment, MARS_TEST_MODE="pre-python"))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("[INVENTORY]", result.stdout)
            self.assertIn("Failed to start embedded python interpreter!", result.stdout)
        self.assertEqual(len(self.calls.read_text().splitlines()), 2)

    @unittest.skipUnless(os.environ.get("MARS_TEST_BOOTLOADER"), "Set MARS_TEST_BOOTLOADER to an existing console PyInstaller exe for real bootstrap fault tests")
    def test_real_bootloader_missing_and_corrupt_runtime(self):
        # Copy only a console bootloader and its minimal native runtime; never
        # change the source package. Python cannot start in any of these cases.
        source = Path(os.environ["MARS_TEST_BOOTLOADER"])
        package = self.package()
        executable = package / "diagnostic.exe"
        shutil.copy2(source, executable)
        internal = package / "_internal"
        internal.mkdir()
        for name in ("python312.dll", "vcruntime140.dll", "vcruntime140_1.dll"):
            if (source.parent / "_internal" / name).exists():
                shutil.copy2(source.parent / "_internal" / name, internal / name)
        python_dll = internal / "python312.dll"
        original_dll = python_dll.read_bytes()
        library = internal / "base_library.zip"
        library.write_bytes(b"placeholder for fault injection")
        self.write_inventory(package, ["diagnostic.exe", "_internal/python312.dll", "_internal/base_library.zip"])
        for mode in ("missing-zip", "corrupt-zip", "missing-dll", "corrupt-dll"):
            with self.subTest(mode=mode):
                python_dll.write_bytes(original_dll)
                library.write_bytes(b"invalid zip")
                if mode == "missing-zip":
                    library.unlink()
                elif mode == "missing-dll":
                    python_dll.unlink()
                elif mode == "corrupt-dll":
                    python_dll.write_bytes(b"invalid PE")
                result = self.run_ps(SHELLS[0], package / "diagnose.ps1", "-TimeoutSeconds", "3", "-LogRoot", self.case / "real-bootstrap-logs")
                self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertIn("[INVENTORY]", result.stdout)
                if mode.endswith("zip"):
                    self.assertIn("Failed to start embedded python interpreter!", result.stdout)
                    self.assertIn("encodings", result.stdout)
                else:
                    self.assertIn("python312.dll", result.stdout)
                self.assertFalse(list((self.case / "real-bootstrap-logs").rglob("smoke-report.json")))

    def test_smoke_only_needs_no_environment_and_batch_propagates_status(self):
        package = self.package()
        for shell in SHELLS:
            result = self.run_ps(shell, self.repo / "build.ps1", "-SmokeOnly", "-PackageDir", package)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        result = subprocess.run(["cmd.exe", "/d", "/c", str(self.repo / "build.bat"), "--bad", "--no-pause"], cwd=self.repo, env=self.environment, capture_output=True, text=True, timeout=15)
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("Press Enter", result.stdout)
        result = subprocess.run(["cmd.exe", "/d", "/c", str(package / "diagnose.bat"), "--no-pause"], cwd=package, env=dict(self.environment, MARS_TEST_MODE="failure"), capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 7, result.stdout + result.stderr)


class SmokeReportTests(unittest.TestCase):
    def test_actual_gui_import_controller_and_event_loop(self):
        entry = ROOT / "mars_sc_entry.py"
        if not entry.exists():
            entry = ROOT / "src/main.py"
        with tempfile.TemporaryDirectory() as folder:
            report_path = Path(folder) / "actual gui report.json"
            result = subprocess.run(
                [sys.executable, str(entry), "--smoke-test", "--smoke-report", str(report_path)],
                capture_output=True, text=True, errors="replace", timeout=45,
                env=dict(os.environ, QT_QPA_PLATFORM="windows"), cwd=folder,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            report = json.loads(report_path.read_text())
            self.assertEqual(report["status"], "ready")
            self.assertEqual(report["phase"], "event-loop-complete")
            self.assertIn("controller-created", report["phases"])
            self.assertIn("event-loop-running", report["phases"])

    def test_import_failure_records_early_phase_and_traceback(self):
        spec = importlib.util.spec_from_file_location("startup_smoke", ROOT / "src/startup_smoke.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "report.json"
            def fail(smoke):
                smoke.phase("gui-imports")
                raise ImportError("controller import sentinel")
            self.assertEqual(module.run_smoke(["--smoke-test", "--smoke-report", str(path)], fail), 1)
            report = json.loads(path.read_text())
            self.assertEqual(report["status"], "failed")
            self.assertEqual(report["phases"], ["python-entry", "gui-imports"])
            self.assertIn("controller import sentinel", report["traceback"])


if __name__ == "__main__":
    unittest.main()

"""Called by the spec after COLLECT; ship diagnostics beside the executables."""
import hashlib
import json
from pathlib import Path
import shutil
import struct
import sys


def ship_diagnostics(package_dir, support_dir):
    package_dir, support_dir = Path(package_dir), Path(support_dir)
    for name in ("diagnose.ps1", "diagnose.bat", "windows_common.ps1", "package.json"):
        shutil.copy2(support_dir / name, package_dir / name)
    configuration = json.loads((support_dir / "package.json").read_text(encoding="utf-8"))
    paths = [*configuration["executables"], "_internal/python312.dll", "_internal/base_library.zip"]
    files = []
    for name in paths:
        path = package_dir / name
        with path.open("rb") as stream:
            digest = hashlib.file_digest(stream, "sha256").hexdigest()
        files.append({"path": name, "size": path.stat().st_size,
                      "sha256": digest})
    inventory = {"python": sys.version, "bits": struct.calcsize("P") * 8, "files": files}
    (package_dir / "runtime-inventory.json").write_text(json.dumps(inventory, indent=2), encoding="utf-8")

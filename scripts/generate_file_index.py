#!/usr/bin/env python3
"""Generate FILE_INDEX.md from the live src/ tree."""

from __future__ import annotations

import ast
import re
import sys
import warnings
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = ROOT / "src"
OUTPUT_PATH = ROOT / "FILE_INDEX.md"


@dataclass
class ModuleInfo:
    """Indexed metadata for one Python module."""

    path: Path
    module_name: str
    lines: int
    classes: int
    functions: int
    description: str
    package: str


def _count_physical_lines(path: Path) -> int:
    """Count physical lines, including blank lines and comments."""
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        return sum(1 for _ in handle)


def _first_sentence(docstring: str) -> str:
    """Extract first sentence from a docstring."""
    compact = " ".join(docstring.strip().split())
    if not compact:
        return "No module docstring."

    sentence = re.match(r"^(.+?[.!?])(?:\s|$)", compact)
    if sentence:
        return sentence.group(1).strip()

    return compact


def _safe_description(text: str) -> str:
    """Escape markdown table delimiters."""
    return text.replace("|", r"\|")


def _parse_module(path: Path) -> ModuleInfo:
    """Parse one Python module and return index metadata."""
    rel_from_root = path.relative_to(ROOT)
    rel_from_src = path.relative_to(SRC_ROOT)
    module_name = ".".join(rel_from_root.with_suffix("").parts)
    package = "(root)" if len(rel_from_src.parts) == 1 else rel_from_src.parts[0]

    lines = _count_physical_lines(path)

    source = path.read_text(encoding="utf-8", errors="replace")
    classes = 0
    functions = 0
    description = "No module docstring."

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", SyntaxWarning)
            tree = ast.parse(source, filename=str(path))

        classes = sum(isinstance(node, ast.ClassDef) for node in tree.body)
        functions = sum(
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            for node in tree.body
        )

        docstring = ast.get_docstring(tree)
        if docstring:
            description = _first_sentence(docstring)
    except SyntaxError as exc:
        description = f"Parse error: {exc.msg}."

    return ModuleInfo(
        path=rel_from_root,
        module_name=module_name,
        lines=lines,
        classes=classes,
        functions=functions,
        description=description,
        package=package,
    )


def _package_sort_key(name: str) -> tuple[int, str]:
    if name == "(root)":
        return (0, name)
    return (1, name)


def build_file_index() -> str:
    """Build markdown content for FILE_INDEX.md."""
    if not SRC_ROOT.exists():
        raise FileNotFoundError(f"Source root not found: {SRC_ROOT}")

    module_paths = sorted(SRC_ROOT.rglob("*.py"))
    modules = [_parse_module(path) for path in module_paths]

    package_totals: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    for mod in modules:
        package_totals[mod.package][0] += 1
        package_totals[mod.package][1] += mod.lines

    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    total_lines = sum(mod.lines for mod in modules)

    lines: list[str] = []
    lines.append("# FILE_INDEX")
    lines.append("")
    lines.append(f"Generated: `{generated_at}`")
    lines.append("")
    lines.append("## Scope")
    lines.append("")
    lines.append("- Source root: `src/`")
    lines.append(f"- Python modules indexed: `{len(modules)}`")
    lines.append(f"- Total Python lines (physical): `{total_lines}`")
    lines.append("- Line counts include blank lines and comments.")
    lines.append(
        "- Descriptions come from each module's top docstring "
        "(first sentence when possible)."
    )
    lines.append("")
    lines.append("## Package Totals")
    lines.append("")
    lines.append("| Package | Modules | Lines |")
    lines.append("| --- | ---: | ---: |")
    for package in sorted(package_totals, key=_package_sort_key):
        module_count, line_count = package_totals[package]
        lines.append(f"| `{package}` | {module_count} | {line_count} |")

    lines.append("")
    lines.append("## Module Index")
    lines.append("")
    lines.append("| Path | Module | Lines | Classes | Functions | Description |")
    lines.append("| --- | --- | ---: | ---: | ---: | --- |")
    for mod in modules:
        desc = _safe_description(mod.description)
        lines.append(
            f"| `{mod.path.as_posix()}` | `{mod.module_name}` | "
            f"{mod.lines} | {mod.classes} | {mod.functions} | {desc} |"
        )

    lines.append("")
    return "\n".join(lines)


def main() -> int:
    """Entrypoint."""
    try:
        content = build_file_index()
    except Exception as exc:  # pragma: no cover - defensive CLI path
        print(f"ERROR: {exc}")
        return 1

    OUTPUT_PATH.write_text(content, encoding="utf-8")
    print(f"Wrote {OUTPUT_PATH.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

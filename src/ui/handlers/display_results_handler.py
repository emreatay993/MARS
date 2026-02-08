"""
Helpers for applying solver output datasets to the Display tab.
"""

import os
from typing import Dict, Iterable, Optional, Tuple

import numpy as np
import pandas as pd

from ui.handlers.display_base_handler import DisplayBaseHandler


class DisplayResultsHandler(DisplayBaseHandler):
    """Loads solver results and applies them to the visualization."""

    MODE_LABELS = {
        "max_over_time": "Max over Time",
        "min_over_time": "Min over Time",
        "time_of_max": "Time of Max",
        "time_of_min": "Time of Min",
        "selected_time": "Selected Time",
    }
    MODE_KEYS_BY_LABEL = {label: key for key, label in MODE_LABELS.items()}

    GROUP_ORDER = [
        "Von Mises",
        "Max Principal",
        "Min Principal",
        "Deformation",
        "Velocity",
        "Acceleration",
        "Force/Moment",
        "Corrected Von Mises",
        "Plastic Strain",
    ]

    COMPONENT_ORDER = {
        "Deformation": ["|U|", "UX", "UY", "UZ"],
        "Velocity": ["|V|", "VX", "VY", "VZ"],
        "Acceleration": ["|A|", "AX", "AY", "AZ"],
        "Force/Moment": ["|F|", "FX", "FY", "FZ", "|M|", "MX", "MY", "MZ"],
    }

    MODE_ORDER = list(MODE_LABELS.keys())

    def __init__(self, tab, state, visual_handler):
        super().__init__(tab, state)
        self.visual_handler = visual_handler
        self._active_solver = None

    def apply_solver_results(
        self,
        solver,
        dataset_catalog: Dict[str, Dict[str, Dict[str, dict]]],
        current_field: Optional[str],
    ) -> None:
        """
        Apply a structured batch-results dataset catalog to the display tab.

        Args:
            solver: Solver instance that produced the output CSV files.
            dataset_catalog: Structured mapping
                catalog[group][component][mode] -> metadata dict.
            current_field: Name of field currently shown in display tab.
        """
        self._active_solver = solver
        normalized = self._normalize_catalog(dataset_catalog)
        if not normalized:
            self.clear_result_catalog()
            return

        self._clear_catalog_fields_from_mesh(normalized)
        preferred = self._find_selection_by_field(normalized, current_field)
        if preferred is None:
            preferred = dict(self.state.result_selection or {})
        self._set_catalog(normalized, preferred_selection=preferred)

    def configure_time_point_catalog(self, mesh, default_field: Optional[str]) -> None:
        """Build and apply selector catalog for a time-point mesh result."""
        self._active_solver = None
        catalog = self._build_time_point_catalog(mesh)
        if not catalog:
            self.clear_result_catalog()
            return

        preferred = self._find_selection_by_field(catalog, default_field)
        if preferred is None:
            preferred = dict(self.state.result_selection or {})
        self._set_catalog(catalog, preferred_selection=preferred)

    def clear_result_catalog(self) -> None:
        """Clear current result catalog and disable selector controls."""
        self.state.result_catalog = {}
        self.state.result_selection = {}
        self._block_selector_signals(True)
        try:
            self.tab.result_group_combo.clear()
            self.tab.result_component_combo.clear()
            self.tab.result_mode_combo.clear()
            self.tab.result_group_combo.setEnabled(False)
            self.tab.result_component_combo.setEnabled(False)
            self.tab.result_mode_combo.setEnabled(False)
        finally:
            self._block_selector_signals(False)

    def set_selectors_enabled(self, enabled: bool) -> None:
        """Enable/disable result selector widgets without mutating catalog state."""
        if not enabled:
            self.tab.result_group_combo.setEnabled(False)
            self.tab.result_component_combo.setEnabled(False)
            self.tab.result_mode_combo.setEnabled(False)
            return

        if not self.state.result_catalog:
            return

        self.tab.result_group_combo.setEnabled(self.tab.result_group_combo.count() > 0)
        self.tab.result_component_combo.setEnabled(self.tab.result_component_combo.count() > 0)
        self.tab.result_mode_combo.setEnabled(self.tab.result_mode_combo.count() > 0)

    def reapply_current_selection(self) -> None:
        """Re-apply currently selected entry to sync mesh/scalar bar with selectors."""
        selection = self._get_current_selection()
        if selection is None:
            return
        self._apply_selection(*selection)

    def on_result_group_changed(self) -> None:
        """Handle result-group combo changes."""
        catalog = self.state.result_catalog
        if not catalog:
            return

        group = self.tab.result_group_combo.currentText().strip()
        if not group or group not in catalog:
            return

        preferred_component = self.state.result_selection.get("component")
        preferred_mode = self.state.result_selection.get("mode")
        self._block_selector_signals(True)
        try:
            component = self._populate_component_combo(group, preferred_component)
            mode_key = self._populate_mode_combo(group, component, preferred_mode)
        finally:
            self._block_selector_signals(False)

        self._apply_selection(group, component, mode_key)

    def on_result_component_changed(self) -> None:
        """Handle component combo changes."""
        catalog = self.state.result_catalog
        if not catalog:
            return

        group = self.tab.result_group_combo.currentText().strip()
        component = self.tab.result_component_combo.currentText().strip()
        if not group or not component:
            return
        if group not in catalog or component not in catalog[group]:
            return

        preferred_mode = self.state.result_selection.get("mode")
        self._block_selector_signals(True)
        try:
            mode_key = self._populate_mode_combo(group, component, preferred_mode)
        finally:
            self._block_selector_signals(False)

        self._apply_selection(group, component, mode_key)

    def on_result_mode_changed(self) -> None:
        """Handle mode combo changes."""
        selection = self._get_current_selection()
        if selection is None:
            return
        self._apply_selection(*selection)

    def _set_catalog(self, catalog: Dict[str, Dict[str, Dict[str, dict]]], preferred_selection: Dict[str, str]) -> None:
        """Populate selector controls and apply the selected scalar dataset."""
        self.state.result_catalog = catalog

        groups = self._ordered_group_names(catalog)
        if not groups:
            self.clear_result_catalog()
            return

        preferred_group = preferred_selection.get("group")
        if preferred_group not in catalog:
            preferred_group = groups[0]

        self._block_selector_signals(True)
        try:
            self.tab.result_group_combo.clear()
            self.tab.result_group_combo.addItems(groups)
            self.tab.result_group_combo.setCurrentText(preferred_group)

            preferred_component = preferred_selection.get("component")
            component = self._populate_component_combo(preferred_group, preferred_component)

            preferred_mode = preferred_selection.get("mode")
            mode_key = self._populate_mode_combo(preferred_group, component, preferred_mode)

            self.tab.result_group_combo.setEnabled(True)
            self.tab.result_component_combo.setEnabled(bool(component))
            self.tab.result_mode_combo.setEnabled(bool(mode_key))
        finally:
            self._block_selector_signals(False)

        self._apply_selection(preferred_group, component, mode_key)

    def _populate_component_combo(self, group: str, preferred_component: Optional[str]) -> str:
        """Populate component combo for selected group and return active component."""
        components_map = self.state.result_catalog.get(group, {})
        components = self._ordered_component_names(group, components_map.keys())

        self.tab.result_component_combo.clear()
        self.tab.result_component_combo.addItems(components)

        if not components:
            self.tab.result_component_combo.setEnabled(False)
            return ""

        selected_component = preferred_component if preferred_component in components_map else components[0]
        self.tab.result_component_combo.setCurrentText(selected_component)
        self.tab.result_component_combo.setEnabled(True)
        return selected_component

    def _populate_mode_combo(self, group: str, component: str, preferred_mode: Optional[str]) -> str:
        """Populate mode combo for selected group/component and return active mode key."""
        mode_map = self.state.result_catalog.get(group, {}).get(component, {})
        mode_keys = self._ordered_mode_keys(mode_map.keys())

        self.tab.result_mode_combo.clear()
        for mode_key in mode_keys:
            self.tab.result_mode_combo.addItem(
                self.MODE_LABELS.get(mode_key, mode_key),
                mode_key,
            )

        if not mode_keys:
            self.tab.result_mode_combo.setEnabled(False)
            return ""

        selected_mode = preferred_mode if preferred_mode in mode_map else mode_keys[0]
        mode_index = max(0, self.tab.result_mode_combo.findData(selected_mode))
        self.tab.result_mode_combo.setCurrentIndex(mode_index)
        self.tab.result_mode_combo.setEnabled(True)
        return selected_mode

    def _get_current_selection(self) -> Optional[Tuple[str, str, str]]:
        """Return current selector values as (group, component, mode_key)."""
        group = self.tab.result_group_combo.currentText().strip()
        component = self.tab.result_component_combo.currentText().strip()
        mode_key = self.tab.result_mode_combo.currentData()
        if not mode_key:
            mode_key = self.MODE_KEYS_BY_LABEL.get(self.tab.result_mode_combo.currentText().strip())

        if not group or not component or not mode_key:
            return None
        if group not in self.state.result_catalog:
            return None
        if component not in self.state.result_catalog[group]:
            return None
        if mode_key not in self.state.result_catalog[group][component]:
            return None
        return group, component, mode_key

    def _apply_selection(self, group: str, component: str, mode_key: str) -> None:
        """Resolve selected dataset and apply it to the active mesh."""
        entry = self.state.result_catalog.get(group, {}).get(component, {}).get(mode_key)
        if not entry:
            return

        field_name = entry.get("field_name") or f"{group} - {component} - {self.MODE_LABELS.get(mode_key, mode_key)}"
        values = self._resolve_values(entry, field_name)
        if values is None:
            return

        self._update_scalar_controls(values)
        try:
            applied = self.visual_handler.apply_scalar_field(field_name, values)
            if applied:
                self.state.result_selection = {
                    "group": group,
                    "component": component,
                    "mode": mode_key,
                }
        except Exception as exc:
            print(f"Could not apply scalar field '{field_name}': {exc}")

    def _resolve_values(self, entry: dict, field_name: str) -> Optional[np.ndarray]:
        """Resolve selected entry into a 1D per-node NumPy array."""
        mesh = self.state.current_mesh or self.tab.current_mesh
        if mesh is not None and field_name in mesh.array_names:
            return np.asarray(mesh[field_name], dtype=float).reshape(-1)

        inline_values = entry.get("values")
        if inline_values is not None:
            return np.asarray(inline_values, dtype=float).reshape(-1)

        csv_filename = entry.get("csv_filename")
        if csv_filename:
            values = self._load_solver_array(
                self._active_solver,
                csv_filename,
                entry.get("csv_column"),
            )
            if values is not None:
                return values

        return None

    def _load_solver_array(
        self,
        solver,
        filename: str,
        csv_column: Optional[str] = None,
    ) -> Optional[np.ndarray]:
        """Load a NumPy array from solver output CSV."""
        try:
            if solver is None or not hasattr(solver, "output_directory"):
                return None

            base_dir = getattr(solver, "output_directory", None)
            if not base_dir:
                return None

            file_path = os.path.join(base_dir, filename)
            if not os.path.exists(file_path):
                return None

            df = pd.read_csv(file_path)
            if csv_column and csv_column in df.columns:
                values = df[csv_column].to_numpy(dtype=float, copy=True)
                return values.reshape(-1)

            candidate_cols = [
                col for col in df.columns
                if col.lower() not in {"nodeid", "x", "y", "z", "index"}
            ]
            if not candidate_cols:
                return None
            values = df[candidate_cols[0]].to_numpy(dtype=float, copy=True)
            return values.reshape(-1)
        except Exception as exc:
            print(f"Failed to load solver result array from {filename}: {exc}")
            return None

    def _update_scalar_controls(self, values: np.ndarray) -> None:
        """Set display tab scalar spinboxes based on provided values."""
        if values.size == 0:
            return

        scalar_min = float(np.min(values))
        scalar_max = float(np.max(values))

        if scalar_min == scalar_max:
            epsilon = abs(scalar_min) * 0.01 or 0.01
            scalar_min -= epsilon
            scalar_max += epsilon

        spin_min = self.tab.scalar_min_spin
        spin_max = self.tab.scalar_max_spin

        spin_min.blockSignals(True)
        spin_max.blockSignals(True)
        try:
            spin_min.setRange(scalar_min, scalar_max)
            spin_max.setRange(scalar_min, 1e30)
            spin_min.setValue(scalar_min)
            spin_max.setValue(scalar_max)
        finally:
            spin_min.blockSignals(False)
            spin_max.blockSignals(False)

    def _normalize_catalog(self, dataset_catalog) -> Dict[str, Dict[str, Dict[str, dict]]]:
        """Normalize catalog shape and mode keys."""
        if not dataset_catalog:
            return {}

        # Backward compatibility: a flat list of (field_name, csv_filename).
        if isinstance(dataset_catalog, Iterable) and not isinstance(dataset_catalog, dict):
            try:
                converted = {}
                for field_name, csv_filename in list(dataset_catalog):
                    converted.setdefault("Result", {}).setdefault("Magnitude", {})["max_over_time"] = {
                        "field_name": field_name,
                        "csv_filename": csv_filename,
                    }
                dataset_catalog = converted
            except Exception:
                return {}

        normalized: Dict[str, Dict[str, Dict[str, dict]]] = {}
        for group, components in dataset_catalog.items():
            if not isinstance(components, dict):
                continue
            for component, modes in components.items():
                if not isinstance(modes, dict):
                    continue
                for mode, entry in modes.items():
                    mode_key = mode
                    if mode_key not in self.MODE_LABELS:
                        mode_key = self.MODE_KEYS_BY_LABEL.get(mode_key, mode_key)
                    if not isinstance(entry, dict):
                        continue
                    normalized.setdefault(group, {}).setdefault(component, {})[mode_key] = dict(entry)
        return normalized

    def _ordered_group_names(self, catalog: Dict[str, Dict[str, Dict[str, dict]]]) -> list:
        """Return group names in preferred display order."""
        ordered = [name for name in self.GROUP_ORDER if name in catalog]
        for name in sorted(catalog.keys()):
            if name not in ordered:
                ordered.append(name)
        return ordered

    def _ordered_mode_keys(self, mode_keys: Iterable[str]) -> list:
        """Return mode keys in preferred display order."""
        keys = list(mode_keys)
        ordered = [key for key in self.MODE_ORDER if key in keys]
        for key in sorted(keys):
            if key not in ordered:
                ordered.append(key)
        return ordered

    def _ordered_component_names(self, group: str, component_names: Iterable[str]) -> list:
        """Return component names in preferred display order."""
        names = list(component_names)
        preferred = self.COMPONENT_ORDER.get(group, [])
        ordered = [name for name in preferred if name in names]
        for name in sorted(names):
            if name not in ordered:
                ordered.append(name)
        return ordered

    def _find_selection_by_field(
        self,
        catalog: Dict[str, Dict[str, Dict[str, dict]]],
        field_name: Optional[str],
    ) -> Optional[Dict[str, str]]:
        """Find selector tuple for a given field name."""
        if not field_name:
            return None

        for group, components in catalog.items():
            for component, modes in components.items():
                for mode_key, entry in modes.items():
                    if entry.get("field_name") == field_name:
                        return {
                            "group": group,
                            "component": component,
                            "mode": mode_key,
                        }
        return None

    def _block_selector_signals(self, block: bool) -> None:
        """Block/unblock combo-box signals while repopulating selections."""
        self.tab.result_group_combo.blockSignals(block)
        self.tab.result_component_combo.blockSignals(block)
        self.tab.result_mode_combo.blockSignals(block)

    def _build_time_point_catalog(self, mesh) -> Dict[str, Dict[str, Dict[str, dict]]]:
        """Create selector catalog from scalar arrays already attached to a mesh."""
        if mesh is None:
            return {}

        catalog: Dict[str, Dict[str, Dict[str, dict]]] = {}

        def first_existing(candidates):
            for candidate in candidates:
                if candidate in mesh.array_names:
                    return candidate
            return None

        def add(group, component, candidates):
            field_name = first_existing(candidates)
            if not field_name:
                return
            catalog.setdefault(group, {}).setdefault(component, {})["selected_time"] = {
                "field_name": field_name,
            }

        add("Von Mises", "Magnitude", ["SVM (MPa)"])
        add("Max Principal", "S1", ["S1 (MPa)"])
        add("Min Principal", "S3", ["S3 (MPa)"])
        add("Corrected Von Mises", "Magnitude", ["Corrected SVM (MPa)"])
        add("Plastic Strain", "Equivalent", ["Plastic Strain"])

        for component, candidates in [
            ("|U|", ["Deformation (mm)", "def_mag"]),
            ("UX", ["UX (mm)", "def_x"]),
            ("UY", ["UY (mm)", "def_y"]),
            ("UZ", ["UZ (mm)", "def_z"]),
        ]:
            add("Deformation", component, candidates)

        for component, candidates in [
            ("|V|", ["Velocity (mm/s)", "vel_mag"]),
            ("VX", ["VX (mm/s)", "vel_x"]),
            ("VY", ["VY (mm/s)", "vel_y"]),
            ("VZ", ["VZ (mm/s)", "vel_z"]),
        ]:
            add("Velocity", component, candidates)

        for component, candidates in [
            ("|A|", ["Acceleration (mm/s²)", "acc_mag"]),
            ("AX", ["AX (mm/s²)", "acc_x"]),
            ("AY", ["AY (mm/s²)", "acc_y"]),
            ("AZ", ["AZ (mm/s²)", "acc_z"]),
        ]:
            add("Acceleration", component, candidates)

        for component, candidates in [
            ("|F|", ["Force (N)", "f_mag"]),
            ("FX", ["FX (N)", "fx"]),
            ("FY", ["FY (N)", "fy"]),
            ("FZ", ["FZ (N)", "fz"]),
            ("|M|", ["Moment (N·mm)", "m_mag"]),
            ("MX", ["MX (N·mm)", "mx"]),
            ("MY", ["MY (N·mm)", "my"]),
            ("MZ", ["MZ (N·mm)", "mz"]),
        ]:
            add("Force/Moment", component, candidates)

        return catalog

    def _clear_catalog_fields_from_mesh(self, catalog: Dict[str, Dict[str, Dict[str, dict]]]) -> None:
        """Drop cached scalar arrays for incoming catalog fields before a new batch load."""
        mesh = self.state.current_mesh or self.tab.current_mesh
        if mesh is None:
            return

        for components in catalog.values():
            for modes in components.values():
                for entry in modes.values():
                    field_name = entry.get("field_name")
                    if not field_name:
                        continue
                    if field_name in mesh.array_names:
                        try:
                            mesh.point_data.pop(field_name)
                        except Exception:
                            try:
                                del mesh[field_name]
                            except Exception:
                                pass

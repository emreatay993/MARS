"""
Material profile dialog providing editors for temperature-dependent properties.
"""

import json
import os
from contextlib import contextmanager
from typing import Callable, Dict, Optional

import pandas as pd
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import (
    QApplication,
    QAbstractItemView,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QHBoxLayout,
    QInputDialog,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from core.data_models import MaterialProfileData


class EditableTableWidget(QTableWidget):
    """QTableWidget with copy/paste support and automatic blank-row management."""

    def __init__(
        self,
        headers,
        initial_rows=30,
        display_formats: Optional[Dict[str, Callable[[float], str]]] = None,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(0, len(headers), parent)
        self._headers = headers
        self._initial_rows = initial_rows
        self._display_formats = display_formats or {}
        self._updating = False

        self.setHorizontalHeaderLabels(headers)
        self.horizontalHeader().setStretchLastSection(True)
        self.verticalHeader().setVisible(False)
        self.setSelectionBehavior(QAbstractItemView.SelectItems)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setEditTriggers(QTableWidget.DoubleClicked | QTableWidget.EditKeyPressed | QTableWidget.AnyKeyPressed)

        self._ensure_min_rows()
        self.cellChanged.connect(self._on_cell_changed)

    @contextmanager
    def _block_updates(self):
        previous_state = self._updating
        self._updating = True
        self.blockSignals(True)
        try:
            yield
        finally:
            self.blockSignals(False)
            self._updating = previous_state

    def _format_value(self, column: int, value: float) -> str:
        header = self._headers[column]
        formatter = self._display_formats.get(header)
        if formatter is None:
            return f"{value:g}"
        if isinstance(formatter, str):
            if "{" in formatter:
                return formatter.format(value)
            return format(value, formatter)
        return formatter(value)

    def _set_item_value(self, row: int, column: int, value):
        item = self.item(row, column)
        if item is None:
            item = QTableWidgetItem()
            item.setTextAlignment(Qt.AlignCenter)
            super().setItem(row, column, item)

        if value is None or (isinstance(value, str) and value.strip() == ""):
            item.setText("")
            item.setData(Qt.UserRole, None)
            return

        try:
            float_value = float(value)
        except (TypeError, ValueError):
            item.setText(str(value))
            item.setData(Qt.UserRole, None)
            return

        item.setData(Qt.UserRole, float_value)
        item.setText(self._format_value(column, float_value))

    def _append_row(self, values=None):
        row_index = self.rowCount()
        super().insertRow(row_index)
        for col in range(self.columnCount()):
            if values is not None and col < len(values) and pd.notna(values[col]):
                self._set_item_value(row_index, col, values[col])
            else:
                self._set_item_value(row_index, col, None)

    def append_empty_row(self):
        with self._block_updates():
            self._append_row()

    def _ensure_min_rows(self):
        with self._block_updates():
            while self.rowCount() < self._initial_rows:
                self._append_row()

    def _row_is_blank(self, row: int) -> bool:
        for col in range(self.columnCount()):
            item = self.item(row, col)
            if item is not None and item.text().strip():
                return False
        return True

    def _row_has_data(self, row: int) -> bool:
        return not self._row_is_blank(row)

    def ensure_empty_row(self, force=False):
        if self._updating:
            return
        if self.rowCount() == 0:
            self.append_empty_row()
            return
        last_row = self.rowCount() - 1
        if force:
            if not self._row_is_blank(last_row):
                self.append_empty_row()
        else:
            if self._row_has_data(last_row):
                self.append_empty_row()
        self._ensure_min_rows()

    def _on_cell_changed(self, row, column):
        if self._updating:
            return
        item = self.item(row, column)
        if item is None:
            return
        text = item.text().strip()
        with self._block_updates():
            if text == "":
                item.setData(Qt.UserRole, None)
            else:
                try:
                    float_value = float(text)
                except ValueError:
                    item.setData(Qt.UserRole, None)
                else:
                    item.setData(Qt.UserRole, float_value)
                    item.setText(self._format_value(column, float_value))
        self.ensure_empty_row()

    def load_dataframe(self, dataframe: Optional[pd.DataFrame]):
        with self._block_updates():
            self.setRowCount(0)
            if dataframe is not None and not dataframe.empty:
                for _, row in dataframe.iterrows():
                    values = [row.get(header, None) for header in self._headers]
                    self._append_row(values)
            self._ensure_min_rows()
        self.ensure_empty_row(force=True)

    def to_dataframe(self) -> pd.DataFrame:
        data = []
        for row in range(self.rowCount()):
            row_values = []
            has_data = False
            for col in range(self.columnCount()):
                item = self.item(row, col)
                stored_value = item.data(Qt.UserRole) if item is not None else None
                if stored_value is not None:
                    row_values.append(stored_value)
                    has_data = True
                    continue

                text_value = item.text().strip() if item is not None else ""
                if text_value == "":
                    row_values.append(None)
                    continue

                try:
                    numeric_value = float(text_value)
                except ValueError as exc:
                    raise ValueError(
                        f"Invalid numeric entry '{text_value}' in column '{self._headers[col]}'"
                    ) from exc

                row_values.append(numeric_value)
                has_data = True

            if not has_data:
                continue
            data.append(row_values)

        if not data:
            return pd.DataFrame(columns=self._headers)

        df = pd.DataFrame(data, columns=self._headers)
        for header in self._headers:
            df[header] = pd.to_numeric(df[header], errors="raise")
        return df

    def remove_selected_rows(self):
        selection = self.selectedIndexes()
        if not selection:
            return
        rows = sorted({index.row() for index in selection}, reverse=True)
        with self._block_updates():
            for row in rows:
                self.removeRow(row)
            self._ensure_min_rows()
        self.ensure_empty_row(force=True)

    def copy_selection_to_clipboard(self):
        selection = self.selectedIndexes()
        if not selection:
            return
        top_row = min(index.row() for index in selection)
        left_col = min(index.column() for index in selection)
        bottom_row = max(index.row() for index in selection)
        right_col = max(index.column() for index in selection)

        rows_text = []
        for row in range(top_row, bottom_row + 1):
            values = []
            for col in range(left_col, right_col + 1):
                item = self.item(row, col)
                values.append("" if item is None else item.text())
            rows_text.append("\t".join(values))

        QApplication.clipboard().setText("\n".join(rows_text))

    def paste_from_clipboard(self):
        clipboard_text = QApplication.clipboard().text()
        if not clipboard_text:
            return
        selection = self.selectedIndexes()
        if selection:
            start_row = min(index.row() for index in selection)
            start_col = min(index.column() for index in selection)
        else:
            start_row = self.currentRow() if self.currentRow() >= 0 else 0
            start_col = self.currentColumn() if self.currentColumn() >= 0 else 0

        rows = clipboard_text.splitlines()
        with self._block_updates():
            for r_offset, line in enumerate(rows):
                columns = line.split("\t")
                row = start_row + r_offset
                while row >= self.rowCount():
                    self._append_row()
                for c_offset, value in enumerate(columns):
                    col = start_col + c_offset
                    if col >= self.columnCount():
                        continue
                    self._set_item_value(row, col, value.strip())
        self.ensure_empty_row(force=True)

    def keyPressEvent(self, event):
        if event.matches(QKeySequence.Copy):
            self.copy_selection_to_clipboard()
            return
        if event.matches(QKeySequence.Paste):
            self.paste_from_clipboard()
            return
        super().keyPressEvent(event)

class MaterialProfileDialog(QDialog):
    """Dialog to edit, import, and export material profile data."""

    def __init__(self, parent: Optional[QWidget] = None, material_data: Optional[MaterialProfileData] = None):
        super().__init__(parent)
        self.setWindowTitle("Material Profile")
        self.resize(900, 620)

        self._material_data = material_data if material_data is not None else MaterialProfileData.empty()
        self._material_data = MaterialProfileData(
            youngs_modulus=self._material_data.youngs_modulus.copy(),
            poisson_ratio=self._material_data.poisson_ratio.copy(),
            plastic_curves={temp: df.copy() for temp, df in self._material_data.plastic_curves.items()}
        )
        self._plastic_curves: Dict[float, pd.DataFrame] = {
            temp: df.copy() for temp, df in self._material_data.plastic_curves.items()
        }
        self._current_plastic_temp: Optional[float] = None
        self._result_data: MaterialProfileData = self._material_data
        self.base_directory = self._determine_base_directory(parent)

        self._build_ui()
        self._load_initial_data()
        self.import_profile_button.clicked.connect(self._import_material_profile)
        self.export_profile_button.clicked.connect(self._export_material_profile)

    def _build_ui(self):
        main_layout = QVBoxLayout(self)

        self.tab_widget = QTabWidget()
        self._build_youngs_tab()
        self._build_poisson_tab()
        self._build_plastic_tab()

        main_layout.addWidget(self.tab_widget)

        profile_buttons_layout = QHBoxLayout()
        self.import_profile_button = QPushButton("Import Material Profile")
        self.export_profile_button = QPushButton("Export Material Profile")
        profile_buttons_layout.addWidget(self.import_profile_button)
        profile_buttons_layout.addWidget(self.export_profile_button)
        profile_buttons_layout.addStretch()
        main_layout.addLayout(profile_buttons_layout)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self._handle_accept)
        self.button_box.rejected.connect(self.reject)

        main_layout.addWidget(self.button_box)

    def _determine_base_directory(self, parent: Optional[QWidget]) -> str:
        if parent is not None and hasattr(parent, "project_directory"):
            project_dir = getattr(parent, "project_directory")
            if project_dir and os.path.isdir(project_dir):
                return project_dir
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        if os.path.isdir(desktop):
            return desktop
        return os.path.expanduser("~")

    def _initial_directory(self) -> str:
        if self.base_directory and os.path.isdir(self.base_directory):
            return self.base_directory
        return self._determine_base_directory(self.parent())

    def _initial_path(self, suggested_name: str = "") -> str:
        directory = self._initial_directory()
        if suggested_name:
            return os.path.join(directory, suggested_name)
        return directory

    def _update_base_directory(self, path: str):
        if not path:
            return
        directory = os.path.dirname(path)
        if directory and os.path.isdir(directory):
            self.base_directory = directory

    # ---- Tab construction helpers ----
    def _build_youngs_tab(self):
        tab = QWidget()
        tab_layout = QVBoxLayout(tab)

        self.youngs_table = self._create_table(
            ["Temperature (°C)", "Young's Modulus [MPa]"],
            display_formats={"Temperature (°C)": "{:.2f}"}
        )

        controls = self._build_table_control_row(
            add_callback=lambda: self._add_row(self.youngs_table),
            remove_callback=lambda: self._remove_selected_rows(self.youngs_table),
            import_callback=lambda: self._import_table(self.youngs_table, ["Temperature (°C)", "Young's Modulus [MPa]"]),
            export_callback=lambda: self._export_table(self.youngs_table, "youngs_modulus.csv"),
        )

        tab_layout.addLayout(controls)
        tab_layout.addWidget(self.youngs_table)

        self.tab_widget.addTab(tab, "Young's Modulus")

    def _build_poisson_tab(self):
        tab = QWidget()
        tab_layout = QVBoxLayout(tab)

        self.poisson_table = self._create_table(
            ["Temperature (°C)", "Poisson's Ratio"],
            display_formats={"Temperature (°C)": "{:.2f}"}
        )

        controls = self._build_table_control_row(
            add_callback=lambda: self._add_row(self.poisson_table),
            remove_callback=lambda: self._remove_selected_rows(self.poisson_table),
            import_callback=lambda: self._import_table(self.poisson_table, ["Temperature (°C)", "Poisson's Ratio"]),
            export_callback=lambda: self._export_table(self.poisson_table, "poisson_ratio.csv"),
        )

        tab_layout.addLayout(controls)
        tab_layout.addWidget(self.poisson_table)

        self.tab_widget.addTab(tab, "Poisson's Ratio")

    def _build_plastic_tab(self):
        tab = QWidget()
        tab_layout = QHBoxLayout(tab)

        left_column = QVBoxLayout()
        self.plastic_temp_list = QListWidget()
        self.plastic_temp_list.currentRowChanged.connect(self._on_plastic_temperature_changed)
        left_column.addWidget(self.plastic_temp_list)

        temp_button_row = QHBoxLayout()
        add_temp_button = QPushButton("Add Temperature")
        remove_temp_button = QPushButton("Remove Temperature")
        add_temp_button.clicked.connect(self._add_plastic_temperature)
        remove_temp_button.clicked.connect(self._remove_plastic_temperature)
        temp_button_row.addWidget(add_temp_button)
        temp_button_row.addWidget(remove_temp_button)
        left_column.addLayout(temp_button_row)

        curve_button_row = QHBoxLayout()
        import_curve_button = QPushButton("Import Curve CSV")
        export_curve_button = QPushButton("Export Curve CSV")
        import_curve_button.clicked.connect(self._import_plastic_curve)
        export_curve_button.clicked.connect(self._export_plastic_curve)
        curve_button_row.addWidget(import_curve_button)
        curve_button_row.addWidget(export_curve_button)
        left_column.addLayout(curve_button_row)

        right_column = QVBoxLayout()
        self.plastic_table = self._create_table(
            ["Plastic Strain", "True Stress [MPa]"],
            display_formats={"Plastic Strain": "{:.4f}", "True Stress [MPa]": "{:.1f}"}
        )
        right_column.addWidget(self.plastic_table)

        tab_layout.addLayout(left_column, 1)
        tab_layout.addLayout(right_column, 2)

        self.tab_widget.addTab(tab, "Plastic Strain Curves")

    # ---- Table helpers ----
    @staticmethod
    def _create_table(headers, display_formats=None):
        return EditableTableWidget(headers, initial_rows=30, display_formats=display_formats)

    @staticmethod
    def _build_table_control_row(add_callback, remove_callback, import_callback, export_callback):
        row = QHBoxLayout()
        add_button = QPushButton("Add Row")
        remove_button = QPushButton("Remove Selected")
        import_button = QPushButton("Import CSV")
        export_button = QPushButton("Export CSV")
        add_button.clicked.connect(add_callback)
        remove_button.clicked.connect(remove_callback)
        import_button.clicked.connect(import_callback)
        export_button.clicked.connect(export_callback)
        row.addWidget(add_button)
        row.addWidget(remove_button)
        row.addStretch()
        row.addWidget(import_button)
        row.addWidget(export_button)
        return row

    def _add_row(self, table: EditableTableWidget):
        table.append_empty_row()

    def _remove_selected_rows(self, table: EditableTableWidget):
        table.remove_selected_rows()

    # ---- Import/export ----
    def _import_table(self, table: EditableTableWidget, expected_columns):
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Import Data",
            self._initial_directory(),
            "CSV Files (*.csv);;Text Files (*.txt);;All Files (*)"
        )
        if not filename:
            return
        try:
            df = pd.read_csv(filename)
        except Exception as exc:
            QMessageBox.warning(self, "Import Error", f"Failed to import file.\n\n{exc}")
            return

        missing = [col for col in expected_columns if col not in df.columns]
        if missing:
            QMessageBox.warning(
                self,
                "Import Error",
                f"The selected file is missing required columns:\n - " + "\n - ".join(missing)
            )
            return

        table.load_dataframe(df[expected_columns])
        self._update_base_directory(filename)

    def _export_table(self, table: EditableTableWidget, suggested_name: str):
        try:
            df = table.to_dataframe()
        except ValueError as exc:
            QMessageBox.warning(self, "Export Error", str(exc))
            return
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Export Data",
            self._initial_path(suggested_name),
            "CSV Files (*.csv);;All Files (*)"
        )
        if not filename:
            return
        try:
            df.to_csv(filename, index=False, encoding='utf-8-sig')
        except Exception as exc:
            QMessageBox.warning(self, "Export Error", f"Failed to export file.\n\n{exc}")
        else:
            self._update_base_directory(filename)

    def _import_plastic_curve(self):
        if self._current_plastic_temp is None:
            QMessageBox.information(self, "Select Temperature", "Select a temperature to import a curve.")
            return
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Import Plastic Curve",
            self._initial_directory(),
            "CSV Files (*.csv);;Text Files (*.txt);;All Files (*)"
        )
        if not filename:
            return
        try:
            df = pd.read_csv(filename)
        except Exception as exc:
            QMessageBox.warning(self, "Import Error", f"Failed to import plastic curve.\n\n{exc}")
            return

        expected = ["Plastic Strain", "True Stress [MPa]"]
        missing = [col for col in expected if col not in df.columns]
        if missing:
            QMessageBox.warning(
                self,
                "Import Error",
                f"The selected file is missing required columns:\n - " + "\n - ".join(missing)
            )
            return

        df = df[expected]
        self._plastic_curves[self._current_plastic_temp] = df.copy()
        self.plastic_table.load_dataframe(df)
        self._update_base_directory(filename)

    def _export_plastic_curve(self):
        if self._current_plastic_temp is None:
            QMessageBox.information(self, "Select Temperature", "Select a temperature to export a curve.")
            return
        try:
            df = self._sync_current_plastic_table()
        except ValueError as exc:
            QMessageBox.warning(self, "Export Error", str(exc))
            return
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Export Plastic Curve",
            self._initial_path(f"plastic_curve_{self._current_plastic_temp:.2f}.csv"),
            "CSV Files (*.csv);;All Files (*)"
        )
        if not filename:
            return
        try:
            df.to_csv(filename, index=False, encoding='utf-8-sig')
        except Exception as exc:
            QMessageBox.warning(self, "Export Error", f"Failed to export plastic curve.\n\n{exc}")
        else:
            self._update_base_directory(filename)

    # ---- Plastic temperature management ----
    def _add_plastic_temperature(self):
        temp, ok = QInputDialog.getDouble(self, "Add Temperature", "Temperature (°C):", decimals=4)
        if not ok:
            return
        if temp in self._plastic_curves:
            QMessageBox.information(self, "Exists", "A curve already exists for this temperature.")
            return
        self._plastic_curves[temp] = pd.DataFrame(columns=["Plastic Strain", "True Stress [MPa]"])
        self._populate_plastic_temperature_list(select_temperature=temp)

    def _remove_plastic_temperature(self):
        current_row = self.plastic_temp_list.currentRow()
        if current_row < 0:
            return
        temp_item = self.plastic_temp_list.item(current_row)
        if temp_item is None:
            return
        temp_value = float(temp_item.data(Qt.UserRole))
        self._plastic_curves.pop(temp_value, None)
        self._current_plastic_temp = None
        self._populate_plastic_temperature_list()
        self.plastic_table.load_dataframe(pd.DataFrame(columns=["Plastic Strain", "True Stress [MPa]"]))

    def _on_plastic_temperature_changed(self, row: int):
        self._sync_current_plastic_table()
        if row < 0:
            self._current_plastic_temp = None
            self.plastic_table.load_dataframe(pd.DataFrame(columns=["Plastic Strain", "True Stress [MPa]"]))
            return
        item = self.plastic_temp_list.item(row)
        if item is None:
            return
        temp_value = float(item.data(Qt.UserRole))
        self._current_plastic_temp = temp_value
        df = self._plastic_curves.get(temp_value, pd.DataFrame(columns=["Plastic Strain", "True Stress [MPa]"]))
        self.plastic_table.load_dataframe(df)

    def _populate_plastic_temperature_list(self, select_temperature: Optional[float] = None):
        self.plastic_temp_list.clear()
        for temp in sorted(self._plastic_curves.keys()):
            item = QListWidgetItem(f"{temp:.2f} °C")
            item.setData(Qt.UserRole, temp)
            self.plastic_temp_list.addItem(item)
        if select_temperature is not None:
            for index in range(self.plastic_temp_list.count()):
                if float(self.plastic_temp_list.item(index).data(Qt.UserRole)) == select_temperature:
                    self.plastic_temp_list.setCurrentRow(index)
                    return
        elif self.plastic_temp_list.count() > 0:
            self.plastic_temp_list.setCurrentRow(0)

    # ---- Data loading ----
    def _load_initial_data(self):
        self.youngs_table.load_dataframe(self._material_data.youngs_modulus)
        self.poisson_table.load_dataframe(self._material_data.poisson_ratio)
        self._populate_plastic_temperature_list()

    def _sync_current_plastic_table(self) -> pd.DataFrame:
        if self._current_plastic_temp is None:
            return pd.DataFrame(columns=["Plastic Strain", "True Stress [MPa]"])
        df = self.plastic_table.to_dataframe()
        self._plastic_curves[self._current_plastic_temp] = df
        return df

    def _collect_material_data(self) -> MaterialProfileData:
        youngs_df = self.youngs_table.to_dataframe()
        poisson_df = self.poisson_table.to_dataframe()

        plastic_curves: Dict[float, pd.DataFrame] = {}
        for temp, df in self._plastic_curves.items():
            if df is None or df.empty:
                continue
            plastic_curves[temp] = df.copy()

        return MaterialProfileData(
            youngs_modulus=youngs_df,
            poisson_ratio=poisson_df,
            plastic_curves=plastic_curves
        )

    def _material_profile_to_payload(self, profile: MaterialProfileData) -> Dict:
        payload = {
            "youngs_modulus": {
                "columns": list(profile.youngs_modulus.columns),
                "data": profile.youngs_modulus.values.tolist()
            },
            "poisson_ratio": {
                "columns": list(profile.poisson_ratio.columns),
                "data": profile.poisson_ratio.values.tolist()
            },
            "plastic_curves": []
        }

        for temp in sorted(profile.plastic_curves.keys()):
            curve_df = profile.plastic_curves[temp]
            payload["plastic_curves"].append({
                "temperature": float(temp),
                "columns": list(curve_df.columns),
                "data": curve_df.values.tolist()
            })

        return payload

    def _material_profile_from_payload(self, payload: Dict) -> MaterialProfileData:
        def build_dataframe(section: Dict, expected_columns):
            if not section:
                return pd.DataFrame(columns=expected_columns)
            columns = section.get("columns", expected_columns)
            data = section.get("data", [])
            df = pd.DataFrame(data, columns=columns)
            rename_map = {
                columns[i]: expected_columns[i]
                for i in range(min(len(columns), len(expected_columns)))
            }
            df = df.rename(columns=rename_map)
            missing = [col for col in expected_columns if col not in df.columns]
            if missing:
                raise ValueError(f"Missing expected columns: {', '.join(missing)}")
            df = df[expected_columns]
            for column in expected_columns:
                df[column] = pd.to_numeric(df[column], errors="raise")
            return df

        youngs_section = payload.get("youngs_modulus", {})
        poisson_section = payload.get("poisson_ratio", {})
        plastic_section = payload.get("plastic_curves", [])

        youngs_df = build_dataframe(youngs_section, ["Temperature (°C)", "Young's Modulus [MPa]"])
        poisson_df = build_dataframe(poisson_section, ["Temperature (°C)", "Poisson's Ratio"])

        plastic_curves: Dict[float, pd.DataFrame] = {}
        for entry in plastic_section:
            if not isinstance(entry, dict):
                raise ValueError("Invalid plastic curve entry in material profile.")
            temperature = entry.get("temperature")
            if temperature is None:
                raise ValueError("Plastic curve entry missing temperature value.")
            df = build_dataframe(entry, ["Plastic Strain", "True Stress [MPa]"])
            plastic_curves[float(temperature)] = df

        return MaterialProfileData(
            youngs_modulus=youngs_df,
            poisson_ratio=poisson_df,
            plastic_curves=plastic_curves
        )

    def _import_material_profile(self):
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Import Material Profile",
            self._initial_path("material_profile.json"),
            "JSON Files (*.json);;All Files (*)"
        )
        if not filename:
            return
        try:
            with open(filename, "r", encoding="utf-8-sig") as fh:
                payload = json.load(fh)
        except Exception as exc:
            QMessageBox.warning(self, "Import Error", f"Failed to import material profile.\n\n{exc}")
            return

        try:
            profile = self._material_profile_from_payload(payload)
        except ValueError as exc:
            QMessageBox.warning(self, "Import Error", str(exc))
            return

        self._material_data = MaterialProfileData(
            youngs_modulus=profile.youngs_modulus.copy(),
            poisson_ratio=profile.poisson_ratio.copy(),
            plastic_curves={temp: df.copy() for temp, df in profile.plastic_curves.items()}
        )
        self._plastic_curves = {temp: df.copy() for temp, df in profile.plastic_curves.items()}
        self._current_plastic_temp = None

        self.youngs_table.load_dataframe(profile.youngs_modulus)
        self.poisson_table.load_dataframe(profile.poisson_ratio)
        self._populate_plastic_temperature_list()
        if self.plastic_temp_list.count() == 0:
            self.plastic_table.load_dataframe(pd.DataFrame(columns=["Plastic Strain", "True Stress [MPa]"]))
        self._update_base_directory(filename)

    def _export_material_profile(self):
        try:
            self._sync_current_plastic_table()
            profile = self._collect_material_data()
        except ValueError as exc:
            QMessageBox.warning(self, "Export Error", str(exc))
            return

        payload = self._material_profile_to_payload(profile)
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Export Material Profile",
            self._initial_path("material_profile.json"),
            "JSON Files (*.json);;All Files (*)"
        )
        if not filename:
            return
        try:
            with open(filename, "w", encoding="utf-8-sig") as fh:
                json.dump(payload, fh, ensure_ascii=False, indent=2)
        except Exception as exc:
            QMessageBox.warning(self, "Export Error", f"Failed to export material profile.\n\n{exc}")
            return
        self._update_base_directory(filename)

    # ---- Dialog actions ----
    def _handle_accept(self):
        try:
            self._sync_current_plastic_table()
            self._result_data = self._collect_material_data()
        except ValueError as exc:
            QMessageBox.warning(self, "Validation Error", str(exc))
            return
        self.accept()

    def get_data(self) -> MaterialProfileData:
        return self._result_data

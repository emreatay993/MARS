"""
Material profile dialog providing editors for temperature-dependent properties.
"""

from typing import Dict, Optional

import pandas as pd
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QHBoxLayout,
    QInputDialog,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QAbstractItemView,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from core.data_models import MaterialProfileData


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

        self._build_ui()
        self._load_initial_data()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)

        self.tab_widget = QTabWidget()
        self._build_youngs_tab()
        self._build_poisson_tab()
        self._build_plastic_tab()

        main_layout.addWidget(self.tab_widget)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self._handle_accept)
        self.button_box.rejected.connect(self.reject)

        main_layout.addWidget(self.button_box)

    # ---- Tab construction helpers ----
    def _build_youngs_tab(self):
        tab = QWidget()
        tab_layout = QVBoxLayout(tab)

        self.youngs_table = self._create_table(["Temperature (°C)", "Young's Modulus [MPa]"])

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

        self.poisson_table = self._create_table(["Temperature (°C)", "Poisson's Ratio"])

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
        self.plastic_table = self._create_table(["Plastic Strain", "True Stress [MPa]"])
        right_column.addWidget(self.plastic_table)

        tab_layout.addLayout(left_column, 1)
        tab_layout.addLayout(right_column, 2)

        self.tab_widget.addTab(tab, "Plastic Strain Curves")

    # ---- Table helpers ----
    @staticmethod
    def _create_table(headers):
        table = QTableWidget(0, len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.horizontalHeader().setStretchLastSection(True)
        table.verticalHeader().setVisible(False)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setEditTriggers(QTableWidget.DoubleClicked | QTableWidget.EditKeyPressed | QTableWidget.AnyKeyPressed)
        return table

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

    def _add_row(self, table: QTableWidget):
        table.insertRow(table.rowCount())

    def _remove_selected_rows(self, table: QTableWidget):
        selected = table.selectionModel().selectedRows()
        for index in sorted(selected, key=lambda idx: idx.row(), reverse=True):
            table.removeRow(index.row())

    # ---- Import/export ----
    def _import_table(self, table: QTableWidget, expected_columns):
        filename, _ = QFileDialog.getOpenFileName(
            self, "Import Data", "", "CSV Files (*.csv);;Text Files (*.txt);;All Files (*)"
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

        df = df[expected_columns]
        table.setRowCount(0)
        for _, row in df.iterrows():
            current_row = table.rowCount()
            table.insertRow(current_row)
            for col_index, column in enumerate(expected_columns):
                item = QTableWidgetItem(str(row[column]))
                item.setTextAlignment(Qt.AlignCenter)
                table.setItem(current_row, col_index, item)

    def _export_table(self, table: QTableWidget, suggested_name: str):
        try:
            df = self._table_to_dataframe(table)
        except ValueError as exc:
            QMessageBox.warning(self, "Export Error", str(exc))
            return
        filename, _ = QFileDialog.getSaveFileName(
            self, "Export Data", suggested_name, "CSV Files (*.csv);;All Files (*)"
        )
        if not filename:
            return
        try:
            df.to_csv(filename, index=False)
        except Exception as exc:
            QMessageBox.warning(self, "Export Error", f"Failed to export file.\n\n{exc}")

    def _import_plastic_curve(self):
        if self._current_plastic_temp is None:
            QMessageBox.information(self, "Select Temperature", "Select a temperature to import a curve.")
            return
        filename, _ = QFileDialog.getOpenFileName(
            self, "Import Plastic Curve", "", "CSV Files (*.csv);;Text Files (*.txt);;All Files (*)"
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
        self._load_plastic_curve_into_table(df)

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
            f"plastic_curve_{self._current_plastic_temp:.2f}.csv",
            "CSV Files (*.csv);;All Files (*)"
        )
        if not filename:
            return
        try:
            df.to_csv(filename, index=False)
        except Exception as exc:
            QMessageBox.warning(self, "Export Error", f"Failed to export plastic curve.\n\n{exc}")

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
        self.plastic_table.setRowCount(0)

    def _on_plastic_temperature_changed(self, row: int):
        self._sync_current_plastic_table()
        if row < 0:
            self._current_plastic_temp = None
            self.plastic_table.setRowCount(0)
            return
        item = self.plastic_temp_list.item(row)
        if item is None:
            return
        temp_value = float(item.data(Qt.UserRole))
        self._current_plastic_temp = temp_value
        df = self._plastic_curves.get(temp_value, pd.DataFrame(columns=["Plastic Strain", "True Stress [MPa]"]))
        self._load_plastic_curve_into_table(df)

    def _populate_plastic_temperature_list(self, select_temperature: Optional[float] = None):
        self.plastic_temp_list.clear()
        for temp in sorted(self._plastic_curves.keys()):
            item = QListWidgetItem(f"{temp:.4f} °C")
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
        self._load_dataframe_into_table(self.youngs_table, self._material_data.youngs_modulus)
        self._load_dataframe_into_table(self.poisson_table, self._material_data.poisson_ratio)
        self._populate_plastic_temperature_list()

    @staticmethod
    def _load_dataframe_into_table(table: QTableWidget, dataframe: pd.DataFrame):
        table.setRowCount(0)
        if dataframe is None or dataframe.empty:
            return
        for _, row in dataframe.iterrows():
            current_row = table.rowCount()
            table.insertRow(current_row)
            for col_index, column in enumerate(dataframe.columns):
                item = QTableWidgetItem(str(row[column]))
                item.setTextAlignment(Qt.AlignCenter)
                table.setItem(current_row, col_index, item)

    def _load_plastic_curve_into_table(self, dataframe: pd.DataFrame):
        self.plastic_table.setRowCount(0)
        if dataframe is None or dataframe.empty:
            return
        for _, row in dataframe.iterrows():
            current_row = self.plastic_table.rowCount()
            self.plastic_table.insertRow(current_row)
            for col_index, column in enumerate(dataframe.columns):
                item = QTableWidgetItem(str(row[column]))
                item.setTextAlignment(Qt.AlignCenter)
                self.plastic_table.setItem(current_row, col_index, item)

    # ---- Data collection ----
    def _table_to_dataframe(self, table: QTableWidget):
        headers = [table.horizontalHeaderItem(col).text() for col in range(table.columnCount())]
        data = []
        for row in range(table.rowCount()):
            row_values = []
            blank = True
            for col in range(table.columnCount()):
                item = table.item(row, col)
                value = item.text().strip() if item else ""
                if value != "":
                    blank = False
                row_values.append(value)
            if blank:
                continue
            data.append(row_values)

        if not data:
            return pd.DataFrame(columns=headers)

        df = pd.DataFrame(data, columns=headers)
        for column in headers:
            try:
                df[column] = pd.to_numeric(df[column], errors='raise')
            except Exception as exc:
                raise ValueError(f"Column '{column}' contains invalid numeric entries.") from exc
        return df

    def _sync_current_plastic_table(self) -> pd.DataFrame:
        if self._current_plastic_temp is None:
            return pd.DataFrame(columns=["Plastic Strain", "True Stress [MPa]"])
        df = self._table_to_dataframe(self.plastic_table)
        self._plastic_curves[self._current_plastic_temp] = df
        return df

    def _collect_material_data(self) -> MaterialProfileData:
        youngs_df = self._table_to_dataframe(self.youngs_table)
        poisson_df = self._table_to_dataframe(self.poisson_table)

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

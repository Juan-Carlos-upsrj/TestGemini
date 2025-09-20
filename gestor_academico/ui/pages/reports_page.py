import csv
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
                               QTableWidget, QPushButton, QHeaderView, QTableWidgetItem,
                               QFileDialog, QMessageBox)
from typing import List, Dict, Any

from gestor_academico.core import logic, reporting

class ReportsPage(QWidget):
    """
    The main widget for the Reports ('Reportes') page.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.report_data = [] # To store the currently displayed report data

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        title = QLabel("Generación de Reportes")
        title.setObjectName("HeaderTitle")
        main_layout.addWidget(title)

        controls_layout = QHBoxLayout()
        self.group_combo = QComboBox()
        self.report_type_combo = QComboBox()
        self.report_type_combo.addItems(["Resumen de Calificaciones", "Resumen de Asistencia"])
        self.generate_button = QPushButton("Generar Reporte")
        self.generate_button.setObjectName("PrimaryButton")

        controls_layout.addWidget(QLabel("Grupo:"))
        controls_layout.addWidget(self.group_combo, 1)
        controls_layout.addSpacing(20)
        controls_layout.addWidget(QLabel("Tipo de Reporte:"))
        controls_layout.addWidget(self.report_type_combo, 1)
        controls_layout.addWidget(self.generate_button)
        controls_layout.addStretch(2)
        main_layout.addLayout(controls_layout)

        self.report_table = QTableWidget()
        self.report_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.report_table.verticalHeader().setVisible(False)
        main_layout.addWidget(self.report_table)

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        self.export_button = QPushButton("Exportar a CSV")
        self.export_button.setEnabled(False) # Disabled until a report is generated
        button_layout.addWidget(self.export_button)
        main_layout.addLayout(button_layout)

        # Connect signals
        self.generate_button.clicked.connect(self._generate_report)
        self.export_button.clicked.connect(self._export_to_csv)

    def refresh_data(self):
        """Refreshes the group list in the combo box."""
        current_group = self.group_combo.currentText()
        self.group_combo.clear()
        try:
            groups = logic.get_group_list()
            self.group_combo.addItems(groups)
            if current_group in groups:
                self.group_combo.setCurrentText(current_group)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudieron cargar los grupos: {e}")

    def _generate_report(self):
        """Generates and displays the selected report."""
        group_name = self.group_combo.currentText()
        report_type = self.report_type_combo.currentText()

        if not group_name:
            QMessageBox.warning(self, "Atención", "Por favor, seleccione un grupo.")
            return

        try:
            if report_type == "Resumen de Calificaciones":
                self.report_data = reporting.generate_grades_report(group_name)
                headers = ["ID Estudiante", "Nombre", "Calificación Final"]
                data_keys = ["student_id", "student_name", "final_grade"]
            else: # Resumen de Asistencia
                self.report_data = reporting.generate_attendance_report(group_name)
                headers = ["ID Estudiante", "Nombre", "% Asistencia", "En Riesgo"]
                data_keys = ["student_id", "student_name", "attendance_percentage", "is_at_risk"]

            self._populate_report_table(headers, data_keys)
            self.export_button.setEnabled(True)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo generar el reporte: {e}")
            self.report_table.setRowCount(0)
            self.export_button.setEnabled(False)

    def _populate_report_table(self, headers: List[str], data_keys: List[str]):
        """Fills the table with the generated report data."""
        self.report_table.setColumnCount(len(headers))
        self.report_table.setHorizontalHeaderLabels(headers)
        self.report_table.setRowCount(len(self.report_data))

        for row_idx, row_data in enumerate(self.report_data):
            for col_idx, key in enumerate(data_keys):
                item_value = str(row_data.get(key, ''))
                self.report_table.setItem(row_idx, col_idx, QTableWidgetItem(item_value))

        self.report_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)

    def _export_to_csv(self):
        """Exports the current report data to a CSV file."""
        if not self.report_data:
            QMessageBox.warning(self, "Atención", "No hay datos en el reporte para exportar.")
            return

        group_name = self.group_combo.currentText()
        report_type = self.report_type_combo.currentText().replace(" ", "_")
        default_filename = f"reporte_{group_name}_{report_type}.csv"

        file_path, _ = QFileDialog.getSaveFileName(self, "Guardar Reporte", default_filename,
                                                   "CSV Files (*.csv);;All Files (*)")

        if not file_path:
            return # User cancelled

        try:
            headers = list(self.report_data[0].keys())
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=headers)
                writer.writeheader()
                writer.writerows(self.report_data)

            QMessageBox.information(self, "Éxito", f"El reporte ha sido exportado exitosamente a:\n{file_path}")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo exportar el reporte: {e}")

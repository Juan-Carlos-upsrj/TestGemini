from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
                               QTableWidget, QPushButton, QHeaderView, QTableWidgetItem,
                               QMessageBox, QInputDialog)
from PySide6.QtCore import Qt

from gestor_academico.core import logic
from gestor_academico.ui.dialogs.grade_entry_dialog import GradeEntryDialog

class GradesPage(QWidget):
    """
    The main widget for the Grades ('Calificaciones') page.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_assignments = []

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        title = QLabel("Gestión de Calificaciones")
        title.setObjectName("HeaderTitle")
        main_layout.addWidget(title)

        controls_layout = QHBoxLayout()
        self.group_combo = QComboBox()
        self.period_combo = QComboBox()

        controls_layout.addWidget(QLabel("Grupo:"))
        controls_layout.addWidget(self.group_combo, 1)
        controls_layout.addSpacing(20)
        controls_layout.addWidget(QLabel("Periodo:"))
        controls_layout.addWidget(self.period_combo, 1)
        controls_layout.addStretch(2)
        main_layout.addLayout(controls_layout)

        self.assignments_table = QTableWidget()
        self.assignments_table.setColumnCount(3)
        self.assignments_table.setHorizontalHeaderLabels(["Actividad", "Ponderación (%)", "Acciones"])
        header = self.assignments_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.assignments_table.verticalHeader().setVisible(False)
        self.assignments_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        main_layout.addWidget(self.assignments_table)

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        self.add_assignment_button = QPushButton("Añadir Actividad")
        button_layout.addWidget(self.add_assignment_button)
        main_layout.addLayout(button_layout)

        # Connect signals
        self.group_combo.currentTextChanged.connect(self.refresh_periods)
        self.period_combo.currentIndexChanged.connect(self.refresh_assignments_table) # Use index changed to get period_id
        self.add_assignment_button.clicked.connect(self._on_add_assignment)

    def refresh_data(self):
        """Public method to refresh all data on the page."""
        current_group = self.group_combo.currentText()
        self.group_combo.clear()
        try:
            groups = logic.get_group_list()
            self.group_combo.addItems(groups)
            if current_group in groups:
                self.group_combo.setCurrentText(current_group)
            else:
                self.refresh_periods() # Trigger refresh if group changed or is new
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudieron cargar los grupos: {e}")

    def refresh_periods(self):
        """Refreshes the grading periods combo box based on the selected group."""
        self.period_combo.clear()
        group_name = self.group_combo.currentText()
        if not group_name:
            return
        try:
            periods = logic.get_grading_periods(group_name)
            for period in periods:
                self.period_combo.addItem(period["name"], userData=period["id"])
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudieron cargar los periodos: {e}")

    def refresh_assignments_table(self):
        """Refreshes the assignments table based on the selected group and period."""
        self.assignments_table.setRowCount(0)
        group_name = self.group_combo.currentText()
        period_id = self.period_combo.currentData()
        if not group_name or not period_id:
            return

        try:
            periods = logic.get_grading_periods(group_name)
            self.current_assignments = []
            for p in periods:
                if p["id"] == period_id:
                    self.current_assignments = p.get("assignments", [])
                    break

            self.assignments_table.setRowCount(len(self.current_assignments))
            for row, assignment in enumerate(self.current_assignments):
                self.assignments_table.setItem(row, 0, QTableWidgetItem(assignment["name"]))
                self.assignments_table.setItem(row, 1, QTableWidgetItem(str(assignment["weight"])))

                edit_button = QPushButton("Registrar Calificaciones")
                edit_button.clicked.connect(lambda ch, a=assignment: self._on_enter_grades(a))
                self.assignments_table.setCellWidget(row, 2, edit_button)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudieron cargar las actividades: {e}")

    def _on_add_assignment(self):
        group_name = self.group_combo.currentText()
        period_id = self.period_combo.currentData()
        if not group_name or not period_id:
            QMessageBox.warning(self, "Atención", "Por favor, seleccione un grupo y un periodo.")
            return

        name, ok = QInputDialog.getText(self, "Añadir Actividad", "Nombre de la actividad:")
        if not (ok and name): return

        weight, ok = QInputDialog.getInt(self, "Añadir Actividad", "Ponderación (%):", value=10, min=0, max=100)
        if not ok: return

        try:
            logic.add_assignment(group_name, period_id, name, float(weight))
            self.refresh_assignments_table()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo añadir la actividad: {e}")

    def _on_enter_grades(self, assignment):
        group_name = self.group_combo.currentText()
        period_id = self.period_combo.currentData()

        try:
            students = logic.get_students_for_group(group_name)
            dialog = GradeEntryDialog(assignment["name"], students, assignment["grades"], self)
            if dialog.exec():
                new_grades = dialog.get_grades()
                logic.save_grades_for_assignment(group_name, period_id, assignment["id"], new_grades)
                self.refresh_assignments_table() # Refresh data
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo registrar las calificaciones: {e}")

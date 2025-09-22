from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
                               QTableWidget, QPushButton, QHeaderView, QTableWidgetItem,
                               QMessageBox, QInputDialog)
from typing import List, Dict

from gestor_academico.core import logic
from gestor_academico.ui.dialogs.grade_entry_dialog import GradeEntryDialog

class GradesPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_assignments = []

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

        self.assignments_stack = QStackedWidget()
        self.assignments_table = QTableWidget()
        self.assignments_table.setColumnCount(3)
        self.assignments_table.setHorizontalHeaderLabels(["Actividad", "Ponderación (%)", "Acciones"])
        header = self.assignments_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.assignments_table.verticalHeader().setVisible(False)
        self.assignments_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        self.empty_assignments_label = QLabel("No hay actividades en este periodo.\nAñade una para empezar.")
        self.empty_assignments_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_assignments_label.setStyleSheet("color: #6b7280; font-style: italic;")

        self.assignments_stack.addWidget(self.assignments_table)
        self.assignments_stack.addWidget(self.empty_assignments_label)
        main_layout.addWidget(self.assignments_stack)

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        self.add_assignment_button = QPushButton("Añadir Actividad")
        button_layout.addWidget(self.add_assignment_button)
        main_layout.addLayout(button_layout)

        self.group_combo.currentTextChanged.connect(self.refresh_periods)
        self.period_combo.currentIndexChanged.connect(self.refresh_assignments_table)
        self.add_assignment_button.clicked.connect(self._on_add_assignment)

    def refresh_data(self):
        current_group = self.group_combo.currentText()
        self.group_combo.clear()
        try:
            self.group_combo.addItems(logic.get_group_list())
            if current_group in [self.group_combo.itemText(i) for i in range(self.group_combo.count())]:
                self.group_combo.setCurrentText(current_group)
            else:
                self.refresh_periods()
        except Exception as e:
            print(f"ERROR in refresh_data (grades): {e}")
            QMessageBox.critical(self, "Error", f"{e}")

    def refresh_periods(self):
        self.period_combo.clear()
        group_name = self.group_combo.currentText()
        if not group_name: return
        try:
            periods = logic.get_grading_periods(group_name)
            for period in periods:
                self.period_combo.addItem(period["name"], userData=period["id"])
        except Exception as e:
            print(f"ERROR in refresh_periods (grades): {e}")
            QMessageBox.critical(self, "Error", f"{e}")

    def refresh_assignments_table(self):
        group_name = self.group_combo.currentText()
        period_id = self.period_combo.currentData()
        if not group_name or not period_id:
            self.assignments_stack.setCurrentWidget(self.empty_assignments_label)
            return
        try:
            periods = logic.get_grading_periods(group_name)
            self.current_assignments = next((p.get("assignments", []) for p in periods if p["id"] == period_id), [])

            if self.current_assignments:
                self.assignments_stack.setCurrentWidget(self.assignments_table)
                self.assignments_table.setRowCount(len(self.current_assignments))
                for row, assignment in enumerate(self.current_assignments):
                    self.assignments_table.setItem(row, 0, QTableWidgetItem(assignment["name"]))
                    self.assignments_table.setItem(row, 1, QTableWidgetItem(str(assignment["weight"])))
                    edit_button = QPushButton("Registrar Calificaciones")
                    edit_button.clicked.connect(lambda ch, a=assignment: self._on_enter_grades(a))
                    self.assignments_table.setCellWidget(row, 2, edit_button)
            else:
                self.assignments_stack.setCurrentWidget(self.empty_assignments_label)
        except Exception as e:
            print(f"ERROR in refresh_assignments_table: {e}")
            QMessageBox.critical(self, "Error", f"{e}")

    def _on_add_assignment(self):
        group_name = self.group_combo.currentText()
        period_id = self.period_combo.currentData()
        if not group_name or not period_id:
            QMessageBox.warning(self, "Atención", "Por favor, seleccione un grupo y un periodo.")
            return
        name, ok = QInputDialog.getText(self, "Añadir Actividad", "Nombre de la actividad:")
        if not (ok and name): return
        weight, ok = QInputDialog.getInt(self, "Añadir Actividad", "Ponderación (%):", 10, 0, 100)
        if not ok: return
        try:
            logic.add_assignment(group_name, period_id, name, float(weight))
            self.refresh_assignments_table()
        except Exception as e:
            print(f"ERROR in _on_add_assignment: {e}")
            QMessageBox.critical(self, "Error", f"{e}")

    def _on_enter_grades(self, assignment):
        group_name = self.group_combo.currentText()
        period_id = self.period_combo.currentData()
        try:
            students = logic.get_students_for_group(group_name)
            dialog = GradeEntryDialog(assignment["name"], students, assignment["grades"], self)
            if dialog.exec():
                new_grades = dialog.get_grades()
                logic.save_grades_for_assignment(group_name, period_id, assignment["id"], new_grades)
                self.refresh_assignments_table()
        except Exception as e:
            print(f"ERROR in _on_enter_grades: {e}")
            QMessageBox.critical(self, "Error", f"{e}")

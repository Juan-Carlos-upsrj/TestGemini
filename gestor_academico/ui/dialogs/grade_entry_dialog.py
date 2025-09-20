from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QTableWidget, QDoubleSpinBox,
                               QPushButton, QDialogButtonBox, QHeaderView, QTableWidgetItem)
from PySide6.QtCore import Qt
from typing import Dict, List, Any

class GradeEntryDialog(QDialog):
    """
    A dialog for entering or editing grades for a specific assignment.
    """
    def __init__(self, assignment_name: str, students: List[Dict[str, Any]], grades: Dict[str, float], parent=None):
        super().__init__(parent)
        self.students = students

        self.setWindowTitle(f"Calificaciones para: {assignment_name}")
        self.setMinimumWidth(400)

        # Main layout
        layout = QVBoxLayout(self)

        # Title
        title_label = QLabel(f"Registrar calificaciones para: <b>{assignment_name}</b>")
        layout.addWidget(title_label)

        # Grades table
        self.grades_table = QTableWidget()
        self.grades_table.setColumnCount(2)
        self.grades_table.setHorizontalHeaderLabels(["Estudiante", "Calificación"])
        self.grades_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.grades_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.grades_table.verticalHeader().setVisible(False)
        self.populate_table(grades)
        layout.addWidget(self.grades_table)

        # OK and Cancel buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def populate_table(self, grades: Dict[str, float]):
        """Fills the table with student names and grade input widgets."""
        self.grades_table.setRowCount(len(self.students))
        for row, student in enumerate(self.students):
            student_id = student["id"]

            # Student name item (not editable)
            name_item = QTableWidgetItem(student["name"])
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            name_item.setData(Qt.ItemDataRole.UserRole, student_id) # Store ID

            # Grade spinbox
            grade_spinbox = QDoubleSpinBox()
            grade_spinbox.setRange(0.0, 100.0)
            grade_spinbox.setValue(float(grades.get(student_id, 0.0)))

            self.grades_table.setItem(row, 0, name_item)
            self.grades_table.setCellWidget(row, 1, grade_spinbox)

    def get_grades(self) -> Dict[str, float]:
        """Retrieves the grades from the table."""
        grades = {}
        for row in range(self.grades_table.rowCount()):
            student_id = self.grades_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
            grade_spinbox = self.grades_table.cellWidget(row, 1)
            grades[student_id] = grade_spinbox.value()
        return grades

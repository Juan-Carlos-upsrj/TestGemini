from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QTableWidget, QDoubleSpinBox, QDialogButtonBox, QHeaderView, QTableWidgetItem
from typing import Dict, List
class GradeEntryDialog(QDialog):
    def __init__(self, assignment_name: str, students: List[Dict], grades: Dict, parent=None):
        super().__init__(parent)
        self.students = students
        self.setWindowTitle(f"Calificaciones para: {assignment_name}")
        self.setMinimumWidth(400)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(f"Registrar calificaciones para: <b>{assignment_name}</b>"))
        self.grades_table = QTableWidget()
        self.grades_table.setColumnCount(2)
        self.grades_table.setHorizontalHeaderLabels(["Estudiante", "Calificación"])
        self.grades_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.populate_table(grades)
        layout.addWidget(self.grades_table)
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    def populate_table(self, grades: Dict):
        self.grades_table.setRowCount(len(self.students))
        for row, student in enumerate(self.students):
            student_id = student["id"]
            name_item = QTableWidgetItem(student["name"])
            name_item.setData(0x0100, student_id) # UserRole
            self.grades_table.setItem(row, 0, name_item)
            grade_spinbox = QDoubleSpinBox()
            grade_spinbox.setRange(0.0, 100.0)
            grade_spinbox.setValue(float(grades.get(student_id, 0.0)))
            self.grades_table.setCellWidget(row, 1, grade_spinbox)
    def get_grades(self) -> Dict:
        grades = {}
        for row in range(self.grades_table.rowCount()):
            student_id = self.grades_table.item(row, 0).data(0x0100)
            grades[student_id] = self.grades_table.cellWidget(row, 1).value()
        return grades

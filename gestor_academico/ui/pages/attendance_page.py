from PySide6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QLabel, QComboBox,
                               QCalendarWidget, QTableWidget, QProgressBar, QPushButton,
                               QTableWidgetItem, QHeaderView, QMessageBox)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QColor

from gestor_academico.core import logic
from gestor_academico.ui.widgets.status_combobox import StatusComboBox

class AttendancePage(QWidget):
    """
    The main widget for the Attendance Registration page.
    """
    def __init__(self, parent=None):
        super().__init__(parent)

        # Main layout
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(20)

        # Create left and right columns
        self.left_column = self._create_left_column()
        self.right_column = self._create_right_column()

        self.main_layout.addWidget(self.left_column, 1) # Proportion 1
        self.main_layout.addWidget(self.right_column, 2) # Proportion 2

        # Connect signals now that all widgets are created
        self.group_combo.currentTextChanged.connect(self._update_attendance_view)
        self.calendar.selectionChanged.connect(self._update_attendance_view)

        # Initial data load
        self.refresh_data()

    def _create_left_column(self) -> QWidget:
        """Creates the left column with group selector and calendar."""
        left_widget = QWidget()
        left_widget.setObjectName("Surface")
        layout = QVBoxLayout(left_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        layout.setAlignment(Qt.AlignTop)

        group_label = QLabel("Grupo")
        self.group_combo = QComboBox()

        layout.addWidget(group_label)
        layout.addWidget(self.group_combo)

        self.calendar = QCalendarWidget()
        self.calendar.setSelectedDate(QDate.currentDate())
        layout.addWidget(self.calendar)

        return left_widget

    def _create_right_column(self) -> QWidget:
        """Creates the right column with the student attendance table."""
        right_widget = QWidget()
        right_widget.setObjectName("Surface")
        layout = QVBoxLayout(right_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        self.title_label = QLabel("Asistencia del Grupo...")
        self.title_label.setObjectName("HeaderTitle")
        self.title_label.setStyleSheet("font-size: 20px;")
        layout.addWidget(self.title_label)

        self.attendance_table = QTableWidget()
        self.attendance_table.setColumnCount(3)
        self.attendance_table.setHorizontalHeaderLabels(["Estudiante", "Estado", "Notas"])
        self.attendance_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.attendance_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.attendance_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.attendance_table.verticalHeader().setVisible(False)
        layout.addWidget(self.attendance_table)

        summary_widget = self._create_summary_section()
        layout.addWidget(summary_widget)

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        self.cancel_button = QPushButton("Cancelar")
        self.save_button = QPushButton("Guardar Cambios")
        self.save_button.setObjectName("PrimaryButton")
        self.save_button.clicked.connect(self._save_attendance)
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.save_button)
        layout.addLayout(button_layout)

        return right_widget

    def _create_summary_section(self) -> QWidget:
        summary_widget = QWidget()
        layout = QVBoxLayout(summary_widget)
        layout.setContentsMargins(0, 10, 0, 0)

        percent_layout = QHBoxLayout()
        summary_label = QLabel("Resumen de Asistencia")
        self.summary_percent_label = QLabel("100%")
        self.summary_percent_label.setStyleSheet("font-weight: bold;")
        percent_layout.addWidget(summary_label)
        percent_layout.addStretch()
        percent_layout.addWidget(self.summary_percent_label)
        layout.addLayout(percent_layout)

        self.summary_progress_bar = QProgressBar()
        self.summary_progress_bar.setValue(100)
        self.summary_progress_bar.setTextVisible(False)
        layout.addWidget(self.summary_progress_bar)

        self.summary_text_label = QLabel("Todos los estudiantes presentes.")
        self.summary_text_label.setStyleSheet("font-size: 12px; color: #666;")
        layout.addWidget(self.summary_text_label)
        return summary_widget

    def refresh_data(self):
        """Public method to refresh all data, starting with the group list."""
        current_group = self.group_combo.currentText()
        self.group_combo.clear()
        try:
            groups = logic.get_group_list()
            self.group_combo.addItems(groups)
            if current_group in groups:
                self.group_combo.setCurrentText(current_group)
            # This will trigger _update_attendance_view via the signal if the text changes,
            # or we call it manually if it's the same.
            self._update_attendance_view()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudieron cargar los grupos: {e}")

    def _update_attendance_view(self):
        """Loads and displays attendance data for the selected group and date."""
        group_name = self.group_combo.currentText()
        selected_date = self.calendar.selectedDate().toString("yyyy-MM-dd")

        if not group_name:
            self.attendance_table.setRowCount(0)
            self.title_label.setText("Seleccione un grupo")
            return

        self.title_label.setText(f"Asistencia del {group_name} - {self.calendar.selectedDate().toString('dd MMMM yyyy')}")

        try:
            students = logic.get_students_for_group(group_name)
            attendance_data = logic.get_attendance_for_date(group_name, selected_date)

            self.attendance_table.setRowCount(len(students))

            for row, student in enumerate(students):
                student_id = student["id"]
                student_name = student["name"]

                # Store student ID in the first item for later retrieval
                name_item = QTableWidgetItem(student_name)
                name_item.setData(Qt.ItemDataRole.UserRole, student_id)
                name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)

                status_combo = StatusComboBox()
                notes_item = QTableWidgetItem()

                # Set initial status and notes
                status = ""
                if student_id in attendance_data:
                    status = attendance_data[student_id]["status"]
                    status_combo.set_selected_status(status)
                    notes_item.setText(attendance_data[student_id]["notes"])

                self.attendance_table.setItem(row, 0, name_item)
                self.attendance_table.setCellWidget(row, 1, status_combo)
                self.attendance_table.setItem(row, 2, notes_item)

                # Dynamic row styling for 'Ausente'
                self._style_row_by_status(row, status)
                status_combo.currentTextChanged.connect(lambda text, r=row: self._style_row_by_status(r, text))


        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo cargar la asistencia: {e}")
            self.attendance_table.setRowCount(0)

    def _style_row_by_status(self, row, status):
        """Applies a background color to a row based on attendance status."""
        color = None
        if status == "Ausente":
            color = QColor("#fef2f2") # Light red for 'Ausente'

        for col in range(self.attendance_table.columnCount()):
            item = self.attendance_table.item(row, col)
            if item:
                if color:
                    item.setBackground(color)
                else:
                    # Reset to default background
                    item.setBackground(QColor(Qt.GlobalColor.transparent))

    def _save_attendance(self):
        """Saves the current state of the attendance table."""
        group_name = self.group_combo.currentText()
        target_date = self.calendar.selectedDate().toString("yyyy-MM-dd")

        if not group_name:
            QMessageBox.warning(self, "Atención", "Por favor, seleccione un grupo.")
            return

        records_to_save = []
        for row in range(self.attendance_table.rowCount()):
            student_id = self.attendance_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
            status_combo = self.attendance_table.cellWidget(row, 1)
            notes_item = self.attendance_table.item(row, 2)

            records_to_save.append({
                "student_id": student_id,
                "status": status_combo.get_selected_status(),
                "notes": notes_item.text() if notes_item else ""
            })

        try:
            logic.save_attendance_for_date(group_name, target_date, records_to_save)
            QMessageBox.information(self, "Éxito", f"La asistencia para el {target_date} ha sido guardada.")
            self._update_attendance_view() # Refresh view to confirm
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo guardar la asistencia: {e}")

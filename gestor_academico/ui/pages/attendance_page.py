from PySide6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QLabel, QComboBox,
                               QCalendarWidget, QTableWidget, QProgressBar, QPushButton,
                               QTableWidgetItem, QHeaderView, QMessageBox)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QColor, QTextCharFormat, QFont

from gestor_academico.core import logic
from gestor_academico.ui.widgets.status_combobox import StatusComboBox

class AttendancePage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(20)

        self.left_column = self._create_left_column()
        self.right_column = self._create_right_column()

        self.main_layout.addWidget(self.left_column, 1)
        self.main_layout.addWidget(self.right_column, 2)

        self.group_combo.currentTextChanged.connect(self.refresh_periods)
        self.period_combo.currentIndexChanged.connect(self._update_attendance_view)
        self.calendar.selectionChanged.connect(self._update_attendance_view)
        self.calendar.currentPageChanged.connect(self._update_attendance_view)

        self.refresh_data()

    def _create_left_column(self) -> QWidget:
        left_widget = QWidget()
        left_widget.setObjectName("Surface")
        layout = QVBoxLayout(left_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        layout.setAlignment(Qt.AlignTop)

        self.group_combo = QComboBox()
        layout.addWidget(QLabel("Grupo"))
        layout.addWidget(self.group_combo)

        self.period_combo = QComboBox()
        layout.addWidget(QLabel("Periodo para Resaltar:"))
        layout.addWidget(self.period_combo)

        self.calendar = QCalendarWidget()
        self.calendar.setSelectedDate(QDate.currentDate())
        layout.addWidget(self.calendar)

        return left_widget

    def _create_right_column(self) -> QWidget:
        right_widget = QWidget()
        right_widget.setObjectName("Surface")
        layout = QVBoxLayout(right_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        title_layout = QHBoxLayout()
        self.title_label = QLabel("Asistencia del Grupo...")
        self.title_label.setObjectName("HeaderTitle")
        self.title_label.setStyleSheet("font-size: 20px;")

        self.mark_all_present_button = QPushButton("Marcar Todos como Presentes")
        self.mark_all_present_button.clicked.connect(self._on_mark_all_present)

        title_layout.addWidget(self.title_label)
        title_layout.addStretch()
        title_layout.addWidget(self.mark_all_present_button)
        layout.addLayout(title_layout)

        self.attendance_table = QTableWidget()
        self.attendance_table.setColumnCount(3)
        self.attendance_table.setHorizontalHeaderLabels(["Estudiante", "Estado", "Notas"])
        header = self.attendance_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        header.resizeSection(1, 130) # Give the status column a fixed, generous width
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.attendance_table.verticalHeader().setVisible(False)
        layout.addWidget(self.attendance_table)

        summary_widget = self._create_summary_section()
        layout.addWidget(summary_widget)

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        self.save_button = QPushButton("Guardar Cambios")
        self.save_button.setObjectName("PrimaryButton")
        self.save_button.clicked.connect(self._save_attendance)
        button_layout.addWidget(self.save_button)
        layout.addLayout(button_layout)

        return right_widget

    def _create_summary_section(self) -> QWidget:
        summary_widget = QWidget()
        layout = QVBoxLayout(summary_widget)
        layout.setContentsMargins(0, 10, 0, 0)
        percent_layout = QHBoxLayout()
        self.summary_percent_label = QLabel("100%")
        percent_layout.addWidget(QLabel("Resumen de Asistencia"))
        percent_layout.addStretch()
        percent_layout.addWidget(self.summary_percent_label)
        layout.addLayout(percent_layout)
        self.summary_progress_bar = QProgressBar()
        self.summary_progress_bar.setTextVisible(False)
        layout.addWidget(self.summary_progress_bar)
        self.summary_text_label = QLabel("")
        layout.addWidget(self.summary_text_label)
        return summary_widget

    def refresh_data(self):
        current_group = self.group_combo.currentText()
        self.group_combo.clear()
        try:
            groups = logic.get_group_list()
            self.group_combo.addItems(groups)
            if current_group in groups:
                self.group_combo.setCurrentText(current_group)
            else:
                self.refresh_periods()
        except Exception as e:
            print(f"ERROR in refresh_data (attendance): {e}")
            QMessageBox.critical(self, "Error", f"No se pudieron cargar los grupos: {e}")

    def refresh_periods(self):
        """Refreshes the grading periods combo box based on the selected group."""
        self.period_combo.clear()
        group_name = self.group_combo.currentText()
        if not group_name:
            self._update_attendance_view()
            return
        try:
            periods = logic.get_grading_periods(group_name)
            for period in periods:
                self.period_combo.addItem(period["name"], userData=period)
        except Exception as e:
            print(f"ERROR in refresh_periods (attendance): {e}")
            QMessageBox.critical(self, "Error", f"No se pudieron cargar los periodos: {e}")

    def _update_attendance_view(self):
        self._highlight_scheduled_dates()
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
            present_count = 0
            for row, student in enumerate(students):
                student_id = student["id"]
                name_item = QTableWidgetItem(student["name"])
                name_item.setData(Qt.ItemDataRole.UserRole, student_id)
                name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                status_combo = StatusComboBox()
                notes_item = QTableWidgetItem()
                status = ""
                if student_id in attendance_data:
                    status = attendance_data[student_id]["status"]
                    status_combo.set_selected_status(status)
                    notes_item.setText(attendance_data[student_id]["notes"])
                self.attendance_table.setItem(row, 0, name_item)
                self.attendance_table.setCellWidget(row, 1, status_combo)
                self.attendance_table.setItem(row, 2, notes_item)
                self._style_row_by_status(row, status)
                status_combo.currentTextChanged.connect(lambda text, r=row: self._style_row_by_status(r, text))
                if status.lower() in logic.PRESENT_STATUSES:
                    present_count += 1
            self._update_summary(len(students), present_count)
        except Exception as e:
            print(f"ERROR in _update_attendance_view: {e}")
            QMessageBox.critical(self, "Error", f"No se pudo cargar la asistencia: {e}")

    def _update_summary(self, total_students, present_students):
        if total_students > 0:
            percent = (present_students / total_students) * 100
            self.summary_percent_label.setText(f"{percent:.0f}%")
            self.summary_progress_bar.setValue(int(percent))
            self.summary_text_label.setText(f"{present_students} de {total_students} estudiantes presentes.")
        else:
            self.summary_percent_label.setText("N/A")
            self.summary_progress_bar.setValue(0)
            self.summary_text_label.setText("No hay estudiantes en este grupo.")

    def _highlight_scheduled_dates(self):
        """Highlights the dates on the calendar where classes are scheduled within the selected period."""
        default_format = QTextCharFormat()
        self.calendar.setDateTextFormat(QDate(), default_format)

        group_name = self.group_combo.currentText()
        selected_period = self.period_combo.currentData()

        if not group_name or not selected_period:
            return

        start_date_str = selected_period.get("start_date")
        end_date_str = selected_period.get("end_date")

        if not start_date_str or not end_date_str:
            return

        highlight_format = QTextCharFormat()
        highlight_format.setFontWeight(QFont.Weight.Bold)
        highlight_format.setBackground(QColor("#eef5ff"))

        try:
            class_dates = logic.generate_class_dates(group_name, start_date_str, end_date_str)
            for date_str in class_dates:
                q_date = QDate.fromString(date_str, "yyyy-MM-dd")
                self.calendar.setDateTextFormat(q_date, highlight_format)
        except Exception as e:
            print(f"ERROR in _highlight_scheduled_dates: {e}")

    def _style_row_by_status(self, row, status):
        color = QColor("#fef2f2") if status == "Ausente" else QColor(Qt.GlobalColor.transparent)
        for col in range(self.attendance_table.columnCount()):
            item = self.attendance_table.item(row, col)
            if item: item.setBackground(color)

    def _save_attendance(self):
        group_name = self.group_combo.currentText()
        target_date = self.calendar.selectedDate().toString("yyyy-MM-dd")
        if not group_name:
            QMessageBox.warning(self, "Atención", "Por favor, seleccione un grupo.")
            return
        records = []
        for row in range(self.attendance_table.rowCount()):
            student_id = self.attendance_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
            status = self.attendance_table.cellWidget(row, 1).get_selected_status()
            notes = self.attendance_table.item(row, 2).text()
            records.append({"student_id": student_id, "status": status, "notes": notes})
        try:
            logic.save_attendance_for_date(group_name, target_date, records)
            QMessageBox.information(self, "Éxito", f"La asistencia para el {target_date} ha sido guardada.")
            self._update_attendance_view()
        except Exception as e:
            print(f"ERROR in _save_attendance: {e}")
            QMessageBox.critical(self, "Error", f"No se pudo guardar la asistencia: {e}")

    def _on_mark_all_present(self):
        """Sets the status of all students in the table to 'Presente'."""
        for row in range(self.attendance_table.rowCount()):
            status_combo = self.attendance_table.cellWidget(row, 1)
            if isinstance(status_combo, StatusComboBox):
                status_combo.set_selected_status("Presente")

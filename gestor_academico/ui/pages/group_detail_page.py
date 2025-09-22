from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                               QTabWidget, QTableWidget, QPushButton, QFormLayout,
                               QSpinBox, QHeaderView, QTableWidgetItem, QMessageBox,
                               QInputDialog, QFileDialog, QCheckBox, QTimeEdit,
                               QGroupBox, QDateEdit)
from PySide6.QtCore import Qt, Signal, QTime, QDate
from typing import List, Dict

from gestor_academico.core import logic

class GroupDetailPage(QWidget):
    backRequested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.group_name = None
        main_layout = QVBoxLayout(self)
        header_layout = QHBoxLayout()
        self.back_button = QPushButton("← Volver a Grupos")
        self.back_button.clicked.connect(self.backRequested.emit)
        self.title_label = QLabel("Detalles del Grupo")
        self.title_label.setObjectName("HeaderTitle")
        header_layout.addWidget(self.back_button)
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()
        main_layout.addLayout(header_layout)

        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)

        self.students_tab = self._create_students_tab()
        self.schedule_tab = self._create_schedule_tab()
        self.settings_tab = self._create_settings_tab()

        self.tab_widget.addTab(self.students_tab, "Alumnos")
        self.tab_widget.addTab(self.schedule_tab, "Horario")
        self.tab_widget.addTab(self.settings_tab, "Configuración")

    def set_group(self, group_name: str):
        self.group_name = group_name
        self.title_label.setText(f"Detalles de: {self.group_name}")
        self.load_group_data()

    def load_group_data(self):
        if not self.group_name: return

        # Disable save buttons on data load, as form is now "clean"
        self.save_settings_button.setEnabled(False)
        self.save_schedule_button.setEnabled(False)

        try:
            group_data = logic.get_group_details(self.group_name)
            if not group_data: self.backRequested.emit(); return

            # Students
            students = group_data.get("students", [])
            self.students_table.setRowCount(len(students))
            for row, student in enumerate(students):
                self.students_table.setItem(row, 0, QTableWidgetItem(student["id"]))
                self.students_table.setItem(row, 1, QTableWidgetItem(student["name"]))

            # Settings
            self.group_name_input.setText(group_data.get("name", ""))
            self.threshold_input.setValue(int(group_data.get("attendance_threshold", 80)))
            self._populate_periods_settings(group_data.get("grading_periods", []))

            # Schedule
            self._populate_schedule_tab(group_data.get("schedule", {}))
        except Exception as e:
            print(f"ERROR in load_group_data: {e}")
            QMessageBox.critical(self, "Error", f"No se pudieron cargar los detalles: {e}")
            self.backRequested.emit()

    def _create_students_tab(self) -> QWidget:
        tab_widget = QWidget()
        layout = QVBoxLayout(tab_widget)
        self.students_table = QTableWidget()
        self.students_table.setColumnCount(2)
        self.students_table.setHorizontalHeaderLabels(["ID", "Nombre del Estudiante"])
        self.students_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.students_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.students_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.students_table.itemSelectionChanged.connect(self._on_student_selection_changed)
        layout.addWidget(self.students_table)

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        self.add_student_button = QPushButton("Añadir Estudiante")
        self.edit_student_button = QPushButton("Editar Estudiante")
        self.remove_student_button = QPushButton("Eliminar Estudiante")
        self.import_csv_button = QPushButton("Importar desde CSV")

        self.edit_student_button.setEnabled(False)
        self.remove_student_button.setEnabled(False)

        self.add_student_button.clicked.connect(self._on_add_student)
        self.edit_student_button.clicked.connect(self._on_edit_student)
        self.remove_student_button.clicked.connect(self._on_remove_student)
        self.import_csv_button.clicked.connect(self._on_import_from_csv)

        button_layout.addWidget(self.import_csv_button)
        button_layout.addSpacing(20)
        button_layout.addWidget(self.add_student_button)
        button_layout.addWidget(self.edit_student_button)
        button_layout.addWidget(self.remove_student_button)
        layout.addLayout(button_layout)
        return tab_widget

    def _create_settings_tab(self) -> QWidget:
        tab_widget = QWidget()
        self.settings_layout = QVBoxLayout(tab_widget)
        self.settings_layout.setAlignment(Qt.AlignTop)

        general_groupbox = QGroupBox("Configuración General")
        form_layout = QFormLayout()
        self.group_name_input = QLineEdit()
        self.group_name_input.textChanged.connect(lambda: self.save_settings_button.setEnabled(True))
        self.threshold_input = QSpinBox()
        self.threshold_input.valueChanged.connect(lambda: self.save_settings_button.setEnabled(True))
        self.threshold_input.setRange(0, 100); self.threshold_input.setSuffix(" %")
        form_layout.addRow("Nombre del Grupo:", self.group_name_input)
        form_layout.addRow("Umbral de Asistencia Mínima:", self.threshold_input)
        general_groupbox.setLayout(form_layout)
        self.settings_layout.addWidget(general_groupbox)

        self.periods_settings_layout = QVBoxLayout()
        self.settings_layout.addLayout(self.periods_settings_layout)
        self.periods_widgets = {}

        self.settings_layout.addStretch()
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        self.save_settings_button = QPushButton("Guardar Configuración")
        self.save_settings_button.setObjectName("PrimaryButton")
        self.save_settings_button.setEnabled(False)
        self.save_settings_button.clicked.connect(self._on_save_settings)
        button_layout.addWidget(self.save_settings_button)
        self.settings_layout.addLayout(button_layout)
        return tab_widget

    def _create_schedule_tab(self) -> QWidget:
        tab_widget = QWidget()
        layout = QVBoxLayout(tab_widget)
        layout.setAlignment(Qt.AlignTop)
        form_layout = QFormLayout()
        self.schedule_widgets = {}
        days = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
        for day in days:
            day_layout = QHBoxLayout()
            checkbox = QCheckBox("Activo"); start_time = QTimeEdit(); end_time = QTimeEdit()

            checkbox.stateChanged.connect(lambda: self.save_schedule_button.setEnabled(True))
            start_time.timeChanged.connect(lambda: self.save_schedule_button.setEnabled(True))
            end_time.timeChanged.connect(lambda: self.save_schedule_button.setEnabled(True))

            day_layout.addWidget(checkbox); day_layout.addWidget(QLabel("De:")); day_layout.addWidget(start_time)
            day_layout.addWidget(QLabel("a:")); day_layout.addWidget(end_time); day_layout.addStretch()
            form_layout.addRow(day, day_layout)
            self.schedule_widgets[day] = {"active": checkbox, "start": start_time, "end": end_time}
        layout.addLayout(form_layout)
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        self.save_schedule_button = QPushButton("Guardar Horario")
        self.save_schedule_button.setObjectName("PrimaryButton")
        self.save_schedule_button.setEnabled(False)
        self.save_schedule_button.clicked.connect(self._on_save_schedule)
        button_layout.addWidget(self.save_schedule_button)
        layout.addLayout(button_layout)
        return tab_widget

    def _on_add_student(self):
        name, ok = QInputDialog.getText(self, "Añadir Estudiante", "Nombre:")
        if ok and name:
            try:
                logic.add_student_to_group(self.group_name, name)
                self.load_group_data()
            except Exception as e:
                print(f"ERROR in _on_add_student: {e}")
                QMessageBox.critical(self, "Error", f"{e}")

    def _on_remove_student(self):
        selected_items = self.students_table.selectedItems()
        if not selected_items: return
        row = selected_items[0].row()
        student_id = self.students_table.item(row, 0).text()
        student_name = self.students_table.item(row, 1).text()
        reply = QMessageBox.question(self, "Confirmar", f"Eliminar a '{student_name}'?")
        if reply == QMessageBox.StandardButton.Yes:
            try:
                logic.remove_student_from_group(self.group_name, student_id)
                self.load_group_data()
            except Exception as e:
                print(f"ERROR in _on_remove_student: {e}")
                QMessageBox.critical(self, "Error", f"{e}")

    def _on_edit_student(self):
        selected_items = self.students_table.selectedItems()
        if not selected_items: return
        row = selected_items[0].row()
        student_id = self.students_table.item(row, 0).text()
        current_name = self.students_table.item(row, 1).text()
        new_name, ok = QInputDialog.getText(self, "Editar Nombre", "Nuevo nombre:", text=current_name)
        if ok and new_name and new_name != current_name:
            try:
                logic.update_student_in_group(self.group_name, student_id, new_name)
                self.load_group_data()
            except Exception as e:
                print(f"ERROR in _on_edit_student: {e}")
                QMessageBox.critical(self, "Error", f"{e}")

    def _populate_periods_settings(self, periods: List[Dict]):
        while self.periods_settings_layout.count():
            child = self.periods_settings_layout.takeAt(0)
            if child.widget(): child.widget().deleteLater()
        self.periods_widgets = {}
        for period in periods:
            period_id = period["id"]
            group_box = QGroupBox(period["name"])
            form_layout = QFormLayout()
            start_date_edit = QDateEdit(calendarPopup=True); start_date_edit.setDisplayFormat("yyyy-MM-dd")
            if period.get("start_date"): start_date_edit.setDate(QDate.fromString(period["start_date"], "yyyy-MM-dd"))
            end_date_edit = QDateEdit(calendarPopup=True); end_date_edit.setDisplayFormat("yyyy-MM-dd")
            if period.get("end_date"): end_date_edit.setDate(QDate.fromString(period["end_date"], "yyyy-MM-dd"))

            start_date_edit.dateChanged.connect(lambda: self.save_settings_button.setEnabled(True))
            end_date_edit.dateChanged.connect(lambda: self.save_settings_button.setEnabled(True))

            form_layout.addRow("Fecha de Inicio:", start_date_edit)
            form_layout.addRow("Fecha de Fin:", end_date_edit)
            group_box.setLayout(form_layout)
            self.periods_settings_layout.addWidget(group_box)
            self.periods_widgets[period_id] = {"start_date": start_date_edit, "end_date": end_date_edit}

    def _populate_schedule_tab(self, schedule: dict):
        for day, widgets in self.schedule_widgets.items():
            day_data = schedule.get(day, {})
            widgets["active"].setChecked(day_data.get("active", False))
            widgets["start"].setTime(QTime.fromString(day_data.get("start", "00:00"), "HH:mm"))
            widgets["end"].setTime(QTime.fromString(day_data.get("end", "00:00"), "HH:mm"))

    def _on_save_settings(self):
        try:
            general_settings = {"name": self.group_name_input.text(), "attendance_threshold": self.threshold_input.value()}
            logic.update_group_settings(self.group_name, general_settings)
            group_data = logic.get_group_details(self.group_name)
            periods = group_data.get("grading_periods", [])
            for period in periods:
                if period["id"] in self.periods_widgets:
                    period["start_date"] = self.periods_widgets[period["id"]]["start_date"].date().toString("yyyy-MM-dd")
                    period["end_date"] = self.periods_widgets[period["id"]]["end_date"].date().toString("yyyy-MM-dd")
            logic.update_group_settings(self.group_name, {"grading_periods": periods})
            if general_settings["name"] != self.group_name:
                self.group_name = general_settings["name"]
                self.title_label.setText(f"Detalles de: {self.group_name}")
            QMessageBox.information(self, "Éxito", "Configuración guardada.")
            self.load_group_data() # Resets button state
        except Exception as e:
            print(f"ERROR in _on_save_settings: {e}")
            QMessageBox.critical(self, "Error", f"No se pudo guardar la configuración: {e}")

    def _on_import_from_csv(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Seleccionar CSV", "", "CSV Files (*.csv)")
        if not file_path: return
        try:
            result = logic.add_students_from_csv(self.group_name, file_path)
            QMessageBox.information(self, "Éxito", f"Añadidos: {result['added']}.\nOmitidos: {result['skipped']}.")
            self.load_group_data()
        except Exception as e:
            print(f"ERROR in _on_import_from_csv: {e}")
            QMessageBox.critical(self, "Error", f"No se pudo importar: {e}")

    def _on_save_schedule(self):
        new_schedule = {}
        for day, widgets in self.schedule_widgets.items():
            new_schedule[day] = {
                "active": widgets["active"].isChecked(),
                "start": widgets["start"].time().toString("HH:mm"),
                "end": widgets["end"].time().toString("HH:mm")
            }
        try:
            logic.update_group_settings(self.group_name, {"schedule": new_schedule})
            QMessageBox.information(self, "Éxito", "Horario guardado.")
            self.save_schedule_button.setEnabled(False)
        except Exception as e:
            print(f"ERROR in _on_save_schedule: {e}")
            QMessageBox.critical(self, "Error", f"No se pudo guardar el horario: {e}")

    def _on_student_selection_changed(self):
        """Enables or disables student action buttons based on selection."""
        is_student_selected = bool(self.students_table.selectedItems())
        self.edit_student_button.setEnabled(is_student_selected)
        self.remove_student_button.setEnabled(is_student_selected)

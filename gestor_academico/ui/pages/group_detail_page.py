from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                               QTabWidget, QTableWidget, QPushButton, QFormLayout,
                               QSpinBox, QHeaderView, QTableWidgetItem, QMessageBox,
                               QInputDialog, QFileDialog, QCheckBox, QTimeEdit)
from PySide6.QtCore import Qt, Signal, QTime

from gestor_academico.core import logic

class GroupDetailPage(QWidget):
    """
    A page to display and manage the details of a single group,
    including its students and settings.
    """
    backRequested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.group_name = None

        # Main layout
        main_layout = QVBoxLayout(self)

        # Header
        header_layout = QHBoxLayout()
        self.back_button = QPushButton("← Volver a Grupos")
        self.back_button.clicked.connect(self.backRequested.emit)
        self.title_label = QLabel("Detalles del Grupo")
        self.title_label.setObjectName("HeaderTitle")

        header_layout.addWidget(self.back_button)
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()
        main_layout.addLayout(header_layout)

        # Tab widget
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)

        # Create tabs
        self.students_tab = self._create_students_tab()
        self.settings_tab = self._create_settings_tab()
        self.schedule_tab = self._create_schedule_tab()

        self.tab_widget.addTab(self.students_tab, "Alumnos")
        self.tab_widget.addTab(self.schedule_tab, "Horario")
        self.tab_widget.addTab(self.settings_tab, "Configuración")

    def set_group(self, group_name: str):
        """Sets the group to be displayed on this page and loads its data."""
        self.group_name = group_name
        self.title_label.setText(f"Detalles de: {self.group_name}")
        self.load_group_data()

    def load_group_data(self):
        """Loads data for the current group and populates the UI fields."""
        if not self.group_name:
            return

        try:
            # Load all group details at once
            group_data = logic.get_group_details(self.group_name)
            if not group_data:
                # Handle case where group was deleted or not found
                self.backRequested.emit()
                return

            # Populate Students Tab
            students = group_data.get("students", [])
            self.students_table.setRowCount(len(students))
            for row, student in enumerate(students):
                id_item = QTableWidgetItem(student["id"])
                name_item = QTableWidgetItem(student["name"])
                self.students_table.setItem(row, 0, id_item)
                self.students_table.setItem(row, 1, name_item)

            # Populate Settings Tab
            self.group_name_input.setText(group_data.get("name", ""))
            self.threshold_input.setValue(int(group_data.get("attendance_threshold", 80)))

            # Populate Schedule Tab
            schedule = group_data.get("schedule", {})
            for day, widgets in self.schedule_widgets.items():
                day_data = schedule.get(day, {})
                widgets["active"].setChecked(day_data.get("active", False))
                widgets["start"].setTime(QTime.fromString(day_data.get("start", "00:00"), "HH:mm"))
                widgets["end"].setTime(QTime.fromString(day_data.get("end", "00:00"), "HH:mm"))

        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudieron cargar los detalles del grupo: {e}")
            self.backRequested.emit()

    def _create_students_tab(self) -> QWidget:
        """Creates the UI for the 'Students' management tab."""
        tab_widget = QWidget()
        layout = QVBoxLayout(tab_widget)

        # Table of students
        self.students_table = QTableWidget()
        self.students_table.setColumnCount(2)
        self.students_table.setHorizontalHeaderLabels(["ID", "Nombre del Estudiante"])
        self.students_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.students_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.students_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.students_table)

        # Action buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        self.add_student_button = QPushButton("Añadir Estudiante")
        self.add_student_button.clicked.connect(self._on_add_student)
        self.edit_student_button = QPushButton("Editar Estudiante")
        self.edit_student_button.clicked.connect(self._on_edit_student)
        self.remove_student_button = QPushButton("Eliminar Estudiante")
        self.remove_student_button.clicked.connect(self._on_remove_student)
        self.import_csv_button = QPushButton("Importar desde CSV")
        self.import_csv_button.clicked.connect(self._on_import_from_csv)

        button_layout.addWidget(self.import_csv_button)
        button_layout.addSpacing(20)
        button_layout.addWidget(self.add_student_button)
        button_layout.addWidget(self.edit_student_button)
        button_layout.addWidget(self.remove_student_button)
        layout.addLayout(button_layout)

        return tab_widget

    def _create_settings_tab(self) -> QWidget:
        """Creates the UI for the 'Settings' management tab."""
        tab_widget = QWidget()
        layout = QVBoxLayout(tab_widget)
        layout.setAlignment(Qt.AlignTop)

        form_layout = QFormLayout()

        # Group Name
        self.group_name_input = QLineEdit()
        form_layout.addRow("Nombre del Grupo:", self.group_name_input)

        # Attendance Threshold
        self.threshold_input = QSpinBox()
        self.threshold_input.setRange(0, 100)
        self.threshold_input.setSuffix(" %")
        form_layout.addRow("Umbral de Asistencia Mínima:", self.threshold_input)

        layout.addLayout(form_layout)

        # Save button
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        self.save_settings_button = QPushButton("Guardar Configuración")
        self.save_settings_button.setObjectName("PrimaryButton")
        self.save_settings_button.clicked.connect(self._on_save_settings)
        button_layout.addWidget(self.save_settings_button)
        layout.addLayout(button_layout)

        return tab_widget

    def _on_add_student(self):
        """Handles adding a new student."""
        name, ok = QInputDialog.getText(self, "Añadir Estudiante", "Nombre del nuevo estudiante:")
        if ok and name:
            try:
                logic.add_student_to_group(self.group_name, name)
                self.load_group_data() # Refresh
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo añadir al estudiante: {e}")

    def _on_remove_student(self):
        """Handles removing the selected student."""
        selected_items = self.students_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Atención", "Por favor, seleccione un estudiante de la tabla.")
            return

        row = selected_items[0].row()
        student_id = self.students_table.item(row, 0).text()
        student_name = self.students_table.item(row, 1).text()

        reply = QMessageBox.question(self, "Confirmar Eliminación",
                                     f"¿Está seguro de que quiere eliminar a '{student_name}'?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            try:
                logic.remove_student_from_group(self.group_name, student_id)
                self.load_group_data() # Refresh
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo eliminar al estudiante: {e}")

    def _on_edit_student(self):
        """Handles editing the selected student's name."""
        selected_items = self.students_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Atención", "Por favor, seleccione un estudiante de la tabla.")
            return

        row = selected_items[0].row()
        student_id = self.students_table.item(row, 0).text()
        current_name = self.students_table.item(row, 1).text()

        new_name, ok = QInputDialog.getText(self, "Editar Estudiante", "Nuevo nombre:", text=current_name)

        if ok and new_name and new_name != current_name:
            try:
                logic.update_student_in_group(self.group_name, student_id, new_name)
                self.load_group_data() # Refresh
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo actualizar al estudiante: {e}")

    def _on_save_settings(self):
        """Saves the changes from the settings tab."""
        try:
            new_settings = {
                "name": self.group_name_input.text(),
                "attendance_threshold": self.threshold_input.value()
            }
            # Note: Renaming the group folder is not handled here, only the name in config.
            logic.update_group_settings(self.group_name, new_settings)

            # If name changed, update the page's context
            if new_settings["name"] != self.group_name:
                self.group_name = new_settings["name"]
                self.title_label.setText(f"Detalles de: {self.group_name}")

            QMessageBox.information(self, "Éxito", "La configuración ha sido guardada.")
            self.load_group_data() # Refresh to be sure
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo guardar la configuración: {e}")

    def _on_import_from_csv(self):
        """Handles importing students from a CSV file."""
        file_path, _ = QFileDialog.getOpenFileName(self, "Seleccionar CSV de Estudiantes", "",
                                                   "CSV Files (*.csv);;All Files (*)")
        if not file_path:
            return

        try:
            result = logic.add_students_from_csv(self.group_name, file_path)
            QMessageBox.information(self, "Importación Completa",
                                    f"Se han añadido {result['added']} nuevos estudiantes.\n"
                                    f"Se han omitido {result['skipped']} estudiantes (posiblemente duplicados).")
            self.load_group_data() # Refresh the student list
        except Exception as e:
            QMessageBox.critical(self, "Error de Importación", f"No se pudo importar el archivo: {e}")

    def _create_schedule_tab(self) -> QWidget:
        """Creates the UI for the 'Schedule' management tab."""
        tab_widget = QWidget()
        layout = QVBoxLayout(tab_widget)
        layout.setAlignment(Qt.AlignTop)

        form_layout = QFormLayout()
        self.schedule_widgets = {}

        days = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
        for day in days:
            day_layout = QHBoxLayout()

            checkbox = QCheckBox("Activo")
            start_time = QTimeEdit()
            end_time = QTimeEdit()

            day_layout.addWidget(checkbox)
            day_layout.addWidget(QLabel("De:"))
            day_layout.addWidget(start_time)
            day_layout.addWidget(QLabel("a:"))
            day_layout.addWidget(end_time)
            day_layout.addStretch()

            form_layout.addRow(day, day_layout)
            self.schedule_widgets[day] = {
                "active": checkbox,
                "start": start_time,
                "end": end_time
            }

        layout.addLayout(form_layout)

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        self.save_schedule_button = QPushButton("Guardar Horario")
        self.save_schedule_button.setObjectName("PrimaryButton")
        self.save_schedule_button.clicked.connect(self._on_save_schedule)
        button_layout.addWidget(self.save_schedule_button)
        layout.addLayout(button_layout)

        return tab_widget

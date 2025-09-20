import sys
from PySide6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
                               QPushButton, QLabel, QStackedWidget, QScrollArea,
                               QApplication, QInputDialog, QMessageBox)
from PySide6.QtCore import Qt, QSize
# Note: For icons, you might need to pip install pyside6-icons
# from PySide6.QtGui import QIcon

from gestor_academico.core import logic
from .widgets.group_card import GroupCard
from .pages.attendance_page import AttendancePage
from .pages.group_detail_page import GroupDetailPage
from .pages.grades_page import GradesPage

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gestor Académico")
        self.setObjectName("MainWindow")
        self.resize(1200, 800)

        # Main widget and layout
        central_widget = QWidget()
        self.main_layout = QHBoxLayout(central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # Create and add sidebar and content area
        self.sidebar = self._create_sidebar()
        self.content_area = self._create_content_area()

        self.main_layout.addWidget(self.sidebar)
        self.main_layout.addWidget(self.content_area)

        self.setCentralWidget(central_widget)

    def _create_sidebar(self) -> QWidget:
        sidebar_widget = QWidget()
        sidebar_widget.setObjectName("Sidebar")
        sidebar_widget.setFixedWidth(240)

        layout = QVBoxLayout(sidebar_widget)
        layout.setContentsMargins(10, 20, 10, 20)
        layout.setSpacing(10)
        layout.setAlignment(Qt.AlignTop)

        title = QLabel("Académico")
        title.setObjectName("HeaderTitle")
        title.setStyleSheet("font-size: 22px; margin-left: 10px; margin-bottom: 20px;")
        layout.addWidget(title)

        # Navigation buttons
        self.btn_groups = QPushButton("Grupos")
        self.btn_groups.setCheckable(True)
        self.btn_groups.setChecked(True)
        # self.btn_groups.setIcon(QIcon(":/icons/users.svg")) # Example icon

        self.btn_asistencia = QPushButton("Asistencia")
        self.btn_asistencia.setCheckable(True)

        self.btn_calificaciones = QPushButton("Calificaciones")
        self.btn_calificaciones.setCheckable(True)

        self.btn_reportes = QPushButton("Reportes")
        self.btn_reportes.setCheckable(True)

        layout.addWidget(self.btn_groups)
        layout.addWidget(self.btn_asistencia)
        layout.addWidget(self.btn_calificaciones)
        layout.addWidget(self.btn_reportes)

        layout.addStretch() # Pushes settings to the bottom

        self.btn_config = QPushButton("Configuración")
        self.btn_config.setCheckable(True)
        layout.addWidget(self.btn_config)

        # Connect buttons to change pages
        self.btn_groups.clicked.connect(lambda: self.stacked_widget.setCurrentWidget(self.groups_page))
        self.btn_asistencia.clicked.connect(lambda: self.stacked_widget.setCurrentWidget(self.attendance_page))
        self.btn_calificaciones.clicked.connect(lambda: self.stacked_widget.setCurrentWidget(self.grades_page))
        # ... connect other buttons as pages are created

        return sidebar_widget

    def _create_content_area(self) -> QWidget:
        content_widget = QWidget()
        content_widget.setObjectName("ContentArea")

        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(30, 20, 30, 20)

        self.stacked_widget = QStackedWidget()

        # Create and add pages
        self.groups_page = self._create_groups_page()
        self.attendance_page = AttendancePage()
        self.group_detail_page = GroupDetailPage()
        self.group_detail_page.backRequested.connect(lambda: self.stacked_widget.setCurrentWidget(self.groups_page))
        self.grades_page = GradesPage()

        self.stacked_widget.addWidget(self.groups_page)
        self.stacked_widget.addWidget(self.attendance_page)
        self.stacked_widget.addWidget(self.group_detail_page)
        self.stacked_widget.addWidget(self.grades_page)

        self.stacked_widget.currentChanged.connect(self._on_page_changed)

        layout.addWidget(self.stacked_widget)
        return content_widget

    def _create_groups_page(self) -> QWidget:
        page_widget = QWidget()
        layout = QVBoxLayout(page_widget)
        layout.setSpacing(20)

        # Header
        header_layout = QHBoxLayout()
        title = QLabel("Mis Grupos")
        title.setObjectName("HeaderTitle")

        btn_create_group = QPushButton("Crear Nuevo Grupo")
        btn_create_group.setObjectName("PrimaryButton")
        btn_create_group.clicked.connect(self._on_create_group_clicked)

        header_layout.addWidget(title)
        header_layout.addStretch()
        # header_layout.addWidget(QPushButton("Ver Todos los Grupos", objectName="SecondaryButton"))
        header_layout.addWidget(btn_create_group)
        layout.addLayout(header_layout)

        # Scroll Area for Group Cards
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        scroll_content = QWidget()
        self.groups_layout = QHBoxLayout(scroll_content)
        self.groups_layout.setAlignment(Qt.AlignLeft)
        self.groups_layout.setSpacing(20)

        scroll_area.setWidget(scroll_content)
        layout.addWidget(scroll_area)

        self._load_group_cards()

        return page_widget

    def _load_group_cards(self):
        # Clear existing cards before loading
        while self.groups_layout.count():
            child = self.groups_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        try:
            # This is where the UI calls the core logic
            groups_summary = logic.get_all_groups_summary()

            if not groups_summary:
                no_groups_label = QLabel("No se han encontrado grupos. ¡Crea uno nuevo para empezar!")
                no_groups_label.setAlignment(Qt.AlignCenter)
                self.groups_layout.addWidget(no_groups_label)
                return

            for group_data in groups_summary:
                card = GroupCard(
                    group_name=group_data["name"],
                    student_count=group_data["student_count"],
                    at_risk_percentage=group_data["at_risk_percentage"]
                )
                card.deleteRequested.connect(self._on_delete_group_requested)
                card.viewRequested.connect(self._on_view_group_details_requested)
                self.groups_layout.addWidget(card)

        except Exception as e:
            # Handle potential errors from the logic layer gracefully
            error_label = QLabel(f"Ocurrió un error al cargar los grupos: {e}")
            error_label.setAlignment(Qt.AlignCenter)
            self.groups_layout.addWidget(error_label)

    def _on_create_group_clicked(self):
        """Handles the 'Create New Group' button click."""
        text, ok = QInputDialog.getText(self, "Crear Nuevo Grupo", "Nombre del grupo:")

        if ok and text:
            try:
                logic.create_new_group(text)
                QMessageBox.information(self, "Éxito", f"El grupo '{text}' ha sido creado.")
                self._load_group_cards() # Refresh the view
            except ValueError as e:
                QMessageBox.warning(self, "Error", str(e))
        elif ok and not text:
            QMessageBox.warning(self, "Atención", "El nombre del grupo no puede estar vacío.")

    def _on_delete_group_requested(self, group_name: str):
        """Handles the 'deleteRequested' signal from a GroupCard."""
        reply = QMessageBox.question(
            self,
            "Confirmar Eliminación",
            f"¿Estás seguro de que quieres enviar el grupo '{group_name}' al fondo del mar?\n¡Esta acción no se puede deshacer!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                logic.delete_group(group_name)
                QMessageBox.information(self, "Éxito", f"El grupo '{group_name}' ha sido eliminado.")
                self._load_group_cards() # Refresh the view
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo eliminar el grupo: {e}")

    def _on_view_group_details_requested(self, group_name: str):
        """Handles the 'viewRequested' signal from a GroupCard."""
        self.group_detail_page.set_group(group_name)
        self.stacked_widget.setCurrentWidget(self.group_detail_page)

    def _on_page_changed(self, index: int):
        """Slot for when the current page in the QStackedWidget changes."""
        current_widget = self.stacked_widget.widget(index)
        if isinstance(current_widget, AttendancePage):
            # If we navigate to the attendance page, refresh its group list
            current_widget.reload_groups()
        elif isinstance(current_widget, GroupDetailPage):
            # This is a good place to refresh the group details as well,
            # in case they were changed elsewhere.
            current_widget.load_group_data()
        elif isinstance(current_widget, GradesPage):
            current_widget.refresh_data()


# This block is for testing the window directly
if __name__ == '__main__':
    # Create some dummy data for testing
    if not logic.get_group_list():
        print("No groups found, creating dummy data for demonstration...")
        try:
            calc_group = "Grupo de Cálculo"
            logic.create_new_group(calc_group)
            logic.add_student_to_group(calc_group, "Sofia Rodriguez")
            logic.add_student_to_group(calc_group, "Mateo Vargas")
            logic.add_student_to_group(calc_group, "Isabella Perez")
            logic.add_student_to_group(calc_group, "Alejandro Gomez")
            logic.add_student_to_group(calc_group, "Camila Torres")

            logic.create_new_group("Lab. de Física", prefix="IAEV-")
            logic.create_new_group("Taller de Redacción")
        except ValueError as e:
            print(f"Dummy data might already exist: {e}")

    app = QApplication(sys.argv)

    # Load stylesheet
    style_path = "../assets/styles.qss" # Relative path for direct execution
    try:
        with open(style_path, "r") as f:
            app.setStyleSheet(f.read())
    except FileNotFoundError:
        print("Stylesheet not found. Run from the root directory.")

    window = MainWindow()
    window.show()
    sys.exit(app.exec())

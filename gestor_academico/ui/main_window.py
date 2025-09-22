import sys
from PySide6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QLabel, QStackedWidget, QScrollArea, QApplication, QInputDialog, QMessageBox
from PySide6.QtCore import Qt
from gestor_academico.core import logic
from .widgets.group_card import GroupCard
from .pages.attendance_page import AttendancePage
from .pages.group_detail_page import GroupDetailPage
from .pages.grades_page import GradesPage
from .pages.reports_page import ReportsPage
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gestor Académico"); self.setObjectName("MainWindow"); self.resize(1200, 800)
        central_widget = QWidget(); self.setCentralWidget(central_widget)
        self.main_layout = QHBoxLayout(central_widget); self.main_layout.setContentsMargins(0, 0, 0, 0); self.main_layout.setSpacing(0)
        self.sidebar = self._create_sidebar(); self.content_area = self._create_content_area()
        self.main_layout.addWidget(self.sidebar); self.main_layout.addWidget(self.content_area)
    def _create_sidebar(self):
        sidebar_widget = QWidget(); sidebar_widget.setObjectName("Sidebar"); sidebar_widget.setFixedWidth(240)
        layout = QVBoxLayout(sidebar_widget); layout.setContentsMargins(10, 20, 10, 20); layout.setSpacing(10); layout.setAlignment(Qt.AlignTop)
        title = QLabel("AcademiPro"); title.setObjectName("HeaderTitle"); title.setStyleSheet("font-size: 22px; margin-left: 10px; margin-bottom: 20px;")
        layout.addWidget(title)
        self.btn_groups = QPushButton("Grupos"); self.btn_asistencia = QPushButton("Asistencia"); self.btn_calificaciones = QPushButton("Calificaciones"); self.btn_reportes = QPushButton("Reportes"); self.btn_config = QPushButton("Configuración")
        for btn in [self.btn_groups, self.btn_asistencia, self.btn_calificaciones, self.btn_reportes, self.btn_config]: btn.setCheckable(True)
        self.btn_groups.setChecked(True)
        layout.addWidget(self.btn_groups); layout.addWidget(self.btn_asistencia); layout.addWidget(self.btn_calificaciones); layout.addWidget(self.btn_reportes); layout.addStretch(); layout.addWidget(self.btn_config)
        self.btn_groups.clicked.connect(lambda: self.stacked_widget.setCurrentWidget(self.groups_page))
        self.btn_asistencia.clicked.connect(lambda: self.stacked_widget.setCurrentWidget(self.attendance_page))
        self.btn_calificaciones.clicked.connect(lambda: self.stacked_widget.setCurrentWidget(self.grades_page))
        self.btn_reportes.clicked.connect(lambda: self.stacked_widget.setCurrentWidget(self.reports_page))
        self.btn_config.clicked.connect(self._on_config_button_clicked)
        return sidebar_widget
    def _create_content_area(self):
        content_widget = QWidget(); content_widget.setObjectName("ContentArea")
        layout = QVBoxLayout(content_widget); layout.setContentsMargins(30, 20, 30, 20)
        self.stacked_widget = QStackedWidget()
        self.groups_page = self._create_groups_page(); self.attendance_page = AttendancePage(); self.group_detail_page = GroupDetailPage(); self.grades_page = GradesPage(); self.reports_page = ReportsPage()
        self.group_detail_page.backRequested.connect(lambda: self.stacked_widget.setCurrentWidget(self.groups_page))
        self.stacked_widget.addWidget(self.groups_page); self.stacked_widget.addWidget(self.attendance_page); self.stacked_widget.addWidget(self.group_detail_page); self.stacked_widget.addWidget(self.grades_page); self.stacked_widget.addWidget(self.reports_page)
        self.stacked_widget.currentChanged.connect(self._on_page_changed)
        layout.addWidget(self.stacked_widget)
        return content_widget
    def _create_groups_page(self):
        page_widget = QWidget(); layout = QVBoxLayout(page_widget); layout.setSpacing(20)
        header_layout = QHBoxLayout(); title = QLabel("Mis Grupos"); title.setObjectName("HeaderTitle"); btn_create_group = QPushButton("Crear Nuevo Grupo"); btn_create_group.setObjectName("PrimaryButton"); btn_create_group.clicked.connect(self._on_create_group_clicked)
        header_layout.addWidget(title); header_layout.addStretch(); header_layout.addWidget(btn_create_group); layout.addLayout(header_layout)
        scroll_area = QScrollArea(); scroll_area.setWidgetResizable(True)
        scroll_content = QWidget(); self.groups_layout = QHBoxLayout(scroll_content); self.groups_layout.setAlignment(Qt.AlignLeft); self.groups_layout.setSpacing(20)
        scroll_area.setWidget(scroll_content); layout.addWidget(scroll_area)
        self._load_group_cards()
        return page_widget
    def _load_group_cards(self):
        while self.groups_layout.count():
            child = self.groups_layout.takeAt(0)
            if child.widget(): child.widget().deleteLater()
        try:
            groups_summary = logic.get_all_groups_summary()
            if not groups_summary: self.groups_layout.addWidget(QLabel("No groups found."))
            for group_data in groups_summary:
                card = GroupCard(**group_data)
                card.deleteRequested.connect(self._on_delete_group_requested)
                card.viewRequested.connect(self._on_view_group_details_requested)
                self.groups_layout.addWidget(card)
        except Exception as e:
            print(f"ERROR in _load_group_cards: {e}")
            self.groups_layout.addWidget(QLabel(f"Error: {e}"))
    def _on_create_group_clicked(self):
        text, ok = QInputDialog.getText(self, "Crear Grupo", "Nombre del grupo:")
        if ok and text:
            try:
                logic.create_new_group(text)
                self._load_group_cards()
                QMessageBox.information(self, "Éxito", f"Grupo '{text}' creado.")
            except ValueError as e:
                QMessageBox.warning(self, "Error", str(e))
    def _on_delete_group_requested(self, group_name):
        reply = QMessageBox.question(self, "Confirmar", f"Eliminar '{group_name}'?")
        if reply == QMessageBox.StandardButton.Yes:
            try:
                logic.delete_group(group_name)
                self._load_group_cards()
                QMessageBox.information(self, "Éxito", f"Grupo '{group_name}' eliminado.")
            except Exception as e:
                print(f"ERROR in _on_delete_group_requested: {e}")
                QMessageBox.critical(self, "Error", f"No se pudo eliminar el grupo: {e}")
    def _on_view_group_details_requested(self, group_name):
        self.group_detail_page.set_group(group_name)
        self.stacked_widget.setCurrentWidget(self.group_detail_page)
    def _on_page_changed(self, index):
        widget = self.stacked_widget.widget(index)
        if hasattr(widget, 'refresh_data'): widget.refresh_data()

    def _on_config_button_clicked(self):
        """Navigates to the settings tab of the first available group."""
        try:
            groups = logic.get_group_list()
            if not groups:
                QMessageBox.information(self, "Información", "No hay grupos para configurar. Por favor, cree un grupo primero.")
                return

            first_group = groups[0]
            self.group_detail_page.set_group(first_group)
            self.stacked_widget.setCurrentWidget(self.group_detail_page)

            # Find the "Configuración" tab and set it as current
            for i in range(self.group_detail_page.tab_widget.count()):
                if self.group_detail_page.tab_widget.tabText(i) == "Configuración":
                    self.group_detail_page.tab_widget.setCurrentIndex(i)
                    break
        except Exception as e:
            print(f"ERROR in _on_config_button_clicked: {e}")
            QMessageBox.critical(self, "Error", f"No se pudo navegar a la configuración: {e}")

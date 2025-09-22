from PySide6.QtWidgets import QFrame, QLabel, QProgressBar, QVBoxLayout, QWidget, QHBoxLayout, QMenu
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction

class GroupCard(QFrame):
    deleteRequested = Signal(str)
    viewRequested = Signal(str)
    def __init__(self, name: str, student_count: int, at_risk_percentage: float, parent=None):
        super().__init__(parent)
        self.group_name = name # Internally we can still call it group_name
        self.setObjectName("GroupCard")
        self.setCursor(Qt.PointingHandCursor)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.addWidget(QLabel(objectName="CardImage"))
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(15, 10, 15, 15)
        content_layout.setSpacing(5)
        main_layout.addWidget(content_widget)
        content_layout.addWidget(QLabel(name, objectName="CardTitle"))
        content_layout.addWidget(QLabel(f"{student_count} estudiantes", objectName="CardSubtitle"))
        content_layout.addStretch()
        progress_layout = QHBoxLayout()
        progress_layout.setSpacing(8)
        progress_bar = QProgressBar()
        progress_bar.setValue(int(at_risk_percentage))
        progress_bar.setTextVisible(False)
        progress_layout.addWidget(progress_bar)
        progress_layout.addWidget(QLabel(f"{at_risk_percentage}% en riesgo", objectName="CardSubtitle"))
        content_layout.addLayout(progress_layout)
    def contextMenuEvent(self, event):
        menu = QMenu(self)
        delete_action = QAction(f"Eliminar '{self.group_name}'", self)
        delete_action.triggered.connect(lambda: self.deleteRequested.emit(self.group_name))
        menu.addAction(delete_action)
        menu.exec_(event.globalPos())
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.viewRequested.emit(self.group_name)
        super().mousePressEvent(event)

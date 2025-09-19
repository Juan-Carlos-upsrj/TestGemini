from PySide6.QtWidgets import QFrame, QLabel, QProgressBar, QVBoxLayout, QWidget, QHBoxLayout, QMenu
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction

class GroupCard(QFrame):
    """
    A custom widget to display a summary of a single group.
    This corresponds to the cards shown in the 'Mis Grupos' view.
    Emits a 'deleteRequested' signal when the user chooses to delete.
    """
    deleteRequested = Signal(str)

    def __init__(self, group_name: str, student_count: int, at_risk_percentage: float, parent=None):
        super().__init__(parent)

        self.group_name = group_name
        self.setObjectName("GroupCard")
        self.setCursor(Qt.PointingHandCursor) # Changes cursor on hover to indicate it's clickable

        # Main vertical layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0) # No margins, the border of the frame is enough
        main_layout.setSpacing(0)

        # 1. Image Placeholder
        image_label = QLabel()
        image_label.setObjectName("CardImage")
        # In a real app, you'd load a QPixmap here:
        # pixmap = QPixmap("path/to/image.png")
        # image_label.setPixmap(pixmap.scaled(250, 120, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation))
        # image_label.setScaledContents(True)
        main_layout.addWidget(image_label)

        # 2. Content Area (for padding)
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(15, 10, 15, 15)
        content_layout.setSpacing(5)
        main_layout.addWidget(content_widget)

        # 2a. Title (Group Name)
        title_label = QLabel(group_name)
        title_label.setObjectName("CardTitle")
        content_layout.addWidget(title_label)

        # 2b. Subtitle (Student Count)
        subtitle_label = QLabel(f"{student_count} estudiantes")
        subtitle_label.setObjectName("CardSubtitle")
        content_layout.addWidget(subtitle_label)

        # Add a spacer to push the progress bar down
        content_layout.addStretch()

        # 2c. Risk Progress Bar and Label
        progress_layout = QHBoxLayout()
        progress_layout.setSpacing(8)

        progress_bar = QProgressBar()
        progress_bar.setValue(int(at_risk_percentage))
        progress_bar.setTextVisible(False) # Hide the default percentage text

        risk_label = QLabel(f"{at_risk_percentage}% en riesgo")
        risk_label.setObjectName("CardSubtitle") # Same style as other small text

        progress_layout.addWidget(progress_bar)
        progress_layout.addWidget(risk_label)

        content_layout.addLayout(progress_layout)

        self.setLayout(main_layout)

    def contextMenuEvent(self, event):
        """Creates a context menu on right-click."""
        context_menu = QMenu(self)
        delete_action = QAction(f"Eliminar '{self.group_name}'", self)
        delete_action.triggered.connect(self._emit_delete_signal)
        context_menu.addAction(delete_action)

        context_menu.exec_(event.globalPos())

    def _emit_delete_signal(self):
        """Emits the signal to request deletion."""
        self.deleteRequested.emit(self.group_name)

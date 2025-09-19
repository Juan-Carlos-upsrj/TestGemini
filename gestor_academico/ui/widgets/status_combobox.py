from PySide6.QtWidgets import QComboBox
from PySide6.QtGui import QColor

STATUSES = {
    "Presente": QColor("#10b981"),
    "Ausente": QColor("#ef4444"),
    "Tarde": QColor("#f59e0b"),
    "Justificado": QColor("#3b82f6"),
    "": QColor("#6b7280") # Default/empty
}

class StatusComboBox(QComboBox):
    """
    A custom QComboBox for selecting attendance status, with color coding.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.populate_items()
        self.currentTextChanged.connect(self.update_style)

    def populate_items(self):
        self.addItems(STATUSES.keys())

    def get_selected_status(self) -> str:
        return self.currentText()

    def set_selected_status(self, status: str):
        if status in STATUSES:
            self.setCurrentText(status)
        else:
            self.setCurrentIndex(0) # Default to the first item
        self.update_style(status)

    def update_style(self, text: str):
        color = STATUSES.get(text, STATUSES[""])
        self.setStyleSheet(f"""
            QComboBox {{
                color: {color.name()};
                font-weight: 500;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                padding: 4px;
            }}
            QComboBox::drop-down {{
                border: none;
            }}
        """)

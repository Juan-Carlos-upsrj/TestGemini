from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QTextEdit, QDialogButtonBox)
from typing import List

class MultipleEntryDialog(QDialog):
    """
    A dialog for entering a list of items, one per line.
    """
    def __init__(self, title: str, label_text: str, parent=None):
        super().__init__(parent)

        self.setWindowTitle(title)
        self.setMinimumWidth(400)

        layout = QVBoxLayout(self)

        label = QLabel(label_text)
        layout.addWidget(label)

        self.text_edit = QTextEdit()
        layout.addWidget(self.text_edit)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def get_lines(self) -> List[str]:
        """
        Retrieves the entered text and splits it into a list of non-empty lines.
        """
        text = self.text_edit.toPlainText()
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        return lines

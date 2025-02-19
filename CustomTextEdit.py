from PyQt5.QtWidgets import QTextEdit
from PyQt5.QtCore import Qt, pyqtSignal

class CustomTextEdit(QTextEdit):
    """
    A custom QTextEdit that emits a signal on Enter (and inserts newline on Shift+Enter).
    """
    returnPressed = pyqtSignal()  # Define a custom signal

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setPlaceholderText("Type your message here. Press Enter to send; Shift+Enter for new line.")

    def keyPressEvent(self, event):
        # Check for Enter key without Shift
        if event.key() in (Qt.Key_Return, Qt.Key_Enter) and not (event.modifiers() & Qt.ShiftModifier):
            self.returnPressed.emit()  # Emit the signal instead of directly calling a parent method
            event.accept()
        else:
            super().keyPressEvent(event)
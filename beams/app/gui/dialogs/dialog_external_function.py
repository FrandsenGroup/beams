from PyQt5 import QtWidgets, QtCore, QtGui

from app.gui.dialogs.dialog_misc import WarningMessageDialog
from app.model import fit
from app.util import qt_widgets
import sympy as sp


class ExternalFunctionDialog(QtWidgets.QDialog):
    def __init__(self, function_invocation):
        super(ExternalFunctionDialog, self).__init__()
        self.import_button = qt_widgets.StyleOneButton('Save')
        self.cancel_button = qt_widgets.StyleOneButton('Cancel')

        self.question_text = QtWidgets.QLabel()
        self.function_text = QtWidgets.QLabel()

        self.function_invocation = function_invocation

        self.setMinimumWidth(600)
        self._set_widget_attributes()
        self._set_widget_layout()

        self._presenter = ExternalFunctionDialogPresenter(self)

    def _set_widget_attributes(self):
        self.import_button.setText("Save")
        self.import_button.setMinimumWidth(60)

        self.cancel_button.setText("Cancel")
        self.cancel_button.setMinimumWidth(60)

        self.question_text.setText("Import function with the following invocation?")

        monospace_font = QtGui.QFont()
        monospace_font.setFamily("Courier")

        self.function_text.setText(self.function_invocation)
        self.function_text.setFont(monospace_font)

    def _set_widget_layout(self):
        main_layout = QtWidgets.QVBoxLayout()

        main_layout.addWidget(self.question_text)
        main_layout.addWidget(self.function_text)

        button_row_layout = QtWidgets.QHBoxLayout()
        button_row_layout.addWidget(self.cancel_button)
        button_row_layout.addWidget(self.import_button)

        main_layout.addLayout(button_row_layout)
        self.setLayout(main_layout)

    def copy_character_to_cursor(self, char):
        self.display_input.insert(char)


class ExternalFunctionDialogPresenter(QtCore.QObject):
    def __init__(self, view):
        super().__init__()
        self._view = view

        self._set_callbacks()

    def _set_callbacks(self):
        self._view.import_button.released.connect(self._save_function_name)
        self._view.cancel_button.released.connect(self._cancel)

    @QtCore.pyqtSlot()
    def _on_insert_character_clicked(self, character):
        self._view.copy_character_to_cursor(character)

    @QtCore.pyqtSlot()
    def _save_function_name(self):
            self._view.accept()

    @QtCore.pyqtSlot()
    def _cancel(self):
        self._view.reject()

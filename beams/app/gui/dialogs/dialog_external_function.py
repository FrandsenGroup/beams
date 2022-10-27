from PyQt5 import QtWidgets, QtCore

from app.gui.dialogs.dialog_misc import WarningMessageDialog
from app.model import fit
from app.util import qt_widgets
import sympy as sp



class ExternalFunctionDialog(QtWidgets.QDialog):
    def __init__(self):
        super(ExternalFunctionDialog, self).__init__()
        self.display_input = QtWidgets.QLineEdit()
        self.save_button = qt_widgets.StyleOneButton('Save')

        self.insert_phi = qt_widgets.StyleTwoButton(fit.PHI)
        self.insert_alpha = qt_widgets.StyleTwoButton(fit.ALPHA)
        self.insert_sigma = qt_widgets.StyleTwoButton(fit.SIGMA)
        self.insert_naught = qt_widgets.StyleTwoButton(fit.NAUGHT)
        self.insert_lambda = qt_widgets.StyleTwoButton(fit.LAMBDA)
        self.insert_delta = qt_widgets.StyleTwoButton(fit.DELTA)
        self.insert_beta = qt_widgets.StyleTwoButton(fit.BETA)
        self.insert_pi = qt_widgets.StyleOneButton(fit.PI)
        self.insert_nu = qt_widgets.StyleOneButton(fit.NU)

        self.setMinimumWidth(600)
        self._set_widget_attributes()
        self._set_widget_layout()

        self._presenter = ExternalFunctionDialogPresenter(self)

    def _set_widget_attributes(self):
        self.display_input.setPlaceholderText("Input function invocation")
        self.save_button.setText("Save")
        self.save_button.setMinimumWidth(60)

    def _set_widget_layout(self):
        main_layout = QtWidgets.QVBoxLayout()

        input_row_layout = QtWidgets.QHBoxLayout()
        input_row_layout.addWidget(self.display_input)
        input_row_layout.addWidget(self.save_button)
        main_layout.addLayout(input_row_layout)

        symbol_row_layout = QtWidgets.QHBoxLayout()
        symbol_row_layout.addWidget(self.insert_phi)
        symbol_row_layout.addWidget(self.insert_alpha)
        symbol_row_layout.addWidget(self.insert_sigma)
        symbol_row_layout.addWidget(self.insert_naught)
        symbol_row_layout.addWidget(self.insert_lambda)
        symbol_row_layout.addWidget(self.insert_delta)
        symbol_row_layout.addWidget(self.insert_beta)
        symbol_row_layout.addWidget(self.insert_pi)
        symbol_row_layout.addWidget(self.insert_nu)

        main_layout.addLayout(symbol_row_layout)
        self.setLayout(main_layout)

    def copy_character_to_cursor(self, char):
        self.display_input.insert(char)


class ExternalFunctionDialogPresenter(QtCore.QObject):
    def __init__(self, view):
        super().__init__()
        self._view = view

        self._set_callbacks()

    def _set_callbacks(self):
        self._view.insert_sigma.released.connect(lambda: self._on_insert_character_clicked(fit.SIGMA))
        self._view.insert_pi.released.connect(lambda: self._on_insert_character_clicked(fit.PI))
        self._view.insert_phi.released.connect(lambda: self._on_insert_character_clicked(fit.PHI))
        self._view.insert_naught.released.connect(lambda: self._on_insert_character_clicked(fit.NAUGHT))
        self._view.insert_lambda.released.connect(lambda: self._on_insert_character_clicked(fit.LAMBDA))
        self._view.insert_delta.released.connect(lambda: self._on_insert_character_clicked(fit.DELTA))
        self._view.insert_alpha.released.connect(lambda: self._on_insert_character_clicked(fit.ALPHA))
        self._view.insert_beta.released.connect(lambda: self._on_insert_character_clicked(fit.BETA))
        self._view.insert_nu.released.connect(lambda: self._on_insert_character_clicked(fit.NU))

        self._view.save_button.released.connect(self._save_function_name)

    @QtCore.pyqtSlot()
    def _on_insert_character_clicked(self, character):
        self._view.copy_character_to_cursor(character)

    @QtCore.pyqtSlot()
    def _save_function_name(self):
        text = self._view.display_input.text()
        try:
            syms = [v for v in sp.sympify(text).atoms(sp.Symbol)]
            ascii_syms = fit.convert_symbols_to_ascii(syms)
        except:
            WarningMessageDialog.launch(["Function call must be of the form 'func(sym1, sym2, ..., symN)'"])
        pass
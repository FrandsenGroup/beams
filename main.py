# Basics for Efficient Analysis of Muon Spin-Spectroscopy

import BEAMS_App_Library
import sys
from PyQt5 import QtWidgets, QtGui

app = QtWidgets.QApplication(sys.argv)
GUI = BEAMS_App_Library.Window()
GUI.show()
sys.exit(app.exec_())
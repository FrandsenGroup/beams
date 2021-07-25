
import socket
import enum

from PyQt5 import QtWidgets
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas, NavigationToolbar2QT
from matplotlib.figure import Figure

from app.util import qt_widgets, qt_constants


# noinspection PyArgumentList
class AddFileDialog(QtWidgets.QDialog):
    class Codes(enum.IntEnum):
        FILE_SYSTEM = 1
        MUSR_DOWNLOAD = 2
        PSI_DOWNLOAD = 3
        ISIS_DOWNLOAD = 4

    def __init__(self):
        super(AddFileDialog, self).__init__()

        self.setWindowTitle('Permission')
        message = QtWidgets.QLabel('Would you like to add files from the local file system or online.')
        self.pos_button = qt_widgets.StyleOneButton('From disk')
        self.neg_button = qt_widgets.StyleOneButton('From TRIUMF')
        self.psi_button = qt_widgets.StyleOneButton('From PSI')
        self.isis_button = qt_widgets.StyleOneButton('From ISIS')
        self.setMinimumWidth(300)
        self.setMinimumWidth(80)
        self.pos_button.setFixedWidth(100)
        self.neg_button.setFixedWidth(100)
        self.psi_button.setFixedWidth(100)
        self.isis_button.setFixedWidth(100)

        self.pos_button.released.connect(lambda: self.done(AddFileDialog.Codes.FILE_SYSTEM))
        self.neg_button.released.connect(lambda: self.done(AddFileDialog.Codes.MUSR_DOWNLOAD))
        self.psi_button.released.connect(lambda: self.done(AddFileDialog.Codes.PSI_DOWNLOAD))
        self.isis_button.released.connect(lambda: self.done(AddFileDialog.Codes.ISIS_DOWNLOAD))

        try:
            socket.create_connection(("www.google.com", 80))
        except OSError:
            self.neg_button.setEnabled(False)
            self.psi_button.setEnabled(False)
            self.isis_button.setEnabled(False)

        col = QtWidgets.QVBoxLayout()
        col.addWidget(message)

        col.setAlignment(message, qt_constants.AlignCenter)
        row = QtWidgets.QHBoxLayout()
        row.addWidget(self.pos_button)
        row.addWidget(self.neg_button)
        row.addWidget(self.isis_button)
        row.addWidget(self.psi_button)

        row.setAlignment(self.pos_button, qt_constants.AlignRight)
        row.setAlignment(self.neg_button, qt_constants.AlignLeft)
        row.setAlignment(self.psi_button, qt_constants.AlignCenter)
        col.addLayout(row)
        self.setLayout(col)

    @staticmethod
    def launch():
        dialog = AddFileDialog()
        return dialog.exec()


# noinspection PyArgumentList
class WarningMessageDialog(QtWidgets.QDialog):
    def __init__(self, args=None):
        super(WarningMessageDialog, self).__init__()
        if args:
            if len(args) == 2:
                pos_function = args[1]
                error_message = args[0]
            else:
                pos_function = None
                error_message = args[0]
        else:
            error_message = None
            pos_function = None

        self.setWindowTitle('Error')
        message = QtWidgets.QLabel(error_message)
        pos_button = qt_widgets.StyleOneButton('Okay')
        self.setMinimumWidth(300)
        self.setMinimumHeight(80)
        pos_button.setFixedWidth(80)

        if pos_function:
            pos_button.released.connect(lambda: pos_function())

        pos_button.released.connect(lambda: self.close())

        col = QtWidgets.QVBoxLayout()

        col.addWidget(message)
        col.addWidget(pos_button)
        col.setAlignment(message, qt_constants.AlignCenter)
        col.setAlignment(pos_button, qt_constants.AlignCenter)
        self.setLayout(col)

    @staticmethod
    def launch(args=None):
        dialog = WarningMessageDialog(args)
        return dialog.exec()


# noinspection PyArgumentList
class PermissionsMessageDialog(QtWidgets.QDialog):
    class Codes(enum.IntEnum):
        OKAY = 0
        CANCEL = 1

    def __init__(self, args):
        super(PermissionsMessageDialog, self).__init__()
        self.setWindowTitle('Permission')
        message = QtWidgets.QLabel(args[0])
        self.pos_button = qt_widgets.StyleOneButton('Okay')
        self.neg_button = qt_widgets.StyleTwoButton('Cancel')
        self.setMinimumWidth(300)
        self.setMinimumWidth(80)
        self.pos_button.setFixedWidth(80)
        self.neg_button.setFixedWidth(80)

        self.pos_button.released.connect(lambda: self.done(PermissionsMessageDialog.Codes.OKAY))

        self.neg_button.released.connect(lambda: self.done(PermissionsMessageDialog.Codes.CANCEL))

        self.neg_button.released.connect(lambda: self.close())
        self.pos_button.released.connect(lambda: self.close())

        col = QtWidgets.QVBoxLayout()
        col.addWidget(message)
        col.setAlignment(message, qt_constants.AlignCenter)
        row = QtWidgets.QHBoxLayout()
        row.addWidget(self.pos_button)
        row.addWidget(self.neg_button)
        row.setAlignment(self.pos_button, qt_constants.AlignRight)
        row.setAlignment(self.neg_button, qt_constants.AlignLeft)
        col.addLayout(row)
        self.setLayout(col)

    @staticmethod
    def launch(args):
        dialog = PermissionsMessageDialog(args)
        return dialog.exec()


# noinspection PyArgumentList
class IntegrationDisplayDialog(QtWidgets.QDialog):
    class IntegrationCanvas(FigureCanvas):
        def __init__(self):
            self._draw_pending = True
            self._is_drawing = True
            FigureCanvas.__init__(self, Figure())
            self.canvas_axes = self.figure.add_subplot(111, label='Canvas')

    class IntegrationToolbar(NavigationToolbar2QT):
        # only display the buttons we need
        NavigationToolbar2QT.toolitems = (
            ('Home', 'Reset original view', 'home', 'home'),
            ('Back', 'Back to previous view', 'back', 'back'),
            ('Forward', 'Forward to next view', 'forward', 'forward'),
            # (None, None, None, None),
            ('Pan', 'Pan axes with left mouse, zoom with right', 'move', 'pan'),
            ('Zoom', 'Zoom to rectangle', 'zoom_to_rect', 'zoom'),
            # ('Subplots', 'Configure subplots', 'subplots', 'configure_subplots'),
            # (None, None, None, None),
            ('Save', 'Save the figure', 'filesave', 'save_figure'),
        )

    def __init__(self, args):
        integration = args[0]
        x_axis_label = args[1]
        x_axis_data = args[2]

        super(IntegrationDisplayDialog, self).__init__()
        self._main = QtWidgets.QMainWindow()
        self.canvas = IntegrationDisplayDialog.IntegrationCanvas()
        self._main.addToolBar(IntegrationDisplayDialog.IntegrationToolbar(self.canvas, self._main))

        layout = QtWidgets.QVBoxLayout()
        self._main.setCentralWidget(self.canvas)
        layout.addWidget(self._main)
        self.setLayout(layout)

        self.canvas.canvas_axes.plot(x_axis_data, integration, linestyle='None', marker='o')
        self.canvas.canvas_axes.set_xlabel(x_axis_label)
        self.canvas.canvas_axes.set_ylabel("Integrated Asymmetry")

    @staticmethod
    def launch(args):
        dialog = IntegrationDisplayDialog(args)
        return dialog.exec()


# noinspection PyArgumentList
class FileDisplayDialog(QtWidgets.QDialog):
    def __init__(self, args):
        super(FileDisplayDialog, self).__init__()
        self.setWindowTitle(args[0])

        text_edit = QtWidgets.QPlainTextEdit()
        text_edit.setPlainText(args[1])
        text_edit.setWordWrapMode(False)
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(text_edit)

        self.setLayout(layout)
        self.setGeometry(500, 300, 400, 400)

    @staticmethod
    def launch(args):
        dialog = FileDisplayDialog(args)
        return dialog.exec()


# noinspection PyArgumentList
class ProgressBarDialog(QtWidgets.QProgressDialog):
    class Codes(enum.IntEnum):
        FINISHED = 0
        INTERRUPTED = 1

    def __init__(self, *args, **kwargs):
        super(ProgressBarDialog, self).__init__(*args, **kwargs)
        self.setModal(True)

    @staticmethod
    def launch(*args, **kwargs):
        dialog = ProgressBarDialog(*args, **kwargs)
        return dialog.exec()

    def update(self, value):
        self.setValue(value)

        if value == 100:
            self.done(self.Codes.FINISHED)

    def interrupt(self):
        self.done(self.Codes.INTERRUPTED)

    def cancel(self):
        self.done(self.Codes.INTERRUPTED)




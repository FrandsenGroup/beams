
import socket
import enum

from PyQt5 import QtWidgets, QtCore, QtGui
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas, NavigationToolbar2QT
from matplotlib.figure import Figure
import darkdetect

from app.util import qt_widgets, qt_constants, report
from app.resources import resources
from app.model import services


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

        self.pos_button.setToolTip("Select files from your computer")
        self.neg_button.setToolTip("Download files from TRIUMF")
        self.psi_button.setToolTip("Download files from PSI")
        self.isis_button.setToolTip("Download files from ISIS")

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
            pos_button.released.connect(pos_function)

        pos_button.released.connect(self.close)

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
class PromptWithOptionsDialog(QtWidgets.QDialog):
    def __init__(self, message, options):
        super().__init__()

        self.setWindowTitle('Choose an option')
        message = QtWidgets.QLabel(message)
        pos_button = qt_widgets.StyleOneButton('Okay')
        options_box = QtWidgets.QComboBox()

        options_box.addItems(options)
        self.setMinimumWidth(300)
        self.setMinimumHeight(80)
        pos_button.setFixedWidth(80)

        pos_button.released.connect(lambda: self.done(options_box.currentIndex()))

        col = QtWidgets.QVBoxLayout()

        col.addWidget(message)
        col.addWidget(options_box)
        col.addWidget(pos_button)
        col.setAlignment(options_box, qt_constants.AlignCenter)
        col.setAlignment(message, qt_constants.AlignCenter)
        col.setAlignment(pos_button, qt_constants.AlignCenter)
        self.setLayout(col)

    @staticmethod
    def launch(message, options):
        dialog = PromptWithOptionsDialog(message, options)
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

        self.neg_button.released.connect(self.close)
        self.pos_button.released.connect(self.close)

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


class NotificationDialog(QtWidgets.QDialog):
    def __init__(self, message, silence_message, okay_function):
        super(NotificationDialog, self).__init__()
        self.setWindowTitle('Notification')
        message = QtWidgets.QLabel(message)
        notify_box = QtWidgets.QCheckBox()
        silence_label = QtWidgets.QLabel("Do not show again." if silence_message is None else silence_message)
        pos_button = qt_widgets.StyleOneButton('Okay')
        self.setMinimumWidth(300)
        self.setMinimumHeight(80)
        pos_button.setFixedWidth(80)

        if okay_function:
            pos_button.released.connect(lambda: okay_function(notify_box.isChecked()))

        pos_button.released.connect(self.close)

        col = QtWidgets.QVBoxLayout()

        col.addWidget(message)
        row = QtWidgets.QHBoxLayout()
        row.addStretch()
        row.addWidget(notify_box)
        row.addWidget(silence_label)
        row.addStretch()
        col.addLayout(row)
        col.addWidget(pos_button)
        col.setAlignment(message, qt_constants.AlignCenter)
        col.setAlignment(pos_button, qt_constants.AlignCenter)
        self.setLayout(col)

    @staticmethod
    def launch(message, silence_message=None, okay_function=None):
        dialog = NotificationDialog(message, silence_message, okay_function)
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
            ('Pan', 'Pan axes with left mouse, zoom with right', 'move', 'pan'),
            ('Zoom', 'Zoom to rectangle', 'zoom_to_rect', 'zoom'),
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


class LoadingDialog(QtWidgets.QDialog):
    def __init__(self, message, worker):
        super(LoadingDialog, self).__init__()
        worker.signals.finished.connect(self._stop)
        self.setWindowTitle(" ")
        self.setModal(True)
        self.setWindowFlags(self.windowFlags() | qt_constants.Popup)

        self.message = QtWidgets.QLabel(message)
        font = QtGui.QFont()
        font.setBold(True)
        font.setPointSize(12)
        self.message.setFont(font)

        self.label = QtWidgets.QLabel()
        self.label.setGeometry(QtCore.QRect(25, 25, 225, 225))
        self.label.setMinimumSize(QtCore.QSize(200, 200))
        self.label.setMaximumSize(QtCore.QSize(200, 200))

        system_service = services.SystemService()
        style = system_service.get_theme_preference()
        if style == system_service.Themes.DEFAULT:
            if darkdetect.isDark():
                style = system_service.Themes.DARK
            else:
                style = system_service.Themes.LIGHT

        if style == system_service.Themes.DARK:
            self.movie = QtGui.QMovie(resources.DARK_LOADING_GIF)
        elif style == system_service.Themes.LIGHT:
            self.movie = QtGui.QMovie(resources.LIGHT_LOADING_GIF)

        self.label.setMovie(self.movie)

        layout = QtWidgets.QVBoxLayout()
        layout.setAlignment(qt_constants.AlignCenter)
        layout.addWidget(self.message, alignment=qt_constants.AlignCenter)
        layout.addWidget(self.label, alignment=qt_constants.AlignCenter)
        self.setLayout(layout)
        self.movie.start()

    @staticmethod
    def launch(message, worker):
        dialog = LoadingDialog(message, worker)
        dialog.exec()

    def _stop(self):
        self.done(0)

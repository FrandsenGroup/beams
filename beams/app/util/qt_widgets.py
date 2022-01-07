"""
Ever gone to StackOverflow and found the solution to your problem there all in a convenient class? This module is
full of custom widgets that either I made (some of the seemingly empty ones are so we can apply QSS to specific
buttons) or found online. Feel free to expand our useful little library!
"""
import os

from PyQt5 import QtWidgets, QtCore, QtGui

from app.resources import resources
from app.util import qt_constants
from app.gui.dialogs.dialog_misc import PermissionsMessageDialog
from app.model import services


class StyleOneButton(QtWidgets.QPushButton):
    """ A custom class so we can apply QSS to specific buttons. See the QSS stylesheet. """
    def __init__(self, *args):
        super(StyleOneButton, self).__init__(*args)


class StyleTwoButton(QtWidgets.QPushButton):
    """ A custom class so we can apply QSS to specific buttons. See the QSS stylesheet. """
    def __init__(self, *args):
        super(StyleTwoButton, self).__init__(*args)


class StyleThreeButton(QtWidgets.QPushButton):
    """ A custom class so we can apply QSS to specific buttons. See the QSS stylesheet. """
    def __init__(self, *args):
        super(StyleThreeButton, self).__init__(*args)


# noinspection PyArgumentList
class CollapsibleBox(QtWidgets.QWidget):
    """ A custom class that creates a box, like a QGroupBox, that can be collapsed. """

    def __init__(self, title="", parent=None, background='#ffffff'):
        """
        Parameters
        ----------
        title : string
            Title of box, this will show when the box is collapsed and expanded.
        parent : widget
            Parent widget.
        background : string
            Background color of the collapsible box.
        """

        super(CollapsibleBox, self).__init__(parent)
        self.__dumb_constant = False

        self.setAutoFillBackground(True)
        self.setBackgroundRole(QtGui.QPalette.Base)
        p = self.palette()
        p.setColor(self.backgroundRole(), QtGui.QColor(background))
        self.setPalette(p)

        self.toggle_button = QtWidgets.QToolButton(
            text=title, checkable=True, checked=False
        )

        text_color = '#070536' if background != '#070536' else '#ffffff'
        # self.toggle_button.setStyleSheet("QToolButton {{ border: none; color: {}; background: {}}}".format(text_color, background))
        self.toggle_button.setToolButtonStyle(
            qt_constants.ToolButtonTextBesideIcon
        )
        self.toggle_button.setArrowType(qt_constants.RightArrow)
        # self.toggle_button.pressed.connect(self.on_pressed)

        self.toggle_animation = QtCore.QParallelAnimationGroup(self)

        self.content_area = QtWidgets.QScrollArea(
            maximumHeight=0, minimumHeight=0
        )
        self.content_area.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed
        )
        self.content_area.setFrameShape(QtWidgets.QFrame.NoFrame)
        style = 'QScrollArea {{background: {}; color: white;}}'.format(background)
        self.content_area.setStyleSheet(style)

        add_button = StyleOneButton("+")
        lay = QtWidgets.QVBoxLayout(self)
        lay.setSpacing(0)
        lay.setContentsMargins(0, 0, 0, 0)
        row = QtWidgets.QHBoxLayout()
        row.addWidget(self.toggle_button)
        row.addStretch()
        # row.addWidget(add_button)
        lay.addLayout(row)
        lay.addWidget(self.content_area)

        self.toggle_animation.addAnimation(
            QtCore.QPropertyAnimation(self, b"minimumHeight")
        )
        self.toggle_animation.addAnimation(
            QtCore.QPropertyAnimation(self, b"maximumHeight")
        )
        self.toggle_animation.addAnimation(
            QtCore.QPropertyAnimation(self.content_area, b"maximumHeight")
        )

    def is_open(self):
        """ Returns a bool indicating whether or not the box is collapsed. """
        return self.__dumb_constant

    def on_pressed(self):
        """ Collapses or opens the box, depending on it's current state. """
        checked = self.__dumb_constant
        self.toggle_button.setArrowType(
            qt_constants.DownArrow if not checked else qt_constants.RightArrow
        )
        self.toggle_animation.setDirection(
            QtCore.QAbstractAnimation.Forward
            if not checked
            else QtCore.QAbstractAnimation.Backward
        )
        self.toggle_animation.start()
        self.__dumb_constant = not self.__dumb_constant

    def setContentLayout(self, layout):
        """ Sets the layout of the CollapsibleBox (this is everything you want to put in the box). """
        lay = self.content_area.layout()
        del lay
        self.content_area.setLayout(layout)
        collapsed_height = (
            self.sizeHint().height() - self.content_area.maximumHeight()
        )
        content_height = layout.sizeHint().height()
        for i in range(self.toggle_animation.animationCount()):
            animation = self.toggle_animation.animationAt(i)
            animation.setDuration(2)
            animation.setStartValue(collapsed_height)
            animation.setEndValue(collapsed_height + content_height)

        content_animation = self.toggle_animation.animationAt(
            self.toggle_animation.animationCount() - 1
        )
        content_animation.setDuration(2)
        content_animation.setStartValue(0)
        content_animation.setEndValue(content_height)


class StyleOneToolButton(QtWidgets.QToolButton):
    """ A custom class so we can apply QSS to specific buttons. See the QSS stylesheet. """
    def __init__(self):
        super(StyleOneToolButton, self).__init__()


class StyleOneDockWidget(QtWidgets.QDockWidget):
    """ A custom class so we can apply QSS to specific dock widgets. See the QSS stylesheet. """
    def __init__(self):
        super(StyleOneDockWidget, self).__init__()
        self.setAutoFillBackground(True)
        self.setBackgroundRole(QtGui.QPalette.Highlight)
        p = self.palette()
        p.setColor(self.backgroundRole(), QtGui.QColor('#070536'))
        self.setPalette(p)


class StyleOneListWidget(QtWidgets.QListWidget):
    """ A custom class so we can apply QSS to specific list widgets. See the QSS stylesheet. """
    def __init__(self):
        super(StyleOneListWidget, self).__init__()


class StyleOneMenuBar(QtWidgets.QMenuBar):
    def __init__(self):
        super(StyleOneMenuBar, self).__init__()


# noinspection PyArgumentList
class TitleBar(QtWidgets.QWidget):
    """ A title bar with customized window icon and window control tool buttons. """
    def __init__(self, parent):
        super(TitleBar, self).__init__()
        self.parent = parent
        self.setParent(parent)

        self.__system_service = services.SystemService()
        self.__file_service = services.FileService()

        self.setContentsMargins(0, 0, 0, 0)

        self.setAutoFillBackground(True)
        self.setBackgroundRole(QtGui.QPalette.Base)
        p = self.palette()
        p.setColor(self.backgroundRole(), QtGui.QColor('#f2f2f2'))
        self.setPalette(p)
        self.setStyleSheet(" TitleBar {"
                           "border-style: solid;"
                           "border-width: 5px;"
                           "border-color: #ffffff"
                           "}")

        self.minimize = StyleOneToolButton()
        self.minimize.setFixedWidth(60)
        self.minimize.setFixedHeight(45)

        self.maximize = StyleOneToolButton()
        self.maximize.setFixedWidth(60)
        self.maximize.setFixedHeight(45)

        self.close = StyleOneToolButton()
        self.close.setFixedWidth(60)
        self.close.setFixedHeight(45)
        self.close.setStyleSheet("StyleOneToolButton:hover:!pressed { background-color: #ff3333 }")

        pix = QtGui.QIcon(resources.CLOSE_IMAGE)
        self.close.setIcon(pix)
        self.close.setIconSize(QtCore.QSize(12, 12))

        self._max_pix = QtGui.QIcon(resources.MAXIMIZE_IMAGE)
        self._restore_pix = QtGui.QIcon(resources.RESTORE_IMAGE)
        self.maximize.setIcon(self._max_pix)
        self.maximize.setIconSize(QtCore.QSize(12, 12))

        pix = QtGui.QIcon(resources.MINIMIZE_IMAGE)
        self.minimize.setIcon(pix)
        self.minimize.setIconSize(QtCore.QSize(12, 12))

        self.minimize.setMinimumHeight(25)
        self.maximize.setMinimumHeight(25)
        self.close.setMinimumHeight(25)

        self.menu_bar = StyleOneMenuBar()
        self.menu_bar.setFixedWidth(40)

        self.menu = QtWidgets.QMenu("&File", self.menu_bar)
        self.menu.setIcon(QtGui.QIcon(resources.MENU_IMAGE))
        self.menu.addAction("&Save Session", self._action_save)
        self.menu.addAction("&Open Session", self._action_open)

        self.menu_bar.addMenu(self.menu)

        row = QtWidgets.QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        row.addSpacing(15)
        col = QtWidgets.QVBoxLayout()
        col.setContentsMargins(0, 0, 0, 0)
        col.addSpacing(8)
        col.addWidget(self.menu_bar)
        row.addLayout(col)
        col = QtWidgets.QVBoxLayout()
        col.setContentsMargins(0, 0, 0, 0)
        col.addSpacing(5)
        col.addWidget(Logo())
        row.addLayout(col)
        row.addWidget(self.minimize)
        row.addWidget(self.maximize)
        row.addWidget(self.close)

        row.setSpacing(0)

        self._max_normal = False
        self._start_pos = None
        self._click_pos = None
        self.setMaximumHeight(40)

        self._set_callbacks()

    def _action_open(self):
        open_file = QtWidgets.QFileDialog.getOpenFileName(self, 'Open Session',
                                                          self.__system_service.get_last_used_directory(),
                                                          "Beams Session (*.beams)")

        open_file = [path for path in open_file if path != '']
        if len(open_file) > 0:
            code = PermissionsMessageDialog.launch(
                ["Opening a saved session will remove all current session data, do you wish to continue?"])
            if code == PermissionsMessageDialog.Codes.OKAY:
                print(self.__file_service.signals)
                self.__file_service.add_files([open_file[0]])
                self.__file_service.load_session(self.__file_service.get_file_by_path(open_file[0]).id)

    def _action_save(self):
        save_file = QtWidgets.QFileDialog.getSaveFileName(self, 'Save Session',
                                                          self.__system_service.get_last_used_directory(),
                                                          "Beams Session (*.beams)")

        save_file = [path for path in save_file if path != '']
        if len(save_file) > 0:
            path = os.path.split(save_file[0])
            self.__file_service.save_session(save_file[0])
            self.__system_service.set_last_used_directory(path[0])

    def _set_callbacks(self):
        self.close.clicked.connect(self._close)
        self.minimize.clicked.connect(self._show_small)
        self.maximize.clicked.connect(self._show_max_restored)

    def _close(self):
        self.parentWidget().close()

    def _show_small(self):
        self.parentWidget().showMinimized()

    def _show_max_restored(self):
        if self._max_normal:
            self.parentWidget().showNormal()
            self._max_normal = not self._max_normal
            self.maximize.setIcon(self._max_pix)
        else:
            self.parentWidget().showMaximized()
            self._max_normal = not self._max_normal
            self.maximize.setIcon(self._restore_pix)

        self.maximize.setIconSize(QtCore.QSize(12, 12))

    def mousePressEvent(self, me: QtGui.QMouseEvent):
        self._start_pos = me.globalPos()
        try:
            self._click_pos = self.mapToParent(me.pos())
        except Exception as e:
            print(e)

    def mouseMoveEvent(self, me: QtGui.QMouseEvent):
        if self._max_normal:
            return

        self.parentWidget().move(me.globalPos() - self._click_pos)


# noinspection PyArgumentList
class Frame(QtWidgets.QFrame):
    """ A custom frame for the main window so we can control the background color of the entire application. """
    def __init__(self):
        super(Frame, self).__init__()

        self._m_mouse_down = False
        self.setFrameShape(QtWidgets.QFrame.Panel)
        self.setWindowFlags(qt_constants.FramelessWindowHint)
        self.setMouseTracking(True)

        self.title_bar = TitleBar(self)
        self.title_bar.setParent(self)

        self._m_content = QtWidgets.QWidget()

        col = QtWidgets.QVBoxLayout(self)
        col.addWidget(self.title_bar)
        col.addWidget(Separator())
        col.setSpacing(0)
        col.setContentsMargins(QtCore.QMargins(0, 0, 0, 0))

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self._m_content)
        layout.setSpacing(0)
        layout.setContentsMargins(QtCore.QMargins(25, 0, 25, 25))
        col.addLayout(layout)

        self._m_old_pos = None
        self._m_mouse_down = None
        self.__left = False
        self.__right = False
        self.__bottom = False

        self.setAutoFillBackground(True)
        self.setBackgroundRole(QtGui.QPalette.Base)
        p = self.palette()
        p.setColor(self.backgroundRole(), QtGui.QColor('#ffffff'))
        self.setPalette(p)

    def content_widget(self):
        return self._m_content

    def title_bar(self):
        return self.title_bar

    def mousePressEvent(self, me: QtGui.QMouseEvent):
        self._m_old_pos = me.pos()
        self._m_mouse_down = me.button() == qt_constants.LeftButton

    def mouseMoveEvent(self, me: QtGui.QMouseEvent):
        x = me.x()
        y = me.y()

        if self._m_mouse_down:
            dx = x - self._m_old_pos.x()
            dy = y - self._m_old_pos.y()

            g = self.geometry()

            if self.__left:
                g.setLeft(g.left() + dx)
            if self.__right:
                g.setRight(g.right() + dx)
            if self.__bottom:
                g.setBottom(g.bottom() + dy)

            self.setGeometry(g)

            self._m_old_pos = QtCore.QPoint(me.x() if not self.__left else self._m_old_pos.x(), me.y())
        else:
            r = self.rect()
            self.__left = QtCore.qAbs(x - r.left()) <= 2
            self.__right = QtCore.qAbs(x - r.right()) <= 2
            self.__bottom = QtCore.qAbs(y - r.bottom()) <= 2
            hor = self.__left or self.__right

            if hor and self.__bottom:
                if self.__left:
                    self.setCursor(qt_constants.SizeBDiagCursor)
                else:
                    self.setCursor(qt_constants.SizeFDiagCursor)
            elif hor:
                self.setCursor(qt_constants.SizeHorCursor)
            elif self.__bottom:
                self.setCursor(qt_constants.SizeVerCursor)
            else:
                self.setCursor(qt_constants.ArrowCursor)

    def mouseReleaseEvent(self, me: QtGui.QMouseEvent):
        self._m_mouse_down = False


# noinspection PyArgumentList
class Separator(QtWidgets.QFrame):
    """ A custom widget thats acts as a visual separating line. """
    def __init__(self):
        super(Separator, self).__init__()
        self.setFrameShape(QtWidgets.QFrame.HLine)
        # self.setSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Expanding)
        self.setFixedHeight(1)
        self.setAutoFillBackground(True)
        self.setBackgroundRole(QtGui.QPalette.Highlight)
        p = self.palette()
        p.setColor(self.backgroundRole(), QtGui.QColor('#000000'))
        self.setPalette(p)


# noinspection PyArgumentList
class Logo(QtWidgets.QLabel):
    """ A custom widget for our logo. """
    def __init__(self):
        super(Logo, self).__init__()
        logo_icon_pixmap = QtGui.QPixmap(resources.LOGO_IMAGE)
        self.setPixmap(logo_icon_pixmap.scaledToHeight(30, qt_constants.SmoothTransformation))
        self.setMask(logo_icon_pixmap.mask())


class StyleOneLabel(QtWidgets.QLabel):
    """ A custom class so we can apply QSS to specific labels. See the QSS stylesheet. """
    def __init__(self, *args):
        super(StyleOneLabel, self).__init__(*args)


class IdentifiableListWidgetItem(QtWidgets.QListWidgetItem):
    """ A custom class so we can store an identifier in a list widget item.

        This keeps us from having to use titles or other temporary strings to use in lookups in the database.
        E.g. We used to use the run titles in the list on the plotting window to look up the runs that were selected,
            this way we can use the actual identifier associated with the run and store it with the widget.
    """
    def __init__(self, identifier, *pars, **kwargs):
        super().__init__(*pars, **kwargs)
        self.identifier = identifier


class IdentifiableTableWidgetItem(QtWidgets.QTableWidgetItem):
    """ A custom class so we can store an identifier in a list widget item.

        This keeps us from having to use titles or other temporary strings to use in lookups in the database.
        E.g. We used to use the run titles in the list on the plotting window to look up the runs that were selected,
            this way we can use the actual identifier associated with the run and store it with the widget.
    """
    def __init__(self, identifier, *pars, **kwargs):
        super().__init__(*pars, **kwargs)
        self.identifier = identifier

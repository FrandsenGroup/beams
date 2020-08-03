
import abc
import enum

from PyQt5 import QtWidgets, QtCore, QtGui


class StyleOneButton(QtWidgets.QPushButton):
    def __init__(self, *args):
        super(StyleOneButton, self).__init__(*args)


class StyleTwoButton(QtWidgets.QPushButton):
    def __init__(self, *args):
        super(StyleTwoButton, self).__init__(*args)


class StyleThreeButton(QtWidgets.QPushButton):
    def __init__(self, *args):
        super(StyleThreeButton, self).__init__(*args)


# noinspection PyArgumentList
class CollapsibleBox(QtWidgets.QWidget):
    def __init__(self, title="", parent=None):
        super(CollapsibleBox, self).__init__(parent)
        self.__dumb_constant = False

        self.toggle_button = QtWidgets.QToolButton(
            text=title, checkable=True, checked=False
        )
        self.toggle_button.setStyleSheet("QToolButton { border: none; }")
        self.toggle_button.setToolButtonStyle(
            QtCore.Qt.ToolButtonTextBesideIcon
        )
        self.toggle_button.setArrowType(QtCore.Qt.RightArrow)
        # self.toggle_button.pressed.connect(self.on_pressed)

        self.toggle_animation = QtCore.QParallelAnimationGroup(self)

        self.content_area = QtWidgets.QScrollArea(
            maximumHeight=0, minimumHeight=0
        )
        self.content_area.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed
        )
        self.content_area.setFrameShape(QtWidgets.QFrame.NoFrame)

        lay = QtWidgets.QVBoxLayout(self)
        lay.setSpacing(0)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.toggle_button)
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
        return self.__dumb_constant

    def on_pressed(self):
        checked = self.__dumb_constant
        self.toggle_button.setArrowType(
            QtCore.Qt.DownArrow if not checked else QtCore.Qt.RightArrow
        )
        self.toggle_animation.setDirection(
            QtCore.QAbstractAnimation.Forward
            if not checked
            else QtCore.QAbstractAnimation.Backward
        )
        self.toggle_animation.start()
        self.__dumb_constant = not self.__dumb_constant

    def setContentLayout(self, layout):
        lay = self.content_area.layout()
        del lay
        self.content_area.setLayout(layout)
        collapsed_height = (
            self.sizeHint().height() - self.content_area.maximumHeight()
        )
        content_height = layout.sizeHint().height()
        for i in range(self.toggle_animation.animationCount()):
            animation = self.toggle_animation.animationAt(i)
            animation.setDuration(200)
            animation.setStartValue(collapsed_height)
            animation.setEndValue(collapsed_height + content_height)

        content_animation = self.toggle_animation.animationAt(
            self.toggle_animation.animationCount() - 1
        )
        content_animation.setDuration(200)
        content_animation.setStartValue(0)
        content_animation.setEndValue(content_height)


# noinspection PyArgumentList
class TitleBar(QtWidgets.QWidget):
    def __init__(self, parent):
        super(TitleBar, self).__init__()
        self.parent = parent
        self.setParent(parent)
        self.setAutoFillBackground(True)
        self.setBackgroundRole(QtGui.QPalette.Highlight)

        self.minimize = QtWidgets.QToolButton()
        self.maximize = QtWidgets.QToolButton()
        self.close = QtWidgets.QToolButton()

        pix = QtGui.QIcon(self.style().standardPixmap(QtWidgets.QStyle.SP_TitleBarCloseButton))
        self.close.setIcon(pix)

        self._max_pix = QtGui.QIcon(self.style().standardPixmap(QtWidgets.QStyle.SP_TitleBarMaxButton))
        self._restore_pix = QtGui.QIcon(self.style().standardPixmap(QtWidgets.QStyle.SP_TitleBarNormalButton))
        self.maximize.setIcon(self._max_pix)

        pix = QtGui.QIcon(self.style().standardPixmap(QtWidgets.QStyle.SP_TitleBarMinButton))
        self.minimize.setIcon(pix)

        self.minimize.setMinimumHeight(20)
        self.maximize.setMinimumHeight(20)
        self.close.setMinimumHeight(20)

        # self.parentWidget().setWindowTitle("BEAMS 1")

        row = QtWidgets.QHBoxLayout(self)
        row.addWidget(QtWidgets.QLabel("BEAMS 2"))
        row.addWidget(self.minimize)
        row.addWidget(self.maximize)
        row.addWidget(self.close)

        row.insertStretch(1, 500)
        row.setSpacing(0)

        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)

        self._max_normal = False
        self._start_pos = None
        self._click_pos = None

        self._set_callbacks()

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
    def __init__(self):
        super(Frame, self).__init__()

        self._m_mouse_down = False
        self.setFrameShape(QtWidgets.QFrame.Panel)
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.setMouseTracking(True)

        self._m_title_bar = TitleBar(self)
        self._m_title_bar.setParent(self)

        self._m_content = QtWidgets.QWidget()

        col = QtWidgets.QVBoxLayout(self)
        col.addWidget(self._m_title_bar)
        col.setSpacing(0)
        col.setContentsMargins(QtCore.QMargins(0, 0, 0, 0))

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self._m_content)
        layout.setSpacing(0)
        layout.setContentsMargins(QtCore.QMargins(5, 5, 5, 5))
        col.addLayout(layout)

        self._m_old_pos = None
        self._m_mouse_down = None
        self.__left = False
        self.__right = False
        self.__bottom = False

    def content_widget(self):
        return self._m_content

    def title_bar(self):
        return self._m_title_bar

    def mousePressEvent(self, me: QtGui.QMouseEvent):
        self._m_old_pos = me.pos()
        self._m_mouse_down = me.button() == QtCore.Qt.LeftButton

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
            self.__left = QtCore.qAbs(x - r.left()) <= 5
            self.__right = QtCore.qAbs(x - r.right()) <= 5
            self.__bottom = QtCore.qAbs(y - r.bottom()) <= 5
            hor = self.__left or self.__right

            if hor and self.__bottom:
                if self.__left:
                    self.setCursor(QtCore.Qt.SizeBDiagCursor)
                else:
                    self.setCursor(QtCore.Qt.SizeFDiagCursor)
            elif hor:
                self.setCursor(QtCore.Qt.SizeHorCursor)
            elif self.__bottom:
                self.setCursor(QtCore.Qt.SizeVerCursor)
            else:
                self.setCursor(QtCore.Qt.ArrowCursor)

    def mouseReleaseEvent(self, me: QtGui.QMouseEvent):
        self._m_mouse_down = False


if __name__ == '__main__':
    import sys

    app = QtWidgets.QApplication(sys.argv)
    box = Frame()
    box.move(0, 0)

    col = QtWidgets.QVBoxLayout(box.content_widget())
    col.setContentsMargins(QtCore.QMargins(0, 0, 0, 0))
    col.addWidget(QtWidgets.QTextEdit(box.content_widget()))

    box.show()
    app.exec()


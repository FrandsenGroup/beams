
import abc
import enum
from pathlib import Path
from app.resources import resources

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
    def __init__(self, title="", parent=None, background='#ffffff'):
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
        self.toggle_button.setStyleSheet("QToolButton {{ border: none; color: {}; background: {}}}".format(text_color, background))
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
    def __init__(self):
        super(StyleOneToolButton, self).__init__()


class StyleOneDockWidget(QtWidgets.QDockWidget):
    def __init__(self):
        super(StyleOneDockWidget, self).__init__()
        self.setAutoFillBackground(True)
        self.setBackgroundRole(QtGui.QPalette.Highlight)
        p = self.palette()
        p.setColor(self.backgroundRole(), QtGui.QColor('#070536'))
        self.setPalette(p)


class StyleOneListWidget(QtWidgets.QListWidget):
    def __init__(self):
        super(StyleOneListWidget, self).__init__()


# noinspection PyArgumentList
class TitleBar(QtWidgets.QWidget):
    def __init__(self, parent):
        super(TitleBar, self).__init__()
        self.parent = parent
        self.setParent(parent)
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
        self.maximize = StyleOneToolButton()
        self.close = StyleOneToolButton()

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

        row = QtWidgets.QHBoxLayout(self)
        row.addWidget(Logo())
        row.addWidget(self.minimize)
        row.addSpacing(25)
        row.addWidget(self.maximize)
        row.addSpacing(25)
        row.addWidget(self.close)
        row.addSpacing(15)

        row.setSpacing(0)

        self._max_normal = False
        self._start_pos = None
        self._click_pos = None
        self.setMaximumHeight(40)

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
        col.addWidget(Separator())
        col.setSpacing(0)
        col.setContentsMargins(QtCore.QMargins(0, 0, 0, 0))

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self._m_content)
        layout.setSpacing(0)
        layout.setContentsMargins(QtCore.QMargins(5, 5, 5, 5))
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
            self.__left = QtCore.qAbs(x - r.left()) <= 2
            self.__right = QtCore.qAbs(x - r.right()) <= 2
            self.__bottom = QtCore.qAbs(y - r.bottom()) <= 2
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


# noinspection PyArgumentList
class Separator(QtWidgets.QFrame):
    def __init__(self):
        super(Separator, self).__init__()
        self.setFrameShape(QtWidgets.QFrame.HLine)
        # self.setSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Expanding)
        self.setFixedHeight(0.75)
        self.setAutoFillBackground(True)
        self.setBackgroundRole(QtGui.QPalette.Highlight)
        p = self.palette()
        p.setColor(self.backgroundRole(), QtGui.QColor('#000000'))
        self.setPalette(p)


# noinspection PyArgumentList
class Logo(QtWidgets.QLabel):
    def __init__(self):
        super(Logo, self).__init__()
        logo_icon_pixmap = QtGui.QPixmap(resources.LOGO_IMAGE)
        self.setPixmap(logo_icon_pixmap.scaledToHeight(30, QtCore.Qt.SmoothTransformation))
        self.setMask(logo_icon_pixmap.mask())


class StyleOneLabel(QtWidgets.QLabel):
    def __init__(self, *args):
        super(StyleOneLabel, self).__init__(*args)


"""
The MIT License (MIT)
Copyright (c) 2012-2014 Alexander Turkin
Copyright (c) 2014 William Hallatt
Copyright (c) 2015 Jacob Dawid
Copyright (c) 2016 Luca Weiss
"""

import math

class QtWaitingSpinner(QtWidgets.QWidget):
    def __init__(self, parent, centerOnParent=True, disableParentWhenSpinning=False, modality=QtCore.Qt.NonModal):
        super().__init__(parent)

        self._centerOnParent = centerOnParent
        self._disableParentWhenSpinning = disableParentWhenSpinning

        # WAS IN initialize()
        self._color = QtGui.QColor(QtCore.Qt.black)
        self._roundness = 100.0
        self._minimumTrailOpacity = 3.14159265358979323846
        self._trailFadePercentage = 80.0
        self._revolutionsPerSecond = 1.57079632679489661923
        self._numberOfLines = 20
        self._lineLength = 10
        self._lineWidth = 2
        self._innerRadius = 10
        self._currentCounter = 0
        self._isSpinning = False

        self._timer = QtCore.QTimer(self)
        self._timer.timeout.connect(self.rotate)
        self.updateSize()
        self.updateTimer()
        self.hide()
        # END initialize()

        self.setWindowModality(modality)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)

    def paintEvent(self, QPaintEvent):
        self.updatePosition()
        painter = QtGui.QPainter(self)
        painter.fillRect(self.rect(), QtCore.Qt.transparent)
        painter.setRenderHint(QtGui.QPainter.Antialiasing, True)

        if self._currentCounter >= self._numberOfLines:
            self._currentCounter = 0

        painter.setPen(QtCore.Qt.NoPen)
        for i in range(0, self._numberOfLines):
            painter.save()
            painter.translate(self._innerRadius + self._lineLength, self._innerRadius + self._lineLength)
            rotateAngle = float(360 * i) / float(self._numberOfLines)
            painter.rotate(rotateAngle)
            painter.translate(self._innerRadius, 0)
            distance = self.lineCountDistanceFromPrimary(i, self._currentCounter, self._numberOfLines)
            color = self.currentLineColor(distance, self._numberOfLines, self._trailFadePercentage,
                                          self._minimumTrailOpacity, self._color)
            painter.setBrush(color)
            painter.drawRoundedRect(QtCore.QRect(0, -self._lineWidth / 2, self._lineLength, self._lineWidth), self._roundness,
                                    self._roundness, QtCore.Qt.RelativeSize)
            painter.restore()

    def start(self):
        self.updatePosition()
        self._isSpinning = True
        self.show()

        if self.parentWidget and self._disableParentWhenSpinning:
            self.parentWidget().setEnabled(False)

        if not self._timer.isActive():
            self._timer.start()
            self._currentCounter = 0

    def stop(self):
        self._isSpinning = False
        self.hide()

        if self.parentWidget() and self._disableParentWhenSpinning:
            self.parentWidget().setEnabled(True)

        if self._timer.isActive():
            self._timer.stop()
            self._currentCounter = 0

    def setNumberOfLines(self, lines):
        self._numberOfLines = lines
        self._currentCounter = 0
        self.updateTimer()

    def setLineLength(self, length):
        self._lineLength = length
        self.updateSize()

    def setLineWidth(self, width):
        self._lineWidth = width
        self.updateSize()

    def setInnerRadius(self, radius):
        self._innerRadius = radius
        self.updateSize()

    def color(self):
        return self._color

    def roundness(self):
        return self._roundness

    def minimumTrailOpacity(self):
        return self._minimumTrailOpacity

    def trailFadePercentage(self):
        return self._trailFadePercentage

    def revolutionsPersSecond(self):
        return self._revolutionsPerSecond

    def numberOfLines(self):
        return self._numberOfLines

    def lineLength(self):
        return self._lineLength

    def lineWidth(self):
        return self._lineWidth

    def innerRadius(self):
        return self._innerRadius

    def isSpinning(self):
        return self._isSpinning

    def setRoundness(self, roundness):
        self._roundness = max(0.0, min(100.0, roundness))

    def setColor(self, color=QtCore.Qt.black):
        self._color = QtGui.QColor(color)

    def setRevolutionsPerSecond(self, revolutionsPerSecond):
        self._revolutionsPerSecond = revolutionsPerSecond
        self.updateTimer()

    def setTrailFadePercentage(self, trail):
        self._trailFadePercentage = trail

    def setMinimumTrailOpacity(self, minimumTrailOpacity):
        self._minimumTrailOpacity = minimumTrailOpacity

    def rotate(self):
        self._currentCounter += 1
        if self._currentCounter >= self._numberOfLines:
            self._currentCounter = 0
        self.update()

    def updateSize(self):
        size = (self._innerRadius + self._lineLength) * 2
        self.setFixedSize(size, size)

    def updateTimer(self):
        self._timer.setInterval(1000 / (self._numberOfLines * self._revolutionsPerSecond))

    def updatePosition(self):
        if self.parentWidget() and self._centerOnParent:
            self.move(self.parentWidget().width() / 2 - self.width() / 2,
                      self.parentWidget().height() / 2 - self.height() / 2)

    def lineCountDistanceFromPrimary(self, current, primary, totalNrOfLines):
        distance = primary - current
        if distance < 0:
            distance += totalNrOfLines
        return distance

    def currentLineColor(self, countDistance, totalNrOfLines, trailFadePerc, minOpacity, colorinput):
        color = QtGui.QColor(colorinput)
        if countDistance == 0:
            return color
        minAlphaF = minOpacity / 100.0
        distanceThreshold = int(math.ceil((totalNrOfLines - 1) * trailFadePerc / 100.0))
        if countDistance > distanceThreshold:
            color.setAlphaF(minAlphaF)
        else:
            alphaDiff = color.alphaF() - minAlphaF
            gradient = alphaDiff / float(distanceThreshold + 1)
            resultAlpha = color.alphaF() - gradient * countDistance
            # If alpha is out of bounds, clip it.
            resultAlpha = min(1.0, max(0.0, resultAlpha))
            color.setAlphaF(resultAlpha)
        return color




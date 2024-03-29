"""
This module stores the constants used from Qt to make it backwards compatible with older version of PyQt5, as they
moved their constants relatively recently so it is best if both are supported.
"""

from PyQt5 import QtCore, QtWidgets

# If we run in to an exception here we know they are using a new version of PyQt5
try:
    Checked = QtCore.Qt.Checked
    Unchecked = QtCore.Qt.Unchecked
    PartiallyChecked = QtCore.Qt.PartiallyChecked
    CustomContextMenu = QtCore.Qt.CustomContextMenu
    Horizontal = QtCore.Qt.Horizontal
    ToolButtonTextBesideIcon = QtCore.Qt.ToolButtonTextBesideIcon
    AlignCenter = QtCore.Qt.AlignCenter
    AlignRight = QtCore.Qt.AlignRight
    AlignLeft = QtCore.Qt.AlignLeft
    ItemIsUserCheckable = QtCore.Qt.ItemIsUserCheckable
    RightArrow = QtCore.Qt.RightArrow
    DownArrow = QtCore.Qt.DownArrow
    FramelessWindowHint = QtCore.Qt.FramelessWindowHint
    LeftButton = QtCore.Qt.LeftButton
    SizeBDiagCursor = QtCore.Qt.SizeBDiagCursor
    SizeFDiagCursor = QtCore.Qt.SizeFDiagCursor
    SizeHorCursor = QtCore.Qt.SizeHorCursor
    SizeVerCursor = QtCore.Qt.SizeVerCursor
    ArrowCursor = QtCore.Qt.ArrowCursor
    SmoothTransformation = QtCore.Qt.SmoothTransformation
    NonModal = QtCore.Qt.NonModal
    Black = QtCore.Qt.black
    LeftDockWidgetArea = QtCore.Qt.LeftDockWidgetArea
    RightDockWidgetArea = QtCore.Qt.RightDockWidgetArea
    ScrollBarAsNeeded = QtCore.Qt.ScrollBarAsNeeded
    WA_TranslucentBackground = QtCore.Qt.WA_TranslucentBackground
    Transparent = QtCore.Qt.transparent
    NoPen = QtCore.Qt.NoPen
    RelativeSize = QtCore.Qt.RelativeSize
    NoEditTriggers = QtWidgets.QAbstractItemView.NoEditTriggers
    Popup = QtCore.Qt.Popup
    ItemIsEditable = QtCore.Qt.ItemIsEditable
    ExtendedSelection = QtWidgets.QAbstractItemView.ExtendedSelection
    ToolTipRole = QtCore.Qt.ToolTipRole

except AttributeError:
    Checked = QtCore.Qt.CheckState.Checked
    Unchecked = QtCore.Qt.CheckState.Unchecked
    PartiallyChecked = QtCore.Qt.CheckState.PartiallyChecked
    CustomContextMenu = QtCore.Qt.ContextMenuPolicy.CustomContextMenu
    Horizontal = QtCore.Qt.Orientation.Horizontal
    ToolButtonTextBesideIcon = QtCore.Qt.ToolButtonStyle.ToolButtonTextBesideIcon
    AlignCenter = QtCore.Qt.AlignmentFlag.AlignCenter
    AlignRight = QtCore.Qt.AlignmentFlag.AlignRight
    AlignLeft = QtCore.Qt.AlignmentFlag.AlignLeft
    ItemIsUserCheckable = QtCore.Qt.ItemFlag.ItemIsUserCheckable
    RightArrow = QtCore.Qt.ArrowType.RightArrow
    DownArrow = QtCore.Qt.ArrowType.DownArrow
    FramelessWindowHint = QtCore.Qt.WindowType.FramelessWindowHint
    LeftButton = QtCore.Qt.MouseButton.LeftButton
    SizeBDiagCursor = QtCore.Qt.CursorShape.SizeBDiagCursor
    SizeFDiagCursor = QtCore.Qt.CursorShape.SizeFDiagCursor
    SizeHorCursor = QtCore.Qt.CursorShape.SizeHorCursor
    SizeVerCursor = QtCore.Qt.CursorShape.SizeVerCursor
    ArrowCursor = QtCore.Qt.CursorShape.ArrowCursor
    SmoothTransformation = QtCore.Qt.TransformationMode.SmoothTransformation
    NonModal = QtCore.Qt.WindowModality.NonModal
    Black = QtCore.Qt.GlobalColor.black
    LeftDockWidgetArea = QtCore.Qt.DockWidgetArea.LeftDockWidgetArea
    RightDockWidgetArea = QtCore.Qt.DockWidgetArea.RightDockWidgetArea
    ScrollBarAsNeeded = QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded
    WA_TranslucentBackground = QtCore.Qt.WidgetAttribute.WA_TranslucentBackground
    Transparent = QtCore.Qt.GlobalColor.transparent
    NoPen = QtCore.Qt.PenStyle.NoPen
    RelativeSize = QtCore.Qt.SizeMode.RelativeSize
    NoEditTriggers = QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers
    Popup = QtCore.Qt.WindowType.Popup
    ItemIsEditable = QtCore.Qt.ItemFlag.ItemIsEditable
    ExtendedSelection = QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection
    ToolTipRole = QtCore.Qt.ItemDataRole.ToolTipRole

from enum import Enum
from typing import List, Optional

from qthandy import vbox, transparent, clear_layout, line, margins, decr_font, hbox
from qtpy.QtCore import Qt, Signal, QSize, QPropertyAnimation, QEasingCurve, QPoint, QObject, QEvent, QTimer
from qtpy.QtGui import QAction, QRegion, QMouseEvent, QCursor, QShowEvent, QHideEvent
from qtpy.QtWidgets import QApplication, QAbstractButton, QToolButton, QLabel, QFrame, QWidget, QPushButton, QMenu, \
    QScrollArea


def wrap(widget: QWidget, margin_left: int = 0, margin_top: int = 0, margin_right: int = 0,
         margin_bottom: int = 0) -> QWidget:
    parent = QWidget()
    vbox(parent, 0, 0).addWidget(widget)
    margins(parent, margin_left, margin_top, margin_right, margin_bottom)

    return parent


def group(*widgets, margin: int = 2, spacing: int = 3, parent=None, vertical: bool = False) -> QWidget:
    container = QWidget(parent)
    if vertical:
        vbox(container, margin, spacing)
    else:
        hbox(container, margin, spacing)

    for w in widgets:
        container.layout().addWidget(w)
    return container


class MouseEventDelegate(QObject):
    def __init__(self, target, delegate):
        super().__init__(target)
        self._delegate = delegate

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.Type.MouseButtonPress:
            self._delegate.mousePressEvent(event)
            return False
        elif event.type() == QEvent.Type.MouseButtonRelease:
            self._delegate.mouseReleaseEvent(event)
            return False

        return super(MouseEventDelegate, self).eventFilter(watched, event)


class ActionTooltipDisplayMode(Enum):
    NONE = 0
    ON_HOVER = 1
    DISPLAY_UNDER = 2


class MenuItemWidget(QFrame):
    triggered = Signal()

    def __init__(self, action: QAction, parent=None, tooltipMode=ActionTooltipDisplayMode.ON_HOVER):
        super().__init__(parent)
        self._action = action
        self._tooltipDisplayMode = tooltipMode

        vbox(self, 5, 0)

        self._icon = QToolButton(self)
        transparent(self._icon)
        self._icon.setIconSize(QSize(16, 16))
        self._icon.installEventFilter(MouseEventDelegate(self._icon, self))
        self._text = QLabel(self)
        transparent(self._text)
        self._description = QLabel(self._action.toolTip())
        self._description.setProperty('description', True)
        transparent(self._description)
        decr_font(self._description)

        self.layout().addWidget(group(self._icon, self._text, margin=0, spacing=1))
        self.layout().addWidget(self._description)

        self._action.changed.connect(self.refresh)
        self.refresh()

    def action(self) -> QAction:
        return self._action

    def setTooltipDisplayMode(self, mode: ActionTooltipDisplayMode):
        self._tooltipDisplayMode = mode
        self.refresh()

    def refresh(self):
        self._icon.setIcon(self._action.icon())
        self._text.setText(self._action.text())
        if self._tooltipDisplayMode == ActionTooltipDisplayMode.NONE:
            self._icon.setToolTip('')
            self._text.setToolTip('')
            self._description.setHidden(True)
        else:
            self._icon.setToolTip(self._action.toolTip())
            self._text.setToolTip(self._action.toolTip())
            if self._tooltipDisplayMode == ActionTooltipDisplayMode.DISPLAY_UNDER:
                self._description.setText(self._action.toolTip())
                self._description.setVisible(True)
            else:
                self._description.setHidden(True)

        self.setEnabled(self._action.isEnabled())

    def mousePressEvent(self, event: QMouseEvent) -> None:
        self.setProperty('pressed', True)
        self._restyle()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        self.setProperty('pressed', False)
        QTimer.singleShot(10, self._trigger)
        self._restyle()

    def _restyle(self):
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()

    def _trigger(self):
        self.triggered.emit()
        self._action.trigger()


class MenuWidget(QWidget):
    aboutToShow = Signal()
    aboutToHide = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.setStyleSheet('''
        QFrame {
            background-color: #F5F5F5;
            padding-left: 5px;
            padding-right: 5px;
            border-radius: 5px;
        }
        MenuItemWidget:hover {
            background-color:#EDEDED;
        }
        MenuItemWidget[pressed=true] {
            background-color:#DCDCDC;
        }
        QLabel[description=true] {
            color: grey;
        }
        ''')

        self._tooltipDisplayMode = ActionTooltipDisplayMode.ON_HOVER
        vbox(self, 0, 0)
        self._menuItems: List[MenuItemWidget] = []
        self._frame = QFrame()
        vbox(self._frame, spacing=0)
        self._initLayout()

        if isinstance(parent, QAbstractButton):
            MenuDelegate(parent, self)
            parent.clicked.connect(lambda: self.exec())

        self._posAnim = QPropertyAnimation(self, b'pos', self)
        self._posAnim.setDuration(120)
        self._posAnim.setEasingCurve(QEasingCurve.Type.OutQuad)
        self._posAnim.valueChanged.connect(self._positionAnimChanged)

    def _initLayout(self):
        self.layout().addWidget(self._frame)

    def actions(self) -> List[QAction]:
        return [x.action() for x in self._menuItems]

    def tooltipDisplayMode(self) -> ActionTooltipDisplayMode:
        return self._tooltipDisplayMode

    def setTooltipDisplayMode(self, mode: ActionTooltipDisplayMode):
        self._tooltipDisplayMode = mode
        for item in self._menuItems:
            item.setTooltipDisplayMode(self._tooltipDisplayMode)

    def clear(self):
        self._menuItems.clear()
        clear_layout(self._frame)

    def isEmpty(self) -> bool:
        return self._frame.layout().count() == 0

    def addAction(self, action: QAction):
        wdg = MenuItemWidget(action, self, self._tooltipDisplayMode)
        wdg.triggered.connect(self.close)
        self._frame.layout().addWidget(wdg)
        self._menuItems.append(wdg)

    def addWidget(self, widget):
        self._frame.layout().addWidget(widget)

    def addSection(self, text: str, icon=None):
        section = QPushButton(text)
        transparent(section)
        if icon:
            section.setIcon(icon)
        self._frame.layout().addWidget(wrap(section, margin_left=2, margin_top=2), alignment=Qt.AlignmentFlag.AlignLeft)
        self.addSeparator()

    def addSeparator(self):
        self._frame.layout().addWidget(line(color='#DCDCDC'))

    def hideEvent(self, e):
        self.aboutToHide.emit()
        e.accept()

    def exec(self, pos: Optional[QPoint] = None):
        if pos is None:
            if self.parent() and self.parent().parent():
                pos = self.parent().parent().mapToGlobal(self.parent().pos())
                pos.setY(pos.y() + self.parent().height())
            else:
                pos = QCursor.pos()

        screen_rect = QApplication.screenAt(pos).availableGeometry()
        w, h = self.width() + 5, self.height() + 5
        pos.setX(min(pos.x() - self.layout().contentsMargins().left(), screen_rect.right() - w))
        pos.setY(min(pos.y() - 4, screen_rect.bottom() - h))

        self.aboutToShow.emit()
        self._posAnim.setStartValue(pos - QPoint(0, int(h / 2)))
        self._posAnim.setEndValue(pos)
        self._posAnim.setEasingCurve(QEasingCurve.Type.OutQuad)
        self._posAnim.start()

        self.show()

    def _positionAnimChanged(self, pos: QPoint):
        m = self.layout().contentsMargins()
        w = self.width() + m.left() + m.right()
        h = self.height() + m.top() + m.bottom()
        y = self._posAnim.endValue().y() - pos.y()
        self.setMask(QRegion(0, y, w, h))


class ScrollableMenuWidget(MenuWidget):
    def __init__(self, parent=None):
        self._scrollarea = QScrollArea()
        self._scrollarea.setWidgetResizable(True)
        super(ScrollableMenuWidget, self).__init__(parent)

    def _initLayout(self):
        self.layout().addWidget(self._scrollarea)
        self._scrollarea.setWidget(self._frame)


class MenuDelegate(QMenu):
    def __init__(self, parent, menu: MenuWidget):
        super(MenuDelegate, self).__init__(parent)
        self._menu = menu
        self._menu.aboutToShow.connect(self.aboutToShow.emit)
        self._menu.aboutToHide.connect(self.aboutToHide.emit)

        if isinstance(parent, (QPushButton, QToolButton)):
            parent.setMenu(self)

        self.setDisabled(True)

    def showEvent(self, a0: QShowEvent) -> None:
        self._menu.exec()

    def hideEvent(self, event: QHideEvent) -> None:
        super(MenuDelegate, self).hideEvent(event)

    def isVisible(self) -> bool:
        return self._menu.isVisible()

    def actions(self) -> List[QAction]:
        return self._menu.actions()

from typing import List

from qthandy import hbox, vbox, transparent, clear_layout, line, margins
from qtpy.QtCore import Qt, Signal, QSize, QPropertyAnimation, QEasingCurve, QPoint, QObject, QEvent, QTimer
from qtpy.QtGui import QCursor, QAction, QRegion, QMouseEvent
from qtpy.QtWidgets import QApplication, QAbstractButton, QToolButton, QLabel, QFrame, QWidget, QPushButton


def wrap(widget: QWidget, margin_left: int = 0, margin_top: int = 0, margin_right: int = 0,
         margin_bottom: int = 0) -> QWidget:
    parent = QWidget()
    vbox(parent, 0, 0).addWidget(widget)
    margins(parent, margin_left, margin_top, margin_right, margin_bottom)

    return parent


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


class MenuItemWidget(QFrame):
    triggered = Signal()

    def __init__(self, action: QAction, parent=None):
        super().__init__(parent)
        self._action = action
        hbox(self, 5)

        self._icon = QToolButton(self)
        transparent(self._icon)
        self._icon.setIconSize(QSize(16, 16))
        self._icon.installEventFilter(MouseEventDelegate(self._icon, self))
        self._text = QLabel(self)
        transparent(self._text)

        self.layout().addWidget(self._icon)
        self.layout().addWidget(self._text)

        self._action.changed.connect(self.refresh)
        self.refresh()

    def action(self) -> QAction:
        return self._action

    def refresh(self):
        self._icon.setIcon(self._action.icon())
        self._text.setText(self._action.text())
        self._icon.setToolTip(self._action.toolTip())
        self._text.setToolTip(self._action.toolTip())

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
        # self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
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
        ''')

        vbox(self, 0, 0)
        self._actions: List[MenuItemWidget] = []
        self._frame = QFrame()
        self.layout().addWidget(self._frame)
        vbox(self._frame, spacing=0)
        if isinstance(parent, QAbstractButton):
            parent.clicked.connect(self.exec)

        self._posAnim = QPropertyAnimation(self, b'pos', self)
        self._posAnim.setDuration(120)
        self._posAnim.setEasingCurve(QEasingCurve.Type.OutQuad)
        self._posAnim.valueChanged.connect(self._positionAnimChanged)

    def actions(self) -> List[QAction]:
        return [x.action() for x in self._actions]

    def clear(self):
        self._actions.clear()
        clear_layout(self._frame)

    def isEmpty(self) -> bool:
        return len(self._actions) == 0

    def addAction(self, action: QAction):
        wdg = MenuItemWidget(action, self)
        wdg.triggered.connect(self.close)
        self._frame.layout().addWidget(wdg)
        self._actions.append(wdg)

    def addSection(self, text: str, icon=None):
        section = QPushButton(text)
        transparent(section)
        if icon:
            section.setIcon(icon)
        self._frame.layout().addWidget(wrap(section, margin_left=2, margin_top=2), alignment=Qt.AlignmentFlag.AlignLeft)
        self.addSeparator()

    def addSeparator(self):
        self._frame.layout().addWidget(line(color='lightgrey'))

    def hideEvent(self, e):
        self.aboutToHide.emit()
        e.accept()

    def exec(self):
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

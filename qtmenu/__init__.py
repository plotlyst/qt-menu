from qthandy import hbox, vbox, transparent
from qtpy.QtCore import Qt, Signal, QSize, QPropertyAnimation, QEasingCurve, QPoint, QObject, QEvent
from qtpy.QtGui import QCursor, QAction, QRegion, QMouseEvent
from qtpy.QtWidgets import QApplication, QAbstractButton, QToolButton, QLabel, QFrame, QWidget


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
        self._restyle()
        self.triggered.emit()
        self._action.trigger()

    def _restyle(self):
        self.style().unpolish(self)
        self.style().polish(self)


class MenuWidget(QWidget):
    aboutToShow = Signal()
    aboutToHide = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint |
                            Qt.WindowType.NoDropShadowWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
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
        self._frame = QFrame()
        self.layout().addWidget(self._frame)
        vbox(self._frame, spacing=0)
        if isinstance(parent, QAbstractButton):
            parent.clicked.connect(self.exec)

        self._posAnim = QPropertyAnimation(self, b'pos', self)
        self._posAnim.setDuration(50)
        self._posAnim.setEasingCurve(QEasingCurve.Type.OutQuad)
        self._posAnim.valueChanged.connect(self._positionAnimChanged)

    def addAction(self, action: QAction):
        wdg = MenuItemWidget(action, self)
        wdg.triggered.connect(self.close)
        self._frame.layout().addWidget(wdg)

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
        self._posAnim.setEasingCurve(QEasingCurve.OutQuad)
        self._posAnim.start()

        self.show()

    def _positionAnimChanged(self, pos: QPoint):
        m = self.layout().contentsMargins()
        w = self.width() + m.left() + m.right()
        h = self.height() + m.top() + m.bottom()
        y = self._posAnim.endValue().y() - pos.y()
        self.setMask(QRegion(0, y, w, h))

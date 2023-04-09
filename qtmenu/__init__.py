from PySide6.QtCore import QPropertyAnimation, QEasingCurve, QPoint
from PySide6.QtGui import QRegion
from qthandy import hbox, vbox, pointy
from qtpy.QtCore import Qt, Signal, QSize
from qtpy.QtGui import QCursor, QAction
from qtpy.QtWidgets import QWidget, QApplication, QAbstractButton, QPushButton


class MenuItemWidget(QWidget):
    def __init__(self, action: QAction, parent=None):
        super().__init__(parent)
        self._action = action
        hbox(self, 0, 0)

        self._btnAction = QPushButton()
        pointy(self._btnAction)
        self._btnAction.setIconSize(QSize(18, 18))
        self.layout().addWidget(self._btnAction)

        self._action.changed.connect(self.refresh)
        self.refresh()

    def refresh(self):
        self._btnAction.setIcon(self._action.icon())
        self._btnAction.setText(self._action.text())
        self._btnAction.setToolTip(self._action.toolTip())


class MenuWidget(QWidget):
    aboutToShow = Signal()
    aboutToHide = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint |
                            Qt.WindowType.NoDropShadowWindowHint)
        self.setStyleSheet('QWidget {background-color: #f8f9fa;}')

        vbox(self, 0, 3)
        if isinstance(parent, QAbstractButton):
            parent.clicked.connect(self.exec)

        self._posAnim = QPropertyAnimation(self, b'pos', self)
        self._posAnim.setDuration(50)
        self._posAnim.setEasingCurve(QEasingCurve.Type.OutQuad)
        self._posAnim.valueChanged.connect(self._positionAnimChanged)

    def addAction(self, action: QAction):
        wdg = MenuItemWidget(action, self)
        self.layout().addWidget(wdg)

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

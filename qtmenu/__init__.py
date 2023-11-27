import re
from enum import Enum
from functools import partial
from typing import List, Optional

from qthandy import vbox, transparent, clear_layout, margins, decr_font, hbox, grid, line, sp, vspacer
from qtpy.QtCore import Qt, Signal, QSize, QPropertyAnimation, QEasingCurve, QPoint, QObject, QEvent, QTimer, QMargins
from qtpy.QtGui import QAction, QMouseEvent, QCursor, QShowEvent, QHideEvent, QIcon, QFont
from qtpy.QtWidgets import QApplication, QAbstractButton, QToolButton, QLabel, QFrame, QWidget, QPushButton, QMenu, \
    QScrollArea, QLineEdit, QCheckBox, QTabWidget


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


def separator(vertical: bool = False) -> QFrame:
    return line(vertical=vertical, color='#DCDCDC')


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

        self._checkBox = QCheckBox()
        self._checkBox.clicked.connect(self._trigger)
        sp(self._checkBox).h_max()
        self._icon = QToolButton(self)
        transparent(self._icon)
        self._icon.setIconSize(QSize(16, 16))
        self._icon.installEventFilter(MouseEventDelegate(self._icon, self))
        self._text = QLabel(self)
        font: QFont = self._text.font()
        font.setItalic(self._action.font().italic())
        font.setBold(self._action.font().bold())
        font.setUnderline(self._action.font().underline())
        self._text.setFont(font)

        transparent(self._text)
        self._description = QLabel(self._action.toolTip())
        self._description.setProperty('description', True)
        transparent(self._description)
        decr_font(self._description)

        self.layout().addWidget(group(self._checkBox, self._icon, self._text, margin=0, spacing=1))
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

        self._checkBox.setChecked(self._action.isChecked())
        self._checkBox.setVisible(self._action.isCheckable())
        self.setEnabled(self._action.isEnabled())
        self.setVisible(self._action.isVisible())

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
        if self._action.isCheckable():
            self._action.toggle()
        self.triggered.emit()
        self._action.triggered.emit(self._action.isChecked())


class MenuSectionWidget(QWidget):
    def __init__(self, text: str, icon=None, parent=None):
        super(MenuSectionWidget, self).__init__(parent)
        hbox(self, 0, 0)
        section = QPushButton(text)
        transparent(section)
        section.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        if icon:
            section.setIcon(icon)

        self.layout().addWidget(section)


class SubmenuWidget(QFrame):
    triggered = Signal()

    def __init__(self, menu: 'MenuWidget', parentMenu: 'MenuWidget'):
        super(SubmenuWidget, self).__init__(parentMenu)
        self._menu = menu
        hbox(self, 5, 0)
        submenu = QPushButton(self._menu.title())
        submenu.installEventFilter(MouseEventDelegate(submenu, self))
        transparent(submenu)

        chevron = QLabel()
        transparent(chevron)
        chevron.setText(u'\u27A4')

        if self._menu.icon():
            submenu.setIcon(self._menu.icon())
        self.layout().addWidget(submenu)
        self.layout().addWidget(chevron, alignment=Qt.AlignmentFlag.AlignRight)

    def menu(self) -> 'MenuWidget':
        return self._menu

    def mousePressEvent(self, event: QMouseEvent) -> None:
        self.setProperty('pressed', True)
        self._restyle()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        self.setProperty('pressed', False)
        QTimer.singleShot(10, self.triggered.emit)
        self._restyle()

    def _restyle(self):
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()


class MenuWidget(QWidget):
    aboutToShow = Signal()
    aboutToHide = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.setStyleSheet('''
            MenuWidget {
                background-color: #F5F5F5;
            }
            QFrame {
                background-color: #F5F5F5;
                padding-left: 2px;
                padding-right: 2px;
                border-radius: 5px;
            }
            MenuItemWidget:hover {
                background-color:#EDEDED;
            }
            MenuItemWidget[pressed=true] {
                background-color:#DCDCDC;
            }
            SubmenuWidget:hover {
                background-color:#EDEDED;
            }
            SubmenuWidget[pressed=true] {
                background-color:#DCDCDC;
            }
            QLabel[description=true] {
                color: grey;
            }
        ''')

        self._icon: Optional[QIcon] = None
        self._title: str = ''
        self._parentMenu: Optional[MenuWidget] = None
        self._tooltipDisplayMode = ActionTooltipDisplayMode.ON_HOVER
        self._search: Optional[QLineEdit] = None
        self._endSpacer: Optional[QWidget] = None
        vbox(self, 0, 0)
        self._menuItems: List[MenuItemWidget] = []
        self._subMenus: List['SubmenuWidget'] = []
        self._frame = QFrame()
        self._initLayout()

        if isinstance(parent, QAbstractButton):
            MenuDelegate(parent, self)
            parent.clicked.connect(lambda: self.exec())
        elif isinstance(parent, MenuWidget):
            self.setParentMenu(parent)

        self._posAnim = QPropertyAnimation(self, b'maximumHeight', self)
        self._posAnim.setDuration(120)
        self._posAnim.setEasingCurve(QEasingCurve.Type.OutQuad)
        self._posAnim.valueChanged.connect(self._positionAnimChanged)

    def _initLayout(self):
        vbox(self._frame, spacing=0)
        self.layout().addWidget(self._frame)

    def actions(self) -> List[QAction]:
        return [x.action() for x in self._menuItems]

    def icon(self) -> Optional[QIcon]:
        return self._icon

    def setIcon(self, icon: QIcon):
        self._icon = icon

    def title(self) -> str:
        return self._title

    def setTitle(self, title: str):
        self._title = title

    def setParentMenu(self, parentMenu: 'MenuWidget'):
        self._parentMenu = parentMenu
        margins(self, left=0, right=0)

    def tooltipDisplayMode(self) -> ActionTooltipDisplayMode:
        return self._tooltipDisplayMode

    def setTooltipDisplayMode(self, mode: ActionTooltipDisplayMode):
        self._tooltipDisplayMode = mode
        for item in self._menuItems:
            item.setTooltipDisplayMode(self._tooltipDisplayMode)

    def setSearchEnabled(self, enabled: bool):
        if enabled:
            self._search = QLineEdit()
            self._search.setPlaceholderText('Search...')
            self._search.setClearButtonEnabled(True)
            self._search.textChanged.connect(self._applySearch)
            self.layout().insertWidget(0, wrap(self._search, margin_left=5, margin_right=5),
                                       alignment=Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)

            self._endSpacer = vspacer()
            self._endSpacer.setMinimumHeight(1)
            self.layout().addWidget(self._endSpacer)
        elif self._search:
            self.layout().removeWidget(self._search)
            self._search = None
            self.layout().removeWidget(self._endSpacer)
            self._endSpacer = None

    def clear(self):
        self._menuItems.clear()
        self._subMenus.clear()
        clear_layout(self._frame)

    def isEmpty(self) -> bool:
        return self._frame.layout().count() == 0

    def addAction(self, action: QAction):
        wdg = self._newMenuItem(action)
        self._frame.layout().addWidget(wdg)

    def addWidget(self, widget):
        self._frame.layout().addWidget(widget)

    def addSection(self, text: str, icon=None):
        section = MenuSectionWidget(text, icon)
        self._frame.layout().addWidget(wrap(section, margin_left=2, margin_top=2), alignment=Qt.AlignmentFlag.AlignLeft)

    def addSeparator(self):
        self._frame.layout().addWidget(separator())

    def addMenu(self, menu: 'MenuWidget'):
        submenu = SubmenuWidget(menu, self)
        menu.setParentMenu(self)
        submenu.triggered.connect(partial(self._showSubmenu, submenu))
        self._subMenus.append(submenu)
        self._frame.layout().addWidget(submenu)

    def hideEvent(self, e):
        self.aboutToHide.emit()
        e.accept()
        if self._parentMenu:
            self._parentMenu.close()

    def exec(self, pos: Optional[QPoint] = None):
        self.aboutToShow.emit()
        if pos is None:
            if self.parent() and self.parent().parent():
                pos = self.parent().parent().mapToGlobal(self.parent().pos())
                pos.setY(pos.y() + self.parent().height())
            else:
                pos = QCursor.pos()

        screen_rect = QApplication.screenAt(pos).availableGeometry()
        w, h = self.sizeHint().width() + 5, self.sizeHint().height() + 5
        pos.setX(min(pos.x() - self.layout().contentsMargins().left(), screen_rect.right() - w))
        pos.setY(min(pos.y() - 4, screen_rect.bottom() - h))

        self.move(pos)

        self._posAnim.setStartValue(20)
        self._posAnim.setEndValue(self.sizeHint().height())
        self._posAnim.start()

        if self._search:
            self._search.setFocus()

        self.show()

    def _showSubmenu(self, submenu: SubmenuWidget):
        margins: QMargins = self.layout().contentsMargins()
        pos = submenu.mapToGlobal(QPoint(submenu.width() + margins.left() + margins.right(), 0))
        submenu.menu().exec(pos)

    def _positionAnimChanged(self, value: int):
        self.setFixedHeight(value)

    def _newMenuItem(self, action: QAction) -> MenuItemWidget:
        wdg = MenuItemWidget(action, self, self._tooltipDisplayMode)
        wdg.triggered.connect(self.close)
        self._menuItems.append(wdg)
        return wdg

    def _applySearch(self, text: str):
        if not text:
            for item in self._menuItems:
                item.setVisible(True)

        for item in self._menuItems:
            if re.search(text, item.action().text(), re.IGNORECASE):
                item.setVisible(True)
            else:
                item.setHidden(True)


class ScrollableMenuWidget(MenuWidget):
    def __init__(self, parent=None):
        self._scrollarea = QScrollArea()
        self._scrollarea.setWidgetResizable(True)
        super(ScrollableMenuWidget, self).__init__(parent)

    def _initLayout(self):
        self.layout().addWidget(self._scrollarea)
        vbox(self._frame, spacing=0)
        self._scrollarea.setWidget(self._frame)


class GridMenuWidget(MenuWidget):
    def __init__(self, parent=None):
        super(GridMenuWidget, self).__init__(parent)

    def _initLayout(self):
        grid(self._frame)
        self.layout().addWidget(self._frame)

    def addAction(self, action: QAction, row: int, column: int, rowSpan: int = 1, colSpan: int = 1):
        wdg = self._newMenuItem(action)
        self._frame.layout().addWidget(wdg, row, column, rowSpan, colSpan)

    def addSection(self, text: str, row: int, column: int, rowSpan: int = 1, colSpan: int = 1, icon=None):
        section = MenuSectionWidget(text, icon)
        self._frame.layout().addWidget(wrap(section, margin_left=2, margin_top=2), row, column, rowSpan, colSpan,
                                       alignment=Qt.AlignmentFlag.AlignLeft)

    def addSeparator(self, row: int, column: int, rowSpan: int = 1, colSpan: int = 1, vertical: bool = False):
        self._frame.layout().addWidget(separator(vertical), row, column, rowSpan, colSpan)


class TabularGridMenuWidget(MenuWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

    def _initLayout(self):
        self._frame = QTabWidget()
        self.layout().addWidget(self._frame)

    def addTab(self, name: str, icon: Optional[QIcon] = None) -> QWidget:
        tab = QWidget(self._frame)
        grid(tab)
        if icon:
            self._frame.addTab(tab, icon, name)
        else:
            self._frame.addTab(tab, name)

        return tab

    def addWidget(self, tabWidget: QWidget, wdg: QWidget, row: int, column: int, rowSpan: int = 1, colSpan: int = 1):
        tabWidget.layout().addWidget(wdg, row, column, rowSpan, colSpan)

    def addAction(self, tabWidget: QWidget, action: QAction, row: int, column: int, rowSpan: int = 1, colSpan: int = 1):
        wdg = self._newMenuItem(action)
        tabWidget.layout().addWidget(wdg, row, column, rowSpan, colSpan)

    def addSection(self, tabWidget: QWidget, text: str, row: int, column: int, rowSpan: int = 1, colSpan: int = 1,
                   icon=None):
        section = MenuSectionWidget(text, icon)
        tabWidget.layout().addWidget(wrap(section, margin_left=2, margin_top=2), row, column, rowSpan, colSpan,
                                     alignment=Qt.AlignmentFlag.AlignLeft)

    def addSeparator(self, tabWidget: QWidget, row: int, column: int, rowSpan: int = 1, colSpan: int = 1,
                     vertical: bool = False):
        tabWidget.layout().addWidget(separator(vertical), row, column, rowSpan, colSpan)


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

    def hide(self) -> None:
        self._menu.hide()

    def close(self) -> bool:
        return self._menu.close()

    def hideEvent(self, event: QHideEvent) -> None:
        super(MenuDelegate, self).hideEvent(event)

    def isVisible(self) -> bool:
        return self._menu.isVisible()

    def actions(self) -> List[QAction]:
        return self._menu.actions()

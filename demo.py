import sys

import qtawesome
from qtpy.QtGui import QAction
from qtpy.QtWidgets import QMainWindow, QApplication, QWidget, QVBoxLayout, QPushButton

from qtmenu import ActionTooltipDisplayMode, GridMenuWidget, MenuWidget


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)

        self.widget = QWidget(self)
        self.setCentralWidget(self.widget)

        self.widget.setLayout(QVBoxLayout())

        self._btnSimple = QPushButton('Simple menu')
        self._menuSimple = MenuWidget(self._btnSimple)
        action = QAction('Action 1')
        action.setCheckable(True)
        action.toggled.connect(lambda x: print(f'toggled {x}'))
        action.triggered.connect(lambda: print('triggered but why'))
        self._menuSimple.addAction(action)

        self._btnGrid = QPushButton('Grid menu')
        self._menuGrid = GridMenuWidget(self._btnGrid)
        action = QAction(qtawesome.icon('ei.adjust'), 'Action 1')
        action.triggered.connect(lambda: print('clicked'))
        action.setToolTip('Test description which is much longer than before')
        self._menuGrid.setTooltipDisplayMode(ActionTooltipDisplayMode.DISPLAY_UNDER)
        self._menuGrid.addSection('Section 1', 0, 0, colSpan=2)
        self._menuGrid.addSeparator(1, 0, colSpan=2)
        self._menuGrid.addAction(action, 2, 0)
        self._menuGrid.addAction(QAction(qtawesome.icon('ei.adjust-alt'), 'Action 2'), 2, 1)
        # self._menu.addSection('Section', 3, 1, icon=qtawesome.icon('ei.child'))
        self._menuGrid.addAction(QAction(qtawesome.icon('ei.child'), 'Action 3'), 3, 0)
        self._menuGrid.setSearchEnabled(True)

        self.widget.layout().addWidget(self._btnSimple)
        self.widget.layout().addWidget(self._btnGrid)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()

    window.show()

    app.exec()

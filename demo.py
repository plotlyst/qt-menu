import sys

import qtawesome
from qtpy.QtGui import QAction
from qtpy.QtWidgets import QMainWindow, QApplication, QWidget, QVBoxLayout, QPushButton

from qtmenu import ActionTooltipDisplayMode, GridMenuWidget


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)

        self.widget = QWidget(self)
        self.setCentralWidget(self.widget)

        self.widget.setLayout(QVBoxLayout())

        self._btn = QPushButton('Test')
        self.widget.layout().addWidget(self._btn)

        self._menu = GridMenuWidget(self._btn)
        action = QAction(qtawesome.icon('ei.adjust'), 'Action 1')
        action.triggered.connect(lambda: print('clicked'))
        action.setToolTip('Test description which is much longer than before')
        self._menu.setTooltipDisplayMode(ActionTooltipDisplayMode.DISPLAY_UNDER)
        self._menu.addSection('Section 1', 0, 0, colSpan=2)
        self._menu.addSeparator(1, 0, colSpan=2)
        self._menu.addAction(action, 2, 0)
        self._menu.addAction(QAction(qtawesome.icon('ei.adjust-alt'), 'Action 2'), 2, 1)
        # self._menu.addSection('Section', 3, 1, icon=qtawesome.icon('ei.child'))
        self._menu.addAction(QAction(qtawesome.icon('ei.child'), 'Action 3'), 3, 0)
        self._menu.setSearchEnabled(True)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()

    window.show()

    app.exec()

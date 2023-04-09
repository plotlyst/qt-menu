from qtpy.QtGui import QAction
from qtpy.QtWidgets import QPushButton

from qtmenu import MenuWidget


def test_menu_show(qtbot):
    btn = QPushButton('Button')
    menu = MenuWidget(btn)
    menu.addAction(QAction('Action 1'))

    btn.show()
    qtbot.addWidget(btn)

    assert menu.isHidden()
    btn.click()
    assert menu.isVisible()

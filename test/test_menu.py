from qtpy.QtGui import QAction
from qtpy.QtWidgets import QPushButton

from qtmenu import MenuWidget


def test_init(qtbot):
    btn = QPushButton('Button')
    menu = MenuWidget(btn)
    menu.addAction(QAction('Action 1'))

    btn.show()
    qtbot.addWidget(btn)

    assert menu.isHidden()
    assert btn.menu()
    assert not menu.isVisible()
    assert not btn.menu().isEnabled()


def test_clear(qtbot):
    menu = MenuWidget()
    menu.exec()
    qtbot.addWidget(menu)
    action1 = QAction('Action 1')
    menu.addAction(action1)
    action2 = QAction('Action 2')
    menu.addAction(action2)

    assert menu.actions() == [action1, action2]
    assert not menu.isEmpty()
    menu.clear()
    assert not menu.actions()
    assert menu.isEmpty()

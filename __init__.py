from .cardgenerator import Cardgenerator_wi
from aqt import mw
from aqt.qt import QAction
from .log import logger

def exec():
    app = Cardgenerator_wi()
    app.window.show()
    app.window.exec_()


action = QAction("Card generator", mw)
action.triggered.connect(exec)
mw.form.menuTools.addAction(action)

from PySide6.QtWidgets import (
    QMainWindow, QLayout, QGraphicsView
)
from PySide6.QtGui import (
    QUndoStack
)

from core.widgets.game_widget import GameScene
from core.game.game_controller import GameController


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.layout().setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)

        self.game = GameController(
            rows=4,
            columns=4,
            parent=self
        )
        self.undo_stack = QUndoStack(self)
        self.game.setUndoStack(self.undo_stack)
        undo_action = self.undo_stack.createUndoAction(self)
        undo_action.setShortcut('Ctrl+Z')
        redo_action = self.undo_stack.createRedoAction(self)
        redo_action.setShortcut('Ctrl+Shift+Z')
        self.addActions([undo_action, redo_action])

        self.scene = GameScene(self)
        self.game.setScene(self.scene)

        self.view = QGraphicsView(self.scene, self)
        self.setCentralWidget(self.view)

        self.game.start()

from PySide6.QtWidgets import (
    QMainWindow, QLayout, QGraphicsView
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

        self.scene = GameScene(self)
        self.scene.setController(self.game)
        self.view = QGraphicsView(self.scene, self)
        self.setCentralWidget(self.view)

        self.game.start()

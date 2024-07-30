from PySide6.QtWidgets import (
    QMainWindow, QLayout
)

from core.widgets.game_widget import GameWidget
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

        self.view = GameWidget(self)
        self.view.setController(self.game)
        self.setCentralWidget(self.view)

        self.game.start()

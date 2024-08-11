from PySide6.QtCore import (
    Qt, QPoint, QVariantAnimation,
    QSequentialAnimationGroup, QParallelAnimationGroup
)
from PySide6.QtGui import (
    QUndoCommand
)

from core.widgets.game_widget import (
    GameScene, Tile2D,
    AppearAnimation, MovingAnimation
)
from core.game.tile import TileGrid


_execution_order = {
    'RemoveCommand': 1,
    'MergeCommand': 2,
    'MoveCommand': 2,
    'AddCommand': 4}


class TurnCommand(QUndoCommand):
    _commands_list = []

    def __init__(self, grid: TileGrid, parent: QUndoCommand | None = None):
        super().__init__(parent)
        self._children: list[QUndoCommand] = []
        TurnCommand._commands_list.append(self)
        self.grid = grid

        self._is_first = True

    def do(self):
        self._is_first = False

        self._children.sort(
            key=lambda c: _execution_order[c.__class__.__name__]
        )

        self.anim = QSequentialAnimationGroup()
        self.add_anim = QParallelAnimationGroup()
        self.move_anim = QParallelAnimationGroup()
        self.anim.addAnimation(self.move_anim)
        self.anim.addAnimation(self.add_anim)

        for cmd in self._children:
            cmd.redo()
            if isinstance(cmd, AddCommand):
                self.add_anim.addAnimation(cmd.anim)
            elif isinstance(cmd, (MergeCommand, MoveCommand)):
                self.move_anim.addAnimation(cmd.anim)

        self.anim.start()
        self.grid.print()

    def redo(self):
        if self._is_first:
            self.do()
            return

        self._children.reverse()

        for cmd in self._children:
            cmd.redo()

        self.anim.setDirection(QVariantAnimation.Direction.Forward)
        self.anim.start()
        self.grid.print()

    def undo(self):
        self._children.reverse()

        for cmd in self._children:
            cmd.undo()

        self.anim.setDirection(QVariantAnimation.Direction.Backward)
        self.anim.start()
        self.grid.print()


class AddCommand(QUndoCommand):
    def __init__(self, value: int, cell: QPoint,
                 scene: GameScene, grid: TileGrid,
                 parent: TurnCommand):
        super().__init__(parent)
        parent._children.append(self)

        self.scene = scene
        self.grid = grid
        self.value = value
        self.cellT = cell

        self.anim = AppearAnimation(
            self.value, self.cellT.transposed(), self.scene
        )

    def redo(self):
        # grid
        self.grid.addTile(self.cellT.x(), self.cellT.y(), self.value)

        # scene
        tile: Tile2D = self.scene.addTile(self.value, self.cellT.transposed())

        tile.setOpacity(0.)
        self.anim.finished.connect(
            lambda: tile.setOpacity(1.),
            Qt.ConnectionType.SingleShotConnection
        )
        self.anim.setDirection(QVariantAnimation.Direction.Forward)

    def undo(self):
        # grid
        self.grid.removeTile(self.cellT.x(), self.cellT.y())

        # scene
        self.scene.removeTile(self.cellT.transposed())

        self.anim.setDirection(QVariantAnimation.Direction.Backward)


class MergeCommand(QUndoCommand):
    def __init__(self, new_cell: QPoint, old_cell: QPoint,
                 scene: GameScene, grid: TileGrid,
                 parent: TurnCommand):
        super().__init__(parent)
        parent._children.append(self)

        self.scene = scene
        self.grid = grid
        self.new_cellT = new_cell
        self.old_cellT = old_cell

        self.anim = MovingAnimation(
            self.new_cellT.transposed(),
            self.old_cellT.transposed(),
            self.scene
        )

    def redo(self):
        # grid
        self.tile = self.grid.mergeTile(
            self.old_cellT.x(), self.old_cellT.y(),
            self.new_cellT.x(), self.new_cellT.y()
        )

        # scene
        self.scene.removeTile(
            self.new_cellT.transposed()
        )
        tile2d: Tile2D = self.scene.moveTile(
            self.new_cellT.transposed(),
            self.old_cellT.transposed()
        )
        tile2d.setValue(self.tile.value)
        self.anim.tile.setValue(self.tile.value / 2)

        tile2d.setOpacity(0.)
        self.anim.finished.connect(
            lambda: tile2d.setOpacity(1.),
            Qt.ConnectionType.SingleShotConnection
        )
        self.anim.setDirection(QVariantAnimation.Direction.Forward)

    def undo(self):
        # grid
        self.tile = self.grid.unmergeTile(
            self.new_cellT.x(), self.new_cellT.y(),
            self.old_cellT.x(), self.old_cellT.y()
        )

        # scene
        tile2d: Tile2D = self.scene.moveTile(
            self.old_cellT.transposed(),
            self.new_cellT.transposed()
        )
        self.scene.addTile(
            self.tile.value,
            self.new_cellT.transposed()
        )
        tile2d.setValue(self.tile.value)

        tile2d.setOpacity(0.)
        self.anim.finished.connect(
            lambda: tile2d.setOpacity(1.),
            Qt.ConnectionType.SingleShotConnection
        )
        self.anim.setDirection(QVariantAnimation.Direction.Backward)


class MoveCommand(QUndoCommand):
    def __init__(self, new_cell: QPoint, old_cell: QPoint,
                 scene: GameScene, grid: TileGrid,
                 parent: TurnCommand):
        super().__init__(parent)
        parent._children.append(self)

        self.scene = scene
        self.grid = grid
        self.new_cellT = new_cell
        self.old_cellT = old_cell

        self.anim = MovingAnimation(
            self.new_cellT.transposed(),
            self.old_cellT.transposed(),
            self.scene
        )

    def redo(self):
        # grid
        tile = self.grid.moveTile(
            self.old_cellT.x(), self.old_cellT.y(),
            self.new_cellT.x(), self.new_cellT.y()
        )

        # scene
        tile2d: Tile2D = self.scene.moveTile(
            self.new_cellT.transposed(),
            self.old_cellT.transposed()
        )
        self.anim.tile.setValue(tile.value)

        tile2d.setOpacity(0.)
        self.anim.finished.connect(
            lambda: tile2d.setOpacity(1.),
            Qt.ConnectionType.SingleShotConnection
        )
        self.anim.setDirection(QVariantAnimation.Direction.Forward)

    def undo(self):
        # grid
        self.grid.moveTile(
            self.new_cellT.x(), self.new_cellT.y(),
            self.old_cellT.x(), self.old_cellT.y()
        )

        # scene
        tile2d: Tile2D = self.scene.moveTile(
            self.old_cellT.transposed(),
            self.new_cellT.transposed()
        )

        tile2d.setOpacity(0.)
        self.anim.finished.connect(
            lambda: tile2d.setOpacity(1.),
            Qt.ConnectionType.SingleShotConnection
        )
        self.anim.setDirection(QVariantAnimation.Direction.Backward)

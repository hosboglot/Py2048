from math import log2

from PySide6.QtCore import (
    QObject, QRectF, QRect, Slot, Signal, QPoint, Qt,
    QEasingCurve, QVariantAnimation
)
from PySide6.QtGui import (
    QColor
)
from PySide6.QtWidgets import (
    QWidget, QGraphicsView, QGraphicsScene,
    QGraphicsObject, QGraphicsItem
)

from core.game.game_controller import GameController


TILE_SIZE = 100


class Tile2D(QGraphicsObject):
    def __init__(self, cell: QPoint, value: int,
                 parent: QGraphicsItem | None = None
                 ) -> None:
        super().__init__(parent)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)

        self.setCell(cell)
        self._value = value

    _cell = None

    def cell(self):
        return self._cell

    def setCell(self, cell: QPoint):
        if self._cell != cell:
            self.setPos(cell.x() * TILE_SIZE, cell.y() * TILE_SIZE)
            self._cell = cell

    def value(self):
        return self._value

    def setValue(self, v):
        if self._value != v:
            self._value = v
            self.update(self.boundingRect())

    def boundingRect(self) -> QRectF:
        return QRect(0, 0, TILE_SIZE, TILE_SIZE)

    def paint(self, painter, option, widget):
        easing = QEasingCurve(QEasingCurve.Type.OutCubic)
        color = QColor.fromHsvF(
            (1 - easing.valueForProgress(log2(self.value()) / 11)) / 6,
            1, 1, 1)
        painter.fillRect(self.boundingRect(), color)
        painter.drawRect(self.boundingRect())
        painter.drawText(
            self.boundingRect(),
            f'{self.value()}',
            Qt.AlignmentFlag.AlignCenter
        )


class AnimatedTile2D(Tile2D):
    pass


class AddingAnimation(QVariantAnimation):
    def __init__(self, tile: Tile2D, view: 'GameWidget') -> None:
        super().__init__(view)

        self.tile = AnimatedTile2D(tile.cell(), tile.value())
        self.tile.setZValue(-1)
        center = self.tile.mapRectToScene(self.tile.boundingRect()).center()
        self.tile.setPos(center)

        self.view = view
        self.view.scene().addItem(self.tile)

        self.valueChanged.connect(self.tile.setScale)
        self.valueChanged.connect(
            lambda v: self.tile.setPos(
                center * (1 - v) + tile.pos() * v)
        )
        self.setStartValue(0.)
        self.setEndValue(1.)
        self.setDuration(200)
        self.setEasingCurve(QEasingCurve(QEasingCurve.Type.OutExpo))

    def start(self):
        super().start(QVariantAnimation.DeletionPolicy.DeleteWhenStopped)

    def __del__(self):
        self.view.scene().removeItem(self.tile)


class RemovingAnimation(QVariantAnimation):
    def __init__(self, tile: Tile2D, view: 'GameWidget') -> None:
        super().__init__(view)

        self.tile = AnimatedTile2D(tile.cell(), tile.value())
        self.tile.setZValue(-1)

        self.view = view
        self.view.scene().addItem(self.tile)

        self.valueChanged.connect(self.tile.setScale)
        self.setStartValue(1.)
        self.setEndValue(0.)
        self.setDuration(200)
        self.setEasingCurve(QEasingCurve(QEasingCurve.Type.InExpo))

    def start(self):
        super().start(QVariantAnimation.DeletionPolicy.DeleteWhenStopped)

    def __del__(self):
        self.view.scene().removeItem(self.tile)


class MovingAnimation(QVariantAnimation):
    def __init__(self, tile: Tile2D,
                 old_cell: QPoint, view: 'GameWidget') -> None:
        super().__init__(view)

        self.tile = AnimatedTile2D(old_cell, tile.value())
        self.tile.setZValue(0)

        self.view = view
        self.view.scene().addItem(self.tile)

        self.valueChanged.connect(self.tile.setPos)
        self.setStartValue((old_cell * TILE_SIZE).toPointF())
        self.setEndValue(tile.pos())
        self.setDuration(200)
        # self.setEasingCurve(QEasingCurve(QEasingCurve.Type.InOutExpo))

    def start(self):
        super().start(QVariantAnimation.DeletionPolicy.DeleteWhenStopped)

    def __del__(self):
        self.view.scene().removeItem(self.tile)


class GameWidget(QGraphicsView):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setScene(QGraphicsScene(self))

    _controller = None
    controllerChanged = Signal(GameController)

    def setController(self, controller: GameController):
        if self._controller == controller:
            return

        if self._controller is not None:
            self._controller.tileAdded.disconnect(self.addTile)
            self._controller.tileRemoved.disconnect(self.removeTile)
            self._controller.tileValueChanged.disconnect(self.changeTileValue)
            self._controller.tileMoved.disconnect(self.moveTile)

        controller.tileAdded.connect(self.addTile)
        controller.tileRemoved.connect(self.removeTile)
        controller.tileValueChanged.connect(self.changeTileValue)
        controller.tileMoved.connect(self.moveTile)

        self.setSceneRect(0, 0,
                          TILE_SIZE * controller.row_count,
                          TILE_SIZE * controller.column_count)

        self._controller = controller
        self.controllerChanged.emit(controller)

    def controller(self):
        return self._controller

    def findTiles2D(self, cell: QPoint):
        result: list[Tile2D] = []
        for child in self.scene().items():
            if type(child) is Tile2D and child.cell() == cell:
                result.append(child)

        if result:
            return result
        raise ValueError(f'Tile 2D for {cell.transposed()} not found on scene')

    @Slot(int, QPoint)
    def addTile(self, value: int, cellT: QPoint):
        cell = cellT.transposed()
        print(f'add on {cellT}')
        tile2d = Tile2D(cell, value)
        tile2d.setZValue(1)
        self.scene().addItem(tile2d)

        tile2d.setOpacity(0.)
        anim = AddingAnimation(tile2d, self)
        anim.finished.connect(lambda: tile2d.setOpacity(1.))
        anim.start()

    @Slot(QPoint)
    def removeTile(self, cellT: QPoint):
        cell = cellT.transposed()
        print(f'remove on {cellT}')
        tile2d = self.findTiles2D(cell=cell)[0]
        anim = RemovingAnimation(tile2d, self)
        self.scene().removeItem(tile2d)
        anim.start()

    @Slot(int, QPoint)
    def changeTileValue(self, value: int, cellT: QPoint):
        cell = cellT.transposed()
        tiles = self.findTiles2D(cell=cell)
        # print(tiles)
        for tile2d in tiles:
            anim = QVariantAnimation(tile2d)
            anim.valueChanged.connect(tile2d.setValue)
            anim.setStartValue(tile2d.value())
            anim.setEndValue(value)
            anim.setDuration(100)
            anim.start(QVariantAnimation.DeletionPolicy.DeleteWhenStopped)

    @Slot(QPoint, QPoint)
    def moveTile(self, new_cellT: QPoint, old_cellT: QPoint):
        print(f'move {old_cellT} to {new_cellT}')
        new_cell, old_cell = new_cellT.transposed(), old_cellT.transposed()
        tile2d = self.findTiles2D(cell=old_cell)[0]
        tile2d.setCell(new_cell)

        tile2d.setOpacity(0.)
        anim = MovingAnimation(tile2d, old_cell, self)
        anim.finished.connect(lambda: tile2d.setOpacity(1.))
        anim.start()

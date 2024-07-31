from math import log2

from PySide6.QtCore import (
    QAbstractAnimation, QRectF, QRect, Slot, QPoint, Qt,
    QEasingCurve, QVariantAnimation
)
from PySide6.QtGui import (
    QColor
)
from PySide6.QtWidgets import (
    QWidget, QGraphicsScene,
    QGraphicsObject, QGraphicsItem
)


TILE_SIZE = 100


class Tile2D(QGraphicsObject):
    def __init__(self, cell: QPoint, value: int,
                 parent: QGraphicsItem | None = None
                 ) -> None:
        super().__init__(parent)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)

        self.setCell(cell)
        self._value = int(value)

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
        v = int(v)
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


class AppearAnimation(QVariantAnimation):
    def __init__(self,
                 value: int, cell: QPoint,
                 scene: 'GameScene') -> None:
        super().__init__(scene)

        self.tile = AnimatedTile2D(cell, value)
        self.tile.setZValue(-1)
        target_pos = self.tile.pos()
        center = self.tile.mapRectToScene(self.tile.boundingRect()).center()
        self.tile.setPos(center)

        self.scene = scene

        self.valueChanged.connect(self.tile.setScale)
        self.valueChanged.connect(
            lambda v: self.tile.setPos(
                center * (1 - v) + target_pos * v)
        )
        self.setStartValue(0.)
        self.setEndValue(1.)
        self.setDuration(200)

    def setDirection(self, direction: QVariantAnimation.Direction) -> None:
        if direction == QVariantAnimation.Direction.Forward:
            self.setEasingCurve(QEasingCurve(QEasingCurve.Type.OutExpo))
        else:
            self.setEasingCurve(QEasingCurve(QEasingCurve.Type.InExpo))
        super().setDirection(direction)

    def updateState(
        self,
        newState: QAbstractAnimation.State,
        oldState: QAbstractAnimation.State
    ) -> None:
        if newState == QAbstractAnimation.State.Running:
            self.scene.addItem(self.tile)
        elif newState == QAbstractAnimation.State.Stopped:
            self.scene.removeItem(self.tile)
        return super().updateState(newState, oldState)


class MovingAnimation(QVariantAnimation):
    def __init__(self,
                 new_cell: QPoint, old_cell: QPoint,
                 scene: 'GameScene') -> None:
        super().__init__(scene)

        self.tile = AnimatedTile2D(old_cell, 0)
        self.tile.setZValue(0)

        self.scene = scene

        self.valueChanged.connect(self.tile.setPos)
        self.setStartValue((old_cell * TILE_SIZE).toPointF())
        self.setEndValue((new_cell * TILE_SIZE).toPointF())
        self.setDuration(100)

    def updateState(
        self,
        newState: QAbstractAnimation.State,
        oldState: QAbstractAnimation.State
    ) -> None:
        if newState == QAbstractAnimation.State.Running:
            self.scene.addItem(self.tile)
        elif newState == QAbstractAnimation.State.Stopped:
            self.scene.removeItem(self.tile)
        return super().updateState(newState, oldState)


class GameScene(QGraphicsScene):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)

    def setSize(self, row_count, column_count):
        self.setSceneRect(0, 0,
                          TILE_SIZE * row_count,
                          TILE_SIZE * column_count)

    def findTiles2D(self, cell: QPoint):
        result: list[Tile2D] = []
        for child in self.items():
            if type(child) is Tile2D and child.cell() == cell:
                result.append(child)

        if result:
            return result
        raise ValueError(f'Tile 2D for {cell.transposed()} not found on scene')

    @Slot(int, QPoint)
    def addTile(self, value: int, cell: QPoint):
        tile2d = Tile2D(cell, value)
        tile2d.setZValue(1)
        self.addItem(tile2d)
        return tile2d

    @Slot(QPoint)
    def removeTile(self, cell: QPoint):
        tile2d = self.findTiles2D(cell=cell)[0]
        self.removeItem(tile2d)
        return tile2d

    # @Slot(int, QPoint)
    # def changeTileValue(self, value: int, cell: QPoint):
    #     tiles = self.findTiles2D(cell=cell)
    #     for tile2d in tiles:
    #         old = tile2d.value()
    #         tile2d.setValue(value)
    #     return old

    @Slot(QPoint, QPoint)
    def moveTile(self, new_cell: QPoint, old_cell: QPoint):
        tile2d = self.findTiles2D(cell=old_cell)[0]
        tile2d.setCell(new_cell)
        return tile2d

import random

from PySide6.QtCore import (
    QObject, Signal, Qt, QPoint
)
from PySide6.QtGui import QKeyEvent

from core.game.tile import TileGrid, MoveResult

TILES_AT_START = 4
TILES_AT_TURN = 1


class GameController(QObject):

    tileAdded = Signal(int, QPoint)
    tileRemoved = Signal(QPoint)
    tileValueChanged = Signal(int, QPoint)
    tileMoved = Signal(QPoint, QPoint)

    def __init__(self, rows=4, columns=4,
                 parent: QObject | None = None) -> None:
        super().__init__(parent)
        parent.installEventFilter(self)

        self.setGrid(TileGrid(rows, columns))

    _grid = None
    gridChanged = Signal(TileGrid)

    def setGrid(self, grid: TileGrid):
        if self._grid == grid:
            return

        if self._grid is not None:
            self._grid.tileAdded.disconnect(self.tileAdded)
            self._grid.tileRemoved.disconnect(self.tileRemoved)
            self._grid.tileValueChanged.disconnect(self.tileValueChanged)
            self._grid.tileMoved.disconnect(self.tileMoved)

        grid.tileAdded.connect(self.tileAdded)
        grid.tileRemoved.connect(self.tileRemoved)
        grid.tileValueChanged.connect(self.tileValueChanged)
        grid.tileMoved.connect(self.tileMoved)

        self._grid = grid
        self.row_count = grid.row_count
        self.column_count = grid.column_count
        self.gridChanged.emit(self._grid)

    def grid(self):
        return self._grid

    def start(self):
        self.spawnRandom(TILES_AT_START)
        print('\n'.join(['\t'.join([str(it) for it in row]) for row in self.grid()._grid]))

    def addTile(self, row, col, value):
        tile = self.grid().addTile(row, col, value)
        return tile

    def spawnRandom(self, num=TILES_AT_TURN):
        empty_cells: list[tuple[int, int]] = []
        for i in range(self.grid().row_count):
            for j in range(self.grid().column_count):
                if self.grid().isCellEmpty(i, j):
                    empty_cells.append((i, j))
        for i, j in random.sample(empty_cells, num):
            self.addTile(i, j, 2 if random.randint(0, 3) else 4)

    def eventFilter(self, obj, event):
        if type(event) is QKeyEvent \
                and event.type() == QKeyEvent.Type.KeyRelease:
            self._processMove(event.key())
        return False

    def _processMove(self, key: Qt.Key):
        if key == Qt.Key.Key_Up:
            result = self._moveUp()
        elif key == Qt.Key.Key_Down:
            result = self._moveDown()
        elif key == Qt.Key.Key_Left:
            result = self._moveLeft()
        elif key == Qt.Key.Key_Right:
            result = self._moveRight()
        else:
            result = False

        if result:
            self.spawnRandom()
        print('\n'.join(['\t'.join([str(it) for it in row]) for row in self.grid()._grid]))

    def _moveUp(self):
        field_changed = False
        for j in range(self.grid().column_count):
            target_cell = 0
            for i in range(1, self.grid().row_count):
                for k in range(target_cell, i):
                    result = self.grid().tryMoveTile(
                        i, j, k, j
                    )
                    # print(result)
                    if result in (MoveResult.Moved, MoveResult.Merged):
                        break
                if result == MoveResult.Moved:
                    target_cell = k
                    field_changed = True
                elif result == MoveResult.Merged:
                    target_cell = k + 1
                    field_changed = True
                elif result == MoveResult.Stayed:
                    target_cell = i
        return field_changed

    def _moveDown(self):
        field_changed = False
        for j in range(self.grid().column_count):
            target_cell = self.grid().row_count - 1
            for i in range(target_cell - 1, -1, -1):
                for k in range(target_cell, i, -1):
                    result = self.grid().tryMoveTile(
                        i, j, k, j
                    )
                    # print(result)
                    if result in (MoveResult.Moved, MoveResult.Merged):
                        break
                if result == MoveResult.Moved:
                    target_cell = k
                    field_changed = True
                elif result == MoveResult.Merged:
                    target_cell = k - 1
                    field_changed = True
                elif result == MoveResult.Stayed:
                    target_cell = i
        return field_changed

    def _moveLeft(self):
        field_changed = False
        for i in range(self.grid().row_count):
            target_cell = 0
            for j in range(1, self.grid().column_count):
                for k in range(target_cell, j):
                    result = self.grid().tryMoveTile(
                        i, j, i, k
                    )
                    # print(result)
                    if result in (MoveResult.Moved, MoveResult.Merged):
                        break
                if result == MoveResult.Moved:
                    target_cell = k
                    field_changed = True
                elif result == MoveResult.Merged:
                    target_cell = k + 1
                    field_changed = True
                elif result == MoveResult.Stayed:
                    target_cell = j
        return field_changed

    def _moveRight(self):
        field_changed = False
        for i in range(self.grid().row_count):
            target_cell = self.grid().column_count - 1
            for j in range(target_cell - 1, -1, -1):
                for k in range(target_cell, j, -1):
                    result = self.grid().tryMoveTile(
                        i, j, i, k
                    )
                    # print(result)
                    if result in (MoveResult.Moved, MoveResult.Merged):
                        break
                if result == MoveResult.Moved:
                    target_cell = k
                    field_changed = True
                elif result == MoveResult.Merged:
                    target_cell = k - 1
                    field_changed = True
                elif result == MoveResult.Stayed:
                    target_cell = j
        return field_changed

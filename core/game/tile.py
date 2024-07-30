from enum import Enum

from PySide6.QtCore import (
    QObject, Signal, Property, QPoint
)


class Tile(QObject):
    def __init__(self, value=2, parent: QObject | None = None) -> None:
        super().__init__(parent)

        self._value = value

    valueChanged = Signal(int)

    @Property(int, notify=valueChanged)
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        if self._value != value:
            self._value = value
            self.valueChanged.emit(value)

    _cell = QPoint()

    def cell(self):
        parent: TileGrid = self.parent()
        try:
            self._cell = parent.findTile(self)
        finally:
            return self._cell

    def __str__(self) -> str:
        return str(self.value)


class MoveResult(Enum):
    Empty = 1
    Moved = 2
    Merged = 3
    Stayed = 4


class TileGrid(QObject):

    tileAdded = Signal(int, QPoint)
    tileRemoved = Signal(QPoint)
    tileValueChanged = Signal(int, QPoint)
    tileMoved = Signal(QPoint, QPoint)

    def __init__(self, rows=4, columns=4,
                 parent: QObject | None = None) -> None:
        super().__init__(parent)

        self.row_count = rows
        self.column_count = columns
        self._grid: list[list[Tile | None]] = \
            [[None for _ in range(rows)] for _ in range(columns)]

    def addTile(self, row, col, value):
        if self._grid[row][col] is not None:
            raise IndexError(f'Cell [{row}, {col}] is not empty')
        tile = Tile(value, self)
        self._grid[row][col] = tile
        tile.valueChanged.connect(
            lambda v: self.tileValueChanged.emit(v, tile.cell())
        )
        self.tileAdded.emit(tile.value, tile.cell())
        return tile

    def removeTile(self, tile: Tile):
        self.tileRemoved.emit(tile.cell())

    def tryMoveTile(self, old_row, old_col, row, col):
        # print(old_row, old_col, row, col)
        target_tile: Tile = self._grid[row][col]
        source_tile: Tile = self._grid[old_row][old_col]
        if source_tile is None:
            return MoveResult.Empty
        elif target_tile is None:
            self._moveTile(old_row, old_col, row, col)
            return MoveResult.Moved
        else:
            if source_tile.value == target_tile.value:
                source_tile.value = target_tile.value = source_tile.value * 2
                self._moveTile(old_row, old_col, row, col)
                self.removeTile(target_tile)
                return MoveResult.Merged
            else:
                return MoveResult.Stayed

    def _moveTile(self, old_row, old_col, row, col):
        tile: Tile = self._grid[old_row][old_col]
        self._grid[row][col] = tile
        self._grid[old_row][old_col] = None
        self.tileMoved.emit(tile.cell(), QPoint(old_row, old_col))

    def isCellEmpty(self, row, col):
        return self._grid[row][col] is None

    def findTile(self, tile: Tile):
        for i in range(self.row_count):
            for j in range(self.column_count):
                if self._grid[i][j] == tile:
                    return QPoint(i, j)
        raise ValueError('Tile not in grid')

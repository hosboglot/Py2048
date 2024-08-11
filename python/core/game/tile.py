from enum import Enum

from PySide6.QtCore import (
    QObject, Signal, Property, QPoint
)


class Tile(QObject):
    def __init__(self, value=2, parent: QObject | None = None) -> None:
        super().__init__(parent)

        self._value = int(value)

    valueChanged = Signal(int)

    @Property(int, notify=valueChanged)
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        value = int(value)
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


class MoveAction(Enum):
    Empty = 1
    'Source cell is empty'
    Move = 2
    'Move source to target'
    Merge = 3
    'Merge source cell to target'
    Stay = 4
    'Cannot merge source to target'


class TileGrid(QObject):

    turnStarted = Signal()
    turnEnded = Signal()

    tileAdded = Signal(int, QPoint)
    tileRemoved = Signal(QPoint)
    tileMerged = Signal(int, QPoint, QPoint)
    tileMoved = Signal(QPoint, QPoint)
    tileValueChanged = Signal(int, QPoint)

    def __init__(self, rows=4, columns=4,
                 parent: QObject | None = None) -> None:
        super().__init__(parent)

        self.row_count = rows
        self.column_count = columns
        self._grid: list[list[Tile | None]] = \
            [[None for _ in range(rows)] for _ in range(columns)]

    def beginTurn(self):
        self._new_grid = [row.copy() for row in self._grid]
        self.turnStarted.emit()

    def endTurn(self):
        self._new_grid = None
        self.turnEnded.emit()

    def addTile(self, row, col, value):
        target: Tile | None = self._grid[row][col]
        if target is not None:
            self.print()
            raise IndexError(f'[Add] Cell {row, col} is not empty')

        tile = Tile(value, self)
        self._grid[row][col] = tile
        self.tileAdded.emit(tile.value, tile.cell())
        return tile

    def mergeTile(self, old_row, old_col, row, col):
        source: Tile | None = self._grid[old_row][old_col]
        target: Tile | None = self._grid[row][col]
        if source is None:
            self.print()
            raise ValueError(
                f'[Merge] Source cell {old_row, old_col} is empty'
            )
        if target is None:
            self.print()
            raise ValueError(f'[Merge] Target cell {row, col} is empty')
        if source.value != target.value:
            self.print()
            raise ValueError(
                '[Merge] Source and target cell values are not equal ' +
                f'({source.value} vs {target.value})'
            )

        self._grid[row][col] = source
        self._grid[old_row][old_col] = None
        source.value *= 2
        self.tileMerged.emit(
            source.value,
            QPoint(row, col),
            QPoint(old_row, old_col))
        return source

    def unmergeTile(self, old_row, old_col, row, col):
        source: Tile | None = self._grid[old_row][old_col]
        target: Tile | None = self._grid[row][col]
        if source is None:
            self.print()
            raise ValueError(
                f'[Unmerge] Source cell {old_row, old_col} is empty'
            )
        if target is not None:
            self.print()
            raise ValueError(f'[Unmerge] Target cell {row, col} is not empty')

        self._grid[row][col] = Tile(source.value / 2, self)
        source.value /= 2
        # self.tileMerged.emit(
        #     source.value,
        #     QPoint(row, col),
        #     QPoint(old_row, old_col))
        return self._grid[row][col]

    def moveTile(self, old_row, old_col, row, col):
        source: Tile | None = self._grid[old_row][old_col]
        target: Tile | None = self._grid[row][col]
        if source is None:
            self.print()
            raise ValueError(f'[Move] Source cell {old_row, old_col} is empty')
        if target is not None:
            self.print()
            raise ValueError(f'[Move] Target cell {row, col} is not empty')

        self._grid[row][col] = source
        self._grid[old_row][old_col] = None
        self.tileMoved.emit(QPoint(row, col), QPoint(old_row, old_col))
        return source

    def changeTileValue(self, value, row, col):
        target: Tile | None = self._grid[row][col]
        if target is None:
            self.print()
            raise ValueError(f'[Change value] Target cell {row, col} is empty')

        target.value = value
        self.tileValueChanged.emit(value, QPoint(row, col))
        return target

    def removeTile(self, row, col):
        target: Tile | None = self._grid[row][col]
        if target is None:
            self.print()
            raise ValueError(f'[Remove] Target cell {row, col} is empty')

        self._grid[row][col] = None
        self.tileRemoved.emit(QPoint(row, col))
        return target

    def checkMove(self, old_row, old_col, row, col):
        target: Tile | None = self._new_grid[row][col]
        source: Tile | None = self._new_grid[old_row][old_col]
        if source is None:
            return MoveAction.Empty
        elif target is None:
            self._new_grid[row][col] = source
            self._new_grid[old_row][old_col] = None
            return MoveAction.Move
        else:
            if source.value == target.value:
                self._new_grid[row][col] = source
                self._new_grid[old_row][old_col] = None
                return MoveAction.Merge
            else:
                return MoveAction.Stay

    def isCellEmpty(self, row, col):
        grid = self._new_grid if self._new_grid else self._grid
        return grid[row][col] is None

    def findTile(self, tile: Tile):
        for i in range(self.row_count):
            for j in range(self.column_count):
                if self._grid[i][j] == tile:
                    return QPoint(i, j)
        raise ValueError('Tile not in grid')

    def print(self):
        grid = self._new_grid if self._new_grid else self._grid
        print('====================')
        print('\n'.join(
            ['\t'.join([str(it) for it in row])
             for row in grid]
        ))
        print('====================')

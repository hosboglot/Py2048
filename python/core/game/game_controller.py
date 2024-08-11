import random

from PySide6.QtCore import (
    QObject, Signal, Qt, QPoint
)
from PySide6.QtGui import (
    QKeyEvent, QUndoStack
)

from core.game.tile import TileGrid, MoveAction
from core.widgets.game_widget import GameScene
from core.commands.turn_commands import (
    TurnCommand, AddCommand, MoveCommand, MergeCommand
)

TILES_AT_START = 4
TILES_AT_TURN = 1


class GameController(QObject):

    turnStarted = Signal()
    turnEnded = Signal()

    tileAdded = Signal(int, QPoint)
    tileRemoved = Signal(QPoint)
    tileValueChanged = Signal(int, QPoint)
    tileMoved = Signal(QPoint, QPoint)

    def __init__(self, rows=4, columns=4,
                 parent: QObject | None = None) -> None:
        super().__init__(parent)
        parent.installEventFilter(self)

        self._undo_stack = None
        self._turn_command = None

        self._grid = None
        self._scene = None

        self.setGrid(TileGrid(rows, columns))

    def setUndoStack(self, undo_stack: QUndoStack):
        self._undo_stack = undo_stack

    gridChanged = Signal(TileGrid)

    def setGrid(self, grid: TileGrid):
        if self._grid == grid:
            return

        self._grid = grid
        self.row_count = grid.row_count
        self.column_count = grid.column_count
        self.gridChanged.emit(self._grid)

    def grid(self):
        return self._grid

    def setScene(self, scene: GameScene):
        if self._scene == scene:
            return

        self._scene = scene
        self._scene.setSize(self.row_count, self.column_count)

    def scene(self):
        return self._scene

    def start(self):
        self.beginTurn()
        self.spawnRandom(TILES_AT_START)
        self.endTurn()

    def spawnRandom(self, num=TILES_AT_TURN):
        empty_cells: list[tuple[int, int]] = []
        for i in range(self.grid().row_count):
            for j in range(self.grid().column_count):
                if self.grid().isCellEmpty(i, j):
                    empty_cells.append((i, j))
        for i, j in random.sample(empty_cells, num):
            self.addTile(
                2 if random.randint(0, 3) else 4,
                QPoint(i, j)
            )

    def beginTurn(self):
        self._grid.beginTurn()
        self._turn_command = TurnCommand(self.grid())
        print('start turn')

    def endTurn(self, do_push=True):
        self._grid.endTurn()
        if do_push:
            self._undo_stack.push(self._turn_command)
        self._turn_command = None
        print('end turn')

    def addTile(self, value: int, cell: QPoint):
        AddCommand(value, cell,
                   self.scene(), self.grid(), self._turn_command)
        print('add tile')

    # @Slot(QPoint)
    # def removeTile(self, cell: QPoint):
    #     RemoveCommand(cell, self.scene(), self._turn_command)
    #     print('remove tile')

    def mergeTile(self, new_cell: QPoint, old_cell: QPoint):
        MergeCommand(new_cell, old_cell,
                     self.scene(), self.grid(), self._turn_command)
        print('merge tile')

    def moveTile(self, new_cell: QPoint, old_cell: QPoint):
        MoveCommand(new_cell, old_cell,
                    self.scene(), self.grid(), self._turn_command)
        print('move tile')

    def eventFilter(self, obj, event):
        if type(event) is QKeyEvent \
                and event.type() == QKeyEvent.Type.KeyRelease:
            if event.key() in (Qt.Key.Key_Up, Qt.Key.Key_Down,
                               Qt.Key.Key_Left, Qt.Key.Key_Right):
                self._processMove(event.key())
        return False

    def _processMove(self, key: Qt.Key):
        self.beginTurn()

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

        self.endTurn(result)

    def _moveUp(self):
        field_changed = False
        for j in range(self.grid().column_count):
            target_cell = 0
            for i in range(1, self.grid().row_count):
                for k in range(target_cell, i):
                    result = self.grid().checkMove(
                        i, j, k, j
                    )
                    # print(result)
                    if result in (MoveAction.Move, MoveAction.Merge):
                        break
                if result == MoveAction.Move:
                    self.moveTile(QPoint(k, j), QPoint(i, j))
                    target_cell = k
                    field_changed = True
                elif result == MoveAction.Merge:
                    self.mergeTile(QPoint(k, j), QPoint(i, j))
                    target_cell = k + 1
                    field_changed = True
                elif result == MoveAction.Stay:
                    target_cell = i
        return field_changed

    def _moveDown(self):
        field_changed = False
        for j in range(self.grid().column_count):
            target_cell = self.grid().row_count - 1
            for i in range(target_cell - 1, -1, -1):
                for k in range(target_cell, i, -1):
                    result = self.grid().checkMove(
                        i, j, k, j
                    )
                    # print(result)
                    if result in (MoveAction.Move, MoveAction.Merge):
                        break
                if result == MoveAction.Move:
                    self.moveTile(QPoint(k, j), QPoint(i, j))
                    target_cell = k
                    field_changed = True
                elif result == MoveAction.Merge:
                    self.mergeTile(QPoint(k, j), QPoint(i, j))
                    target_cell = k - 1
                    field_changed = True
                elif result == MoveAction.Stay:
                    target_cell = i
        return field_changed

    def _moveLeft(self):
        field_changed = False
        for i in range(self.grid().row_count):
            target_cell = 0
            for j in range(1, self.grid().column_count):
                for k in range(target_cell, j):
                    result = self.grid().checkMove(
                        i, j, i, k
                    )
                    # print(result)
                    if result in (MoveAction.Move, MoveAction.Merge):
                        break
                if result == MoveAction.Move:
                    self.moveTile(QPoint(i, k), QPoint(i, j))
                    target_cell = k
                    field_changed = True
                elif result == MoveAction.Merge:
                    self.mergeTile(QPoint(i, k), QPoint(i, j))
                    target_cell = k + 1
                    field_changed = True
                elif result == MoveAction.Stay:
                    target_cell = j
        return field_changed

    def _moveRight(self):
        field_changed = False
        for i in range(self.grid().row_count):
            target_cell = self.grid().column_count - 1
            for j in range(target_cell - 1, -1, -1):
                for k in range(target_cell, j, -1):
                    result = self.grid().checkMove(
                        i, j, i, k
                    )
                    # print(result)
                    if result in (MoveAction.Move, MoveAction.Merge):
                        break
                if result == MoveAction.Move:
                    self.moveTile(QPoint(i, k), QPoint(i, j))
                    target_cell = k
                    field_changed = True
                elif result == MoveAction.Merge:
                    self.mergeTile(QPoint(i, k), QPoint(i, j))
                    target_cell = k - 1
                    field_changed = True
                elif result == MoveAction.Stay:
                    target_cell = j
        return field_changed

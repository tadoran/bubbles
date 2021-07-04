from random import sample, choice

import numpy as np
from PyQt5.QtCore import QObject, pyqtSignal, QTimer, QPoint, QRect
from enums import CoordinatesMoves
from tableContainer import NpTableContainer


class GameItem(QObject):
    ''' Ball with color and status '''

    def __init__(self, color, cell=None):
        super(GameItem, self).__init__()
        self.color = color
        self.cell = cell

    @property
    def cell(self):
        return self._cell

    @cell.setter
    def cell(self, cell):
        self._cell = cell
        if cell is None and self._cell:
            del self.item
            return
        if cell:
            if cell.item != self:
                cell.item = self

    @cell.deleter
    def cell(self):
        self._cell.item = None
        self._cell = None

    def __str__(self):
        in_cell = "" if not self.cell else f" in cell {self.cell}"
        return f"{str(self.color).capitalize()} point{in_cell}"

    def __repr__(self):
        return f"GameItem('{self.color}', {self.cell})"


class GameCell(QObject):
    """Contains blueprint of a cell on game field"""
    changed = pyqtSignal()
    next_color = pyqtSignal(object)

    def __init__(self, parent_field, y: int, x: int, item: GameItem = None):
        super(GameCell, self).__init__()
        self.parent_field = parent_field
        parent_field.field_was_reset.connect(self.reset)
        self.x = x
        self.y = y
        self.item = item
        self.changed.emit()
        self._active = False

    @property
    def item(self):
        return self._item

    @item.setter
    def item(self, item):
        self._item = item
        if item is None and self._item:
            del self.item
            return

        if item and item.cell != self._item:
            item.cell = self
        self.changed.emit()

    @item.deleter
    def item(self):
        del self._item.cell
        self._item = None

        self.changed.emit()

    def reset(self):
        self.item = None
        self.active = False
        self.next_color.emit(None)
        self.changed.emit()

    def __str__(self):
        return f"GameCell({self.y},{self.x})"

    def __repr__(self):
        return f"GameCell({self.y},{self.x})"


class GameField(QObject):
    """Contains game field and all logic of it"""
    WIDTH = 10
    HEIGHT = 10
    ITEMS_IN_LINE = 2
    MOVE_SPEED_MS = 30
    COLORS_ON_FIELD = 6
    COLORS = ["darkgreen", "darkmagenta", "darkorange", "deeppink", "yellow",
              "mediumseagreen", "darkblue", "skyblue", "firebrick", "blue"]

    field_was_reset = pyqtSignal()
    items_were_spawned = pyqtSignal()
    cells_cleared = pyqtSignal(int)
    item_moved = pyqtSignal()
    loose = pyqtSignal()

    def __init__(self, height: int = 0, width: int = 0, colors=COLORS_ON_FIELD):
        super(GameField, self).__init__()

        self.field_colors = sample(self.COLORS, colors)
        # self.field_colors = sample(self.COLORS, len(self.COLORS))
        if width != 0:
            self.WIDTH = width
        if height != 0:
            self.HEIGHT = height
        self.items = NpTableContainer(self.HEIGHT, self.WIDTH)
        self.create_field_cells()
        self.move_timer = QTimer()

        self.loose.connect(self.reset)

    def find_filled_cells(self):
        cells = np.ravel(self.items)
        empty_cells = [c for c in cells if c.item is not None]
        return empty_cells

    def find_empty_cells(self):
        cells = np.ravel(self.items)
        empty_cells = [c for c in cells if c.item is None]
        return empty_cells

    def create_field_cells(self):
        for y in range(self.HEIGHT):
            for x in range(self.WIDTH):
                if self.items[y, x] is None:
                    self.items[y, x] = GameCell(self, y, x)
                item = GameItem(choice(self.field_colors))
                self.items[y, x].item = item

    def spawn_items(self, n: int = 0):
        if n == 0:
            n = self.WIDTH

        for x in range(n):
            item = GameItem(choice(self.field_colors))
            cell = self.items[0, x]
            if cell.item is None:
                cell.item = item
                self.move_item(cell)
        self.items_were_spawned.emit()

    def move_item(self, cell, second_try: bool = False):
        current_cell = cell
        next_cell = None
        if cell.x != 0:
            cells_on_left = self.items[:, cell.x]
            left_row_filled_cells = sum([c.item is not None for c in cells_on_left])
            if left_row_filled_cells == 0:
                for x in range(cell.x, 0, -1):
                    for moved_cell in self.items[:, x]:
                        moved_cell.item = self.items[moved_cell.y, x - 1].item
                for moved_cell in self.items[:, 0]:
                    moved_cell.item = None
        try:
            next_cell = self.items[cell.y + 1, cell.x]
        except Exception as e:
            pass

        if next_cell:
            if next_cell.item:
                if sum([c.item is None for c in self.items[cell.y:, cell.x]]) > 0:
                    second_try = False

                if not second_try:
                    self.move_timer.singleShot(self.MOVE_SPEED_MS * 2,
                                               lambda self=self, cell=cell: self.move_item(cell, True))
                    return
                else:
                    return
            next_cell.item = current_cell.item
            current_cell.item = None
            self.item_moved.emit()
            self.move_timer.singleShot(self.MOVE_SPEED_MS,
                                       lambda self=self, next_cell=next_cell: self.move_item(next_cell))

    def reset(self):
        self.field_colors = sample(self.COLORS, self.COLORS_ON_FIELD)
        self.field_was_reset.emit()
        self.create_field_cells()

    def find_same_items(self, cell):
        moves = CoordinatesMoves
        possible_moves = [moves.RIGHT, moves.DOWN, moves.LEFT, moves.UP]
        directions = [QPoint(m.value[1], m.value[0]) for m in possible_moves]

        rect = QRect(0, 0, self.WIDTH, self.HEIGHT)

        same_items = [cell]
        same_items_set = {str(cell)}

        for current_cell in same_items:
            added_cells = []
            for d in directions:
                new_point = QPoint(current_cell.x + d.x(), current_cell.y + d.y())
                if not rect.contains(new_point):
                    continue
                else:
                    new_cell = self.items[new_point.y(), new_point.x()]
                    if not new_cell.item or str(new_cell) in same_items_set:
                        continue

                    if current_cell.item.color == new_cell.item.color:
                        added_cells.append(new_cell)
                        same_items_set.add(str(new_cell))
            same_items.extend(added_cells)
        return same_items

    def cell_clicked(self, cell):
        if cell.item:
            same_items = self.find_same_items(cell)
            if len(same_items) >= self.ITEMS_IN_LINE:
                lines_to_shift_down = set()
                for removed_cell in same_items:
                    removed_cell.item = None
                    lines_to_shift_down.add(removed_cell.x)

                for x in lines_to_shift_down:
                    for y in range(self.HEIGHT - 1, 0, -1):
                        if self.items[y, x].item:
                            pass
                        else:
                            cells_above = [c.y for c in self.items[:y, x] if c.item]
                            if len(cells_above) == 0:
                                break

                            nearest_filled_y = max(cells_above)
                            self.items[y, x].item = self.items[nearest_filled_y, x].item
                            self.items[nearest_filled_y, x].item = None

                max_x = max(lines_to_shift_down)
                for x in range(max_x, 0, -1):
                    column = self.items[:, x]
                    filled_cells_count = sum(c.item is not None for c in column)
                    if filled_cells_count == 0:
                        for xn in range(x - 1, -1, -1):
                            column_n = self.items[:, xn]
                            filled_cells_count_n = sum(c.item is not None for c in column_n)
                            if filled_cells_count_n > 0:
                                for shifted_cell in column:
                                    shifted_cell.item = self.items[shifted_cell.y, xn].item
                                    self.items[shifted_cell.y, xn].item = None
                                break

                top_row_filled_cells = sum([c.item is not None for c in self.items[0, :]])
                if top_row_filled_cells == 0:
                    self.spawn_items()

                self.cells_cleared.emit(len(same_items))

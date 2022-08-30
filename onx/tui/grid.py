from textual import events
from textual.views import GridView

from onx import settings
from onx.tui.tile import Tile


class Grid(GridView):
    def __init__(self, *args, grid_size: int = settings.DEFAULT_GRID_SIZE, **kwargs):
        super().__init__(*args, **kwargs)
        self._grid_size = grid_size
        self.tiles: tuple[Tile, ...] = tuple(
            Tile(num=i) for i in range(self._grid_size**2)
        )
        if self._grid_size >= 11:
            self._col_size, self._row_size = 5, 3
        elif self._grid_size >= 9:
            self._col_size, self._row_size = 6, 4
        elif self._grid_size >= 6:
            self._col_size, self._row_size = 8, 5
        elif self._grid_size == 5:
            self._col_size, self._row_size = 15, 8
        else:
            self._col_size, self._row_size = 20, 9

    async def on_mount(self, event: events.Mount) -> None:
        self.grid.set_align("center", "center")
        self.grid.add_column("col", size=self._col_size, repeat=self._grid_size)
        self.grid.add_row("row", size=self._row_size, repeat=self._grid_size)
        self.grid.place(*self.tiles)

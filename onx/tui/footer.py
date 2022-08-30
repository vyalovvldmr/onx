from rich.console import RenderableType
from rich.text import Text
from textual.widgets import Footer as _Footer


class Footer(_Footer):
    def __init__(self) -> None:
        super().__init__()
        self._connection_text: str = "Disconnected"
        self._connection_style: str = "white on dark_red"

    def render(self) -> RenderableType:
        if self._key_text is None:
            self._key_text = self.make_key_text()
            self._key_text.append_text(Text(f"| Websocket: {self._connection_text}"))
            self._key_text.style = self._connection_style
        return self._key_text

    def on_connect(self) -> None:
        self._key_text = None
        self._connection_text = "Connected"
        self._connection_style = "white on dark_green"
        self.refresh()

    def on_disconnect(self) -> None:
        self._key_text = None
        self._connection_text = "Disconnected"
        self._connection_style = "white on dark_red"
        self.refresh()

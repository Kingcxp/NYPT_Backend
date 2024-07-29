import os
import sys
import math

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/NYPT/")

from io import StringIO
from threading import Thread
from textual.app import App, ComposeResult, on
from textual.binding import Binding, BindingType
from textual.widgets import Header, Footer, Label, Input
from textual.containers import Horizontal, Vertical, VerticalScroll
from rich.text import Text
from typing import ClassVar, List

from NYPT.launcher import main


def parse_rich(text: str) -> Text:
    parsed_text = Text.from_ansi(text)
    return parsed_text


class RichOutput(StringIO):
    def __init__(self, rich_log: Label, scroll: VerticalScroll) -> None:
        super().__init__()
        self.rich_log = rich_log
        self.scroll = scroll

    def write(self, s: str) -> None:
        super().write(s)
        is_maximum: bool = self.scroll.is_vertical_scroll_end
        self.rich_log.update(parse_rich(self.getvalue()))
        if is_maximum:
            self.scroll.scroll_end(animate=False)


class MainApp(App):

    TITLE: str = "NYPT Backend"
    DEFAULT_CSS = \
    """
    VerticalScroll { border: solid white; }
    """
    BINDINGS: ClassVar[List[BindingType]] = [
        Binding("escape", "quit", "Quit App"),
        Binding("ctrl+s", "toggle_dark", "Toggle Dark Mode", priority=True)
    ]

    def compose(self) -> ComposeResult:
        self.input = Input(value="> ", id="main-input")
        self.log_left = Label(id="main-log-left")
        self.log_right = Label(id="main-log-right")
        self.scroll_left = VerticalScroll(self.log_left)
        self.scroll_right = VerticalScroll(self.log_right)
        yield Header()
        yield Vertical(
            Horizontal(
                self.scroll_left,
                self.scroll_right
            ),
            self.input
        )
        yield Footer()

    def update(self) -> None:
        self.input.focus()
        
        if self.input.cursor_position < 2:
            self.input.cursor_position = 2

    def on_mount(self) -> None:
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        self.original_stdin = sys.stdin

        self.stdout = RichOutput(self.log_left, self.scroll_left)
        self.stderr = RichOutput(self.log_right, self.scroll_right)
        self.stdin = StringIO()

        sys.stdout = self.stdout
        sys.stderr = self.stderr
        sys.stdin = self.stdin

        self.set_interval(1/60, self.update)
        
        self.process = Thread(target=main)
        self.process.start()

    def action_quit(self) -> None:
        self.stdin.write("exit\n")
        self.stdin.seek(0)
        self.stdin.flush()
        self.process.join()
        self.stdin.close()
        self.stdout.close()
        self.stderr.close()
        sys.stdin = self.original_stdin
        sys.stdout = self.original_stdout
        sys.stderr = self.original_stderr
        self.exit()

    @on(Input.Changed)
    def on_input_changed(self, event: Input.Changed) -> None:
        event.input.value = event.input.value.lstrip()
        if not event.input.value.startswith("> "):
            if event.input.value.startswith(">"):
                event.input.value = event.input.value.replace(">", "> ", 1)
            else:
                event.input.value = "> " + event.input.value
        if event.input.cursor_position < 2:
            event.input.cursor_position = 2

    @on(Input.Submitted)
    def on_input_submitted(self, event: Input.Submitted) -> None:
        command = event.input.value.replace("> ", "", 1)

        event.input.value = "> "
        event.input.cursor_position = 2

        if command == "clear":
            self.stderr.truncate(0)
            self.log_right.update("")
            return

        self.stdin.truncate(0)
        self.stdin.write(command + "\n")
        self.stderr.write("> " + command + "\n")
        self.stdin.seek(0)
        self.stdin.flush()


def main_app() -> None:
    app = MainApp()
    app.run()


if __name__ == "__main__":
    main_app()

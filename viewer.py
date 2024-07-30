import os
import sys
import math

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/NYPT/")

from io import StringIO
from threading import Thread
from textual.app import App, ComposeResult, on
from textual.binding import Binding, BindingType
from textual.widgets import Header, Footer, RichLog, Input
from textual.containers import Horizontal, Vertical, VerticalScroll
from rich.text import Text
from typing import ClassVar, List

from NYPT.launcher import main


def parse_rich(text: str) -> Text:
    parsed_text = Text.from_ansi(text)
    return parsed_text


class RichOutput(StringIO):
    def __init__(self, rich_log: RichLog) -> None:
        super().__init__()
        self.rich_log = rich_log

    def write(self, s: str) -> None:
        super().write(s)
        is_maximum: bool = self.rich_log.is_vertical_scroll_end
        self.rich_log.write(parse_rich(s))
        if is_maximum:
            self.rich_log.scroll_end(animate=False)


class MainApp(App):

    TITLE: str = "NYPT Backend"
    DEFAULT_CSS = """
    RichLog {
        border: round white;
    }
    RichLog:focus {
        border: round $accent;
    }
    """
    BINDINGS: ClassVar[List[BindingType]] = [
        Binding("escape", "quit", "Quit App"),
        Binding("ctrl+s", "toggle_dark", "Toggle Dark Mode", priority=True)
    ]

    def compose(self) -> ComposeResult:
        self.input = Input(value="> ", id="main-input")
        self.log_left = RichLog(id="main-log-left", wrap=True)
        self.log_right = RichLog(id="main-log-right", wrap=True)
        yield Header()
        yield Vertical(
            Horizontal(
                self.log_left,
                self.log_right
            ),
            self.input
        )
        yield Footer()

    def update(self) -> None:
        if self.input.cursor_position < 2:
            self.input.cursor_position = 2

    def on_mount(self) -> None:
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        self.original_stdin = sys.stdin

        self.stdout = RichOutput(self.log_left)
        self.stderr = RichOutput(self.log_right)
        self.stdin = StringIO()

        sys.stdout = self.stdout
        sys.stderr = self.stderr
        sys.stdin = self.stdin

        self.set_interval(1/60, self.update)
        
        self.process = Thread(target=main)
        self.process.start()

        self.input.focus()

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
            self.log_right.clear()
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

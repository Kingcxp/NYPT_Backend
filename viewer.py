import os
import gc
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/NYPT/")

from io import StringIO
from threading import Thread
from textual.app import App, ComposeResult, on
from textual.binding import Binding, BindingType
from textual.widgets import Header, Footer, TextArea, Input
from textual.containers import Horizontal, Vertical
from typing import ClassVar, List

from NYPT.launcher import main


class MainApp(App):

    TITLE: str = "NYPT Backend"
    BINDINGS: ClassVar[List[BindingType]] = [
        Binding("escape", "quit", "Quit App"),
        Binding("ctrl+s", "toggle_dark", "Toggle Dark Mode", priority=True)
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Vertical(
            Horizontal(
                TextArea(disabled=True, id="main-textarea-left"),
                TextArea(disabled=True, id="main-textarea-right")
            ),
            Input(value="> ", id="main-input")
        )
        yield Footer()

    def update(self) -> None:
        input: Input = self.query_one("#main-input")
        textarea_left: TextArea = self.query_one("#main-textarea-left")
        textarea_right: TextArea = self.query_one("#main-textarea-right")

        if input.cursor_position < 2:
            input.cursor_position = 2

        try:
            textarea_left.text = self.stdout.getvalue()
            textarea_right.text = self.stderr.getvalue()
        except:
            pass

    def on_mount(self) -> None:
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        self.original_stdin = sys.stdin

        self.stdout = StringIO()
        self.stderr = StringIO()
        self.stdin = StringIO()

        sys.stdout = self.stdout
        sys.stderr = self.stderr
        sys.stdin = self.stdin

        self.set_interval(1/15, self.update)
        
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

        if command == "restart":
            self.query_one("#main-textarea-left").text = ""
            self.query_one("#main-textarea-right").text = ""
            
            self.stdin.write("exit\n")
            self.sedin.seek(0)
            self.stdin.flush()
            self.process.join()
            self.process = Thread(target=main)
            gc.collect()
            self.process.start()
            return
        elif command == "clear":
            self.stderr.truncate(0)
            self.query_one("#main-textarea-right").text = ""
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

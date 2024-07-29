from typing import List

from ...manager import CommandInterface, console


class TestCommand(CommandInterface):
    @property
    def command(self) -> str:
        return 'template-test'
    
    @property
    def description(self) -> str:
        return "Template Command"
    
    @property
    def usage(self) -> str:
        return 'template-test'
    
    def execute(self, args: List[str]) -> bool:
        console.info(f'[yellow]Template test command![/yellow]')
        return True
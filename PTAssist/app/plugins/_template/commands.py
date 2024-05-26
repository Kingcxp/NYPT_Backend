from typing import List

from ...manager import CommandInterface, logger


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
        logger.opt(colors=True).info(f'<y>Template test command!</y>')
        return True
from flask import Blueprint

from .commands import *


main = Blueprint("template", __name__)
__blueprint__ = main
__commands__ = [
    TestCommand()
]


from . import template
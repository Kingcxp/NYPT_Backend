from flask import Blueprint

from .commands import *


main = Blueprint('main', __name__)
__blueprint__ = main
__commands__ = [
    TestCommand()
]


from . import template
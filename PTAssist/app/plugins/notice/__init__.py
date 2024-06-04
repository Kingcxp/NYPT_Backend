from flask import Blueprint


main = Blueprint('main', __name__)
__blueprint__ = main
__commands__ = []


from . import notice

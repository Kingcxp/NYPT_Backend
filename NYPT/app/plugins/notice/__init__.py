from flask import Blueprint


main = Blueprint('notice', __name__)
__blueprint__ = main
__commands__ = []


from . import notice

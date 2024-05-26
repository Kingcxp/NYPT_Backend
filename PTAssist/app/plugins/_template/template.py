from . import main


@main.route("/template")
def template():
    return "This is a template plugin."

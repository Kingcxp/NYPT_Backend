from . import main


@main.route("/template")
async def template():
    return "This is a template plugin."

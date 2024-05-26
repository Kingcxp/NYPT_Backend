import os
from flask import Flask
from flask_cors import CORS
from flask_session import Session
from pathlib import Path
from typing import Tuple
from .manager import load_all_plugins, CommandManager

def create_app(launcher_path: Path) -> Tuple[Flask, CommandManager]:
    """
    Create an flask application
    """
    app = Flask(__name__)
    manager = CommandManager()
    app.config['JSON_AS_ASCII'] = False
    app.config['SESSION_TYPE'] = 'filesystem'
    load_all_plugins(app, manager, launcher_path, plugin_dir=[os.path.dirname(__file__) + '/plugins'])
    CORS(app, resources=r"/*", supports_credentials=True)
    Session(app)

    return app, manager
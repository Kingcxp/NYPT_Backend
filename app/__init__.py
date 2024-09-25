import os
import secrets

from fastapi import FastAPI
from dotenv import load_dotenv, find_dotenv
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from .manager import load_all_routers, console


def create_app():
    """创建 FastAPI 实例

    Args:
        launcher_path (str): 模块启动路径
    """

    app = FastAPI(
        title="NYPT_Backend",
        description="FastAPI server for NYPT",
        version="v1.14.514",
    )

    # 注册 middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"]
    )
    app.add_middleware(
        SessionMiddleware,
        secret_key=secrets.token_hex(16)
    )
    # 注册 router
    load_all_routers(
        app,
        plugin_dirs = [
            os.path.dirname(__file__) + "/plugins"
        ]
    )

    return app


app = create_app()
if load_dotenv(find_dotenv(), verbose=True):
    console.log("[green]成功加载[/green] [yellow].env[/yellow] [blue]文件！[/blue]")

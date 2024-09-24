import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base


class DatabaseAsync:
    """
    负责借助提供的 url 创建异步 SQLAlchemy 部件
    """
    def __init__(self, head: str, url: str) -> None:
        self.engine = create_async_engine(
            head + url, connect_args={"check_same_thread": False}
        )
        self.Session = sessionmaker(
            class_=AsyncSession,
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
        if not os.path.exists(url):
            with open(url, "w"):
                pass


class Database:
    """
    负责借助提供的 url 创建 SQLAlchemy 部件
    """
    def __init__(self, head: str, url: str) -> None:
        self.engine = create_engine(
            head + url, connect_args={"check_same_thread": False}
        )
        self.Session = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
        if not os.path.exists(url):
            with open(url, "w"):
                pass

import os

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base


class Database:
    """
    负责借助提供的 url 创建异步 SQLAlchemy 部件
    """
    def __init__(self, head: str, url: str) -> None:
        self.engine = create_async_engine(
            head + url, connect_args={"check_same_thread": False}
        )
        self.Session = async_sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
        self.Base = declarative_base()
        if not os.path.exists(url):
            with open(url, "w"):
                pass

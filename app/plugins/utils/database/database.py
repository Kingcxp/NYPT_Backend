from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base


class DatabaseAsync:
    """
    负责借助提供的 url 创建 SQLAlchemy 部件
    """
    def __init__(self, url: str) -> None:
        self.engine = create_async_engine(
            url, connect_args={"check_same_thread": False}
        )
        self.Session = sessionmaker(
            class_=AsyncSession,
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )

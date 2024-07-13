import os
import sqlalchemy
from uuid import UUID
from enum import Enum
from decimal import Decimal
from datetime import date, datetime, time, timedelta
from typing import List, Dict, Any, Optional, Tuple


class Article:
    """Class designed for long string text.
    """
    pass


class Interface:
    def __init__(self, dirname: str, name: str) -> None:
        """Initialize the interface.

        Args:
            dirname (str): Directory of the database
            name (str): name of the database
        """
        self.db_path = os.path.join(dirname, name + ".sqlite")
        self.engine = sqlalchemy.create_engine("sqlite:///" + self.db_path)
        # Create database if it does not exist.
        if not os.path.exists(self.db_path):
            with open(self.db_path, 'w') as file:
                pass
        self.tables = self.load_tables(self.engine)

    @staticmethod
    def load_tables(engine: sqlalchemy.engine.base.Engine) -> Dict[str, sqlalchemy.Table]:
        """Automatically Load all prevously stored tables.

        Args:
            engine (sqlalchemy.engine.base.Engine): Engine from sqlalchemy, standing for connection to the database

        Returns:
            Dict[str, sqlalchemy.Table]: Results that contains table names as keys and table instances as values
        """
        with engine.connect() as connection:
            tables: List[str] = engine.dialect.get_table_names(connection=connection)
        result: Dict[str, sqlalchemy.Table] = {}
        metadata = sqlalchemy.MetaData()
        for table in tables:
            result[table] = sqlalchemy.Table(table, metadata, autoload_with=engine)
        return result
    
    @staticmethod
    def decide_type(data_type: Optional[type]) -> Any:
        if data_type == str:
            return sqlalchemy.String(4096)
        if data_type == Article:
            return sqlalchemy.String(10485760)
        if data_type == int:
            return sqlalchemy.Integer()
        if data_type == float or data_type == Decimal:
            return sqlalchemy.Numeric()
        if data_type == datetime:
            return sqlalchemy.DateTime()
        if data_type == date:
            return sqlalchemy.Date()
        if data_type == time:
            return sqlalchemy.Time()
        if data_type == bytes:
            return sqlalchemy.BINARY()
        if data_type == Enum:
            return sqlalchemy.Enum()
        if data_type == bool:
            return sqlalchemy.Boolean()
        if data_type == timedelta:
            return sqlalchemy.Interval()
        if data_type == dict:
            return sqlalchemy.JSON()
        if data_type == list:
            return sqlalchemy.ARRAY()
        if data_type == tuple:
            return sqlalchemy.Tuple()
        if data_type == None:
            return sqlalchemy.Null()
        if data_type == UUID:
            return sqlalchemy.UUID()
        raise RuntimeError(
            f"database::Interface - Cannot find proper type for type {data_type}"
        )
        

    def create_table(self, name: str, contents: Dict[str, type]) -> None:
        """Creates a table in the database and stores it in self.tables.
        Table that already exists will be ignored silently.

        E.g.::

            >>> interface = Interface(os.path.dirname(os.path.abspath(__file__)), 'db')
            >>> interface.create_table("USER", { "UID": int, "NAME": str })

        Args:
            name (str): name of the table
            contents (Dict[str, type]): key and type of every column
        """
        table = sqlalchemy.Table(name, sqlalchemy.MetaData(), *[sqlalchemy.Column(item[0], self.decide_type(item[1])) for item in contents.items()])
        self.tables[table.name] = table
        table.create(self.engine, checkfirst=True)
        
    def drop_table(self, table: str) -> None:
        """Drop the targeted table immediately.
        Table that does not exist will be ignored silently.

        Args:
            table (str): Name of the table
        """
        got = self.tables.get(table)
        if got is not None:
            got.drop(self.engine, checkfirst=True)
            self.tables.pop(table)

    def insert(self, name: str, **kwargs) -> Optional[Any]:
        """Insert data into the database.
        Shall returns None if failed.

        E.g.::

            >>> interface = Interface(os.path.dirname(os.path.abspath(__file__)), 'db')
            >>> interface.insert("USER", UID=998244353, NAME="Kingcq")

        Args:
            name (str): name of the table
            **kwargs: keys and values of a row, this must exactly matches the whole row

        Returns:
            Optional[Any]: Result of the executed command, or None if an error occurred
        """
        try:
            with self.engine.connect() as connection:
                result = connection.execute(sqlalchemy.insert(self.tables[name]), [kwargs])
                connection.commit()
            return result
        except Exception as e:
            print(e)
            return None
        
    def select(self, name: str, where: Optional[Dict[str, Tuple[str, Any]]] = None, order_by: Optional[str] = None, is_desc: bool = False) -> Optional[Any]:
        """Select data from the database.
        Shall returns None if failed or no data found.

        E.g.::

            >>> interface = Interface(os.path.dirname(os.path.abspath(__file__)), 'db')
            >>> interface.select("USER").fetchall()
            [(998244353, 'Kingcq')]
            
            You can also select special data by where expression, multiple expressions is allowed and would be connected by AND operator.
            >>> interface.select("USER", where={ "UID": (">", 998244353) }).fetchall()
            []
            >>> interface.select("USER", where={ "UID": (">=", 998244353), "NAME": ("==", "Kingcq") }).fetchall()
            [(998244353, 'Kingcq')]

            You can also select ordered data frin tge database, by order_by expression:
            >>> interface.select("USER", order_by="UID").fetchall()
            [(998244353, 'Kingcq')]

        Args:
            name (str): name of the table
            where (Optional[Dict[str, Tuple[str, Any]]]): the where expression, including name of the column as key and (operator, certain value) as value
            order_by (Optional[str]): name of the column to be used as primary key to order rows.

        Returns:
            Optional[Any]: the result, or None if an error occurred
        """
        try:
            table = self.tables[name]
            command = sqlalchemy.select(table)
            if where is not None:
                for item in where.items():
                    if item[1][0] == "==":
                        command = command.where(table.c.get((item[0])) == item[1][1])
                    elif item[1][0] == "!=":
                        command = command.where(table.c.get((item[0])) != item[1][1])
                    elif item[1][0] == ">=":
                        command = command.where(table.c.get((item[0])) >= item[1][1])
                    elif item[1][0] == "<=":
                        command = command.where(table.c.get((item[0])) <= item[1][1])
                    elif item[1][0] == ">":
                        command = command.where(table.c.get((item[0])) > item[1][1])
                    elif item[1][0] == "<":
                        command = command.where(table.c.get((item[0])) < item[1][1])
            if order_by is not None:
                if is_desc:
                    command = command.order_by(table.c.get(order_by).desc())
                else:
                    command = command.order_by(table.c.get(order_by))
            with self.engine.connect() as connection:
                result = connection.execute(command)
            return result
        except Exception as e:
            print(e)
            return None
        
    def select_first(self, name: str, where: Optional[Dict[str, Tuple[str, Any]]] = None, order_by: Optional[str] = None, is_desc: bool = False) -> Optional[Any]:
        try:
            return self.select(name, where, order_by, is_desc).first()
        except:
            return None
        
        
    def select_all(self, name: str, where: Optional[Dict[str, Tuple[str, Any]]] = None, order_by: Optional[str] = None, is_desc: bool = False) -> Optional[Any]:
        try:
            return self.select(name, where, order_by, is_desc).fetchall()
        except:
            return None
        
    def select_scalar(self, name: str, where: Optional[Dict[str, Tuple[str, Any]]] = None, order_by: Optional[str] = None, is_desc: bool = False) -> Optional[Any]:
        try:
            return self.select(name, where, order_by, is_desc).scalar()
        except:
            return None
        
    def update(self, name: str, where: Optional[Dict[str, Tuple[str, Any]]] = None, **kwargs) -> Optional[Any]:
        """Update data in the database.
        Shall returns None if failed.

        E.g.::

            >>> interface = Interface(os.path.dirname(os.path.abspath(__file__)), 'db')
            >>> interface.update("USER", where={ "UID": ("==", 998244353) }, UID=114514)

        Args:
            name (str): name of the table
            where (Optional[Dict[str, Tuple[str, Any]]]): the where expression, including name of the column as key and (operator, certain value) as value
            kwargs: values to be changed, should exactly match the columns.
        
        Returns:
            Optional[Any]: the result, or None if an error occurred
        """
        try:
            table = self.tables[name]
            command = sqlalchemy.update(table)
            if where is not None:
                for item in where.items():
                    if item[1][0] == "==":
                        command = command.where(table.c.get((item[0])) == item[1][1])
                    elif item[1][0] == "!=":
                        command = command.where(table.c.get((item[0])) != item[1][1])
                    elif item[1][0] == ">=":
                        command = command.where(table.c.get((item[0])) >= item[1][1])
                    elif item[1][0] == "<=":
                        command = command.where(table.c.get((item[0])) <= item[1][1])
                    elif item[1][0] == ">":
                        command = command.where(table.c.get((item[0])) > item[1][1])
                    elif item[1][0] == "<":
                        command = command.where(table.c.get((item[0])) < item[1][1])
            with self.engine.connect() as connection:
                result = connection.execute(command.values({table.c.get((item[0])): item[1] for item in kwargs.items()}))
                connection.commit()
            return result
        except Exception as e:
            print(e)
            return None
        
    def delete(self, name: str, where: Optional[Dict[str, Tuple[str, Any]]] = None) -> Optional[Any]:
        """Delete data in the database.
        Shall returns None if failed.

        E.g.::

            >>> interface = Interface(os.path.dirname(os.path.abspath(__file__)), 'db')
            >>> interface.delete("USER", where={ "UID": ("==", 998244353) })

        Args:
            name (str): name of the table
            where (Optional[Dict[str, Tuple[str, Any]]]): the where expression, including name of the column as key and (operator, certain value) as value
        """
        try:
            table = self.tables[name]
            command = sqlalchemy.delete(table)
            if where is not None:
                for item in where.items():
                    if item[1][0] == "==":
                        command = command.where(table.c.get((item[0])) == item[1][1])
                    elif item[1][0] == "!=":
                        command = command.where(table.c.get((item[0])) != item[1][1])
                    elif item[1][0] == ">=":
                        command = command.where(table.c.get((item[0])) >= item[1][1])
                    elif item[1][0] == "<=":
                        command = command.where(table.c.get((item[0])) <= item[1][1])
                    elif item[1][0] == ">":
                        command = command.where(table.c.get((item[0])) > item[1][1])
                    elif item[1][0] == "<":
                        command = command.where(table.c.get((item[0])) < item[1][1])
            with self.engine.connect() as connection:
                result = connection.execute(command)
                connection.commit()
            return result
        except Exception as e:
            print(e)
            return None

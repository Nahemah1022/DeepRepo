# main_db.py

from __future__ import absolute_import

import logging
import os
from contextlib import contextmanager

from sqlalchemy import create_engine, text
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import sessionmaker, Session

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class DBRole:
    """Defines constants for database roles to ensure type safety."""
    WRITE = "write"
    READ = "read"


class DBHandle:
    """A handle that holds the configured database engines and reflected base class."""
    def __init__(self, write_engine, base_cls, read_engine=None):
        self.write_engine = write_engine
        # If no read engine is provided, read operations will use the write engine.
        self.read_engine = read_engine or write_engine
        self.base_cls = base_cls
        logging.info("DBHandle created. Write Engine: %s, Read Engine: %s", write_engine.url, self.read_engine.url)


def create_database(write_url: str, read_url: str = None, **engine_kwargs) -> DBHandle:
    """
    Creates database engines and returns a handle.

    This function uses SQLAlchemy's automap feature to reflect the database schema.
    To connect to MySQL, you might need to install a driver like PyMySQL:
    'pip install pymysql'
    And format your URL like: 'mysql+pymysql://user:pass@host/db'

    Args:
        write_url (str): The connection string for the primary (write) database.
        read_url (str, optional): The connection string for the read replica. Defaults to None.
        **engine_kwargs: Additional arguments for the SQLAlchemy create_engine function,
                         e.g., pool_recycle=3600.

    Returns:
        DBHandle: A handle containing the database engines and mapped base.
    """
    # Default pool_recycle to 1800 seconds (30 minutes) if not specified
    engine_kwargs.setdefault('pool_recycle', 1800)

    # The write engine is the source of truth for schema reflection
    write_engine = create_engine(write_url, **engine_kwargs)
    
    read_engine = None
    if read_url:
        read_engine = create_engine(read_url, **engine_kwargs)

    # Reflect the database schema from the write engine
    Base = automap_base()
    Base.prepare(autoload_with=write_engine, reflect=True)

    return DBHandle(write_engine, Base, read_engine)


class DatabaseManager:
    """
    Provides a high-level API for interacting with the database.
    Manages sessions and executes SQL operations.
    """
    def __init__(self, db_handle: DBHandle):
        self._db_handle = db_handle
        self._write_engine = db_handle.write_engine
        self._read_engine = db_handle.read_engine
        self._base = db_handle.base_cls

    def list_all_table_names(self) -> list:
        """Returns a list of all table names discovered in the database schema."""
        return list(self._Base.classes.keys())

    def get_table_class(self, table_name: str):
        """
        Returns the mapped class for a given table name.

        Args:
            table_name (str): The name of the table.

        Returns:
            The SQLAlchemy mapped class, or None if not found.
        """
        return self._base.classes.get(table_name)

    @contextmanager
    def session_scope(self, role: str = DBRole.WRITE) -> Session:
        """
        Provides a transactional scope around a series of operations.
        This context manager handles session creation, commit, rollback, and closing.

        Args:
            role (str): The database role, either DBRole.WRITE or DBRole.READ.

        Yields:
            Session: The SQLAlchemy session object.
        """
        if role == DBRole.WRITE:
            engine = self._write_engine
        elif role == DBRole.READ:
            engine = self._read_engine
        else:
            raise ValueError(f"Unknown database role: {role}")

        session = sessionmaker(bind=engine, autoflush=False)()
        logging.info("Session created for role: %s", role)
        
        try:
            yield session
            session.commit()
        except Exception as e:
            logging.error("Session rollback due to an exception: %s", e)
            session.rollback()
            raise
        finally:
            session.close()
            logging.info("Session closed for role: %s", role)

    def execute_sql_from_file(self, file_path: str):
        """
        Executes all SQL statements from a given .sql file.
        
        Note: This is for schema changes or bulk operations and runs outside a session transaction.
        """
        if not file_path.endswith('.sql'):
            raise ValueError("File must be a .sql file.")
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"SQL file not found at: {file_path}")

        with open(file_path, "r") as file:
            sql_script = file.read()
            try:
                # Use the write engine for executing schema changes or data loads
                with self._write_engine.connect() as connection:
                    connection.execute(text(sql_script))
                    # For engines that don't support autocommit on DDL
                    if connection.dialect.supports_alter:
                        connection.commit()
                logging.info("Successfully executed SQL from %s", file_path)
            except Exception as e:
                logging.error("Error executing %s: %s", file_path, e)
                raise
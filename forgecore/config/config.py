"""Configuration and database connector for ForgeCore."""

import os
import mysql.connector
from mysql.connector import pooling


def get_connection_pool():
    """Create and return a connection pool using environment variables."""
    db_config = {
        "host": os.getenv("FORGECORE_DB_HOST", "localhost"),
        "user": os.getenv("FORGECORE_DB_USER", "forgeuser"),
        "password": os.getenv("FORGECORE_DB_PASSWORD", "forgepass"),
        "database": os.getenv("FORGECORE_DB_NAME", "forgecore"),
    }
    return pooling.MySQLConnectionPool(pool_name="forgecore_pool", pool_size=5, **db_config)


# Global connection pool
POOL = get_connection_pool()

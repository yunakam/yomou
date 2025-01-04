import sqlite3
import os
from db.__init__ import db_path

def table_exists(conn, table_name):
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
    return cursor.fetchone() is not None

def create_database():
    if not os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            """
            CREATE TABLE book (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                total_pages INTEGER NOT NULL,
                read_pages INTEGER,
                registered_date DATE NOT NULL,
                target_date DATE NOT NULL,
                finished BOOLEAN
            )
            """
        )
        
        conn.commit()
        conn.close()
        
    else:
        conn = sqlite3.connect(db_path)
        if not table_exists(conn, "book"):
            cursor = conn.cursor()
            
            cursor.execute(
                """
                CREATE TABLE book (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    total_pages INTEGER NOT NULL,
                    read_pages INTEGER,
                    registered_date DATE NOT NULL,
                    target_date DATE NOT NULL,
                    finished BOOLEAN
                )
                """          
            )
            
            conn.commit()
        conn.close()

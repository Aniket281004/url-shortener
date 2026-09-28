import sqlite3
from typing import Optional
from app.database import get_db_connection
from app.utils import generate_short_code

def create_short_url(original_url:str)->str:
    conn = get_db_connection()
    cursor = conn.cursor()
    short_code = generate_short_code()

    try:
        cursor.execute(
            "Insert into urls (original_url,short_code) values(?,?)",
            (original_url,short_code)
        )
        conn.commit()
    except sqlite3.IntegertyError:
        short_code = generate_short_code()
        cursor.execute(
                    "Insert into urls (original_url,short_code) values(?,?)",
                    (original_url,short_code)
                )
        conn.commit()
    finally:conn.close()
    return short_code

def get_and_increment_url(short_code:str) -> Optional[str]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("Select original_url,clicks from urls where short_code = ?",(short_code,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None
    original_url = row["original_url"]
    new_clicks = row["clicks"]+1
    cursor.execute("Update urls set clicks = ? where short_code = ?",(new_clicks,short_code))
    conn.commit()
    conn.close()
    return original_url
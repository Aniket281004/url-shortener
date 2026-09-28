import sqlite3
DB = "urls.db"

def get_db_connection():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        Create table if not exists urls(
        id integer primary key autoincrement,
        original_url text not null,
        short_code text unique not null,
        clicks integer default 0,
        created_at timestamp default current_timestamp
        )
    """)
    conn.commit()
    conn.close()
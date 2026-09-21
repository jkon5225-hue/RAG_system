import sqlite3

DB = "question_log.db"

def create_db():

    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS question_log (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        datetime TEXT NOT NULL,

        username TEXT NOT NULL,

        genre TEXT,

        question TEXT NOT NULL,

        elapsed REAL
    )
    """)

    conn.commit()
    conn.close()

    print("question_log.db を作成しました")


if __name__ == "__main__":
    create_db()
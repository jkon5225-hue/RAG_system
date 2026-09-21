import sqlite3
import bcrypt
from datetime import datetime

DB_FILE = "users.db"

# =========================================
# DB接続
# =========================================

conn = sqlite3.connect(DB_FILE)
cur = conn.cursor()

# =========================================
# テーブル存在確認
# =========================================


def table_exists(name):

    cur.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type='table'
        AND name=?
    """,
        (name,),
    )

    return cur.fetchone() is not None


# =========================================
# カラム存在確認
# =========================================
def column_exists(table, column):

    cur.execute(f"PRAGMA table_info('{table}')")

    return any(row[1] == column for row in cur.fetchall())


# =========================================
# users
# =========================================

cur.execute("""

CREATE TABLE IF NOT EXISTS users(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    username TEXT UNIQUE NOT NULL,

    password_hash TEXT NOT NULL,

    role TEXT NOT NULL DEFAULT 'user',

    enabled INTEGER DEFAULT 1,

    failed_count INTEGER DEFAULT 0,

    lock_until TEXT,

    last_login TEXT,

    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP

)

""")

# =========================================
# login_history
# =========================================

cur.execute("""

CREATE TABLE IF NOT EXISTS login_history(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    username TEXT,

    login_time TEXT NOT NULL,

    success INTEGER NOT NULL,

    ip TEXT,

    user_agent TEXT,

    reason TEXT

)

""")
# =========================================
# usersテーブル更新（マイグレーション用）
# =========================================
columns = {
    "role": "ALTER TABLE users ADD COLUMN role TEXT NOT NULL DEFAULT 'user'",
    "enabled": "ALTER TABLE users ADD COLUMN enabled INTEGER DEFAULT 1",
    "failed_count": "ALTER TABLE users ADD COLUMN failed_count INTEGER DEFAULT 0",
    "lock_until": "ALTER TABLE users ADD COLUMN lock_until TEXT",
    "last_login": "ALTER TABLE users ADD COLUMN last_login TEXT",
    "created_at": "ALTER TABLE users ADD COLUMN created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP",
}

for col, sql in columns.items():

    if not column_exists("users", col):

        print(f"[ADD COLUMN] users.{col}")

        cur.execute(sql)

# =========================================
# login_history更新
# =========================================

history_columns = {
    "user_agent": "ALTER TABLE login_history ADD COLUMN user_agent TEXT",
    "reason": "ALTER TABLE login_history ADD COLUMN reason TEXT",
    "ip": "ALTER TABLE login_history ADD COLUMN ip TEXT",
}

for col, sql in history_columns.items():

    if not column_exists("login_history", col):

        print(f"[ADD COLUMN] login_history.{col}")

        cur.execute(sql)

# =========================================
# INDEX
# =========================================

cur.execute("""

CREATE INDEX IF NOT EXISTS idx_users_username

ON users(username)

""")

cur.execute("""

CREATE INDEX IF NOT EXISTS idx_users_role

ON users(role)

""")

cur.execute("""

CREATE INDEX IF NOT EXISTS idx_users_enabled

ON users(enabled)

""")

cur.execute("""

CREATE INDEX IF NOT EXISTS idx_login_username

ON login_history(username)

""")

cur.execute("""

CREATE INDEX IF NOT EXISTS idx_login_time

ON login_history(login_time)

""")
# =========================================
# adminユーザー作成
# =========================================

cur.execute(
    """
    SELECT COUNT(*)
    FROM users
    WHERE username='admin'
    """
)

exist = cur.fetchone()[0]

if exist == 0:

    password = "admin123"

    password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cur.execute(
        """
        INSERT INTO users(
            username,
            password_hash,
            role,
            enabled,
            failed_count,
            lock_until,
            last_login,
            created_at
        )
        VALUES(?,?,?,?,?,?,?,?)
        """,
        ("admin", password_hash, "admin", 1, 0, None, None, now),
    )

    print()
    print("================================")
    print("初期管理者を作成しました")
    print(" ID : admin")
    print(" PW : admin123")
    print("================================")

else:

    print("adminユーザーは既に存在します。")

# =========================================
# 保存
# =========================================

conn.commit()

# =========================================
# FreeAccessユーザー作成
# =========================================

cur.execute(
    """
    SELECT COUNT(*)
    FROM users
    WHERE username='user1'
    """
)

exist = cur.fetchone()[0]

if exist == 0:

    password = "user123"

    password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cur.execute(
        """
        INSERT INTO users(
            username,
            password_hash,
            role,
            enabled,
            failed_count,
            lock_until,
            last_login,
            created_at
        )
        VALUES(?,?,?,?,?,?,?,?)
        """,
        ("jyu1", password_hash, "user", 1, 0, None, None, now),
    )

    print()
    print("================================")
    print("FreeAccessを作成しました")


else:

    print("FreeAccessユーザーは既に存在します。")

# =========================================
# 保存
# =========================================

conn.commit()


# =========================================
# DB情報
# =========================================

cur.execute("SELECT COUNT(*) FROM users")
user_count = cur.fetchone()[0]

cur.execute(
    """
    SELECT COUNT(*)
    FROM users
    WHERE role='admin'
    """
)
admin_count = cur.fetchone()[0]

cur.execute(
    """
    SELECT COUNT(*)
    FROM users
    WHERE enabled=1
    """
)
enabled_count = cur.fetchone()[0]

cur.execute(
    """
    SELECT COUNT(*)
    FROM login_history
    """
)
history_count = cur.fetchone()[0]

print()
print("========== Database ==========")
print(f"Users        : {user_count}")
print(f"Admins       : {admin_count}")
print(f"Enabled      : {enabled_count}")
print(f"LoginHistory : {history_count}")

# =========================================
# テーブル一覧
# =========================================

print()
print("Tables")

cur.execute("""
SELECT name
FROM sqlite_master
WHERE type='table'
ORDER BY name
""")

for row in cur.fetchall():

    print(" -", row[0])

# =========================================
# 終了
# =========================================

conn.close()

print()
print("users.db 初期化完了")
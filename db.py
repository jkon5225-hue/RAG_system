import sqlite3
from datetime import datetime, timedelta
import bcrypt

#=========================================
# DB接続
#=========================================
def get_conn():
    conn = sqlite3.connect("users.db")
    conn.row_factory = sqlite3.Row
    return conn

def get_question_conn():
    conn = sqlite3.connect("question_log.db")
    conn.row_factory = sqlite3.Row
    return conn

#=========================================
# SELECT
#=========================================
def fetch_all(sql, params=()):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(sql, params)
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def fetch_one(sql, params=()):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(sql, params)
    row = cur.fetchone()
    conn.close()
    if row:

        return dict(row)

    return None

#=========================================
# UPDATE
#=========================================
def execute(sql, params=()):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(sql, params)
    conn.commit()
    conn.close()

#=========================================
# bcrypt
#=========================================
def hash_password(password):

    return bcrypt.hashpw(

        password.encode(),

        bcrypt.gensalt()

    ).decode()


def verify_password(

        password,

        password_hash

):

    return bcrypt.checkpw(

        password.encode(),

        password_hash.encode()

    )


#=========================================
# User取得
#=========================================

def get_user(username):

    sql = """

    SELECT *

    FROM users

    WHERE username=?

    """

    return fetch_one(

        sql,

        (username,)

    )


def list_users():

    sql = """

    SELECT *

    FROM users

    ORDER BY username

    """

    return fetch_all(sql)


def search_users(keyword):

    sql = """

    SELECT *

    FROM users

    WHERE username LIKE ?

    ORDER BY username

    """

    return fetch_all(

        sql,

        ("%"+keyword+"%",)

    )
#=========================================
# ユーザー追加
#=========================================

def add_user(username, password, role="user"):

    if get_user(username):
        return False

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    sql = """
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
    """

    execute(
        sql,
        (
            username,
            hash_password(password),
            role,
            1,
            0,
            None,
            None,      # last_login
            now
        )
    )

    return True


#=========================================
# ユーザー削除
#=========================================

def delete_user(username):

    execute(
        "DELETE FROM users WHERE username=?",
        (username,)
    )


#=========================================
# 件数
#=========================================

def count_users():

    row = fetch_one(
        "SELECT COUNT(*) AS cnt FROM users"
    )

    return row["cnt"]


def count_admins():

    row = fetch_one(
        """
        SELECT COUNT(*) AS cnt
        FROM users
        WHERE role='admin'
        """
    )

    return row["cnt"]


#=========================================
# 権限変更
#=========================================

def change_role(username, role):

    execute(
        """
        UPDATE users
        SET role=?
        WHERE username=?
        """,
        (
            role,
            username
        )
    )


#=========================================
# 有効／無効
#=========================================

def change_enabled(
    username,
    enabled
):

    execute(
        """
        UPDATE users
        SET enabled=?
        WHERE username=?
        """,
        (
            enabled,
            username
        )
    )


#=========================================
# パスワード変更
#=========================================

def change_password_by_admin(
    username,
    password
):
    """
    管理者によるパスワードの強制変更。
    ユースケース「パスワードを忘れてロックされたユーザーの初期化」を想定し、
    パスワードの変更と同時に、失敗カウント(failed_count)の初期化およびロック(lock_until)の解除を自動で行います。
    """
    execute(
        """
        UPDATE users
        SET password_hash=?,
            failed_count=0,
            lock_until=NULL
        WHERE username=?
        """,
        (
            hash_password(password),
            username
        )
    )

#=========================================
# 最終ログイン
#=========================================

def update_last_login(username):

    execute(
        """
        UPDATE users
        SET last_login=?
        WHERE username=?
        """,
        (
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            username
        )
    )


#=========================================
# ログイン履歴
#=========================================

def add_login_history(
    username,
    success,
    ip=""
):

    execute(
        """
        INSERT INTO login_history(
            username,
            login_time,
            success,
            ip
        )
        VALUES(?,?,?,?)
        """,
        (
            username,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            1 if success else 0,
            ip
        )
    )


def get_login_history(limit=100):

    return fetch_all(
        """
        SELECT *
        FROM login_history
        ORDER BY login_time DESC
        LIMIT ?
        """,
        (limit,)
    )


#=========================================
# ログイン失敗回数
#=========================================

def increment_failed_count(username):

    execute(
        """
        UPDATE users
        SET failed_count=failed_count+1
        WHERE username=?
        """,
        (username,)
    )


def reset_failed_count(username):

    execute(
        """
        UPDATE users
        SET failed_count=0,
            lock_until=NULL
        WHERE username=?
        """,
        (username,)
    )


#=========================================
# ロック
#=========================================

def lock_user(
    username,
    minutes=10
):

    lock_until = (
        datetime.now() +
        timedelta(minutes=minutes)
    ).strftime("%Y-%m-%d %H:%M:%S")

    execute(
        """
        UPDATE users
        SET lock_until=?
        WHERE username=?
        """,
        (
            lock_until,
            username
        )
    )


def unlock_user(username):

    execute(
        """
        UPDATE users
        SET failed_count=0,
            lock_until=NULL
        WHERE username=?
        """,
        (username,)
    )

def get_locked_users():

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return fetch_all(
        """
        SELECT *
        FROM users
        WHERE lock_until IS NOT NULL
          AND lock_until > ?
        ORDER BY username
        """,
        (now,)
    )
#=========================================
# ロック判定
#=========================================

def is_locked(username):

    user = get_user(username)

    if user is None:
        return False

    if not user["lock_until"]:
        return False

    lock_until = datetime.strptime(
        user["lock_until"],
        "%Y-%m-%d %H:%M:%S"
    )

    return datetime.now() < lock_until


#=========================================
# ログイン認証
#=========================================

def authenticate(
    username,
    password,
    ip=""
):

    user = get_user(username)

    if user is None:

        add_login_history(
            username,
            False,
            ip
        )

        return False, "ユーザーが存在しません。"

    if user["enabled"] == 0:

        add_login_history(
            username,
            False,
            ip
        )

        return False, "無効なユーザーです。"

    if is_locked(username):

        return False, "アカウントがロックされています。"

    if verify_password(
        password,
        user["password_hash"]
    ):

        reset_failed_count(username)

        update_last_login(username)

        add_login_history(
            username,
            True,
            ip
        )

        return True, user

    increment_failed_count(username)

    user = get_user(username)

    if user["failed_count"] >= 5:

        lock_user(username)

        add_login_history(
            username,
            False,
            ip
        )

        return False, "5回失敗したため10分ロックしました。"

    add_login_history(
        username,
        False,
        ip
    )

    remain = 5 - user["failed_count"]

    return False, f"パスワードが違います。（残り{remain}回）"


#=========================================
# パスワード変更（本人）
#=========================================

def change_password(
    username,
    old_password,
    new_password
):

    user = get_user(username)

    if user is None:
        return False

    if not verify_password(
        old_password,
        user["password_hash"]
    ):
        return False

    execute(
        """
        UPDATE users
        SET password_hash=?
        WHERE username=?
        """,
        (
            hash_password(new_password),
            username
        )
    )

    return True
#=========================================
# 有効ユーザー取得
#=========================================

def get_enabled_users():

    return fetch_all(
        """
        SELECT *
        FROM users
        WHERE enabled=1
        ORDER BY username
        """
    )


#=========================================
# 無効ユーザー取得
#=========================================

def get_disabled_users():

    return fetch_all(
        """
        SELECT *
        FROM users
        WHERE enabled=0
        ORDER BY username
        """
    )


#=========================================
# ユーザー存在確認
#=========================================

def user_exists(username):

    return get_user(username) is not None


#=========================================
# 初期管理者作成
#=========================================

def create_admin(

    username="admin",

    password="admin"

):

    if user_exists(username):
        return

    add_user(
        username,
        password,
        "admin"
    )


#=========================================
# 安全削除
#=========================================

def delete_user_safe(username):

    user = get_user(username)

    if user is None:
        return False

    if user["role"] == "admin":

        if count_admins() <= 1:

            return False

    delete_user(username)

    return True


#=========================================
# 有効化
#=========================================

def enable_user(username):

    change_enabled(
        username,
        1
    )


#=========================================
# 無効化
#=========================================

def disable_user(username):

    change_enabled(
        username,
        0
    )


#=========================================
# 権限一覧
#=========================================

def get_roles():

    return [
        "admin",
        "user"
    ]

#=========================================
# ログイン履歴削除
#=========================================

def delete_login_history():

    execute(
        """
        DELETE FROM login_history
        """
    )


#=========================================
# 動作確認
#=========================================

if __name__ == "__main__":

    print("=" * 40)

    print("users.db Check")

    print("=" * 40)

    print(
        "Users :",
        count_users()
    )

    print(
        "Admins:",
        count_admins()
    )

    print(
        "Locked:",
        len(get_locked_users())
    )

    print(
        "Enabled:",
        len(get_enabled_users())
    )

    print(
        "Disabled:",
        len(get_disabled_users())
    )

    print("=" * 40)

    print("OK")
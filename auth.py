import streamlit as st

from db import authenticate


#=========================================
# Session初期化
#=========================================

def init_session():

    defaults = {

        "logged_in": False,

        "username": None,

        "role": None

    }

    for k, v in defaults.items():

        if k not in st.session_state:

            st.session_state[k] = v


#=========================================
# ログイン
#=========================================

def login(

    username,

    password,

    ip=""

):

    ok, result = authenticate(

        username,

        password,

        ip

    )

    if ok:

        st.session_state.logged_in = True

        st.session_state.username = result["username"]

        st.session_state.role = result["role"]

        return True, ""

    return False, result


#=========================================
# ログアウト
#=========================================

def logout():

    keep = {}

    for key in [

        "theme",

        "language"

    ]:

        if key in st.session_state:

            keep[key] = st.session_state[key]

    st.session_state.clear()

    init_session()

    for k, v in keep.items():

        st.session_state[k] = v


#=========================================
# ログイン確認
#=========================================

def is_logged_in():

    return bool(

        st.session_state.get(

            "logged_in",

            False

        )

    )

#=========================================
# ユーザー情報取得
#=========================================

def get_username():

    return st.session_state.get(
        "username"
    )


def get_role():

    return st.session_state.get(
        "role"
    )


def is_admin():

    return get_role() == "admin"

def is_user():

    return get_role() == "user"

#=========================================
# ログイン必須
#=========================================

def require_login():

    if not is_logged_in():

        st.warning(
            "ログインしてください。"
        )

        st.switch_page("login.py")

        st.stop()


#=========================================
# 管理者必須
#=========================================

def require_admin():

    require_login()

    if not is_admin():

        st.error(
            "管理者のみ利用できます。"
        )

        st.stop()


#=========================================
# 一般ユーザー以上
#=========================================

def require_user():

    require_login()


#=========================================
# セッション更新
#=========================================

def refresh_session(user):

    st.session_state.logged_in = True

    st.session_state.username = user["username"]

    st.session_state.role = user["role"]


#=========================================
# セッション情報
#=========================================

def get_session_info():

    return {

        "logged_in":
            is_logged_in(),

        "username":
            get_username(),

        "role":
            get_role()

    }


#=========================================
# ログインユーザー表示
#=========================================

def login_user_text():

    if not is_logged_in():

        return "Guest"

    return (

        f"{get_username()} "

        f"({get_role()})"

    )
#=========================================
# Sidebar
#=========================================

def sidebar_user():

    require_login()

    with st.sidebar:

        st.title("🔐 User Menu")

        if get_username() != "jyu1":
            st.write(
                f"**ユーザー：** {get_username()}"
            )

        st.write(
            f"**権限：** {get_role()}"
        )

        st.divider()

        if is_admin():

            st.page_link(
                "pages/kanrisya.py",
                label="🏠 ホーム"
            )

            st.page_link(
                "pages/user_manager.py",
                label="👥 ユーザー管理"
            )

        if is_user() ==False:
            st.page_link(
                "pages/change_password.py",
                label="🔑 パスワード変更"
            )

            st.divider()

        if st.button(
            "🚪 ログアウト",
            width='stretch'
        ):

            logout()

            st.switch_page(
                "login.py"
            )

            st.stop()

        st.divider()

#=========================================
# Header
#=========================================

def page_header(title):

    st.title(title)

    st.caption(
        f"ログイン中：{get_username()} "
        f"({get_role()})"
    )


#=========================================
# Footer
#=========================================

def page_footer():

    st.divider()

    st.caption(
        "RAG System "
        "Version 2.0"
    )

#=========================================
# ページ共通
#=========================================
def setup_page(

    title,

    admin=False

):

    init_session()

    if admin:

        require_admin()

    else:

        require_login()

    sidebar_user()

    page_header(title)

from datetime import datetime, timedelta
from functools import wraps

#=========================================
# セッションタイムアウト
#=========================================
SESSION_TIMEOUT = 30   # 分

def update_activity():

    st.session_state["last_activity"] = datetime.now()


def check_session_timeout():

    if not is_logged_in():
        return

    last = st.session_state.get(
        "last_activity"
    )

    if last is None:

        update_activity()

        return

    if datetime.now() - last > timedelta(
        minutes=SESSION_TIMEOUT
    ):

        logout()

        st.warning(
            "セッションがタイムアウトしました。"
        )

        st.switch_page("login.py")

        st.stop()

    update_activity()


#=========================================
# 現在ログインユーザー
#=========================================
def current_user():

    return st.session_state.get(
        "username"
    )


def current_role():

    return st.session_state.get(
        "role"
    )


#=========================================
# デコレータ
#=========================================
def login_required(func):

    @wraps(func)

    def wrapper(*args, **kwargs):

        require_login()

        check_session_timeout()

        return func(
            *args,
            **kwargs
        )

    return wrapper


def admin_required(func):

    @wraps(func)

    def wrapper(*args, **kwargs):

        require_admin()

        check_session_timeout()

        return func(
            *args,
            **kwargs
        )

    return wrapper

#=========================================
# 共通初期化
#=========================================
def initialize(

    title,

    admin=False

):

    init_session()

    check_session_timeout()

    setup_page(

        title,

        admin

    )


#=========================================
# バージョン
#=========================================

AUTH_VERSION = "2.0"


def auth_version():

    return AUTH_VERSION

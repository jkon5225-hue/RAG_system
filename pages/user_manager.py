import math
import pandas as pd
import streamlit as st
import io

from auth import require_admin, sidebar_user
from db import (
    list_users,
    search_users,
    count_users,
    get_locked_users,
    add_user,
    delete_user,
)
from db import (
    change_password_by_admin,
    change_role,
    change_enabled,
    unlock_user
)
from db import (
    get_login_history,
    count_admins,
    delete_login_history
)

# -----------------------------
# 初期設定
# -----------------------------
st.set_page_config(
    page_title="ユーザー管理",
    page_icon="👥",
    layout="wide"
)

require_admin()
sidebar_user()

st.title("👥 ユーザー管理")

# -----------------------------
# Session
# -----------------------------
if "user_keyword" not in st.session_state:
    st.session_state.user_keyword = ""

if "user_page" not in st.session_state:
    st.session_state.user_page = 1

PAGE_SIZE = 15

# -----------------------------
# 検索
# -----------------------------
col1, col2 = st.columns([5,1])

with col1:
    keyword = st.text_input(
        "ユーザー検索",
        value=st.session_state.user_keyword,
        placeholder="ユーザー名を入力"
    )

with col2:
    st.write("")
    if st.button("検索", width='stretch'):
        st.session_state.user_keyword = keyword.strip()
        st.session_state.user_page = 1
        st.rerun()

# -----------------------------
# データ取得
# -----------------------------
if st.session_state.user_keyword:
    users = search_users(st.session_state.user_keyword)
else:
    users = list_users()

# -----------------------------
# 統計
# -----------------------------
c1,c2,c3,c4 = st.columns(4)

c1.metric("総ユーザー", count_users())
c2.metric(
    "有効",
    sum(u["enabled"] for u in users)
)
c3.metric(
    "無効",
    sum(not u["enabled"] for u in users)
)
c4.metric(
    "ロック中",
    len(get_locked_users())
)

st.divider()

# -----------------------------
# ページング
# -----------------------------
page_count = max(
    1,
    math.ceil(len(users) / PAGE_SIZE)
)

c1,c2,c3 = st.columns([2,2,6])

with c1:
    if st.button(
        "◀ 前",
        disabled=st.session_state.user_page <= 1
    ):
        st.session_state.user_page -= 1
        st.rerun()

with c2:
    if st.button(
        "次 ▶",
        disabled=st.session_state.user_page >= page_count
    ):
        st.session_state.user_page += 1
        st.rerun()

st.caption(
    f"Page {st.session_state.user_page} / {page_count}"
)

start = (st.session_state.user_page-1) * PAGE_SIZE
end = start + PAGE_SIZE
page_users = users[start:end]
# -----------------------------
# DataFrame作成
# -----------------------------
rows = []
for u in page_users:
    rows.append({
        "ID": u["id"],
        "ユーザー": u["username"],
        "権限": u["role"],
        "状態": "有効" if u["enabled"] else "無効",
        "失敗": u["failed_count"],
        "ロック": "○" if u["lock_until"] else "",
        "最終ログイン": u["last_login"] or ""
    })

df = pd.DataFrame(rows)

st.subheader("ユーザー一覧")

if df.empty:
    st.info("ユーザーが存在しません。")
    st.stop()

st.dataframe(
    df,
    width='stretch',
    hide_index=True
)

st.divider()

# -----------------------------
# ユーザー選択
# -----------------------------
# 全ユーザーから選択肢を作成
usernames = [u["username"] for u in users]

selected_name = st.selectbox(
    "対象ユーザー",
    usernames,
    index=None,
    key="selected_username",
    placeholder="ユーザーを選択してください"
)

selected_user = None

if selected_name:
    # 全ユーザーから検索
    selected_user = next(
        (
            u for u in users
            if u["username"] == selected_name
        ),
        None
    )

# -----------------------------
# 詳細表示
# -----------------------------
st.subheader("ユーザー情報")

if selected_user is None:
    st.info("ユーザーを選択してください。")
else:

    c1, c2 = st.columns(2)

    with c1:
        st.text_input(
            "ID",
            selected_user["id"],
            disabled=True
        )

        st.text_input(
            "ユーザー",
            selected_user["username"],
            disabled=True
        )

        st.text_input(
            "権限",
            selected_user["role"],
            disabled=True
        )

        st.text_input(
            "状態",
            "有効" if selected_user["enabled"] else "無効",
            disabled=True
        )

    with c2:
        st.text_input(
            "失敗回数",
            str(selected_user["failed_count"]),
            disabled=True
        )

        st.text_input(
            "最終ログイン",
            selected_user["last_login"] or "",
            disabled=True
        )

        st.text_input(
            "作成日",
            selected_user["created_at"],
            disabled=True
        )

st.divider()
# -----------------------------
# 操作ボタン
# -----------------------------
st.subheader("操作")

c1, c2, c3, c4, c5, c6,c7 = st.columns(7)

if c1.button("➕追加", width='stretch'):
    st.session_state.show_add_dialog = True

if c2.button(
    "🗑削除",
    width='stretch',
    disabled=selected_user is None
):
    st.session_state.show_delete_dialog = True

if c7.button(
    "📥一括登録",
    width="stretch"
):
    st.session_state.show_import_dialog = True

# -----------------------------
# ユーザー追加
# -----------------------------
@st.dialog("ユーザー追加")
def add_user_dialog():

    username = st.text_input("ユーザー名")

    password = st.text_input(
        "初期パスワード",
        type="password"
    )

    role = st.selectbox(
        "権限",
        ["user", "admin"]
    )

    col1, col2 = st.columns(2)

    with col1:

        if st.button(
            "登録",
            width='stretch'
        ):

            if username.strip() == "":
                st.error("ユーザー名を入力してください。")
                return

            if password == "":
                st.error("パスワードを入力してください。")
                return

            ok = add_user(
                username.strip(),
                password,
                role
            )

            if ok:

                st.success("ユーザーを追加しました。")

                del st.session_state.show_add_dialog

                st.rerun()

            else:

                st.error("同名ユーザーが存在します。")

    with col2:

        if st.button(
            "キャンセル",
             width='stretch'
        ):

            del st.session_state.show_add_dialog

            st.rerun()

if st.session_state.get(
    "show_add_dialog",
    False
):
    add_user_dialog()

# -----------------------------
# ユーザー削除
# -----------------------------
@st.dialog("ユーザー削除")
def delete_user_dialog():

    st.warning(
        f"【{selected_user['username']}】を削除します。"
    )

    if selected_user["username"] == "admin":

        st.error(
            "adminユーザーは削除できません。"
        )

        if st.button("閉じる"):
            del st.session_state.show_delete_dialog
            st.rerun()

        return

    col1, col2 = st.columns(2)

    with col1:

        if st.button(
            "削除",
            type="primary",
            width='stretch'
        ):

            delete_user(
                selected_user["username"]
            )

            st.success("削除しました。")

            del st.session_state.show_delete_dialog

            st.rerun()

    with col2:

        if st.button(
            "キャンセル",
            width='stretch'
        ):

            del st.session_state.show_delete_dialog

            st.rerun()

if st.session_state.get(
    "show_delete_dialog",
    False
):
    delete_user_dialog()
# -----------------------------
# 残りの操作ボタン
# -----------------------------
if c3.button(
    "🔑PW変更",
    width='stretch',
    disabled=selected_user is None
):
    st.session_state.show_pw_dialog = True

if c4.button(
    "🛡権限変更",
    width='stretch',
    disabled=selected_user is None
):
    st.session_state.show_role_dialog = True

if c5.button(
    "🚫有効/無効",
    width='stretch',
    disabled=selected_user is None
):
    st.session_state.show_enable_dialog = True

if c6.button(
    "🔓ロック解除",
    width='stretch',
    disabled=selected_user is None
):
    st.session_state.show_unlock_dialog = True

# -----------------------------
# パスワード変更
# -----------------------------
@st.dialog("パスワード変更")
def password_dialog():

    st.write(f"対象 : **{selected_user['username']}**")

    password = st.text_input(
        "新しいパスワード",
        type="password"
    )

    password2 = st.text_input(
        "確認入力",
        type="password"
    )

    c1,c2 = st.columns(2)

    with c1:

        if st.button(
            "変更",
            width='stretch'
        ):

            if password == "":
                st.error("パスワードを入力してください。")
                return

            if password != password2:
                st.error("確認入力が一致しません。")
                return

            change_password_by_admin(
                selected_user["username"],
                password
            )

            st.success("変更しました。")

            del st.session_state.show_pw_dialog

            st.rerun()

    with c2:

        if st.button(
            "キャンセル",
            width='stretch'
        ):

            del st.session_state.show_pw_dialog

            st.rerun()

if st.session_state.get(
    "show_pw_dialog",
    False
):
    password_dialog()

# -----------------------------
# 権限変更
# -----------------------------
@st.dialog("権限変更")
def role_dialog():
    roles = ["user", "admin"]

    role = st.selectbox(
        "権限",
        roles,
        index=roles.index(selected_user["role"])
    )

    c1,c2 = st.columns(2)

    with c1:

        if st.button(
            "変更",
            width='stretch'
        ):

            change_role(
                selected_user["username"],
                role
            )

            st.success("変更しました。")

            del st.session_state.show_role_dialog

            st.rerun()

    with c2:

        if st.button(
            "キャンセル",
            width='stretch'
        ):

            del st.session_state.show_role_dialog

            st.rerun()

if st.session_state.get(
    "show_role_dialog",
    False
):
    role_dialog()

# -----------------------------
# 有効／無効
# -----------------------------
@st.dialog("有効／無効")

def enable_dialog():

    enable = not bool(selected_user["enabled"])

    text = "有効化" if enable else "無効化"

    st.write(
        f"【{selected_user['username']}】を{text}します。"
    )

    c1,c2 = st.columns(2)

    with c1:

        if st.button(
            text,
            width='stretch'
        ):

            change_enabled(
                selected_user["username"],
                1 if enable else 0
            )

            st.success(f"{text}しました。")

            del st.session_state.show_enable_dialog

            st.rerun()

    with c2:

        if st.button(
            "キャンセル",
            width='stretch'
        ):

            del st.session_state.show_enable_dialog

            st.rerun()

if st.session_state.get(
    "show_enable_dialog",
    False
):
    enable_dialog()

# -----------------------------
# ロック解除
# -----------------------------
@st.dialog("ロック解除")

def unlock_dialog():

    st.write(
        f"【{selected_user['username']}】のロックを解除します。"
    )

    c1,c2 = st.columns(2)

    with c1:

        if st.button(
            "解除",
            width='stretch'
        ):

            unlock_user(
                selected_user["username"]
            )

            st.success("解除しました。")

            del st.session_state.show_unlock_dialog

            st.rerun()

    with c2:

        if st.button(
            "キャンセル",
            width='stretch'
        ):

            del st.session_state.show_unlock_dialog

            st.rerun()

if st.session_state.get(
    "show_unlock_dialog",
    False
):
    unlock_dialog()

# -----------------------------
# 管理者保護
# -----------------------------
if selected_user:

    if selected_user["username"] == st.session_state["username"]:

        st.info("現在ログイン中のユーザーです。")

        if selected_user["role"] != "admin":
            st.error("管理者権限がありません。")

# -----------------------------
# ログイン履歴
# -----------------------------
st.divider()
st.subheader("ログイン履歴")
history = get_login_history(100)

rows = []

for h in history:

    rows.append({
        "日時": h["login_time"],
        "ユーザー": h["username"],
        "結果": "成功" if h["success"] else "失敗",
        "IP": h["ip"]
    })

history_df = pd.DataFrame(rows)

if history_df.empty:

    st.info("履歴はありません。")

else:

    st.dataframe(
        history_df,
        width="stretch",
        hide_index=True
    )

# -----------------------------
# CSVダウンロード
# -----------------------------
csv = history_df.to_csv(
    index=False,
    encoding="utf-8-sig"
)

c1, c2 = st.columns(2)

with c1:

    st.download_button(
        "📥 ログイン履歴CSV",
        csv,
        file_name="login_history.csv",
        mime="text/csv"
    )

with c2:

    if st.button(
        "🗑 ログイン履歴削除",
        width="stretch"
    ):
        st.session_state.show_delete_history_dialog = True

# -----------------------------
# システム情報
# -----------------------------
st.divider()

st.subheader("システム情報")

c1,c2,c3,c4 = st.columns(4)

c1.metric(
    "ユーザー数",
    count_users()
)

c2.metric(
    "管理者数",
    count_admins()
)

c3.metric(
    "ロック中",
    len(get_locked_users())
)

c4.metric(
    "表示件数",
    len(users)
)

st.caption("User Manager Version 1.0")

@st.dialog("Excelからユーザー一括登録")
def import_user_dialog():

    uploaded = st.file_uploader(
        "xlsxファイル",
        type=["xlsx"]
    )

    if uploaded is None:
        return

    try:

        df = pd.read_excel(uploaded)

    except Exception as e:

        st.error(f"読込失敗 : {e}")
        return

    cols = {"user", "password", "role"}

    if not cols.issubset(df.columns):

        st.error(
            "列名は user,password,role が必要です。"
        )
        return
    
    if st.button(
        "登録開始",
        width="stretch"
    ):

        success = 0
        skip = 0
        error = 0

        for _, row in df.iterrows():

            username = str(row["user"]).strip()
            password = str(row["password"]).strip()
            role = str(row["role"]).strip().lower()

            if username == "" or password == "":
                error += 1
                continue

            if role not in [
                "user",
                "admin"
            ]:
                error += 1
                continue

            if add_user(
                username,
                password,
                role
            ):
                success += 1
            else:
                skip += 1

        # ダイアログを閉じる
        del st.session_state.show_import_dialog

        # 結果を親画面へ渡す
        st.session_state.import_result = (
            f"登録 : {success}　"
            f"重複 : {skip}　"
            f"エラー : {error}"
        )

        st.rerun()

if st.session_state.get(
    "show_import_dialog",
    False
):
    import_user_dialog()
# 追加＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊
if "import_result" in st.session_state:
    st.success(st.session_state.import_result)
    del st.session_state.import_result
# 追加＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊

@st.dialog("ログイン履歴削除")
def delete_history_dialog():

    st.warning(
        "ログイン履歴をすべて削除します。"
    )

    st.error(
        "この操作は元に戻せません。"
    )

    c1, c2 = st.columns(2)

    with c1:

        if st.button(
            "削除",
            type="primary",
            width="stretch"
        ):

            delete_login_history()

            st.success("ログイン履歴を削除しました。")

            del st.session_state.show_delete_history_dialog

            st.rerun()

    with c2:

        if st.button(
            "キャンセル",
            width="stretch"
        ):

            del st.session_state.show_delete_history_dialog

            st.rerun()


if st.session_state.get(
    "show_delete_history_dialog",
    False
):
    delete_history_dialog()
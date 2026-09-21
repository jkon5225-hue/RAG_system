import streamlit as st
from auth import initialize
from db import change_password

initialize("🔑 パスワード変更")

with st.form("change_password"):

    old_password = st.text_input(
        "現在のパスワード",
        type="password"
    )

    new_password = st.text_input(
        "新しいパスワード",
        type="password"
    )

    confirm_password = st.text_input(
        "確認入力",
        type="password"
    )

    submit = st.form_submit_button(
        "変更",
        width='stretch'
    )

if submit:

    if old_password == "":

        st.error("現在のパスワードを入力してください。")

        st.stop()

    if new_password == "":

        st.error("新しいパスワードを入力してください。")

        st.stop()

    if new_password != confirm_password:

        st.error("確認入力が一致しません。")

        st.stop()

    if len(new_password) < 8:

        st.error("8文字以上にしてください。")

        st.stop()

    ok = change_password(

        st.session_state["username"],

        old_password,

        new_password

    )

    if ok:
        st.success("パスワードを変更しました。再ログインしてください。")
        import time
        time.sleep(2)  # メッセージを読ませるためのウェイト
        from auth import logout
        logout()
        st.switch_page("login.py")
        st.stop()

    else:

        st.error("現在のパスワードが違います。")
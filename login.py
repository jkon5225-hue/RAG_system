# streamlit run login.py

import os
import streamlit as st
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
# =========================================
# ページ設定
# =========================================
st.set_page_config(
    page_title="ログイン",
    page_icon="🔐",
    layout="centered"
)
with st.spinner("AIモデルを初期化しています..."):
    from sentence_transformers import SentenceTransformer
from auth import (
    init_session,
    login,
    is_logged_in,
    get_role,
    refresh_session
)

from db import add_login_history

# ******************************************************
# スタイル: ティール〜グリーンのグラデーション + 浮かび上がるバブル
# ******************************************************
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Source+Sans+Pro:wght@200;300;600&family=Noto+Sans+JP:wght@300;400;500;700&display=swap');

[data-testid="stSidebar"], [data-testid="collapsedControl"] {
    display: none;
}

* {
    box-sizing: border-box;
}

body, .stApp, .stApp * {
    font-family: 'Source Sans Pro', 'Noto Sans JP', sans-serif;
}

/* ---------- 背景: ティール〜グリーンの斜めグラデーション ---------- */
.stApp {
    background: linear-gradient(to bottom right, #50a3a2 0%, #53e3a6 100%) !important;
    background-attachment: fixed !important;
}

header[data-testid="stHeader"] {
    background: transparent !important;
}

/* Streamlit固有の背景色を透過してバブルが見えるようにする */
[data-testid="stAppViewContainer"],
[data-testid="stMain"],
[data-testid="stHeader"] {
    background: transparent !important;
}

/* ---------- 浮かび上がるバブル ---------- */
.bg-bubbles {
    position: fixed !important;
    top: 0 !important;
    left: 0 !important;
    width: 100vw !important;
    height: 100vh !important;
    z-index: 1 !important; /* コンテンツの下、背景の上に指定 */
    pointer-events: none !important;
    overflow: hidden !important;
    list-style: none !important;
    margin: 0 !important;
    padding: 0 !important;
}

.bg-bubbles li {
    position: absolute;
    display: block;
    list-style: none;
    width: 40px;
    height: 40px;
    background-color: rgba(255, 255, 255, 0.25);
    border: 1px solid rgba(255, 255, 255, 0.35);
    border-radius: 4px;
    bottom: -160px;
    animation-name: square;
    animation-duration: 25s;
    animation-iteration-count: infinite;
    animation-timing-function: linear;
}

.bg-bubbles li:nth-child(1)  { left: 10%; }
.bg-bubbles li:nth-child(2)  { left: 20%; width: 80px;  height: 80px;  animation-delay: 2s;  animation-duration: 17s; }
.bg-bubbles li:nth-child(3)  { left: 25%; animation-delay: 4s; }
.bg-bubbles li:nth-child(4)  { left: 40%; width: 60px;  height: 60px;  animation-duration: 22s; background-color: rgba(255,255,255,0.25); }
.bg-bubbles li:nth-child(5)  { left: 70%; }
.bg-bubbles li:nth-child(6)  { left: 80%; width: 120px; height: 120px; animation-delay: 3s;  background-color: rgba(255,255,255,0.2); }
.bg-bubbles li:nth-child(7)  { left: 32%; width: 160px; height: 160px; animation-delay: 7s; }
.bg-bubbles li:nth-child(8)  { left: 55%; width: 20px;  height: 20px;  animation-delay: 15s; animation-duration: 40s; }
.bg-bubbles li:nth-child(9)  { left: 25%; width: 10px;  height: 10px;  animation-delay: 2s;  animation-duration: 40s; background-color: rgba(255,255,255,0.3); }
.bg-bubbles li:nth-child(10) { left: 90%; width: 160px; height: 160px; animation-delay: 11s; }

@keyframes square {
    0%   { transform: translateY(0) rotate(0deg); }
    100% { transform: translateY(-120vh) rotate(600deg); }
}

/* ---------- コンテンツ（バブルより前面に表示） ---------- */
[data-testid="stMainBlockContainer"],
.main .block-container {
    position: relative !important;
    z-index: 10 !important; /* バブル(z-index: 1)より上に表示 */
    max-width: 600px;
    margin: 5vh auto 0 auto;
    padding: 2rem 1.5rem 2.5rem 1.5rem !important;
    background: transparent !important;
    text-align: center;
}

/* ---------- タイトル ---------- */
h1 {
    font-weight: 200 !important;
    font-size: clamp(2rem, 5vw, 2.6rem) !important;
    color: #ffffff !important;
    text-align: center;
    letter-spacing: 0.02em;
    margin-bottom: 0.6rem !important;
    animation: fadeDown 0.8s ease both;
}

@keyframes fadeDown {
    from { opacity: 0; transform: translateY(-14px); }
    to   { opacity: 1; transform: translateY(0); }
}

.stCaption, [data-testid="stCaptionContainer"],
[data-testid="stCaptionContainer"] p {
    text-align: center;
    color: rgba(255,255,255,0.9) !important;
    font-weight: 300 !important;
}

.main .block-container p,
.main .block-container span,
.main .block-container label,
.main .block-container div,
[data-testid="stWidgetLabel"],
[data-testid="stWidgetLabel"] * {
    color: #ffffff;
}

/* ---------- 区切り線 ---------- */
hr {
    border: none;
    height: 1px;
    background: rgba(255,255,255,0.35);
    margin: 1.5rem 0 !important;
}

/* ---------- 入力欄 ---------- */
.stTextInput {
    max-width: 300px;
    margin: 0 auto 10px auto !important;
    transition: max-width 0.25s ease;
}

.stTextInput:focus-within {
    max-width: 320px;
}

.stTextInput input {
    display: block;
    appearance: none;
    outline: 0;
    border: 1px solid rgba(255,255,255,0.4) !important;
    background-color: rgba(255,255,255,0.2) !important;
    border-radius: 3px !important;
    padding: 10px 15px !important;
    text-align: center;
    font-size: 18px !important;
    color: #000000 !important;
    -webkit-text-fill-color: #000000 !important;
    font-weight: 300 !important;
    transition: background-color 0.25s ease, color 0.25s ease;
}

.stTextInput input::placeholder {
    color: rgba(255,255,255,0.85);
    font-weight: 300;
    opacity: 1;
}

.stTextInput input:hover {
    background-color: rgba(255,255,255,0.4) !important;
}

.stTextInput input:focus {
    background-color: #ffffff !important;
    color: #000000 !important;
    -webkit-text-fill-color: #000000 !important;
}

/* ---------- ボタン共通 ---------- */
.stButton,
.stFormSubmitButton {
    max-width: 300px;
    margin: 0 auto !important;
}

.stButton button,
.stFormSubmitButton button {
    appearance: none;
    outline: 0;
    background-color: #ffffff !important;
    border: 0 !important;
    padding: 10px 15px !important;
    color: #000000 !important;
    border-radius: 3px !important;
    width: 100%;
    cursor: pointer;
    font-size: 18px !important;
    font-weight: 300 !important;
    transition: background-color 0.25s ease, transform 0.15s ease;
    box-shadow: none !important;
}

.stButton button:hover,
.stFormSubmitButton button:hover {
    background-color: rgb(245,247,249) !important;
    transform: translateY(-1px);
}

.stButton button:active,
.stFormSubmitButton button:active {
    transform: translateY(0);
}

/* ---------- アラート ---------- */
[data-testid="stAlert"] {
    border-radius: 6px !important;
    animation: alertPop 0.35s ease;
}

[data-testid="stAlert"] p,
[data-testid="stAlert"] span,
[data-testid="stAlert"] div {
    color: #1F2937 !important;
    -webkit-text-fill-color: #1F2937 !important;
}

@keyframes alertPop {
    from { opacity: 0; transform: scale(0.97); }
    to   { opacity: 1; transform: scale(1); }
}
</style>

<ul class="bg-bubbles" aria-hidden="true">
  <li></li><li></li><li></li><li></li><li></li>
  <li></li><li></li><li></li><li></li><li></li>
</ul>
""",
    unsafe_allow_html=True,)

init_session()

# =========================================
# ログイン済みなら自動遷移
# =========================================

if is_logged_in():

    if get_role() == "admin":
        st.switch_page("./pages/kanrisya.py")
    else:
        st.switch_page("./pages/user.py")

    st.stop()

# =========================================
# タイトル
# =========================================

st.title("RAG system 👨‍🎓")
# =========================================
# User権限で直接ログイン
# =========================================

if st.button(
    "🏠 Free Accessはこちらをクリック",
    width="stretch"
):
    # パスワード認証は行わず、jyu1としてUser権限のセッションを作成
    user_id = "user1"

    refresh_session({
        "username": user_id,
        "role": "user"
    })

    ip = st.context.ip_address or ""

    # ログイン履歴にはIDと成功結果を記録する
    add_login_history(
        user_id,
        True,
        ip
    )

    st.switch_page("./pages/user.py")
    st.stop()

st.divider()

st.caption(
    "登録IDとパスワードを入力してください。"
)

# =========================================
# ログインフォーム
# =========================================

with st.form(
    "login_form",
    clear_on_submit=False
):

    username = st.text_input(
        "登録ID",
        placeholder="登録ID",
        label_visibility="collapsed"
    ).strip()

    password = st.text_input(
        "パスワード",
        type="password",
        placeholder="パスワード",
        label_visibility="collapsed"
    )

    login_button = st.form_submit_button(
        "ログイン",
        width='stretch'
    )

# =========================================
# ログイン処理
# =========================================

if login_button:

    if username == "":

        st.error(
            "ユーザー名を入力してください。"
        )

        st.stop()

    if password == "":

        st.error(
            "パスワードを入力してください。"
        )

        st.stop()

    #***********追加
    ip = st.context.ip_address or ""

    ok, message = login(
        username,
        password,
        ip
    )

    if ok:

        st.success(
            "ログインしました。"
        )

        if get_role() == "admin":

            st.switch_page(
                "./pages/kanrisya.py"
            )

        else:

            st.switch_page(
                "./pages/user.py"
            )

        st.stop()

    st.error(message)


# =========================================
# Footer
# =========================================

st.divider()

st.caption("©️2026 Freelancer JOE. All Rights Reserved.")
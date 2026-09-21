# streamlit run login.py
# データベース丸ごと消去　rmdir /s /q chroma_db
import streamlit as st
from auth import require_login
from auth import sidebar_user
require_login()
sidebar_user()
import os
import re
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
import chromadb
from sentence_transformers import SentenceTransformer
import ollama
from st_copy_to_clipboard import st_copy_to_clipboard
import streamlit.components.v1 as components
import time
from datetime import datetime
from db import get_question_conn
import requests
from urllib.parse import quote

# =====================================================
# Settings
# =====================================================
BASE_DB = "./chroma_db2"
EMBED_MODEL = "intfloat/multilingual-e5-large"
LLM_MODEL = "granite4.1:8b"
BASE_PDF = "./pages/lite3"

GENRE_SETTINGS = {
    "生活関連":{
        "db":"life","pdf":"life",
        "chunk_size":400,"overlap":80,"top_k":5,
        "prompt":"""
        あなたは社内生活便利帳検索AIです。

        提出された文書のみを根拠に日本語で回答してください。

        【回答ルール】
        ・文書に記載されている内容のみを回答する。
        ・推測や一般論を付け加えない。
        ・手続き、申請先、連絡先、対象者、期限、必要書類などは文書の記載どおりに回答する。
        ・複数の文書に情報がある場合は整理してまとめる。
        ・文書に記載がない場合は「資料には記載がありません」と回答する。
        """,
        "file_types":["pdf"]
        },
    "規約":{
        "db":"rules","pdf":"rules",
        "chunk_size":400,"overlap":80,"top_k":4,
        "prompt":"""
        あなたは規約検索AIです。提出された条文のみを根拠に日本語で回答してください。
        
        【回答ルール】
        ・文書に記載されている内容のみを回答する。
        ・推測や一般論を付け加えない。
        ・手続き、申請先、連絡先、対象者、期限、必要書類などは文書の記載どおりに回答する。
        ・複数の文書に情報がある場合は整理してまとめる。
        """,
        "file_types":["pdf"]
        },
}

# =====================================================
# Models
# =====================================================
@st.cache_resource
def load_embedder():
    return SentenceTransformer(EMBED_MODEL)

embedder = load_embedder()

# =====================================================
# Retrieve
# =====================================================
def retrieve(query, exclude_files=None):
    if exclude_files is None:
        exclude_files = []

    q_emb = embedder.encode(
        query,
        normalize_embeddings=True
    )

    results = collection.query(
        query_embeddings=[q_emb.tolist()],
        n_results=setting["top_k"]
    )
    docs = results["documents"][0]
    metas = results["metadatas"][0]
    distances = results["distances"][0]

    # ----------------------------
    # 除外
    # ----------------------------
    if exclude_files:

        new_docs = []
        new_metas = []
        new_distances = []

        for doc, meta, dist in zip(
            docs,
            metas,
            distances
        ):

            # ファイル名部分一致
            if any(
                key.lower() in meta["file"].lower()
                for key in exclude_files
            ):
                continue

            new_docs.append(doc)
            new_metas.append(meta)
            new_distances.append(dist)

        docs = new_docs
        metas = new_metas
        distances = new_distances

    return docs, metas, distances

# =====================================================
# RAG
# =====================================================
def answer_question(question,exclude_files=None):

    docs, metas, distances = retrieve(
        question,
        exclude_files
    )

    context = "\n\n".join(docs)
    context = context[:2000]

    response = ollama.chat(
        model=LLM_MODEL,
        messages=[
            {
                "role":"system",
                "content":SYSTEM_PROMPT
            },
            {
                "role":"user",
                "content":f"""
                以下の文脈のみを使用してください。

                ====================

                {context}

                ====================

                質問
                {question}
                """
            }
        ], 
    )

    answer = response["message"]["content"]

    return answer, metas, docs, distances

FASTAPI = "http://localhost:8000"

def get_pdf_token(filename):

    r = requests.post(
        f"{FASTAPI}/create_token",
        json={
            "filename": filename,
            "user": st.session_state["username"]
        },
        timeout=5
    )

    r.raise_for_status()

    return r.json()["token"]
def show_pdf(pdf_path, page):

    filename3 = os.path.relpath(pdf_path, BASE_PDF)
    filename3 = filename3.replace("\\", "/")

    token = get_pdf_token(filename3)

    pdf_url = (
        f"{FASTAPI}/view/{filename3}"
        f"?token={token}"
    )

    viewer_url = (
        f"{FASTAPI}/pdfjs/web/viewer.html"
        f"?file={quote(pdf_url, safe='')}"
        f"#page={page+1}"
    )

    components.html(
        f"""
        <iframe
            src="{viewer_url}"
            width="100%"
            height="900"
            style="border:none;">
        </iframe>
        """,
        height=900,
    )

def bold(text):
    return f"<b>{text}</b>"

# =====================================================
# UI
# =====================================================
st.set_page_config(
    page_title="Paper RAG",
    layout="wide"
)
# =====================================
# ジャンル選択
# =====================================
genre= st.sidebar.selectbox(
    "ジャンル",
    list(GENRE_SETTINGS.keys())
)
setting = GENRE_SETTINGS[genre]

DB_PATH = os.path.join(
    BASE_DB,
    setting["db"]
)

PDF_DIR = os.path.join(
    BASE_PDF,
    setting["pdf"]
)

SYSTEM_PROMPT = setting["prompt"]

os.makedirs(DB_PATH, exist_ok=True)
os.makedirs(PDF_DIR, exist_ok=True)
# =====================================
# ジャンル毎の保存先
# =====================================

st.title(f"📚 文書RAG（{genre}）")
if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0
# =====================================================
# ChromaDB
# =====================================================
client = chromadb.PersistentClient(
    path=DB_PATH
)

collection = client.get_or_create_collection(
    name="documents"
)
# =====================================================
# question_log.DB
# =====================================================
question_conn = get_question_conn()
question_cur = question_conn.cursor()

# -----------------------------------------------------
# Ask
# -----------------------------------------------------
st.header("質問")
question = st.text_area("質問内容")
exclude_text = st.text_input(
    "🚫 検索対象から除外するファイル名（カンマ区切り）",
    placeholder="例：細胞接着, 古い資料, test.pdf"
)
# =========================
# 回答生成
# =========================
if "running" not in st.session_state:
    st.session_state.running = False

# ボタンが押されたら処理開始フラグを立てるだけ
if st.button("回答生成", disabled=st.session_state.running):

    # 前回のPDF表示を消す
    st.session_state.pop("selected_pdf", None)
    st.session_state.pop("selected_page", None)
    st.session_state.pop("selected_chunk_text", None)

    st.session_state.running = True
    st.rerun()

# =========================
# 回答生成本体
# =========================
if st.session_state.running:

    try:

        if question:
            start_time = time.perf_counter()

            with st.spinner("検索中..."):

                exclude_files = [
                    x.strip()
                    for x in re.split(r"[、,]", exclude_text)
                    if x.strip()
                ]

                answer, source_meta, source_doc, distances = answer_question(
                    question,
                    exclude_files
                )

            elapsed = time.perf_counter() - start_time

            # logDBに記録
            try:
                question_cur.execute(
                    """
                    INSERT INTO question_log
                    (datetime, username, genre, question, elapsed)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        st.session_state["username"],
                        genre,
                        question,
                        elapsed
                    )
                )
                question_conn.commit()

            except Exception as e:
                print(f"question_log登録失敗: {e}")

            st.session_state.answer = answer
            st.session_state.source_meta = source_meta
            st.session_state.source_doc = source_doc
            st.session_state.source_distance = distances

    finally:
        # 必ず解除
        st.session_state.running = False
        st.rerun()

# =========================
# 回答表示
# =========================
if "answer" in st.session_state:

    st.markdown("### 回答")
    st.write(st.session_state.answer)

    st_copy_to_clipboard(
        st.session_state.answer,
        "📋 回答をコピー"
    )

    st.markdown("---")

    # =====================================================
    # 選択されたPDFを最初に表示
    # =====================================================

    if (
        st.session_state.get("selected_pdf")
        and os.path.exists(st.session_state.selected_pdf)
    ):

        st.markdown("## 📖 PDFビューア（ジャンプ）")

        show_pdf(
            st.session_state["selected_pdf"],
            st.session_state.get("selected_page", 0)
        )

        st.markdown("---")

    # =====================================================
    # 参考文献
    # =====================================================

    st.markdown("## 📚 回答に用いられた資料")

    source_meta = st.session_state.source_meta
    source_doc = st.session_state.source_doc

    shown_files = []

    # =====================================================
    # メタデータ整理
    # =====================================================

    for meta in source_meta:

        file_name = meta["file"]
        page = meta.get("page", 0)
        chunk_id = meta.get("chunk", 0)

        if file_name not in shown_files:
            shown_files.append(file_name)

    # =====================================================
    # PDF + PowerPoint チャンク表示
    # =====================================================

    for idx, meta in enumerate(source_meta):

        file_name = meta["file"]
        page = meta.get("page", 0)
        chunk_id = meta.get("chunk", 0)

        ext = os.path.splitext(file_name)[1].lower()

        col1, col2 = st.columns([3, 1])

        with col1:

            st.markdown(
                bold(source_doc[idx][:400]),
                unsafe_allow_html=True
            )

            if st.button(
                f"📄 {file_name} / chunk {chunk_id} / page {page + 1}",
                key=f"btn_{file_name}_{chunk_id}_{page}"
            ):

                st.session_state["selected_pdf"] = os.path.join(
                    PDF_DIR,
                    file_name
                )

                st.session_state["selected_page"] = page

                st.session_state["selected_chunk_text"] = (
                    source_doc[idx]
                )

                st.rerun()

        with col2:

            st.write(f"p.{page + 1}")

    # =====================================================
    # ダウンロード
    # =====================================================

    st.caption(
        f"クリックでダウンロード　参考文献数: {len(shown_files)}"
    )

    for file_name in shown_files:

        pdf_path = os.path.join(PDF_DIR, file_name)

        if os.path.exists(pdf_path):

            with open(pdf_path, "rb") as f:
                pdf_bytes = f.read()

            st.download_button(
                f"📄 {file_name}",
                pdf_bytes,
                file_name=file_name,
                mime="application/pdf",
                key=f"dl_{file_name}"
            )



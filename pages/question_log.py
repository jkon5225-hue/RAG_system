import streamlit as st
import pandas as pd

from db import get_question_conn
from auth import require_admin


#=============================
# 管理者チェック
#=============================
require_admin()

st.set_page_config(
    page_title="利用履歴",
    page_icon="📊",
    layout="wide"
)

st.title("📊 利用履歴")

#=============================
# DB読み込み
#=============================
conn = get_question_conn()

df = pd.read_sql_query(
    """
    SELECT
        id,
        datetime,
        username,
        genre,
        question,
        ROUND(elapsed,2) AS elapsed
    FROM question_log
    ORDER BY id DESC
    """,
    conn
)

conn.close()
#=============================
# ボタン
#=============================
col1, col2, col3, col4, col5 = st.columns([1,1,1,1,6])

with col1:
    if st.button("🔄 更新"):
        st.rerun()

with col2:
    csv = df.to_csv(index=False).encode("utf-8-sig")

    st.download_button(
        "📥 CSV出力",
        data=csv,
        file_name="question_log.csv",
        mime="text/csv"
    )

with col3:
    if st.button("📈 日別利用件数"):
        st.session_state.show_graph = \
            not st.session_state.get("show_graph", False)

with col4:
    if st.button("🗑 履歴削除"):
        conn = get_question_conn()
        cur = conn.cursor()
        cur.execute("DELETE FROM question_log")
        conn.commit()
        conn.close()
        st.success("履歴を削除しました")
        st.rerun()

with col5:
    if st.button("⬅ 管理画面へ戻る"):
        st.switch_page("pages/kanrisya.py")

st.divider()


#=============================
# 表示
#=============================
if len(df) == 0:
    st.info("まだ質問履歴はありません。")
else:
    if st.session_state.get("show_graph", False):
        graph = df.copy()

        graph["datetime"] = pd.to_datetime(graph["datetime"])

        daily = (
            graph
            .groupby(graph["datetime"].dt.date)
            .size()
            .reset_index(name="count")
        )

        st.subheader("📈 日別利用件数")

        st.line_chart(
            daily.set_index("datetime")["count"],
            use_container_width=True
        )
        st.divider()


    st.dataframe(
        df,
        width='stretch',
        hide_index=True
    )

    st.caption(f"件数：{len(df)}件")
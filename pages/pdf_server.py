# cd pages
# uvicorn pdf_server:app --host 0.0.0.0 --port 8000

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from pathlib import Path

import secrets
import time

app = FastAPI()

# PDF.js
app.mount("/pdfjs", StaticFiles(directory="pdfjs"), name="pdfjs")

PDF_DIR = Path("lite3")

# ============================
# Token管理
# ============================
TOKEN_EXPIRE = 180      # 秒（3分）

token_db = {}

class TokenRequest(BaseModel):
    filename: str
    user: str


@app.post("/create_token")
async def create_token(req: TokenRequest):

    token = secrets.token_urlsafe(32)

    token_db[token] = {
        "filename": req.filename,
        "expire": time.time() + TOKEN_EXPIRE
    }

    return {
        "token": token
    }


@app.get("/view/{filepath:path}")
async def view_pdf(
    filepath: str,
    token: str
):

    # ------------------------
    # token存在確認
    # ------------------------
    if token not in token_db:
        raise HTTPException(
            status_code=403,
            detail="Invalid token"
        )

    info = token_db[token]

    # ------------------------
    # 有効期限
    # ------------------------
    if time.time() > info["expire"]:
        del token_db[token]

        raise HTTPException(
            status_code=403,
            detail="Token expired"
        )

    # ------------------------
    # ファイル一致
    # ------------------------
    if info["filename"] != filepath:

        raise HTTPException(
            status_code=403,
            detail="Invalid file"
        )

    pdf_path = PDF_DIR / filepath

    if not pdf_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"File not found: {pdf_path}"
        )

    # 一度使ったら無効化
    del token_db[token]

    return FileResponse(
        pdf_path,
        media_type="application/pdf"
    )
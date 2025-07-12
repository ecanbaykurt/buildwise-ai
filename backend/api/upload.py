from fastapi import APIRouter, UploadFile, File
from typing import List
from backend.core.ingest import embed_and_upsert
import os

router = APIRouter()

@router.post("/upload_docs")
async def upload_docs(files: List[UploadFile] = File(...)):
    temp_dir = "temp_files"
    os.makedirs(temp_dir, exist_ok=True)  # Ensure temp_files/ exists

    for file in files:
        file_path = f"{temp_dir}/{file.filename}"
        with open(file_path, "wb") as f_out:
            content = await file.read()
            f_out.write(content)

        print(f"✅ Saved: {file_path}")

        # Call your end-to-end pipeline for each file
        embed_and_upsert(file_path)

    return {"message": f"✅ {len(files)} files uploaded & processed successfully!"}

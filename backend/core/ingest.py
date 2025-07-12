import os
from dotenv import load_dotenv
from openai import OpenAI
from pinecone import Pinecone
from backend.loaders.pdf_loader import load_pdf
from backend.loaders.word_loader import load_docx
from backend.loaders.csv_excel_loader import load_csv_excel
from backend.loaders.chunker import chunk_text
import sys

print(sys.path)

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index(os.getenv("PINECONE_INDEX"))

def load_file(file_path: str) -> str:
    if file_path.endswith(".pdf"):
        return load_pdf(file_path)
    elif file_path.endswith(".docx"):
        return load_docx(file_path)
    elif file_path.endswith(".csv") or file_path.endswith(".xlsx"):
        return load_csv_excel(file_path)
    else:
        raise ValueError("Unsupported file type!")

def embed_and_upsert(file_path: str):
    raw_text = load_file(file_path)
    chunks = chunk_text(raw_text, chunk_size=500, overlap=50)

    for i, chunk in enumerate(chunks):
        embedding = client.embeddings.create(
            model="text-embedding-3-small",
            input=chunk
        ).data[0].embedding

        index.upsert(
            vectors=[{
                "id": f"{os.path.basename(file_path)}-{i}",
                "values": embedding,
                "metadata": {
                    "text": chunk,
                    "source": os.path.basename(file_path)
                }
            }]
        )
        print(f"Upserted chunk {i}")

    print("✅ Ingestion complete!")

# Example usage:
if __name__ == "__main__":
    embed_and_upsert("docs/sample_lease.pdf")

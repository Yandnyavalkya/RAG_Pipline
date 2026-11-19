import re
import uuid
from pathlib import Path

from fastapi import UploadFile

from backend.app.core.config import ALLOWED_UPLOAD_EXTENSIONS, MAX_UPLOAD_BYTES, UPLOAD_DIR
from backend.app.core.exceptions import bad_request, not_found
from backend.app.repositories.document_repository import DocumentRepository
from backend.app.services.ingestion_service import process_upload, remove_file


class DocumentService:
    def __init__(self):
        self.documents = DocumentRepository()

    async def upload(self, user_id: str, upload: UploadFile, background_tasks) -> dict:
        original_name = Path(upload.filename or "document.pdf").name
        extension = Path(original_name).suffix.lower()
        if extension not in ALLOWED_UPLOAD_EXTENSIONS or upload.content_type not in {"application/pdf", "application/octet-stream", None}:
            raise bad_request("Upload a valid PDF document")
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        stored_name = f"{uuid.uuid4().hex}.pdf"
        destination = UPLOAD_DIR / stored_name
        size = 0
        try:
            with destination.open("wb") as output:
                while chunk := await upload.read(1024 * 1024):
                    size += len(chunk)
                    if size > MAX_UPLOAD_BYTES:
                        raise bad_request(f"PDF exceeds the {MAX_UPLOAD_BYTES // (1024 * 1024)} MB upload limit")
                    output.write(chunk)
            if size == 0:
                raise bad_request("The uploaded PDF is empty")
            with destination.open("rb") as source:
                if source.read(5) != b"%PDF-":
                    raise bad_request("The uploaded file is not a valid PDF")
            record = await self.documents.create(user_id, {
                "original_filename": original_name, "stored_filename": stored_name,
                "file_path": str(destination), "file_size": size,
                "status": "processing", "file_type": "application/pdf",
            })
            background_tasks.add_task(process_upload, str(destination), record["id"], user_id, original_name, self.documents)
            return record
        except Exception:
            destination.unlink(missing_ok=True)
            raise

    async def list(self, user_id: str) -> list[dict]:
        return await self.documents.list_by_user(user_id)

    async def get(self, document_id: str, user_id: str) -> dict:
        record = await self.documents.find_owned(document_id, user_id)
        if record is None:
            raise not_found("Document not found")
        return record

    async def delete(self, document_id: str, user_id: str) -> None:
        record = await self.get(document_id, user_id)
        def delete_vectors():
            from vectorstores.pinecone_store import PineconeVectorStore
            PineconeVectorStore().delete_by_document_id(document_id, user_id)
        await __import__("asyncio").to_thread(delete_vectors)
        await self.documents.delete_owned(document_id, user_id)
        remove_file(record["file_path"])

    async def suggestions(self, document_id: str, user_id: str) -> dict:
        doc = await self.get(document_id, user_id)
        suggestions = []
        if doc.get("status") == "ready":
            try:
                from loaders.document_loader import load_single_file
                pages = await __import__("asyncio").to_thread(load_single_file, doc["file_path"])
                text = " ".join(page.page_content for page in pages)
                sentences = re.split(r"(?<=[.!?])\s+", text)
                topics = []
                for sentence in sentences:
                    words = re.findall(r"[A-Za-z][A-Za-z'-]*", sentence)
                    if len(words) >= 5:
                        topic = " ".join(words[:7]).strip(" .,;:")
                        if topic and topic.lower() not in {item.lower() for item in topics}:
                            topics.append(topic)
                    if len(topics) == 4:
                        break
                suggestions = [f"What does the document say about {topic}?" for topic in topics]
            except Exception:
                suggestions = []
        return {"document_id": document_id, "status": doc["status"], "suggestions": suggestions}

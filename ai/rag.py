import logging
import os
import re
import uuid
from typing import Iterable

import cohere
import httpx
from sqlalchemy import delete, select
from ai.db import PolicyEmbedding
from database.db import SessionLocal


logger = logging.getLogger(__name__)


class RAGClient:
    def __init__(self, embed_model: str | None = None):
        self.embed_model = embed_model or os.getenv("COHERE_EMBED_MODEL", "embed-english-v3.0")
        self.client = cohere.Client(os.getenv("COHERE_API_KEY"))

    def _looks_like_text(self, raw: bytes) -> bool:
        if not raw:
            return False
        if b"\x00" in raw:
            return False
        sample = raw[:2048]
        non_printable = sum(1 for byte in sample if byte < 9 or (13 < byte < 32))
        return non_printable / max(len(sample), 1) < 0.2

    def _extract_text_from_pdf(self, file_path: str) -> str:
        try:
            from pypdf import PdfReader  # type: ignore
        except Exception:
            return ""
        try:
            reader = PdfReader(file_path)
            return "\n".join(page.extract_text() or "" for page in reader.pages).strip()
        except Exception:
            return ""

    def _extract_text_from_docx(self, file_path: str) -> str:
        try:
            from docx import Document  # type: ignore
        except Exception:
            return ""
        try:
            doc = Document(file_path)
            return "\n".join(paragraph.text for paragraph in doc.paragraphs).strip()
        except Exception:
            return ""

    def _read_text_from_source(self, file_path: str) -> str:
        if file_path.startswith("http://") or file_path.startswith("https://"):
            try:
                response = httpx.get(file_path, timeout=20.0)
                response.raise_for_status()
                raw = response.content
            except Exception:
                return ""
        else:
            if not os.path.exists(file_path):
                return ""
            with open(file_path, "rb") as handle:
                raw = handle.read()

        ext = os.path.splitext(file_path)[1].lower()
        if ext == ".pdf":
            return self._extract_text_from_pdf(file_path)
        if ext == ".docx":
            return self._extract_text_from_docx(file_path)

        if self._looks_like_text(raw):
            return raw.decode("utf-8", errors="ignore").strip()

        return ""

    def _clean_text(self, text: str) -> str:
        return re.sub(r"\s+", " ", text).strip()

    def _chunk_text(self, text: str, max_chars: int = 1200, overlap: int = 200) -> list[str]:
        cleaned = self._clean_text(text)
        if not cleaned:
            return []
        chunks = []
        start = 0
        while start < len(cleaned):
            end = min(len(cleaned), start + max_chars)
            chunk = cleaned[start:end].strip()
            if chunk:
                chunks.append(chunk)
            if end >= len(cleaned):
                break
            start = max(0, end - overlap)
        return chunks

    def _embed_texts(self, texts: Iterable[str], input_type: str) -> list[list[float]]:
        response = self.client.embed(
            texts=list(texts),
            model=self.embed_model,
            input_type=input_type,
        )

        logger.info(f"Embedded {len(texts)} texts with model {self.embed_model} & response: {response}")
        return response.embeddings or []

    def index_policy_document(
        self,
        policy_id: str,
        organization_id: str,
        policy_name: str,
        description: str | None,
        document_name: str | None,
        file_path: str,
    ) -> dict:
        text = self._read_text_from_source(file_path)
        if not text:
            return {"status": "skipped", "reason": "no_text_extracted"}

        chunks = self._chunk_text(text)
        if not chunks:
            return {"status": "skipped", "reason": "no_chunks_created"}

        embeddings = self._embed_texts(chunks, input_type="search_document")
        if not embeddings:
            return {"status": "skipped", "reason": "no_embeddings_created"}

        with SessionLocal() as db:
            db.execute(
                delete(PolicyEmbedding).where(PolicyEmbedding.policy_id == policy_id)
            )
            for idx, (chunk, embedding) in enumerate(
                zip(chunks, embeddings, strict=False)
            ):
                db.add(
                    PolicyEmbedding(
                        policy_id=policy_id,
                        organization_id=organization_id,
                        policy_name=policy_name,
                        description=description,
                        document_name=document_name,
                        file_path=file_path,
                        chunk_index=idx,
                        text=chunk,
                        embedding=embedding,
                    )
                )
            db.commit()
        return {"status": "indexed", "chunks": len(chunks)}

    def remove_policy_from_index(self, policy_id: str) -> dict:
        with SessionLocal() as db:
            result = db.execute(
                delete(PolicyEmbedding).where(PolicyEmbedding.policy_id == policy_id)
            )
            db.commit()
        if result.rowcount == 0:
            return {"status": "skipped", "reason": "policy_not_found"}
        return {"status": "removed", "count": result.rowcount}

    def query_policy_index(
        self,
        query: str,
        top_k: int = 5,
        organization_ids: list[str] | None = None,
    ) -> list[dict]:
        query_embedding = self._embed_texts([query], input_type="search_query")
        if not query_embedding:
            return []
        query_vector = query_embedding[0]

        with SessionLocal() as db:
            stmt = (
                select(PolicyEmbedding)
                .order_by(PolicyEmbedding.embedding.cosine_distance(query_vector))
                .limit(max(top_k, 1))
            )
            if organization_ids:
                try:
                    uuids = [uuid.UUID(oid) for oid in organization_ids]
                    stmt = stmt.where(PolicyEmbedding.organization_id.in_(uuids))
                except (ValueError, TypeError):
                    pass
            results = db.execute(stmt).scalars().all()
        response = []
        for record in results:
            response.append(
                {
                    "policy_id": str(record.policy_id),
                    "organization_id": str(record.organization_id),
                    "policy_name": record.policy_name,
                    "description": record.description,
                    "document_name": record.document_name,
                    "file_path": record.file_path,
                    "chunk_index": record.chunk_index,
                    "text": record.text,
                    "score": None,
                }
            )
        return response

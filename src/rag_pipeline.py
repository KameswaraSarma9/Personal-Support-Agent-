"""
rag_pipeline.py
Document ingestion, chunking, embedding, and retrieval logic for the
support knowledge base. Uses Gemini's text-embedding-004 model and a
persistent local ChromaDB collection so the index only needs to be
built once (see ingest_knowledge_base.py for the one-time build script).
"""
import re
from pathlib import Path

import chromadb
from google import genai
from pypdf import PdfReader

try:
    # Newer LangChain versions moved text splitters to a separate package.
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except ImportError:
    from langchain.text_splitter import RecursiveCharacterTextSplitter

from src import config


class RAGPipeline:
    def __init__(self, db_dir: str = None):
        self.client = genai.Client(api_key=config.GEMINI_API_KEY)
        db_path = db_dir or str(config.CHROMA_DB_DIR)
        self.chroma_client = chromadb.PersistentClient(path=db_path)
        self.collection = self.chroma_client.get_or_create_collection(
            name=config.COLLECTION_NAME
        )
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=config.CHUNK_SIZE,
            chunk_overlap=config.CHUNK_OVERLAP,
        )

    # ------------------------------------------------------------------
    # Embedding helper
    # ------------------------------------------------------------------
    def get_embedding(self, text: str) -> list:
        """Calls the Gemini embedding model for a single text string."""
        response = self.client.models.embed_content(
            model=config.EMBEDDING_MODEL,
            contents=text,
        )
        return response.embeddings[0].values

    # ------------------------------------------------------------------
    # Document parsing
    # ------------------------------------------------------------------
    @staticmethod
    def _extract_section_title(chunk: str) -> str:
        """
        Best-effort extraction of a section/heading name from a chunk, so
        retrieval metadata can include a meaningful section reference
        (per assignment requirement 4.2: chunk metadata must include
        source document + page/section name).
        """
        md_heading = re.search(r"^#{1,3}\s+(.+)$", chunk, re.MULTILINE)
        if md_heading:
            return md_heading.group(1).strip()

        numbered_heading = re.search(r"^\s*\d+\.\s+([A-Z][A-Z \-/&()]{4,})$", chunk, re.MULTILINE)
        if numbered_heading:
            return numbered_heading.group(1).strip().title()

        return "General"

    def _load_text_file(self, path: Path) -> str:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    def _load_pdf_file(self, path: Path) -> list:
        """Returns a list of (page_number, page_text) tuples so page
        numbers can be preserved in chunk metadata."""
        reader = PdfReader(str(path))
        pages = []
        for i, page in enumerate(reader.pages):
            pages.append((i + 1, page.extract_text() or ""))
        return pages

    # ------------------------------------------------------------------
    # Ingestion
    # ------------------------------------------------------------------
    def ingest_document(self, file_path: Path):
        """Parses, chunks, embeds, and stores a single document based on
        its file extension."""
        doc_name = file_path.name
        suffix = file_path.suffix.lower()

        if suffix in (".txt", ".md"):
            content = self._load_text_file(file_path)
            chunks = self.splitter.split_text(content)
            for idx, chunk in enumerate(chunks):
                self._add_chunk(
                    doc_name=doc_name,
                    chunk=chunk,
                    chunk_idx=idx,
                    section=self._extract_section_title(chunk),
                    page=None,
                )

        elif suffix == ".pdf":
            pages = self._load_pdf_file(file_path)
            global_idx = 0
            for page_num, page_text in pages:
                if not page_text.strip():
                    continue
                chunks = self.splitter.split_text(page_text)
                for chunk in chunks:
                    self._add_chunk(
                        doc_name=doc_name,
                        chunk=chunk,
                        chunk_idx=global_idx,
                        section=self._extract_section_title(chunk),
                        page=page_num,
                    )
                    global_idx += 1
        else:
            raise ValueError(f"Unsupported file type for ingestion: {suffix}")

    def _add_chunk(self, doc_name: str, chunk: str, chunk_idx: int, section: str, page):
        if not chunk.strip():
            return
        embedding = self.get_embedding(chunk)
        chunk_id = f"{doc_name}_chunk_{chunk_idx}"
        metadata = {
            "source": doc_name,
            "chunk_index": chunk_idx,
            "section": section,
            "page": page if page is not None else "N/A",
        }
        self.collection.add(
            ids=[chunk_id],
            embeddings=[embedding],
            metadatas=[metadata],
            documents=[chunk],
        )

    def ingest_directory(self, data_dir: Path = None) -> int:
        """Ingests every supported file in the data directory. Returns the
        number of documents processed."""
        data_dir = data_dir or config.DATA_DIR
        supported = {".txt", ".md", ".pdf"}
        files = [f for f in sorted(data_dir.iterdir()) if f.suffix.lower() in supported]
        for f in files:
            self.ingest_document(f)
        return len(files)

    def reset_collection(self):
        """Deletes and recreates the collection — useful for re-indexing
        from scratch during development."""
        self.chroma_client.delete_collection(name=config.COLLECTION_NAME)
        self.collection = self.chroma_client.get_or_create_collection(
            name=config.COLLECTION_NAME
        )

    def count(self) -> int:
        return self.collection.count()

    # ------------------------------------------------------------------
    # Retrieval
    # ------------------------------------------------------------------
    def retrieve_context(self, query: str, top_k: int = None) -> list:
        """
        Embeds the query and performs a cosine-similarity search against
        the indexed chunks. Returns the top-k chunks with their source,
        section/page metadata, and a similarity score in [0, 1].
        """
        top_k = top_k or config.TOP_K
        query_vector = self.get_embedding(query)

        results = self.collection.query(
            query_embeddings=[query_vector],
            n_results=top_k,
        )

        retrieved_items = []
        if results and results.get("documents") and results["documents"][0]:
            for i in range(len(results["documents"][0])):
                distance = results["distances"][0][i] if results.get("distances") else 1.0
                # Chroma's default space is L2 by default for arbitrary embeddings,
                # but with normalized embeddings cosine distance behaves predictably
                # in [0, 2]. We convert to a similarity-style score in [0, 1].
                similarity = max(0.0, 1.0 - (distance / 2.0))
                metadata = results["metadatas"][0][i]
                retrieved_items.append({
                    "text": results["documents"][0][i],
                    "source": metadata.get("source", "unknown"),
                    "section": metadata.get("section", "General"),
                    "page": metadata.get("page", "N/A"),
                    "score": round(similarity, 4),
                })
        return retrieved_items

import sys

import chromadb
from sentence_transformers import SentenceTransformer

from app.rag.ingest import COLLECTION, DB_DIR, MODEL_NAME

_model = SentenceTransformer(MODEL_NAME)
_col = chromadb.PersistentClient(path=DB_DIR).get_collection(COLLECTION)


def search(query: str, k: int = 3, category: str | None = None):
    emb = _model.encode([query], normalize_embeddings=True).tolist()
    where = {"category": category} if category else None
    res = _col.query(query_embeddings=emb, n_results=k, where=where)

    hits = []
    for doc, meta, dist in zip(res["documents"][0], res["metadatas"][0], res["distances"][0]):
        hits.append({"text": doc, "meta": meta, "score": round(1 - dist, 3)})
    return hits


if __name__ == "__main__":
    q = " ".join(sys.argv[1:]) or "vpn not connecting"
    for h in search(q):
        print(f"\n[{h['score']}] {h['meta']['title']}")
        print("ACTIONS :", h["meta"]["actions"])
        print("ESCALATE:", h["meta"]["escalate"])
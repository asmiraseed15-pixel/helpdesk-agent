import sys
from app.rag.rewrite import rewrite_query
from app.rag.retriever import search

q = " ".join(sys.argv[1:]) or "password marandhuten"
rq = rewrite_query(q)

print(f"\nORIGINAL : {q}")
for h in search(q)[:2]:
    print(f"  [{h['score']}] {h['meta']['title']}")

print(f"\nREWRITTEN: {rq}")
for h in search(rq)[:2]:
    print(f"  [{h['score']}] {h['meta']['title']}")
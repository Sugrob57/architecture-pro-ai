import chromadb
from sentence_transformers import SentenceTransformer

client = chromadb.PersistentClient(
    path="./data/knowledge-base/chroma_db"
)

collection = client.get_collection("gooddrink")

model = SentenceTransformer(
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)

query = "посоветуй горькую IPA с насыщенным вкусом"
embedding = model.encode(query).tolist()

res = collection.query(
    query_embeddings=[embedding],
    n_results=3
)

for doc, meta in zip(res["documents"][0], res["metadatas"][0]):
    print("----")
    print(doc[:200])
    print(meta["telegram_url"])

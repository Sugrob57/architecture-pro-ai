import chromadb
from sentence_transformers import SentenceTransformer
from BeerSynonymExpander import BeerSynonymExpander

client = chromadb.PersistentClient(
    path="./data/knowledge-base/chroma_db"
)

sinonimaizer = BeerSynonymExpander()

collection = client.get_collection("gooddrink")

model = SentenceTransformer(
    #"sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    "intfloat/multilingual-e5-large"
)

query = "посоветуй IPA с ярким вкусом хмеля"
query = sinonimaizer.expand_text(query)
print("Enreached text: " + query)
embedding = model.encode(query).tolist()

res = collection.query(
    query_embeddings=[embedding],
    n_results=4
)

for doc, meta in zip(res["documents"][0], res["metadatas"][0]):
    print("----")
    print(doc[:300])
    print(meta["telegram_url"])

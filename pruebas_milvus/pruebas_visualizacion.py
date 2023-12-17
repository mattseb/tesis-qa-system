from sentence_transformers import SentenceTransformer
from pymilvus import (
    connections,
    Collection,
)    

connections.connect("default", host="localhost", port="19530")
collection_name = 'prueba_final_2'
collection = Collection(name=collection_name)
retriever = SentenceTransformer("sentence-transformers/all-mpnet-base-v2", device='cuda')
collection.load()
print(collection.num_entities)

result = collection.query(
    expr="metadata != 'None'",
    output_fields=["embedding","metadata"],
    limit=1,
)
print(result)
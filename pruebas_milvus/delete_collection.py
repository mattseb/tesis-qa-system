from sentence_transformers import SentenceTransformer
from pymilvus import (
    connections,
    utility,
    Collection,
)

if __name__ == '__main__':
    connections.connect("default", host="localhost", port="19530")
    collection_name = 'prueba_final_2'
    collection = Collection(name=collection_name)

    retriever = SentenceTransformer("sentence-transformers/all-mpnet-base-v2", device='cuda')
    collection.load()
    batch_size = 64
    utility.drop_collection("prueba_final_3")
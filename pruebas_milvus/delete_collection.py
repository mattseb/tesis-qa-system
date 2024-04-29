from sentence_transformers import SentenceTransformer
from pymilvus import (
    connections,
    utility,
    Collection,
)

if __name__ == '__main__':
    connections.connect("default", host="localhost", port="19530")
    collection_name = 'prueba_final_3_tesis'

    utility.drop_collection(collection_name)
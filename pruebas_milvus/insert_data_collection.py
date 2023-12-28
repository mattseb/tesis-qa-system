import time
from sentence_transformers import SentenceTransformer
import pandas as pd
from pymilvus import (
    connections,
    Collection,
)

if __name__ == '__main__':
    inicio = time.time()
    ruta_del_csv = 'csv\\dominioFinalSpliteado6.csv'

    df = pd.read_csv(ruta_del_csv)
    df = df

    connections.connect("default", host="localhost", port="19530")
    collection_name = 'prueba_final_3'
    collection = Collection(name=collection_name)

    retriever = SentenceTransformer("sentence-transformers/all-mpnet-base-v2", device='cuda')
    collection.load()

    for index, row in df.iterrows():
        print('==== ITER ========', index)
        emb = retriever.encode(row["split"]).tolist()
        meta = row.to_dict()
        to_upsert = {'embedding': emb, 'metadata': meta}
        collection.insert(data=[to_upsert])
        print(collection.num_entities)
        print(collection.is_empty)
    fin = time.time()
    print("Se demoro un tiempo de ", fin - inicio, " segundos")
import time
from concurrent.futures import ProcessPoolExecutor
from sentence_transformers import SentenceTransformer
import pandas as pd
from concurrent.futures import ProcessPoolExecutor, as_completed
from pymilvus import (
    connections,
    Collection,
)

def insert_data(row, retriever, collection):
    try:
        emb = retriever.encode(row["split"]).tolist()
        meta = row.to_dict()
        to_upsert = {'embedding': emb, 'metadata': '"' + str(meta) + '"'}
        collection.insert(data=[to_upsert])
        print(collection.num_entities)
        print(collection.is_empty)
        return f"Row {row.id} embedded and inserted"
    except Exception as e:
        print(e)
        return f"Row {row.id} NOT embedded and inserted"


if __name__ == '__main__':
    inicio = time.time()
    connections.connect("default", host="localhost", port="19530")
    collection_name = 'prueba_final_2'
    collection = Collection(name=collection_name)
    collection.load()

    ruta_del_csv = 'C:\\Users\\mateo\\Documents\\Universidad\\Tesis\\tesis-qa-system\\DataSplit\\SentenceSplit\\split_data_sentence_5_total_2212.csv'
    retriever = SentenceTransformer("sentence-transformers/all-mpnet-base-v2", device='cuda')

    df = pd.read_csv(ruta_del_csv)
    df = df.head(100)

    with ProcessPoolExecutor(max_workers=1) as executor:
        futures = [executor.submit(insert_data, row, retriever, collection) for index, row in df.iterrows()]
        # Esperar a que se completen todas las inserciones
    result = [task.result() for task in futures]
    fin = time.time()
    print("Se demoró un tiempo de ", fin - inicio, " segundos")

    result = collection.query(
        expr="metadata != 'None'",
        output_fields=["metadata"],
    )
    print(len(result))

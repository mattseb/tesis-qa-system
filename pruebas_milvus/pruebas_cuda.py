import time
from sentence_transformers import SentenceTransformer
import pandas as pd
from pymilvus import (
    connections,
    Collection,
)

if __name__ == '__main__':
    inicio = time.time()
    ruta_del_csv = 'C:\\Users\\mateo\\Documents\\Universidad\\Tesis\\tesis-qa-system\\DataSplit\\SentenceSplit\\split_data_sentence_5_total_2212.csv'

    df = pd.read_csv(ruta_del_csv)
    df = df

    connections.connect("default", host="localhost", port="19530")
    collection_name = 'prueba_final_2'
    collection = Collection(name=collection_name)

    retriever = SentenceTransformer("sentence-transformers/all-mpnet-base-v2", device='cuda')
    collection.load()

    for index, row in df.iterrows():
        print('==== ITER ========', index)
        emb = retriever.encode(row["split"]).tolist()
        meta = row.to_dict()
        to_upsert = {'embedding': emb, 'metadata': '"' + str(meta) + '"'}
        collection.insert(data=[to_upsert])
        print(collection.num_entities)
        print(collection.is_empty)
    fin = time.time()
    print("Se demoro un tiempo de ", fin - inicio, " segundos")

    # result = collection.query(
    #     expr="metadata != 'None'",
    #     output_fields=["metadata"],
    # )
    # print(len(result))
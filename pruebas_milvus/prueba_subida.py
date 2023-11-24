from sentence_transformers import SentenceTransformer
import concurrent.futures
import pandas as pd
import ast
from pymilvus import (
    connections,
    utility,
    FieldSchema,
    CollectionSchema,
    DataType,
    Collection,
)

# Especifica la ruta del archivo CSV

# din = 768


# fields=[
#     FieldSchema(name='id', dtype=DataType.INT64, is_primary=True, auto_id=True),
#     FieldSchema(name='embedding', dtype=DataType.FLOAT_VECTOR, dim=din),
#     FieldSchema(name='metadata', dtype=DataType.VARCHAR, max_length=2560)
# ]
        
# schema = CollectionSchema(fields)
# collection = Collection(name=collection_name, schema=schema)




if __name__ == '__main__':
    ruta_del_csv = 'C:\\Users\\mateo\\Documents\\Universidad\\Tesis\\tesis-qa-system\\DataSplit\\SentenceSplit\\split_data_sentence_5_total_2212.csv'

    df = pd.read_csv(ruta_del_csv)
    df = df.head(10)

    connections.connect("default", host="localhost", port="19530")
    collection_name = 'my_collection'
    collection = Collection(name=collection_name)

    retriever = SentenceTransformer("sentence-transformers/all-mpnet-base-v2", device='cuda')
    collection.load()
    batch_size = 64

    with concurrent.futures.ProcessPoolExecutor(max_workers=23) as executor:
        to_upsert = []
        for i in (range(0, len(df), batch_size)):
            i_end = min(i+batch_size, len(df))
            batch = df.iloc[i:i_end]
            futures = []
            for j in range(len(batch)):
                future = executor.submit(retriever.encode, batch.iloc[j]["split"])
                futures.append(future)
            for future, meta in zip(futures, batch.to_dict(orient="records")):
                emb = future.result().tolist()
                to_upsert.append({'embedding': emb, 'metadata': str(meta)})
            collection.insert(to_upsert)
            print(collection.num_entities)

    # Crea un índice en la colección
    index_params = {
        'metric_type': 'L2',
        'index_type': 'IVF_FLAT', 
        'params': {'nlist': 16384}
    }

    collection.create_index(
        field_name='embedding', 
        index_params=index_params
    )

    print(utility.index_building_progress("my_collection"))
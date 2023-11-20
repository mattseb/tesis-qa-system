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
ruta_del_csv = 'split_data4.csv'

df = pd.read_csv(ruta_del_csv)
df = df.head(10)

connections.connect("default", host="localhost", port="19530")
collection_name = 'my_collection'
# din = 768


# fields=[
#     FieldSchema(name='id', dtype=DataType.INT64, is_primary=True, auto_id=True),
#     FieldSchema(name='embedding', dtype=DataType.FLOAT_VECTOR, dim=din),
#     FieldSchema(name='metadata', dtype=DataType.VARCHAR, max_length=2560)
# ]
        
# schema = CollectionSchema(fields)
# collection = Collection(name=collection_name, schema=schema)
collection = Collection(name=collection_name)

retriever = SentenceTransformer("sentence-transformers/all-mpnet-base-v2", device='cpu')


collection.load()
# batch_size = 64
# with concurrent.futures.ThreadPoolExecutor() as executor:
#     to_upsert = []
#     for i in (range(0, len(df), batch_size)):
#         i_end = min(i+batch_size, len(df))
#         batch = df.iloc[i:i_end]
#         futures = []
#         for j in range(len(batch)):
#             future = executor.submit(retriever.encode, batch.iloc[j]["split"])
#             futures.append(future)
#         for future, meta in zip(futures, batch.to_dict(orient="records")):
#             emb = future.result().tolist()
#             to_upsert.append({'embedding': emb, 'metadata': str(meta)})
#         collection.insert(to_upsert)
#         print(collection.num_entities)

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
# # Espera un momento después de crear el índice
# import time
# time.sleep(1)

# # Make a question
question = "What is Carbon dioxide?"

# # Vectorize the question
question_vector = retriever.encode([question])[0].tolist()

# # Search for the most similar vector in Milvus
search_params = {'nprobe': 16}  # You can adjust nprobe based on your needs
# # search_result = collection.search(query_records=[question_vector], top_k=1, params=search_params)
# # search_result = collection.search(query_records=[question_vector], anns_field='embedding', param=search_params, limit=1)
search_result = collection.search(
    data=[question_vector], 
    anns_field='embedding', 
    param=search_params, 
    limit=2,
    output_fields=['metadata'],
)


hits = [result[0] for result in search_result]
answers = [hit.entity.get('metadata') for hit in hits ]
answers_processed = []
for answer in answers:
    answer = answer.replace('nan', 'None')
    answers_processed.append(ast.literal_eval(answer)['split'])

print("Question:", question)
print("Answer:", answers_processed)
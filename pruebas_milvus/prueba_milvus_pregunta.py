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
# ruta_del_csv = 'split_data4.csv'

# df = pd.read_csv(ruta_del_csv)
# df = df.head(10)

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

model = SentenceTransformer("sentence-transformers/all-mpnet-base-v2", device='cpu')


collection.load()

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
question = "What is CO2?"
# question = "What is covid?"

# # Vectorize the question
question_vector = model.encode([question])[0].tolist()

# # Search for the most similar vector in Milvus
search_params = {'nprobe': 16}  # You can adjust nprobe based on your needs
# # search_result = collection.search(query_records=[question_vector], top_k=1, params=search_params)
# # search_result = collection.search(query_records=[question_vector], anns_field='embedding', param=search_params, limit=1)
search_result = collection.search(
    data=[question_vector], 
    anns_field='embedding', 
    param=search_params, 
    limit=4,
    output_fields=['metadata'],
)


hits = [result[0] for result in search_result]
answers = [hit.entity.get('metadata') for hit in hits ]
answers_processed = []
for answer in answers:
    answer = answer.replace('nan', 'None')
    # answers_processed.append(ast.literal_eval(answer)['split'])
    answers_processed.append(ast.literal_eval(answer))

print("Question:", question)
print("Answer:", answers_processed)
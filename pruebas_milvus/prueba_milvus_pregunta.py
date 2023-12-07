from sentence_transformers import SentenceTransformer
import ast
from pymilvus import (
    connections,
    utility,
    Collection,
)

connections.connect("default", host="localhost", port="19530")
collection_name = 'my_collection'


collection = Collection(name=collection_name)
collection.load()

model = SentenceTransformer("sentence-transformers/all-mpnet-base-v2", device='cpu')

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
question = "Enlist some examples of contaminants that are in a natural environment"

question_vector = model.encode([question])[0].tolist()

search_params = {'nprobe': 16}
search_result = collection.search(
    data=[question_vector], 
    anns_field='embedding', 
    param=search_params, 
    limit=1,
    output_fields=['metadata'],
)


hits = [result[0] for result in search_result]
answers = [hit.entity.get('metadata') for hit in hits ]
answers_processed = []
for answer in answers:
    answer = answer.replace('nan', 'None')
    answers_processed.append(ast.literal_eval(answer))

print("Question:", question)
print("Answer:", answers_processed)
from pymilvus import (
    connections,
    FieldSchema,
    CollectionSchema,
    DataType,
    Collection,
)
import torch

# Especifica la ruta del archivo CSV
connections.connect("default", host="localhost", port="19530")

din = 768

collection_name = 'prueba_final_2'

fields=[
    FieldSchema(name='id', dtype=DataType.INT64, is_primary=True, auto_id=True),
    FieldSchema(name='embedding', dtype=DataType.FLOAT_VECTOR, dim=din),
    FieldSchema(name='metadata', dtype=DataType.VARCHAR, max_length=60000)
]
        
schema = CollectionSchema(fields)
collection = Collection(name=collection_name, schema=schema)

collection_final = Collection("prueba_final_2")

index_params = {
  "metric_type":"L2",
  "index_type":"FLAT",
  "params":{"nlist":1024}
}

collection_final.create_index(
  field_name="embedding", 
  index_params=index_params
)
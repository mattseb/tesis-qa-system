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

collection_name = 'prueba_final_3_tesis'

fields=[
    FieldSchema(name='id', dtype=DataType.INT64, is_primary=True, auto_id=True),
    FieldSchema(name='embedding', dtype=DataType.FLOAT_VECTOR, dim=din),
    FieldSchema(name='metadata', dtype=DataType.JSON)
]
        
schema = CollectionSchema(fields)
collection = Collection(name=collection_name, schema=schema)

collection_final = Collection("prueba_final_3")

index_params = {
  "metric_type":"COSINE",
  "index_type":"FLAT"
}

collection_final.create_index(
  field_name="embedding", 
  index_params=index_params
)

from pymilvus import connections, Collection

# Establecer la conexión a Milvus
connections.connect(host='localhost', port='19530')

# Crear una instancia de la colección
collection = Collection(name="my_collection")

# Conectar a la colección
collection.load()

# Obtener el número de vectores en la colección
num_entities = collection.num_entities

print(f"La colección tiene {num_entities} vectores.")

from concurrent.futures import ThreadPoolExecutor
import os
import time
from haystack.nodes import TextConverter, PreProcessor
import logging
from haystack.nodes import PreProcessor
from langdetect import detect
import pandas as pd
import numpy as np
from transformers import AutoTokenizer
from haystack.utils import convert_files_to_docs
from haystack.nodes import TextConverter, PreProcessor

def create_preprocessor_haystack(split_by_user, split_length_user):
    try:
        if (split_by_user == 'sentence'):
            preprocessor = PreProcessor(
                clean_empty_lines=True,
                clean_whitespace=True,
                clean_header_footer=False,
                split_by= split_by_user,
                split_length = split_length_user,
                split_respect_sentence_boundary=False
            )
        else:
            preprocessor = PreProcessor(
                clean_empty_lines=True,
                clean_whitespace=True,
                clean_header_footer=False,
                split_by= split_by_user,
                split_length = split_length_user,
                split_respect_sentence_boundary=True
            )
        return preprocessor
    except Exception as e:
        print(f"An error occurred in the preprocessor: {e}")


def lenght_token(text, llm):
    try:
        tokenizer = AutoTokenizer.from_pretrained(llm)
        #Tokenize the input text
        tokens = tokenizer.tokenize(text)
        return len(tokens)

    except Exception as e:
        print(f"An error occurred in the lenghtToken: {e}")


# def split_content_haystack():
#     try:
#         # Specify the file path to your CSV file
#         file_path = "test\dominio3Test.csv"

#         # Read the CSV file into a DataFrame
#         df = pd.read_csv(file_path)

#         # Display the DataFrame
#         # df.head()

#         # Extraer las primeras 'numero_de_filas_a_extraer' filas y almacenarlas en un nuevo DataFrame
#         # df_test = df.head(5)
#         df_test = df

#         # Add a new column 'id' starting from 1 at the first position
#         df_test.insert(0, 'id', range(1, len(df_test) + 1))

#         # Create an empty DataFrame with the same columns as the original DataFrame
#         new_columns = ['split', 'split_id', 'tokens']
#         new_df = pd.DataFrame(columns=df_test.columns.tolist() + new_columns)

#         for i in range(len(df_test)):

#             print("----- Linea " , i, " -----")

#             # Especifica el índice de fila y la columna que deseas extraer
#             fila = i  # Por ejemplo, extraeremos la fila 2 (índice 2)
#             columna = 'Contenido'

#             # Almacenar el contenido de la celda en una variable
#             contenido = df_test.at[fila, columna]

#             # Crear el archivo TXT y escribir el contenido
#             nombre_archivo = "haystack-division/ContenidoCelda.txt"
#             with open(nombre_archivo, 'w', encoding='UTF-8') as archivo:
#                 archivo.write(contenido)

#             print(f"El archivo {nombre_archivo} se ha creado y el contenido se ha almacenado correctamente.")

#             converter = TextConverter(remove_numeric_tables= True, valid_languages=["en"])
#             doc_txt = converter.convert(file_path="haystack-division\ContenidoCelda.txt", meta=None)[0]

#             doc_dir = 'haystack-division'

#             all_docs = convert_files_to_docs(dir_path=doc_dir)

#             preprocessor = create_preprocessor_haystack('sentence', 5)

#             docs_default = preprocessor.process([doc_txt])
            
#             print(f"n_docs_input: 1\nn_docs_output: {len(docs_default)}")

#             # Define an array of strings
#             fragments_list = []
#             split_id_list = []
#             tokens_list = []

#             # Iterate through the array elements
#             for element in docs_default:

#                 document_dict = element.to_dict()

#                 for key, value in document_dict.items():

#                     if (key == 'content'):
#                         fragments_list.append(value)
#                         tokens_list.append(lenght_token(value,'google/flan-t5-base'))
                    
#                     elif (key == 'meta'):

#                         for key_meta, value_meta in value.items():
#                             split_id_list.append(value_meta)
#             for num, element in enumerate(fragments_list):
#                 new_df.loc[len(new_df)] = {
#                     'id': df_test.at[i, 'id'],
#                     'PageURL': df_test.at[i, 'PageURL'],
#                     'Title':df_test.at[i, 'Title'],
#                     'CreationDate':df_test.at[i, 'CreationDate'],
#                     'Seccion':df_test.at[i, 'Seccion'],
#                     'Subseccion':df_test.at[i, 'Subseccion'],
#                     'WikipageID':df_test.at[i, 'WikipageID'],
#                     'LastModified':df_test.at[i, 'LastModified'],
#                     'Contenido':df_test.at[i, 'Contenido'],
#                     'split': fragments_list[num], 
#                     'split_id': split_id_list[num], 
#                     'tokens': tokens_list[num]
#                 }

#         # Drop one or more columns by specifying column names
#         columns_to_drop = ['id', 'Contenido']
#         new_df = new_df.drop(columns=columns_to_drop)

#         # Save the DataFrame to a CSV file
#         new_df.to_csv('split_data.csv', index=False)

#         # Check that the file has been saved
#         print("DataFrame has been saved to 'split_data.csv'")

#     except Exception as e:
#         print(f"An error occurred in the splitContent: {e}")


# split_content_haystack()


def leer_csv(file_path):
    try:
        # Leer el CSV en un DataFrame
        df = pd.read_csv(file_path)
        return df
    except Exception as e:
        print(f"Error al leer el CSV: {e}")
        return None

def crear_txt(contenido, i):
    try:
        # Crear el archivo TXT y escribir el contenido
        nombre_archivo = "haystack-division/ContenidoCelda" + str(i) + ".txt"
        with open(nombre_archivo, 'w', encoding='UTF-8') as archivo:
            archivo.write(contenido)
        print(f"El archivo {nombre_archivo} se ha creado y el contenido se ha almacenado correctamente.")
        return nombre_archivo
    except Exception as e:
        print(f"Error al crear el archivo TXT: {e}")
        return None

def procesar_documento(file_path):
    try:
        # Convertir el archivo a documentos
        converter = TextConverter(remove_numeric_tables=True, valid_languages=["en"])
        doc_txt = converter.convert(file_path=file_path, meta=None)[0]
        return doc_txt
    except Exception as e:
        print(f"Error al procesar el documento: {e}")
        return None

def procesar_contenido(contenido):
    preprocessor = create_preprocessor_haystack("sentence", 5)
    docs_default = preprocessor.process([contenido])
    return docs_default

def procesar_fila(i, contenido, df):
    print(f"----- Línea {i} -----")
    nombre_archivo = crear_txt(contenido, i)
    if nombre_archivo is None:
        return None

    doc_txt = procesar_documento(nombre_archivo)
    if doc_txt is None:
        return None

    docs_default = procesar_contenido(doc_txt)
    
    fragments_list = []
    split_id_list = []
    tokens_list = []
    os.remove("haystack-division/ContenidoCelda" + str(i) + ".txt")

    for element in docs_default:
        document_dict = element.to_dict()

        for key, value in document_dict.items():
            if key == 'content':
                fragments_list.append(value)
                tokens_list.append(lenght_token(value,'google/flan-t5-base'))
            elif key == 'meta':
                for key_meta, value_meta in value.items():
                    split_id_list.append(value_meta)

    result = []
    for num, element in enumerate(fragments_list):
        result.append({
            'id': df.at[i, 'id'],
            'PageURL': df.at[i, 'PageURL'],
            'Title': df.at[i, 'Title'],
            'CreationDate': df.at[i, 'CreationDate'],
            'Seccion': df.at[i, 'Seccion'],
            'Subseccion': df.at[i, 'Subseccion'],
            'WikipageID': df.at[i, 'WikipageID'],
            'LastModified': df.at[i, 'LastModified'],
            'Contenido': df.at[i, 'Contenido'],
            'split': fragments_list[num],
            'split_id': split_id_list[num],
            'tokens': tokens_list[num]
        })

    return result
def split_content_haystack(file_path):
    df = leer_csv(file_path)
    if df is None:
        return

    df.insert(0, 'id', range(1, len(df) + 1))
    
    new_df = pd.DataFrame(columns=df.columns.tolist() + ['split', 'split_id', 'tokens'])

    tasks = []

    with ThreadPoolExecutor() as executor:
        for i, contenido in enumerate(df['Contenido']):
            task = executor.submit(procesar_fila, i, contenido, df)
            tasks.append(task)

    for task in tasks:
        result = task.result()
        if result is not None:
            # new_df = new_df.append(pd.DataFrame(result), ignore_index=True)
            for res in result:
                new_df.loc[len(new_df)] = res


    columns_to_drop = ['id', 'Contenido']
    new_df = new_df.drop(columns=columns_to_drop)

    new_df.to_csv('split_data.csv', index=False)
    print("DataFrame se ha guardado en 'split_data.csv'")

# Llamada a la función
start = time.time()
print(start)
split_content_haystack("test/dominio3Test.csv")
end = time.time()
print(end)
final = end - start
print("Se demoro un tiempo de ", final)
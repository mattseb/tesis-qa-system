
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
        # nombre_archivo = "haystack-division/ContenidoCelda" + str(i) + ".txt"
        nombre_archivo = "C:\\Users\\mateo\\Documents\\Universidad\\Tesis\\tesis-qa-system\\haystack-division\\ContenidoCelda" + str(i) + ".txt"
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
    preprocessor = create_preprocessor_haystack("sentence", 4)
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
    os.remove("C:\\Users\\mateo\\Documents\\Universidad\\Tesis\\tesis-qa-system\\haystack-division\\ContenidoCelda" + str(i) + ".txt")

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

    with ThreadPoolExecutor(max_workers=12) as executor:
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
# split_content_haystack("test/dominio3Test.csv")
split_content_haystack("C:\\Users\\mateo\\Documents\\Universidad\\Tesis\\tesis-qa-system\\test\\dominio3Test.csv")
end = time.time()
print(end)
final = end - start
print("Se demoro un tiempo de ", final)
    
from concurrent.futures import ProcessPoolExecutor
import os
import time
from haystack.nodes import TextConverter, PreProcessor
from haystack.nodes import PreProcessor
import pandas as pd
import numpy as np
from transformers import AutoTokenizer
from haystack.nodes import TextConverter, PreProcessor
import torch

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
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(device)
    try:
        tokenizer = AutoTokenizer.from_pretrained(llm, return_tensors='pt')  # Indicar que se usará PyTorch
        # tokenizer.model_max_length = 512
        tokens = tokenizer.encode(text, return_tensors='pt').to(device)  # Mover los tokens a la GPU
        return tokens.size(1)  # Obtener la longitud de los tokens
    except Exception as e:
        print(f"An error occurred in the lengthToken: {e}")


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
        nombre_archivo = ".\\haystack-division\\ContenidoCelda" + str(i) + ".txt"
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
    preprocessor = create_preprocessor_haystack("sentence", 6)
    docs_default = preprocessor.process([contenido])
    return docs_default


def get_max_tokens_llm(llm):
    tokenizer = AutoTokenizer.from_pretrained(llm)
    tokenizer.model_max_length = 512
    max_length = tokenizer.model_max_length
    return max_length


def procesar_fila(fila):
    fragments_list = []
    split_id_list = []
    tokens_list = []
    result = []

    print(f"----- Línea {fila['id']} -----")

    #column_value = row['Contenido']

    num_tokens = lenght_token(fila["Contenido"],'sequelbox/StellarBright')
    max_tokens = get_max_tokens_llm('sequelbox/StellarBright')

    if num_tokens <= max_tokens:
    
        print('===================INICIO=======================')
        print(f"Num tokens columns: {num_tokens} < {max_tokens}")
        print('===================FIN=======================')
        result.append({
            'id': fila['id'],
            'PageURL': fila['PageURL'],
            'Title': fila['Title'],
            'CreationDate': fila['CreationDate'],
            'Seccion': fila['Seccion'],
            'Subseccion': fila['Subseccion'],
            'WikipageID': fila['WikipageID'],
            'LastModified': fila['LastModified'],
            'Contenido': fila['Contenido'],
            'split': fila['Contenido'],
            'split_id': 0,
            'tokens': num_tokens
            })
        
    else:

        print('------------------------ DIVISION ------------------------')

        nombre_archivo = crear_txt(fila["Contenido"], fila["id"])
        if nombre_archivo is None:
            return None

        doc_txt = procesar_documento(nombre_archivo)
        if doc_txt is None:
            return None
        
        docs_default = procesar_contenido(doc_txt)

        os.remove("C:\\Users\\mateo\\Documents\\Universidad\\Tesis\\tesis-qa-system\\haystack-division\\ContenidoCelda" + str(fila["id"]) + ".txt")

        for element in docs_default:
            document_dict = element.to_dict()

            for key, value in document_dict.items():
                if key == 'content':
                    fragments_list.append(value)
                    tokens_list.append(lenght_token(value,'sequelbox/StellarBright'))
                elif key == 'meta':
                    for key_meta, value_meta in value.items():
                        split_id_list.append(value_meta)

        for num, element in enumerate(fragments_list):
            result.append({
                'id': fila['id'],
                'PageURL': fila['PageURL'],
                'Title': fila['Title'],
                'CreationDate': fila['CreationDate'],
                'Seccion': fila['Seccion'],
                'Subseccion': fila['Subseccion'],
                'WikipageID': fila['WikipageID'],
                'LastModified': fila['LastModified'],
                'Contenido': fila['Contenido'],
                'split': fragments_list[num],
                'split_id': split_id_list[num],
                'tokens': tokens_list[num]
            })

    return result   

def split_content_haystack(file_path):
    df = leer_csv(file_path)
    # df_chunks = list(chunked(df['Contenido'], len(df['Contenido']) // 24))  # Dividir el DataFrame en chunks

    if df is None:
        return

    df.insert(0, 'id', range(1, len(df) + 1))
    
    new_df = pd.DataFrame(columns=df.columns.tolist() + ['split', 'split_id', 'tokens'])

    tasks = []

    with ProcessPoolExecutor(max_workers=10) as executor:
        for inidce, fila in df.iterrows():
            task = executor.submit(procesar_fila, fila)
            tasks.append(task)
        print(len(tasks))


    # Recolectas los resultados de las tareas
    result = [task.result() for task in tasks]

    for res in result:
        for item in res:
            new_df.loc[len(new_df)] = item  # Agregar cada elemento al nuevo DataFrame

    new_df.to_csv('csv\\dominioFinalSpliteado7.csv', index=False)
    print("DataFrame se ha guardado en csv dominioFinalSpliteado7.csv")

if __name__ == '__main__':
    # Llamada a la función
    start = time.time()
    print(start)
    # split_content_haystack("test/dominio3Test.csv")
    split_content_haystack("csv\\dominioFinal.csv")
    end = time.time()
    print(end)
    final = end - start
    print("Se demoro un tiempo de ", final)
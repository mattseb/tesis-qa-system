from haystack.telemetry import tutorial_running
from haystack.nodes import TextConverter, PDFToTextConverter, DocxToTextConverter, PreProcessor
import logging
from haystack.nodes import PreProcessor
from langdetect import detect
import nltk
import pandas as pd
import numpy as np
from transformers import AutoTokenizer
from haystack.utils import convert_files_to_docs
from haystack.nodes import TextConverter, PDFToTextConverter, DocxToTextConverter, PreProcessor
from haystack.nodes import TextConverter, PDFToTextConverter, DocxToTextConverter, PreProcessor

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


def split_content_haystack():

    try:

        # Logs
        logging.basicConfig(format="%(levelname)s - %(name)s -  %(message)s", level=logging.WARNING)
        logging.getLogger("haystack").setLevel(logging.INFO)

        # Specify the file path to your CSV file
        file_path = "dominio3Test.csv"

        # Read the CSV file into a DataFrame
        df = pd.read_csv(file_path)

        # Display the DataFrame
        # df.head()

        # Extraer las primeras 'numero_de_filas_a_extraer' filas y almacenarlas en un nuevo DataFrame
        df_test = df.head(6)

        # Add a new column 'id' starting from 1 at the first position
        df_test.insert(0, 'id', range(1, len(df_test) + 1))

        for i in range(len(df_test)):

            # Especifica el índice de fila y la columna que deseas extraer
            fila = i  # Por ejemplo, extraeremos la fila 2 (índice 2)
            columna = 'Contenido'

            # Almacenar el contenido de la celda en una variable
            contenido = df_test.at[fila, columna]

            # Crear el archivo TXT y escribir el contenido
            nombre_archivo = "haystack-division/ContenidoCelda.txt"
            with open(nombre_archivo, 'w', encoding='UTF-8') as archivo:
                archivo.write(contenido)

            print(f"El archivo {nombre_archivo} se ha creado y el contenido se ha almacenado correctamente.")

            converter = TextConverter(remove_numeric_tables=True, valid_languages=["en"])
            doc_txt = converter.convert(file_path="haystack-division\ContenidoCelda.txt", meta=None)[0]

            doc_dir = 'haystack-division'

            all_docs = convert_files_to_docs(dir_path=doc_dir)

            preprocessor = create_preprocessor_haystack('sentence', 5)

            docs_default = preprocessor.process([doc_txt])
            
            print(f"n_docs_input: 1\nn_docs_output: {len(docs_default)}")

            # Define an array of strings
            fragments_list = []
            split_id_list = []
            tokens_list = [] 

            # Iterate through the array elements
            for element in docs_default:

                #print(element)

                document_dict = element.to_dict()

                #print(document_dict)

                for key, value in document_dict.items():

                    if (key == 'content'):
                        
                        #print(f'{key}, {value}')
                        fragments_list.append(value)
                        tokens_list.append(lenght_token(value,'google/flan-t5-base'))
                    
                    elif (key == 'meta'):

                        for key_meta, value_meta in value.items():

                            #print(f'{key_meta} === {value_meta}')
                            #print(value_meta)
                            split_id_list.append(value_meta)

            # Determine the number of rows to add based on the maximum length of the lists
            num_rows_to_add = max(len(fragments_list), len(split_id_list))

            # Create an empty DataFrame with the same columns as the original DataFrame
            new_columns = ['split', 'split_id', 'tokens']
            new_df = pd.DataFrame(columns=df_test.columns.tolist() + new_columns)

            # Fill the new columns with data from the lists
            new_df['split'] = fragments_list[:num_rows_to_add]
            new_df['split_id'] = split_id_list[:num_rows_to_add]
            new_df['tokens'] = split_id_list[:num_rows_to_add]

            # Fill the other columns with NaN values
            for col in new_df.columns:
                if col not in ['id'] + new_columns:
                    new_df[col] = np.nan

            value_id = i + 1

            id_value = value_id
            
            # Use the "id" column to fill the NaN values in the remaining columns
            for index, row in new_df.iterrows():
                original_row = df_test[df_test['id'] == id_value]
                
                if not original_row.empty:
                
                    for col in original_row.columns:
                        
                        if col not in ['id']:
                            
                            new_df.at[index, col] = original_row[col].values[0]

        # Drop one or more columns by specifying column names
        columns_to_drop = ['id', 'Contenido']
        new_df = new_df.drop(columns=columns_to_drop)

        # Save the DataFrame to a CSV file
        new_df.to_csv('split_data.csv', index=False)

        # Check that the file has been saved
        print("DataFrame has been saved to 'split_data.csv'")

    except Exception as e:
        print(f"An error occurred in the splitContent: {e}")
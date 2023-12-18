import time
from django.shortcuts import render
import json
import requests
from SPARQLWrapper import JSON, SPARQLWrapper
from django.shortcuts import render
from django.http import JsonResponse
from urllib.parse import quote
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
import wikipedia
import pandas as pd
from sentence_transformers import SentenceTransformer
from django.http import JsonResponse
import re
from concurrent.futures import ProcessPoolExecutor
import os
import time
from haystack.nodes import TextConverter, PreProcessor
from haystack.nodes import PreProcessor
import pandas as pd
from transformers import AutoTokenizer
from haystack.nodes import TextConverter, PreProcessor
import torch
from pymilvus import (
    connections,
    Collection,
)

import concurrent.futures
# Endpoint to make the query
endPoint = "https://dbpedia.org/sparql"
sparql = SPARQLWrapper(endPoint)

# Query endpoint and parse as JSON
def get_results(query):
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    return results

def index(request):
    # Get all the subdomains when the user clicks Send 
    if request.method == 'POST':
        sections = []
        selectedValues = request.POST.get('valores_seleccionados')
        selectedValues = json.loads(selectedValues)
        lista = []

        lista += get_links(selectedValues)
        print("Links relacionados  ", len(lista))
        with concurrent.futures.ProcessPoolExecutor(max_workers=30) as executor:
            futures = [executor.submit(get_page_sections, item['id_wiki']['value']) for item in lista]
            for num, future in enumerate(concurrent.futures.as_completed(futures)):
                sections += future.result()
        df = pd.DataFrame(sections, columns=['PageURL', 'Title', 'CreationDate', 'Seccion', 'Subseccion', 'Contenido', 'WikipageID', 'LastModified'])
        df.to_csv("csv\\dominioFinal.csv", index=False)
        tiempo_final = results(request, len(lista))

        #Subir datos a milvis
        inicio = time.time()
        ruta_del_csv = 'csv\\dominioFinalSpliteado.csv'

        df = pd.read_csv(ruta_del_csv)
        df = df

        connections.connect("default", host="localhost", port="19530")
        collection_name = 'prueba_final_2'
        collection = Collection(name=collection_name)

        retriever = SentenceTransformer("sentence-transformers/all-mpnet-base-v2", device='cuda')
        collection.load()

        for index, row in df.iterrows():
            print('==== ITER ========', index)
            emb = retriever.encode(row["split"]).tolist()
            meta = row.to_dict()
            to_upsert = {'embedding': emb, 'metadata': '"' + str(meta) + '"'}
            collection.insert(data=[to_upsert])
            print(collection.num_entities)
            print(collection.is_empty)
        fin = time.time()
        print("Se demoro un tiempo de ", fin - inicio, " segundos")
        return render (request, 'results.html', {'contador': len(lista),'tiempo_final': tiempo_final})    
    return render(request, 'index.html')

def results(request, contador):
    start = time.time()
    print(start)
    split_content_haystack("csv\\dominioFinal.csv")
    end = time.time()
    print(end)
    final = end - start
    print("Se demoro un tiempo de ", final)
    return (final)
# Obtain the primary search concepts
def get_search_concepts(request):
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        concepto = request.GET.get('term')
        tipo = request.GET.get('tipo')
        with open('global_config/filters.txt', 'r') as filters_file:
            data = filters_file.readline()
        data = data.split(";")
        data.pop()

        if concepto is not None and concepto != '':
            if tipo == '0':
                query = """
                SELECT DISTINCT ?r (COUNT(?concepts) AS ?conceptsCount)
                WHERE {
                ?r rdf:type skos:Concept; rdfs:label ?label.
                ?r ^skos:broader{1} ?concepts .
                FILTER(CONTAINS(str(?r), "%s"))
                FILTER(LANG(?label) = "en")
                }
                GROUP BY ?r
                HAVING(COUNT(?concepts) > 5)
                ORDER BY DESC(?conceptsCount)
                """ % (concepto)
            elif tipo == '1':
                filters = ""
                for filter_item in data:
                    filters += f"FILTER(!CONTAINS(str(?label), '{filter_item.strip()}'))\n"
                query = """
                    SELECT DISTINCT ?r
                    WHERE
                    {
                        ?r rdf:type skos:Concept; rdfs:label ?label.
                        ?c skos:broader ?r.
                        FILTER CONTAINS(?label, "%s").
                        FILTER (LANG(?label) = "en").
                        %s
                    }
                    GROUP BY ?r ?label HAVING (COUNT(*) > 2)
                    ORDER BY DESC(COUNT(?r))
                    """ % (concepto, filters)
            resultados = get_results(query)
            opciones = [
                {"id": item["r"]["value"], "text": item["r"]["value"]}
                for item in resultados["results"]["bindings"]
            ]
            return JsonResponse({"results": opciones}, safe=False)
        else:
            return JsonResponse({"results": []}, safe=False)
    else:
        return JsonResponse({"error": "Invalid request. Only AJAX requests are allowed."}, status=400)

def get_subdomains(request):
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        concepto = request.GET.get('selectedValue')
        nivel = request.GET.get('level')
        resultados = []
        nivel = request.GET.get('level') if request.GET.get('level') != None else '0' 
        if nivel == '0':
            dominiosSeleccionados = concepto.split("Category:", 1)[1]
            resultado = get_reource_query(dominiosSeleccionados, nivel)
            resultados.append(resultado)
        else:
            dominiosSeleccionados = request.POST.getlist('subdominios')
            dominiosSeleccionados = request.GET.getlist('selectedValue[]')
            for dominio in dominiosSeleccionados:
                dominio = dominio.split(":")[-1]
                resultado = get_reource_query(dominio, nivel)
                resultados.append(resultado)

        if resultados:
            lista = []

            for resultado in resultados:
                for item in resultado:
                    url = item["c1"]["value"]
                    clave = url.split(":")[-1]
                    lista.append(clave)
            json_data = json.dumps(lista)
            return JsonResponse(json_data, safe=False)

    return JsonResponse({'error': 'No se pudo procesar la solicitud'})

def get_reource_query(resource, level):
    resource = re.sub(r"([,()/.'])", r'\\\1', resource)

    with open('global_config/filters.txt', 'r') as filters_file:
        data = filters_file.readline()
        data = data.split(";")
        data.pop()

        filters = ""
        for filter_item in data:
            filters += f"FILTER(!CONTAINS(str(?label), '{filter_item.strip()}'))\n"
    query = """
    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX dct: <http://purl.org/dc/terms/>

    select distinct ?level ?r ?c1
        {
            {VALUES (?r ?level) {(dbc:%s + %s)}
                ?r ^skos:broader{1} ?c1.
                ?c1 rdfs:label ?label.
            FILTER(LANG(?label) = "en")
            %s           
        }
    
    }    
    """ %(resource,str(level), filters)

    resultados = get_results(query)
    return resultados["results"]["bindings"]

def modify_configurations(request):
    with open("global_config/filters.txt", 'r') as file:
        data = file.read()

    data_list = data.split(';')
    data_list.pop()
    return render(request, 'configurations.html', {'data_list': data_list})

def add_filter(request, filter_value, filter_action):
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        if filter_value:
            if filter_action == 'add':
                with open("global_config/filters.txt", 'a') as filters_file:
                    filters_file.write(filter_value)
                    filters_file.write(";")
                return JsonResponse({'message': 'Filtro agregado exitosamente.'})
            elif filter_action == 'delete':
                filter_value = filter_value + ";"
                with open("global_config/filters.txt", 'r') as filters_file:
                    data = filters_file.read()
                data = data.replace(filter_value, '')
                with open("global_config/filters.txt", 'w') as filters_file:
                    filters_file.write(data)
                return JsonResponse({'message': 'Filtro eliminado exitosamente.'})
    return JsonResponse({'error': 'Error al agregar el filtro.'}, status=400)

# Get the links of all the selected values
def get_links(resources):
    batch_size = 50  # Tamaño del lote
    results = []  # Almacenar los resultados de todos los lotes

    for i in range(0, len(resources), batch_size):
        batch = resources[i:i + batch_size]  # Obtener un lote de recursos
        batch = [quote(resource) for resource in batch]  # Citar los recursos
        
        values_clause = " ".join(["(dbc:%s)" % resource.replace("/", r"\/") if "/" in resource else "(dbc:%s)" % resource for resource in batch])

        query = """
        PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX dct: <http://purl.org/dc/terms/>
        PREFIX dbo: <http://dbpedia.org/ontology/>

        SELECT DISTINCT ?wikipedia_resource ?id_wiki
        WHERE {
            VALUES (?r) {%s}
       
            ?subject dcterms:subject ?r.
            ?subject foaf:isPrimaryTopicOf ?wikipedia_resource.
            ?subject dbo:wikiPageID ?id_wiki.
        }   
        """ % (values_clause)

        # Llamar a la función get_results para obtener los resultados del lote actual
        resultados = get_results(query)
        
        # Agregar los resultados del lote actual a la lista de resultados
        results.extend(resultados["results"]["bindings"])

    return results

def get_page_sections(page_id, language='en'):
    try:
        page = wikipedia.page(pageid=page_id, auto_suggest=False)
        title = page.title
        page_url = page.url
        wikipageid = page.pageid
        page_id = wikipageid

        # Fetch the revision history using the Wikipedia API
        url = f"https://en.wikipedia.org/w/api.php?action=query&prop=revisions&rvprop=timestamp&format=json&pageids={page_id}"
        response = requests.get(url)
        data = json.loads(response.text)

        # Extract the timestamp of the latest revision
        latest_rev = data['query']['pages'][str(page_id)]['revisions'][0]
        creation_rev = data['query']['pages'][str(page_id)]['revisions'][-1]
        creation_date = creation_rev['timestamp']
        last_modified = latest_rev['timestamp']
    except:
        sections = []
        return sections

    wikipedia.set_lang(language)
    content = page.content.split('\n')

    sections = []
    current_section = None
    sub_section = None
    exclude_sections = [" See also ", " References ", " External links "]
    filter_content = [element for element in content if element != '']
    for line in filter_content:
        if(line != ''):
            line = line.strip()
        else:
            continue
        if line.startswith("===") and line.endswith("===") and line not in exclude_sections:
            sub_section = line.strip("=")
            # sections.append((page_url, title, creation_date, current_section, sub_section, '', wikipageid, last_modified))
        elif line.startswith("==") and line.endswith("=="):
            section = line.strip("=")
            current_section = section
        else:
            if current_section not in exclude_sections:
                if sections:
                    if sections[-1][4] == sub_section and sections[-1][3] == current_section:
                        sections[-1] = (page_url, title, creation_date, sections[-1][3], sections[-1][4], sections[-1][5] + " " + line, wikipageid, last_modified)
                    else:
                        sections.append((page_url, title, creation_date, current_section, sub_section, line, wikipageid, last_modified))
                else:
                    sections.append((page_url, title, creation_date, current_section, sub_section, line, wikipageid, last_modified))
            elif current_section == None:
                sections.append((page_url, title, creation_date, None, None, line, wikipageid, last_modified))            
    return sections

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

    if df is None:
        return

    df.insert(0, 'id', range(1, len(df) + 1))
    
    new_df = pd.DataFrame(columns=df.columns.tolist() + ['split', 'split_id', 'tokens'])

    tasks = []

    with ProcessPoolExecutor(max_workers=25) as executor:
        for inidce, fila in df.iterrows():
            task = executor.submit(procesar_fila, fila)
            tasks.append(task)
        print(len(tasks))


    # Recolectas los resultados de las tareas
    result = [task.result() for task in tasks]

    for res in result:
        for item in res:
            new_df.loc[len(new_df)] = item  # Agregar cada elemento al nuevo DataFrame

    new_df.to_csv('csv\\dominioFinalSpliteado.csv', index=False)
    print("DataFrame se ha guardado en 'dominioFinalSpliteado.csv'")
import time
from django.shortcuts import render
import json
from SPARQLWrapper import JSON, SPARQLWrapper
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from urllib.parse import quote
from django.contrib.auth.decorators import login_required
import xml.etree.ElementTree as ET
from django.http import JsonResponse
import wikipedia
import pandas as pd
from sentence_transformers import SentenceTransformer
from django.http import JsonResponse
from pymilvus import (
    connections,
    utility,
    FieldSchema,
    CollectionSchema,
    DataType,
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
    print((results['results']['bindings']))
    return results

def index(request):
    # Get all the subdomains
    if request.method == 'POST':
        sections = []
        valoresSeleccionados = request.POST.get('valores_seleccionados')
        valoresSeleccionados = json.loads(valoresSeleccionados)
        lista = []

        lista += get_links(valoresSeleccionados)
        print("Links relacionados  ", len(lista))
        tiempo_inicio = time.time()
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [executor.submit(get_page_sections, item['id_wiki']['value']) for item in lista]
            for num, future in enumerate(concurrent.futures.as_completed(futures)):
                print(num)
                sections += future.result()
        tiempo_fin = time.time()
        print("Se demoro un tiempo de ", str(tiempo_fin - tiempo_inicio))
        df = pd.DataFrame(sections, columns=['Seccion', 'Subseccion', 'Contenido', 'WikipageID', 'LastModified'])
        new_rows = []

        for index, row in df.iterrows():
            content = row['Contenido']
            section = row['Seccion']
            subsection = row['Subseccion']
            wikipageid = row['WikipageID']
            lastModified = row['LastModified'] 
            secciones = subdividir_texto(content)
            
            for seccion in secciones:
                new_rows.append((section, subsection, seccion, wikipageid, lastModified))

        df = pd.DataFrame(new_rows, columns=['Seccion', 'Subseccion', 'Contenido', 'WikipageID', 'LastModified'])
        df.to_csv("dominio3.csv", index=False)

        # connections.connect("default", host="localhost", port="19530")
        # collection_name = 'my_collection'
        # din = 768

        # fields=[
        #     FieldSchema(name='id', dtype=DataType.INT64, is_primary=True, auto_id=True),
        #     FieldSchema(name='embedding', dtype=DataType.FLOAT_VECTOR, dim=din),
        #     FieldSchema(name='metadata', dtype=DataType.VARCHAR, max_length=2560)
        # ]
        
        # schema = CollectionSchema(fields)
        # collection = Collection(name=collection_name, schema=schema)

        # retriever = SentenceTransformer("flax-sentence-embeddings/all_datasets_v3_mpnet-base", device='cpu')
        # batch_size = 64
        # with concurrent.futures.ThreadPoolExecutor() as executor:
        #     to_upsert = []
        #     for i in (range(0, len(df), batch_size)):
        #         i_end = min(i+batch_size, len(df))
        #         batch = df.iloc[i:i_end]
        #         futures = []
        #         for j in range(len(batch)):
        #             future = executor.submit(retriever.encode, batch.iloc[j]["Contenido"])
        #             futures.append(future)
        #         for future, meta in zip(futures, batch.to_dict(orient="records")):
        #             emb = future.result().tolist()
        #             to_upsert.append({'embedding': emb, 'metadata': str(meta)})
        #         collection.insert(to_upsert)
        #         print(collection.num_entities)
        return render(request, 'content.html', {'contador': len(lista)})
    return render(request, 'index.html')

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
    if "," in resource:
        resource = resource.replace(",",r"\,")

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

# Get the links of al the selected values
def get_links(resources):
    batch_size = 1000  # Tamaño del lote
    results = []  # Almacenar los resultados de todos los lotes

    for i in range(0, len(resources), batch_size):
        batch = resources[i:i + batch_size]  # Obtener un lote de recursos
        batch = [quote(resource) for resource in batch]  # Citar los recursos

        values_clause = " ".join(["(dbc:%s)" % resource for resource in batch])
        
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
# PRUEBAAAAA    
# def get_page_sections(page_id, language='en'):
#     print(page_id)
#     try:
#         title = wikipedia.page(pageid=page_id, auto_suggest=False).title
#     except:
#         sections = []
#         return sections
#     wikipedia.set_lang(language)
#     page = wikipedia.page(title, auto_suggest=False)
#     content = page.content.split('\n')

#     sections = []
#     current_section = None
#     exclude_sections = ["== See also ==", "== References ==", "== External links =="]
#     for line in content:
#         if(line):
#             line = line.strip()
#         if line.startswith("===") and line.endswith("===") and line not in exclude_sections:
#             sub_section = line.strip("=")
#             sections.append((current_section, sub_section, ""))
#         elif line.startswith("==") and line.endswith("==") and line not in exclude_sections:
#             section = line.strip("=")
#             current_section = section
#         else:
#             if current_section and line not in exclude_sections:
#                 if sections:
#                     sections[-1] = (sections[-1][0], sections[-1][1], sections[-1][2] + " " + line)
#                 else:
#                     sections.append((current_section, None, line))
#     return sections

def get_page_sections(page_id, language='en'):
    import requests
    import json
    print(page_id)
    try:
        page = wikipedia.page(pageid=page_id, auto_suggest=False)
        title = page.title
        wikipageid = page.pageid
        # Define the page ID
        page_id = wikipageid

        # Fetch the revision history using the Wikipedia API
        url = f"https://en.wikipedia.org/w/api.php?action=query&prop=revisions&rvprop=timestamp&format=json&pageids={page_id}"
        response = requests.get(url)
        data = json.loads(response.text)

        # Extract the timestamp of the latest revision
        latest_rev = data['query']['pages'][str(page_id)]['revisions'][0]
        last_modified = latest_rev['timestamp']
    except:
        sections = []
        return sections

    wikipedia.set_lang(language)
    content = page.content.split('\n')

    sections = []
    current_section = None
    exclude_sections = ["== See also ==", "== References ==", "== External links =="]
    for line in content:
        if(line):
            line = line.strip()
        if line.startswith("===") and line.endswith("===") and line not in exclude_sections:
            sub_section = line.strip("=")
            sections.append((current_section, sub_section, "", wikipageid, last_modified))
        elif line.startswith("==") and line.endswith("==") and line not in exclude_sections:
            section = line.strip("=")
            current_section = section
        else:
            if current_section and line not in exclude_sections:
                if sections:
                    sections[-1] = (sections[-1][0], sections[-1][1], sections[-1][2] + " " + line, wikipageid, last_modified)
                else:
                    sections.append((current_section, None, line, wikipageid, last_modified))
    return sections


def subdividir_texto(texto, max_palabras=100):
    secciones = []
    palabras = texto.split()
    inicio = 0
# 387
    while inicio < len(palabras):
        fin = inicio + max_palabras
        if 'Aerobic' in palabras[inicio]:
            print("holaaaa")
        while fin > inicio and fin < len(palabras) and palabras[fin][-1] != '.' and '.' not in palabras[fin]:
            fin -= 1
        seccion = ' '.join(palabras[inicio:fin + 1])
        if len(seccion.split()) <= 5:
            fin += 100
            seccion = ' '.join(palabras[inicio:fin + 1])
        secciones.append(seccion)
        inicio = fin + 1

    return secciones
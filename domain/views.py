from django.shortcuts import render
import json
from SPARQLWrapper import JSON, SPARQLWrapper
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from urllib.parse import quote
from django.contrib.auth.decorators import login_required
from .decorators import allowed_users
from django.contrib.auth.decorators import login_required
import xml.etree.ElementTree as ET
from django.http import JsonResponse
import wikipedia
import pandas as pd

endPoint = "https://dbpedia.org/sparql"
sparql = SPARQLWrapper(endPoint)

def get_results(query):
    sparql.setReturnFormat(JSON)
    sparql.setQuery(query)
    results = sparql.query().convert()
    return results

@csrf_exempt
@login_required(login_url='login')
@allowed_users(allowed_roles=['admin'])
def index(request):
    if request.method == 'POST':
        sections = []
        valoresSeleccionados = request.POST.get('valores_seleccionados')
        valoresSeleccionados = json.loads(valoresSeleccionados)
        lista = []
        for valor in valoresSeleccionados:
            lista += get_links(valor)
            print(valor)
        print("ELelemtos ", len(lista))
        for item in lista:
            sections += get_page_sections(item['id_wiki']['value'])
        df = pd.DataFrame(sections, columns=['Seccion', 'Subseccion', 'Contenido'])
        
        new_rows = []

        for index, row in df.iterrows():
            content = row['Contenido']
            section = row['Seccion']
            subsection = row['Subseccion']
            
            secciones = subdividir_texto(content)
            
            for seccion in secciones:
                new_rows.append((section, subsection, seccion))

        df_new = pd.DataFrame(new_rows, columns=['Seccion', 'Subseccion', 'Contenido'])
        df_new.to_csv("dominio3.csv", index=False)

        return render(request, 'content.html', {'contador': len(lista)})
    return render(request, 'index.html')

def get_search_concepts(request):
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        concepto = request.GET.get('term')
        tipo = request.GET.get('tipo')
        with open('global_config/filters.txt', 'r') as filters_file:
            data = filters_file.readline()
        data = data.split(";")
        data.pop()

        filters = ""
        for filter_item in data:
            filters += f"FILTER(!CONTAINS(str(?label), '{filter_item.strip()}'))\n"

        if concepto is not None and concepto != '':
            if tipo == '0':
                query = """
                SELECT DISTINCT ?r (COUNT(?concepts) AS ?conceptsCount)
                WHERE {
                ?r rdf:type skos:Concept; rdfs:label ?label.
                ?r ^skos:broader{1} ?concepts .
                FILTER(CONTAINS(str(?r), "%s"))
                FILTER(LANG(?label) = "en")
                %s
                }
                GROUP BY ?r
                HAVING(COUNT(?concepts) > 5)
                ORDER BY DESC(?conceptsCount)
                """ % (concepto, filters)
            elif tipo == '1':    
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
            print(query)
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



def get_links(resource):
    resource = quote(resource)
    query = """
    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX dct: <http://purl.org/dc/terms/>
    PREFIX dbo: <http://dbpedia.org/ontology/>

    SELECT DISTINCT ?wikipedia_resource ?id_wiki
    WHERE
    {
        {VALUES (?r) {(dbc:%s)}
   
        ?subject dcterms:subject ?r.
        ?subject foaf:isPrimaryTopicOf ?wikipedia_resource.
        ?subject dbo:wikiPageID ?id_wiki.
        }
    }   
    """ % (resource)

    resultados = get_results(query)
    return resultados["results"]["bindings"]


# PRUEBAAAAA
def get_page_sections(page_id, language='en'):
    print(page_id)
    try:
        title = wikipedia.page(pageid=page_id, auto_suggest=False).title
    except:
        sections = []
        return sections
    wikipedia.set_lang(language)
    page = wikipedia.page(title, auto_suggest=False)
    content = page.content.split('\n')

    sections = []
    current_section = None
    exclude_sections = ["== See also ==", "== References ==", "== External links =="]
    for line in content:
        if(line):
            line = line.strip()
        if line.startswith("===") and line.endswith("===") and line not in exclude_sections:
            sub_section = line.strip("=")
            sections.append((current_section, sub_section, ""))
        elif line.startswith("==") and line.endswith("==") and line not in exclude_sections:
            section = line.strip("=")
            current_section = section
        else:
            if current_section and line not in exclude_sections:
                if sections:
                    sections[-1] = (sections[-1][0], sections[-1][1], sections[-1][2] + " " + line)
                else:
                    sections.append((current_section, None, line))
    return sections

def subdividir_texto(texto, max_palabras=100):
    secciones = []
    palabras = texto.split()
    inicio = 0

    while inicio < len(palabras):
        fin = inicio + max_palabras
        while fin > inicio and fin < len(palabras) and palabras[fin][-1] != '.':
            fin -= 1

        seccion = ' '.join(palabras[inicio:fin + 1])
        secciones.append(seccion)
        inicio = fin + 1

    return secciones
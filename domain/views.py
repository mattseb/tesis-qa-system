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

endPoint = "https://dbpedia.org/sparql"
sparql = SPARQLWrapper(endPoint)

def get_results(query):
    sparql.setReturnFormat(JSON)
    sparql.setQuery(query)
    results = sparql.query().convert()
    return results

@csrf_exempt
def index(request):
    if request.method == 'POST':
        valoresSeleccionados = request.POST.get('valores_seleccionados')
        print(valoresSeleccionados)
    return render(request, 'index.html')

def loginPage(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

def get_subdomains(request):
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        print(request.GET)
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

def get_reource_query(resource, level):
    if "," in resource:
        resource = resource.replace(",",r"\,")
    query = """
    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX dct: <http://purl.org/dc/terms/>

    select distinct ?level ?r ?c1
        {
            {VALUES (?r ?level) {(dbc:%s + %s)}
                ?r ^skos:broader{1} ?c1.

            FILTER (!regex(?c1, "lists"))
        }
    
    }    
    """ %(resource,str(level))

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
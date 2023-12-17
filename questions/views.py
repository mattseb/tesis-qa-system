import json
from django.http import JsonResponse
from sentence_transformers import SentenceTransformer
import ast
from pymilvus import (
    connections,
    utility,
    Collection,
)
from django.shortcuts import render
from huggingface_hub import hf_hub_download
from llama_cpp import Llama
from transformers import AutoTokenizer

# Create your views here.
def index(request):
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        question = request.POST['question']

        connections.connect("default", host="localhost", port="19530")
        collection_name = 'prueba_final_2'


        collection = Collection(name=collection_name)
        collection.load()

        model = SentenceTransformer("sentence-transformers/all-mpnet-base-v2", device='cpu')

        index_params = {
            'metric_type': 'L2',
            'index_type': 'IVF_FLAT', 
            'params': {'nlist': 16384}
        }

        print(utility.index_building_progress("my_collection"))

        question_vector = model.encode([question])[0].tolist()

        search_params = {'nprobe': 1}
        search_result = collection.search(
            data=[question_vector], 
            anns_field='embedding', 
            param=search_params, 
            limit=1,
            output_fields=['metadata'],
        )


        hits = [result[0] for result in search_result]
        answers = [hit.entity.get('metadata') for hit in hits ]
        answers_processed = []
        for answer in answers:
            answer = answer.replace('nan', 'None')
            answers_processed.append(ast.literal_eval(answer))

        answer_obj = ast.literal_eval(answers_processed[0])
        raw_answer = answer_obj['split']
        print("Answer:", answer_obj['split'])

        #Prompt (Pregunta al modelo)
        prompt = question
        #Context
        context = raw_answer
        topic = 'Contamination'
        #template
        prompt_template=f'''[INST] <<SYS>>
    You are a helpful, respectful and honest assistant. Always answer as helpfully as possible, while being safe. Your answers should not include any harmful, unethical, racist, sexist, toxic, dangerous, or illegal content. Please ensure that your responses are socially unbiased and positive in nature. If a question does not make any sense, or is not factually coherent, explain why instead of answering something not correct. If you don't know the answer to a question, please don't share false information.
    also you are a {topic} expert, answer questions about {topic} as best as you can with this context {context}.
    </SYS>>\n{prompt}[/INST]'''
        max_tokens=100000
        temperature=0.5
        top_p=0.95
        repeat_penalty=1.2
        top_k=150
        echo=True

        model_name_or_path = "TheBloke/Llama-2-13B-chat-GGML"
        model_basename = "llama-2-13b-chat.ggmlv3.q5_1.bin" # the model is in bin format

        model_path = hf_hub_download(repo_id=model_name_or_path, filename=model_basename)
        
        respuesta = llama_with_context(model_path, topic, prompt, context, prompt_template, max_tokens,  temperature, top_p, repeat_penalty, top_k, echo)
        print(respuesta)
        
        json_data = json.dumps(respuesta)
        return JsonResponse(json_data, safe=False)
    return render(request, 'index2.html')

def llama_with_context(model_path_value,topic_value, prompt_value,
                       context_value, prompt_template_value, max_tokens_value,
                       temperature_value, top_p_value, repeat_penalty_value,
                       top_k_value, echo_value):
    lcpp_llm = None
    lcpp_llm = Llama(
        model_path=model_path_value,
        n_threads=8, # CPU cores
        n_batch=1024, # Should be between 1 and n_ctx, consider the amount of VRAM in your GPU.
        n_gpu_layers=32 # Change this value based on your model and your GPU VRAM pool.
        )

    #See the number of layers in GPU
    #lcpp_llm.params.n_gpu_layers

    topic = topic_value

    prompt = prompt_value

    context = context_value

    prompt_template = prompt_template_value

    #print(type(prompt_template))

    response=lcpp_llm(prompt=prompt_template,
                    max_tokens= max_tokens_value,
                    temperature= temperature_value,
                    top_p=top_p_value,
                    repeat_penalty=repeat_penalty_value,
                    top_k = top_k_value,
                    echo= echo_value)

    respuesta = response["choices"][0]["text"].split("[/INST]")[1]

    return respuesta
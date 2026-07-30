import json
import ssl
import urllib.request
from datetime import datetime

from env.list_models import API_URL, TOKEN

IS_ER_API = True

def call_json_api(url, token, print_json=False):
    ssl_context = None
    if 'localhost' in url:
        ssl_context = ssl._create_unverified_context()

    headers = {
        'User-Agent': 'Mozilla/5.0',
        'Authorization': f'Bearer {token}'
    }
    print(f'REQUEST {url}')
    request = urllib.request.Request(url, headers=headers)
    response = urllib.request.urlopen(request, context=ssl_context)
    res_str  = response.read().decode('utf-8')
    ret = json.loads(res_str)

    if print_json:
        print(json.dumps(ret, indent=2))

    return ret

print(datetime.now().isoformat())

if IS_ER_API:
    # openai/er api
    res_dic = call_json_api(f"{API_URL}/v1/models", TOKEN)

    for model in res_dic:
        vision_status = 'VISION' if model["supports_vision"] else ''
        print(f'{model["name"]:<15} {model["provider"]:<20} {model["backend_model"]:<30} {str(int(model["context_window"]/1024)):>6}k {vision_status:<6}')
else:
    # litellm api (used to be suuported by ER LLM platform)
    res_dic = call_json_api(f"{API_URL}/model/info", TOKEN)

    for model in res_dic['data']:
        params = model["litellm_params"]
        info = model["model_info"]
        vision_status = 'VISION' if info["supports_vision"] else ''
        print(f'{model["model_name"]:<15} {params["model"]:<30} {info["backend_model"]:<25} {str(info["max_tokens"]):>7} {vision_status:<6}')

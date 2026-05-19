import urllib.request
import ssl
import json
from env.litellmodels import API_URL, TOKEN

ssl_context = ssl._create_unverified_context()

url = f"{API_URL}/model/info"
headers = {
    'User-Agent': 'Mozilla/5.0',
    'Authorization': f'Bearer {TOKEN}'
}
request = urllib.request.Request(url, headers=headers)
response = urllib.request.urlopen(request, context=ssl_context)
res_str  = response.read().decode('utf-8')
res_dic = json.loads(res_str)

#print(json.dumps(res_dic, indent=2))   

for model in res_dic['data']:
    params = model["litellm_params"]
    info = model["model_info"]
    vision_status = 'VISION' if info["supports_vision"] else ''
    print(f'{model["model_name"]:<15} {params["model"]:<30} {info["backend_model"]:<25} {str(info["max_tokens"]):>7} {vision_status:<6}')

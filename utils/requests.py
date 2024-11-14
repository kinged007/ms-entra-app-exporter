import requests
from loguru import logger as log

def server_request(endpoint, method="GET", data={}, headers={}, params={}, api_key=None, host=None):
    
    try:
        # print("SERVER REQUEST", endpoint, method, data, headers, params, api_key, host)
        
        endpoint = endpoint
        if host: 
            host = host.strip("/")
            endpoint = f"{host}/{endpoint.strip('/')}"
            
        method = method.upper()
        
        if not headers: headers = {}
        
        if api_key:
            headers.update({
                "Authorization": f"Bearer {api_key}"
            })
        
        if method == "GET":
            res = requests.get(endpoint, headers=headers, params=params)
        elif method == "POST":
            res = requests.post(endpoint, headers=headers, json=data, params=params)
        elif method == "PUT":
            res = requests.put(endpoint, headers=headers, json=data, params=params)
        elif method == "DELETE":
            res = requests.delete(endpoint, headers=headers, json=data, params=params)
        elif method == "PATCH":
            res = requests.patch(endpoint, headers=headers, json=data, params=params)
        else:
            raise Exception("Invalid method")
        return res
    
    except Exception as e:
        log.error(e)
    
    return None

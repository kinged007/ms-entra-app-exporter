from loguru import logger as log

import msal
from os import path
import requests
from .requests import server_request
import getpass
from rich.progress import track
import time

from urllib.parse import urlencode

def tenant_request(endpoint, method="GET", data=None, headers=None, params=None, api_key=None, host = None):
    # debug: print url request with params url encoded
    # print(f"DEBUG:tenant_request | URL: {endpoint}?{urlencode(params)}")
    
    req = server_request(endpoint, method=method, data=data, headers=headers, params=params, api_key=api_key, host=host)
    # print(req)
    # print(req.headers)
    if req and req.status_code == 200:
        return req.json()
    # print(req.status_code, req.text)
    log.error(f"Failed to get data from tenant: {req.status_code} {req.text}")
    # raise Exception(f"Failed to get data from tenant: {req.status_code} {req.text}")
    return None

def get_access_token(config: dict):
    # Determine the client credentials to use
    if "secret" in config and config["secret"]:
        client_credential = config["secret"]
    elif "private_key" in config and "thumbprint" in config and config["private_key"]:
        # Prompt for passphrase if using certificate-based authentication
        passphrase = getpass.getpass("Enter passphrase for the private key: ") or None
        if "BEGIN ENCRYPTED PRIVATE KEY" in config["private_key"]:
            _pk = config["private_key"]
        elif path.exists(config["private_key"]):
            _pk = open(config["private_key"]).read()
        else:
            raise ValueError("Private key file or key not found")
        
        client_credential = {
            "private_key": _pk,
            "thumbprint": str(config["thumbprint"]).replace(":", "").lower(),
            "passphrase": passphrase,

        }
    else:
        raise ValueError("Either 'secret' or 'private_key' and 'thumbprint' must be provided in the config.")

    # Initialize the MSAL Confidential Client Application
    source_app = msal.ConfidentialClientApplication(
        config["client_id"],
        authority=config.get("authority"),
        client_credential=client_credential,
    )
    
    result = None
    
    try:
        # Try to acquire a token silently first (cached tokens)
        result = source_app.acquire_token_silent(config["scope"], account=None)
    except Exception as e:
        print("Failed to acquire token silently:", e)
        
    try:
        # If no cached token, request a new one
        if not result:
            result = source_app.acquire_token_for_client(scopes=config["scope"])
    except Exception as e:
        print("Failed to acquire token for client:", e)

    # Check if we successfully acquired an access token
    if result and "access_token" in result:
        return result['access_token']
    else:
        # If we failed, print error details for troubleshooting
        print("Failed to acquire token:", result.get("error"), result.get("error_description"))
        return None


def get_user_access_token(config: dict):
    # Initialize MSAL Public Client Application for user-based authentication
    app = msal.PublicClientApplication(
        client_id=config["client_id"],
        authority=config.get("authority"),
    )

    # Try to acquire a token silently (from cache) if the user has logged in before
    accounts = app.get_accounts()
    result = None
    if accounts:
        # Use the first account found in cache
        result = app.acquire_token_silent(config["scope"], account=accounts[0])

    # If no cached token is available, request a new token interactively
    if not result:
        result = app.acquire_token_interactive(scopes=config["scope"])

    # Check if the token acquisition was successful
    if "access_token" in result:
        return result["access_token"]
    else:
        # Print any errors encountered during the authentication process
        print("Failed to acquire token:", result.get("error"), result.get("error_description"))
        return None


def count_apps( params: dict = {}, baseurl: str = "https://graph.microsoft.com", access_token: str = None):
    if '$search' in params: params["$search"] = params["$search"] if params["$search"].startswith("'") or params["$search"].startswith('"') else f'"{params["$search"]}"'
    # if not params['$search']: params.pop('$search')
    
    _count = tenant_request("/v1.0/applications/$count" , 
        headers={"ConsistencyLevel": "eventual"}, 
        params=params, 
        api_key=access_token, 
        host=baseurl.replace("/v1.0", "")
    )
    return _count


def get_apps(params: dict = {}, baseurl: str = "https://graph.microsoft.com", access_token: str = None, max_results: int = 999):
    if '$search' in params: params["$search"] = params["$search"] if params["$search"].startswith("'") or params["$search"].startswith('"') else f'"{params["$search"]}"'
    # if not params['$search']: params.pop('$search')
    
    count = count_apps(params, baseurl, access_token)
    params["$top"] = max_results
    endpoint = baseurl.replace("/v1.0","").strip('/') + "/v1.0/applications"
    graph_data = []
    skip = 0
    
    for i in track(range(0, count, max_results), description="Fetching data..."):
        
        data = tenant_request( endpoint, 
            headers={"ConsistencyLevel": "eventual"}, 
            params=params, 
            api_key=access_token, 
        )
        # st.write(params)
        # st.json(data)
        if data:
            graph_data.extend(data["value"])
            if "@odata.nextLink" in data:
                skip += max_results
                params = {}
                endpoint = data["@odata.nextLink"]
            else:
                break
        else:
            break
        time.sleep(1)
        
    return graph_data

def count_service_principals( params: dict = {}, baseurl: str = "https://graph.microsoft.com", access_token: str = None):
    if '$search' in params: params["$search"] = params["$search"] if params["$search"].startswith("'") or params["$search"].startswith('"') else f'"{params["$search"]}"'
    # if not params['$search']: params.pop('$search')
    
    _count = tenant_request("/v1.0/servicePrincipals/$count" , 
        headers={"ConsistencyLevel": "eventual"}, 
        params=params, 
        api_key=access_token, 
        host=baseurl.replace("/v1.0", "")
    )
    return _count


def get_service_principals(params: dict = {}, baseurl: str = "https://graph.microsoft.com", access_token: str = None, max_results: int = 999):
    if '$search' in params: params["$search"] = params["$search"] if params["$search"].startswith("'") or params["$search"].startswith('"') else f'"{params["$search"]}"'
    # if not params['$search']: params.pop('$search')
    
    count = count_service_principals(params, baseurl, access_token)
    params["$top"] = max_results
    endpoint = baseurl.replace("/v1.0","").strip('/') + "/v1.0/servicePrincipals"
    graph_data = []
    skip = 0
    # _progress_bar = st.progress(skip/count, text="Fetching data...")
    
    for i in track(range(0, count, max_results), description="Fetching data..."):
        
        data = tenant_request( endpoint, 
            headers={"ConsistencyLevel": "eventual"}, 
            params=params, 
            api_key=access_token, 
        )
        # st.write(params)
        # st.json(data)
        if data:
            graph_data.extend(data["value"])
            # _progress_bar.progress(skip/st.session_state[f'{_query_key}_total'], text="Fetching data...")
            if "@odata.nextLink" in data:
                skip += max_results
                params = {}
                endpoint = data["@odata.nextLink"]
            else:
                break
        else:
            break
        time.sleep(1)
    return graph_data

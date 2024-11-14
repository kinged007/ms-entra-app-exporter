from rich import print
from rich.console import Console
console = Console()

import time

from schema.application import ApplicationModel
from schema.servicePrincipal import ServicePrincipalModel
from utils.dict import dict_walk

def sanitize_app_data(apps: list, app_type: str = 'Application') -> list:
    """
    Method that will loop through a list of apps and sanitize the data against the Application schema
    
    """
    
    santized_apps = []
    
    for app in apps:
        
        redact_value(app, app.get('appId',''), "__APPID_REDACTED__")
        
        if app_type == 'Application':
            santized_apps.append(ApplicationModel(**app))
        else:
            santized_apps.append(ServicePrincipalModel(**app))
        
    
    return santized_apps


# def view_schema():
#     """
#     Method that will display the schema for the Application and Service Principal models
#     """
#     console.rule("[bold red]Application Schema[/bold red]", style="bold magenta")
#     time.sleep(1)
#     a = ApplicationModel(displayName="Not a real app")
#     console.print(a)
#     time.sleep(2)


def redact_value(data:dict, search:str, replace:str) -> dict:
    """
    Method that will redact the AppId from the ApplicationModel and all parameters
    """
    def redact_appid_callback(key, value):
        if isinstance(value,str) and search in value:
            return value.replace(search, replace)
        return value
    
    dict_walk(data, redact_appid_callback)
    
    # print("REDACT APPID", data)

    return data
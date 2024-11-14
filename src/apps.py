from rich.console import Console
console = Console()

import pandas as pd
import inquirer
import time
import os

from utils.msapp import count_apps, get_apps, get_service_principals, count_service_principals
from schema.tenant import Tenant


def get_apps_method(tenant: Tenant):

    while True:
        apps = None
        console.rule("Search and Filter", style="bold magenta")
        console.print("See https://learn.microsoft.com/en-us/graph/search-query-parameter for more information on search/filter. Press Enter to skip", style="bold yellow")
        search = input("Search (or none): ")
        filter = input("Filter (or none): ")
        skip = 0
        top = 1

        params = {}
        if search: params['$search'] = search
        if filter: params['$filter'] = filter
        count = count_apps(
            params, 
            access_token=tenant.access_token,
            baseurl=tenant.endpoint
        )

        selection = ""

        while True:
            console.print(f"Total apps that match search criteria: {count}", style="bold magenta")
            questions = [
                inquirer.List('options',
                            message="What do you want to do?",
                            choices=['View Apps Table', 'View Apps Schema', 'Proceed', 'Start again', 'Exit'],
                        ),
            ]
            answers = inquirer.prompt(questions)
            selection = answers['options']
            console.print(f"You selected {selection}")
            
            if selection == "Exit":
                return None
            
            if selection == "View Apps Table":
                console.print("Fetching apps...", style="bold green")
                apps = get_apps(params=params, access_token=tenant.access_token, baseurl=tenant.endpoint, max_results=999)
                if apps:
                    console.print("Apps retrieved successfully...", style="bold green")
                    # save to pandas dataframe
                    df = pd.DataFrame(apps)
                    # show the following columns
                    _cols = ['id', 'displayName', 'createdDateTime', 'appId']
                    df = df[_cols]
                    console.print(df)
                    continue
                else:
                    console.print("Failed to retrieve apps...", style="bold red")
                    break
                # console.print(apps)
            if selection == "View Apps Schema":
                console.print("Fetching apps...", style="bold green")
                apps = get_apps(params=params, access_token=tenant.access_token, baseurl=tenant.endpoint, max_results=999)
                if apps:
                    console.print("Apps retrieved successfully...", style="bold green")
                    console.print(apps)
                    continue
                else:
                    console.print("Failed to retrieve apps...", style="bold red")
                    break
                # console.print(apps)

            break

        if selection == "Proceed":
            apps = get_apps(params=params, access_token=tenant.access_token, baseurl=tenant.endpoint, max_results=999)
            if apps:
                console.print("Apps retrieved successfully...", style="bold green")
                return apps
            else:
                return None
        
    return None


def get_service_principals_method(tenant: Tenant):

    
    while True:
        apps = None
        console.rule("Search and Filter", style="bold magenta")
        console.print("See https://learn.microsoft.com/en-us/graph/search-query-parameter for more information on search/filter. Press Enter to skip", style="bold yellow")
        search = input("Search (or none): ")
        filter = input("Filter (or none): ")
        skip = 0
        top = 1

        params = {}
        if search: params['$search'] = search
        if filter: params['$filter'] = filter
        count = count_service_principals(
            params, 
            access_token=tenant.access_token,
            baseurl=tenant.endpoint
        )

        selection = ""

        while True:
            console.print(f"Total apps that match search criteria: {count}", style="bold magenta")
            questions = [
                inquirer.List('options',
                            message="What do you want to do?",
                            choices=['View Apps Table', 'View Apps Schema', 'Proceed', 'Start again', 'Exit'],
                        ),
            ]
            answers = inquirer.prompt(questions)
            selection = answers['options']
            console.print(f"You selected {selection}")
            
            if selection == "Exit":
                return None
            
            if selection == "View Apps Table":
                console.print("Fetching apps...", style="bold green")
                apps = get_service_principals(params=params, access_token=tenant.access_token, baseurl=tenant.endpoint, max_results=999)
                if apps:
                    console.print("Apps retrieved successfully...", style="bold green")
                    # save to pandas dataframe
                    df = pd.DataFrame(apps)
                    # show the following columns
                    _cols = ['id', 'displayName', 'createdDateTime', 'appId']
                    df = df[_cols]
                    console.print(df)
                    continue
                else:
                    console.print("Failed to retrieve apps...", style="bold red")
                    break
                # console.print(apps)
            if selection == "View Apps Schema":
                console.print("Fetching apps...", style="bold green")
                apps = get_service_principals(params=params, access_token=tenant.access_token, baseurl=tenant.endpoint, max_results=999)
                if apps:
                    console.print("Apps retrieved successfully...", style="bold green")
                    console.print(apps[0])
                    continue
                else:
                    console.print("Failed to retrieve apps...", style="bold red")
                    break
                # console.print(apps)

            break

        if selection == "Proceed":
            apps = get_service_principals(params=params, access_token=tenant.access_token, baseurl=tenant.endpoint, max_results=999)
            if apps:
                console.print("Apps retrieved successfully...", style="bold green")
                return apps
            else:
                return None
        
    return None


def select_apps(apps: list):
    console.print("Select Apps to migrate", style="bold magenta")
    choices = [" -> All <-" ]
    choices.extend([app.get('appId')+": "+app.get('displayName') for app in apps])
    questions = [
        inquirer.Checkbox('options',
                    message="Select Apps to migrate (Space selects it, Enter to finish):",
                    choices=choices,
                    carousel=True,
                ),
    ]
    answers = inquirer.prompt(questions)
    selection = answers['options']
    if not selection:
        console.print("Please select an option", style="bold red")
        time.sleep(1)
        return select_apps(apps)
    if " -> All <-" not in selection:
        selected_apps = [app for app in apps if app.get('appId')+": "+app.get('displayName') in selection]
    else:
        selected_apps = apps
    # console.print(f"You selected {selection}")
    return selected_apps


def find_select_apps(tenant: Tenant, app_type:str = 'Application'):
    questions = [
        inquirer.List('options',
                    message="How do you want to select apps?",
                    choices=['Search and Filter + Manual Selection', 'Select from CSV', 'Exit'],
                ),
    ]
    answers = inquirer.prompt(questions)
    selection = answers['options']
    console.print(f"You selected {selection}")
    if selection == "Exit":
        return None
    elif selection == "Select from CSV":
        # Load CSV
        # select file from files folder
        console.print("Please make sure the CSV file is in the 'files' folder", style="bold yellow")
        input("Press Enter to continue...")
        files = os.listdir("files")
        questions = [
            inquirer.List('options',
                        message="Select CSV file",
                        choices=files,
                    ),
        ]
        answers = inquirer.prompt(questions)
        csv_file = answers['options']
        apps = pd.read_csv(os.path.join('files',csv_file))
        console.print(apps)
        
        questions = [
            inquirer.List('options',
                          message="Select column that contains the App ID",
                          choices=apps.columns.tolist(),
                          ),
        ]
        answers = inquirer.prompt(questions)
        app_id_column = answers['options']
        apps = apps[app_id_column].tolist()

        console.print(f"Attempting to fetch {len(apps)} {app_type}s...", style="bold green")
        
        if app_type == 'Application':
            _func = get_apps
        else:
            _func = get_service_principals
        
        # batch selection size to 15 apps
        batch_size = 15
        selected_apps = []
        sp_apps = []
        
        for i in range(0, len(apps), batch_size):
            _apps = apps[i:i+batch_size]
            _apps = "','".join(_apps)
            _selected_apps = _func(params={"$filter": "appId in ('"+_apps+"')"}, access_token=tenant.access_token, baseurl=tenant.endpoint)
            selected_apps.extend(_selected_apps)
        
        console.print(f"Successfully fetched {len(selected_apps)} {app_type}s", style="bold green")
        time.sleep(2)
        
        return selected_apps
        
    else:
        # Search and Filter
        if app_type == 'Application':
            apps = get_apps_method(tenant)
        else:
            apps = get_service_principals_method(tenant)
        if not apps:
            console.print("Failed to retrieve apps...", style="bold red")
            return None
        # Select Apps
        apps = select_apps(apps)
        
        return apps
    
    
def batch_fetch_sp_by_appid(tenant:Tenant, apps:list):
    # fetch service principals in batches
    batch_size = 15
    sp_apps = []
    for i in range(0, len(apps), batch_size):
        _apps = apps[i:i+batch_size]
        _apps = "','".join([app.get('appId') for app in _apps])
        _sp_apps = get_service_principals(params={"$filter": "appId in ('"+_apps+"')"}, access_token=tenant.access_token, baseurl=tenant.endpoint)
        sp_apps.extend(_sp_apps)

    console.print(f"Successfully fetched {len(sp_apps)} Service Principals associated to selected Apps", style="bold green")
    time.sleep(2)
    
    return sp_apps
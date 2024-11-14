from pydantic import BaseModel
from typing import Optional
from rich.console import Console
from rich.progress import Progress, track

console = Console()
import inquirer, json

inquirier_theme = None 

import time, datetime
from dateutil.parser import parse
import os
import pandas as pd

from src.tenant import get_source_tenant_method
from utils.msapp import tenant_request
from schema.tenant import Tenant

# Set the display options.
pd.set_option('display.max_rows', None)
# pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
# pd.set_option('display.max_colwidth', 5)

endpoint_types = ["applications", "servicePrincipals","connectorGroup","connector"]

follow_up_endpoints = {
    "applications" : [
        "owners",
        # "servicePrincipals",
    ],
    "servicePrincipals" : [
        "createdObjects",
        "ownedObjects",
        "owners",
        "appRoleAssignments",
        "claimsMappingPolicies",
    ],
    # "applicationTemplates": [],
    # "connectorGroup" : [
    #         "applications",
    #         "members",
    #     ],
    # "connector" : [
    #     "memberOf",
    # ],
}

# def user_choice():
#     questions = [
#         inquirer.List('options',
#                     message="What do you want to do?",
#                     choices=['Search', 'Change App Type', 'Change Tenant', 'Exit'],
#                 ),
#     ]
#     answers = inquirer.prompt(questions)
#     return answers['options']

def list_items(endpoint: str , params: dict = {}, access_token: str = None, max_results: int = 999, total_results:int = None):
    
    if not total_results:
        total_results = tenant_request(f"{endpoint.rstrip('/')}/$count" , 
            headers={"ConsistencyLevel": "eventual"}, 
            params=params, 
            api_key=access_token, 
        )
    params["$top"] = max_results
    graph_data = []
    skip = 0

    for i in track(range(0, total_results, max_results), description="Fetching data..."):
        
        data = tenant_request( endpoint, 
            headers={"ConsistencyLevel": "eventual"}, 
            params=params, 
            api_key=access_token, 
        )
        if data:
            graph_data.extend(data.get("value", data))
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

def fetch_listing(option:str, endpoint:str, tenant:Tenant):
    console.rule(f"Fetching [bold magenta]'{option}'[/bold magenta]...", style="bold yellow")
    
    # Look for saved queries
    saved_queries = [f for f in os.listdir("queries") if f.startswith(f"{option}_")]
    using_saved_query = False
    if saved_queries:
        console.print("Saved Queries:", style="bold yellow")
        for i, q in enumerate(saved_queries):
            console.print(f"{i+1}. {q}", style="bold green")
        choice = inquirer.prompt([
            inquirer.List('options', message="Select a saved query to use", choices= saved_queries + ["New Search"], carousel=True)
        ], theme=inquirier_theme)
        if choice['options'] == "New Search":
            pass
        else:
            with open(f"queries/{choice['options']}", "r") as f:
                params = json.load(f)
                using_saved_query = params
    if using_saved_query:
        last_search = using_saved_query.get('$search', "")
        last_filter = using_saved_query.get('$filter', "")
        last_raw_params = "&".join([f"{k}={v}" for k,v in using_saved_query.items() if k not in ['$search', '$filter']])
        last_skip_apps_without_credentials = using_saved_query.get('skip_apps_without_credentials', "")
    else:
        last_search = ""
        last_filter = ""
        last_raw_params = ""
        last_skip_apps_without_credentials = ""
    
    last_skip_publishers = []
    
    table_columns = ['id', 'displayName', 'createdDateTime', 'appId']
    
    while True:
        # apps = None
        # console.rule("Search and Filter", style="bold magenta")
        console.print("Search and Filter. See https://learn.microsoft.com/en-us/graph/search-query-parameter for more information on search/filter. Press Enter to skip", style="bold yellow")
        # search = input("Search (or none): ")
        # search = inquirer.text("Search (or none): ", default=last_search, theme=inquirier_theme)
        # filter = inquirer.text("Filter (or none): ", default=last_filter, theme=inquirier_theme)
        questions = [
            inquirer.Text('search', message="Search (or none):", default=last_search),
            inquirer.Text('filter', message="Filter (or none):", default=last_filter),
            inquirer.Text('raw_params', message="RAW URL Parameters (or none):", default=last_raw_params),
            inquirer.Text('skip_apps_without_credentials', message="Skip Apps with No or Expired Credentials ('y' or none) (post-processing):", default=last_skip_apps_without_credentials),
        ]
        if option in ['servicePrincipals']:
            # questions.append(inquirer.Text('skip_publishers', message="Skip Publishers (comma seperated):", default=last_skip_publishers))
            questions.append(inquirer.Checkbox('skip_publishers', message="Skip Publishers (Space to select, Enter to confirm):", other=True, default=last_skip_publishers, choices=[
                'n/a',
                "Microsoft Services",
                "Microsoft Accounts",
                "Microsoft 365 PnP",
                "Microsoft 365",
                "Microsoft Azure",
                "Microsoft",
                "graphExplorerMT",
                "Citrix Cloud",
            ]))
            
        answers = inquirer.prompt(questions, theme=inquirier_theme)
        skip = 0
        top = 1
        skip_apps_without_credentials = False

        if answers['search']: answers['search'] = answers['search'] if answers['search'].startswith("'") or answers['search'].startswith('"') else f'"{answers["search"]}"'
        last_search = answers['search']
        last_filter = answers['filter']
        last_raw_params = answers['raw_params']
        last_skip_publishers = answers['skip_publishers'] if 'skip_publishers' in answers else []

        params = {}
        if answers['search']: params['$search'] = answers['search']
        if answers['filter']: params['$filter'] = answers['filter']
        if answers['raw_params']:
            _raw_params = answers['raw_params'].split("&")
            params.update({i.split("=")[0]:i.split("=")[1] for i in _raw_params})
        if 'skip_publishers' in answers and answers['skip_publishers']:
            _pubs = ",".join([f"'{s}'" if s else f"null" for s in answers['skip_publishers']])
            params['$filter'] = f"{last_filter+' and ' if last_filter else ''}NOT(publisherName in ({_pubs}))"
            params['$count'] = "true"
        if 'skip_apps_without_credentials' in answers and answers['skip_apps_without_credentials']:
            # params['$filter'] = f"{params.get('$filter','')} and (passwordCredentials/any(x: x/endDateTime ge now() or x/endDateTime eq null))"
            skip_apps_without_credentials = True
            
        endpoint_url = f"{tenant.endpoint.strip('/')}/beta/{endpoint.strip('/')}"
        
        # console.print(params)
        
        try:
            count = tenant_request(f"{endpoint_url}/$count" , 
                headers={"ConsistencyLevel": "eventual"}, 
                params=params, 
                api_key=tenant.access_token, 
                # host=tenant.endpoint
            )
            if not count:
                raise
            
            console.print(f"Total {option} that match search criteria (pre processing): {count}", style="bold magenta")
        
        except Exception as e:
            # continue
            count = 99999
            pass
            
        try:
            list_of_items = list_items(endpoint_url, params=params, access_token=tenant.access_token, total_results=count, max_results=999)
            today = datetime.datetime.now(tz=datetime.timezone.utc)  #+ datetime.timedelta(days=1) # UTC time
            for i, item in enumerate(list_of_items):
                if item.get('passwordCredentials'):
                    list_of_items[i]['passwordCredentials'] = [x for x in item['passwordCredentials'] if not x.get('endDateTime') or parse(x.get('endDateTime')) > today]
                if item.get('keyCredentials'):
                    list_of_items[i]['keyCredentials'] = [x for x in item['keyCredentials'] if not x.get('endDateTime') or parse(x.get('endDateTime')) > today]
                # list_of_items = [i for i in list_of_items if not i.get('passwordCredentials') or any([not x.get('endDateTime') or parse(x.get('endDateTime')) > today for x in i.get('passwordCredentials')])]
                # console.print(f"Found {count-len(list_of_items)} expired apps. Skipping", style="bold magenta")
            if skip_apps_without_credentials:
                list_of_items = [i for i in list_of_items if i.get('passwordCredentials') or i.get('keyCredentials')]
                console.print(f"Skipping {count-len(list_of_items)} apps without credentials.", style="bold magenta")
                
        except Exception as e:
            console.print(f"Failed to fetch {option}: {e}", style="bold red")
            continue
        
        if not list_of_items:
            console.print(f"No {option} found for this search criteria", style="bold red")
            continue # Start again
        
        while True:
            try:
                console.print(f"Total {option} that match search criteria (post processing): {len(list_of_items)}", style="bold magenta")
                
                df = pd.DataFrame(list_of_items)
                table_columns = list(set(df.columns) & set(table_columns))
                df = df[table_columns].fillna("n/a")
                console.print(df)
            except Exception as e:
                console.print(f"Failed to display {option}: {e}", style="bold red")
                console.print(list_of_items)
                input("Press Enter to continue...")
                continue
            
            console.print()
            
            choice = inquirer.prompt([
                inquirer.List('options', message="What do you want to do?", choices=[
                    'View Item', 
                    'JSON Dump',
                    'Filter for Optional/Group Claims (applications)',
                    'Follow Up Request', 
                    'Change Search Criteria', 
                    "Change Table Columns to Display", 
                    "Save Query", 
                    'Return Selection (ie. to create migration job)',
                    'Abort'
                ])
            ], theme=inquirier_theme)

            _item_titles = []
            for item in list_of_items:
                # _item_titles.append(",".join([v for k,v in item.items() if k in ['id', 'displayName', 'appId']]))
                _item_titles.append(f"{item.get('displayName','n/a')} - id: {item.get('id','n/a')} // appId: {item.get('appId','n/a')}")

            match choice['options']:
                case "JSON Dump":
                    console.print(list_of_items)
                    input("Press Enter to continue...")
                    
                case "Save Query":
                    query_name = inquirer.prompt([inquirer.Text('query_name', message="Enter Query Name", default=str(int(time.time())))], theme=inquirier_theme)
                    with open(f"queries/{option}_{query_name['query_name']}.json", "w") as f:
                        params['skip_apps_without_credentials'] = "yes" if skip_apps_without_credentials else "no"
                        json.dump(params, f)
                    console.print(f"Query saved as queries/{option}_{query_name['query_name']}.json", style="bold green")
                    time.sleep(3)
                    continue
                    
                case 'View Item':
                    # view_item = inquirer.list_input("Select Item to display", choices=_item_titles)
                    view_item = inquirer.prompt([
                        inquirer.List('options', message="Select Item to display", choices=_item_titles, carousel=True)
                    ], theme=inquirier_theme)
                    _ind = view_item['options']
                    # print(_ind, _item_titles.index(_ind))
                    console.print(list_of_items[_item_titles.index(_ind)])
                    input("Press Enter to continue...")
                    
                case 'Filter for Optional/Group Claims (applications)':
                    if option in ['applications']:
                        list_of_items = [i for i in list_of_items if i.get('optionalClaims') or i.get('groupMembershipClaims')]
                        continue
                    
                case 'Follow Up Request':
                    view_item = inquirer.prompt([
                        inquirer.List('options', message=f"Select Item to make Follow up Request for '{option}'", choices=_item_titles, carousel=True)
                    ], theme=inquirier_theme)
                    _ind = view_item['options']
                    # print(_ind, _item_titles.index(_ind))
                    _id = list_of_items[_item_titles.index(_ind)].get('id')
                    if not _id:
                        console.print("No ID found for this item", style="bold red")
                        continue
                    
                    _options = follow_up_endpoints.get(option, [])
                    # if not _options:
                    #     console.print("No follow-up endpoints found for this item", style="bold red")
                    #     continue
                    
                    _follow_up_table_columns = ['id']
                    while True:
                        console.print(f"Follow up request: {endpoint_url}/{_id}/ ", style="bold yellow")
                        _follow_up = inquirer.prompt([
                            inquirer.List('options', message="Select Follow-up Request", choices=_options, carousel=True, other=True)
                        ], theme=inquirier_theme)
                        _follow_up = _follow_up['options']
                        if _follow_up in _options: _follow_up = "/" + _follow_up
                        _follow_up_url = f"{endpoint_url}/{_id}{_follow_up}"
                        console.print(f"Making follow up request to: {_follow_up_url}...", style="bold yellow")
                        _follow_up_data = list_items(_follow_up_url, access_token=tenant.access_token, total_results=99999)
                        # print(_follow_up_data)
                        
                        if not _follow_up_data:
                            console.print("No data found for this item", style="bold red")
                            input("Press Enter to continue...")
                            
                            break
                        
                        _follow_up_table_columns = list(_follow_up_data[0].keys())[:6]
                        # print(_follow_up_table_columns)
                        # print(_follow_up_data[0].keys())
                        # print(list(_follow_up_data[0].keys()[:6]))
                        _follow_up_df = pd.DataFrame(_follow_up_data)
                        _follow_up_df = _follow_up_df[_follow_up_table_columns].fillna("n/a")
                        console.print(_follow_up_df)
                        console.print()
                        choice = inquirer.prompt([
                            inquirer.List('options', message="What do you want to do?", choices=['View Item', 'Change Search Criteria', "Change Table Columns to Display", 'Abort'])
                        ], theme=inquirier_theme)
                        match choice['options']:
                            case 'View Item':
                                _follow_up_item_titles = []
                                for item in _follow_up_data:
                                    # _item_titles.append(",".join([v for k,v in item.items() if k in ['id', 'displayName', 'appId']]))
                                    _follow_up_item_titles.append(" | ".join([f"{it}:{item[it]}" for i,it in enumerate(item.keys()) if i <5]))
                                    
                                view_item = inquirer.prompt([
                                    inquirer.List('options', message="Select Item to display", choices=_follow_up_item_titles, carousel=True)
                                ], theme=inquirier_theme)
                                _ind = view_item['options']
                                # print(_ind, _item_titles.index(_ind))
                                console.print(_follow_up_data[_follow_up_item_titles.index(_ind)])
                                input("Press Enter to continue...")
                                
                            case "Change Table Columns to Display":
                                _follow_up_table_columns_choice = inquirer.prompt([
                                    inquirer.Checkbox('options', message="Select columns to display", choices=_follow_up_data[0].keys(), default=_follow_up_table_columns, carousel=True)
                                ], theme=inquirier_theme)
                                _follow_up_table_columns = _follow_up_table_columns_choice['options']
                                _follow_up_df = pd.DataFrame(_follow_up_data)
                                _follow_up_df = _follow_up_df[_follow_up_table_columns].fillna("n/a")
                                console.print(_follow_up_df)
                                console.print()
                                input("Press Enter to continue...")
                                continue
                            case 'Abort':
                                break

                    
                case 'Change Search Criteria':
                    break
                case "Change Table Columns to Display":
                    table_columns_choice = inquirer.prompt([
                        inquirer.Checkbox('options', message="Select columns to display", choices=list_of_items[0].keys(), default=table_columns, carousel=True)
                    ], theme=inquirier_theme)
                    print(table_columns_choice)
                    table_columns = table_columns_choice['options']
                    # print(table_columns)
                    # df = df[table_columns]
                    # console.print(df)
                    # input("Press Enter to continue...")
                    continue
                case 'Return Selection (ie. to create migration job)':
                    return list_of_items
                case 'Abort':
                    return None


def run_explorer():
    
    source_tenant = get_source_tenant_method()
    
    while True:
        try:
            # console.print("Will be using the BETA API to fetch apps...", style="bold yellow")
            
            questions = [
                inquirer.List('options',
                            message="Select type of Apps to get:",
                            choices=follow_up_endpoints.keys(),
                            carousel=True,
                        ),
            ]
            answers = inquirer.prompt(questions, theme=inquirier_theme)
            if not answers: return None
            apps_type = answers['options']
            
            while True:
                # if apps_type == 'servicePrincipals':
                #     apps = fetch_listing(apps_type, endpoint="/servicePrincipals", tenant=source_tenant)
                    
                # if apps_type == 'applications':
                #     apps = fetch_listing(apps_type, endpoint="/applications", tenant=source_tenant)
                    
                if apps_type == 'connectorGroup':
                    apps = fetch_listing(apps_type, endpoint="/onPremisesPublishingProfiles/applicationProxy/connectorGroups", tenant=source_tenant)
                    
                elif apps_type == 'connector':
                    apps = fetch_listing(apps_type, endpoint="/onPremisesPublishingProfiles/applicationProxy/connectors", tenant=source_tenant)
                else:
                    apps = fetch_listing(apps_type, endpoint=f"/{apps_type}", tenant=source_tenant)
                      
                
                questions = [
                    inquirer.List('options',
                                message="What do you want to do?",
                                choices=[
                                    f'New Search ({apps_type})', 
                                    'Change App Type', 
                                    'Change Tenant', 
                                    'Exit'
                                ],
                            ),
                ]
                answers = inquirer.prompt(questions, theme=inquirier_theme)
                match answers['options']:
                    case 'Change App Type':
                        break
                    case 'Change Tenant':
                        return run_explorer()                    

                    case 'Exit':
                        return None
                    
                continue
            
        except KeyboardInterrupt:
            console.print("Exiting...", style="bold red")
            return None
        except Exception as e:
            console.print(f"Error: {e}", style="bold red")
            continue
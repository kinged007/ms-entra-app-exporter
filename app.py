from rich import print
from rich.console import Console
import os
import time
import inquirer
import json

from utils.validate import sanitize_app_data
from src.apps import  find_select_apps, batch_fetch_sp_by_appid
from src.tenant import get_source_tenant_method, manage_tenants, clean_up_data
from src.explorer import run_explorer   
from utils.time import nice_time

console = Console()

# Check if a proxy is set in the sysargs
import sys
if "--proxy" in sys.argv:
    proxy = sys.argv[sys.argv.index("--proxy")+1]
    os.environ['HTTP_PROXY'] = proxy
    os.environ['HTTPS_PROXY'] = proxy
    os.environ['http_proxy'] = proxy
    os.environ['https_proxy'] = proxy

# Use the option below to create a sample tenant file
os.makedirs("tenants", exist_ok=True)
os.makedirs("queries", exist_ok=True)
os.makedirs("files", exist_ok=True)


while True:
    
    try:
        console.print("\n\n\n\n\n\n\n\n")
        
        console.rule("[bold red]Microsoft Entra ID Migration Helper[/bold red]", style="bold magenta")
        
        ## Main Menu
        questions = [
            inquirer.List('options',
                        message="What do you want to do?",
                        choices=[
                            "🏠 Manage Tenants", 
                            "🔍 Activate API Explorer", 
                            "📦 Export App Metadata", 
                            # "📋 View App Schemas", 
                            "🧹 Clean up and Remove All Data",
                            "🚪 Exit"
                        ],
                    ),
        ]
        answers = inquirer.prompt(questions)
        selection = answers['options']
        console.print(f"You selected {selection}")

        match selection:
            case "🚪 Exit":
                break
            case "🏠 Manage Tenants":
                manage_tenants()
            case "📦 Export App Metadata":
                source_tenant = get_source_tenant_method()
                app_type = inquirer.list_input("Select type of app you will be exporting?", choices=['Application', 'Service Principal'])
                fetch_sp = False

                apps = find_select_apps(source_tenant)
                sps = []
                
                if not apps:
                    console.print("No apps found", style="bold red")
                    continue
                    
                if app_type == 'Application':

                    fetch_sp = inquirer.confirm("Automatically Fetch associated Service Principals?", default=False)

                    if fetch_sp:
                        sps = batch_fetch_sp_by_appid(source_tenant, apps) 
                         
                # Got apps and maybe SPs, now sanitize the data
                santized_apps = sanitize_app_data(apps, app_type)
                sanitized_sps = sanitize_app_data(sps, 'Service Principal')

                # Yes, confusion here as we are using the same variable name for both apps and sps if we are fetching SPs
                
                if app_type == 'Application':
                    print("Exported and Sanitized",len(santized_apps),"App Registrations, and", len(sanitized_sps), "Service Principals")
                else:
                    print("Exported and Sanitized",len(santized_apps),"Service Principals")
                
                console.rule(f"Review Santized {app_type} data", style="bold magenta")
                time.sleep(3)
                
                for app in santized_apps:
                    print(app)
                    if input("Press Enter to continue, or 'q' to quit review: ") == 'q':
                        break
                    
                
                if sanitized_sps:
                    console.rule("Review Sanitized Service Principal data", style="bold magenta")
                    time.sleep(3)
                    for sp in sanitized_sps:
                        print(sp)
                        if input("Press Enter to continue, or 'q' to quit review: ") == 'q':
                            break
                
                console.print("Saving data to file", style="bold green")
                
                # Save the data to a file
                file = os.path.join("files", f"{source_tenant.client_id}_{app_type.replace(' ','').lower()}_{nice_time()}.json")
                with open(file, "w") as f:
                    f.write(json.dumps([a.model_dump() for a in santized_apps]))
                    
                console.print(f"Data saved to {file}", style="bold green")
                
                if sanitized_sps:
                    file = os.path.join("files", f"{source_tenant.client_id}_serviceprincipal_{nice_time()}.json")
                    with open(file, "w") as f:
                        f.write(json.dumps([a.model_dump() for a in sanitized_sps]))
                        
                    console.print(f"Data saved to {file}", style="bold green")

                time.sleep(3)

            # case "📋 View App Schemas":
            #     console.print("Viewing App Schemas")
            #     view_schema()
                
            case "🔍 Activate API Explorer":
                run_explorer()
            case "🧹 Clean up and Remove All Data":
                clean_up_data()
        
        continue
        
        
    except Exception as e:
        console.print(f"An error occured: {e}", style="bold red")
        input("Press Enter to continue...")
        continue
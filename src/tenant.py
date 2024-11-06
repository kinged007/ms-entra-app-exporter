from pydantic import BaseModel
from rich.console import Console
console = Console()
import inquirer, json
from schema.migration_db.tenant import Tenant
import os
from utils.msapp import get_access_token, get_user_access_token
import glob

def create_new_tenant()->None:
    
    base_questions = [
        inquirer.Text('authority', message="Authority URL", default="https://login.microsoftonline.com/"),
        inquirer.Text('client_id', message="Client ID"),
        inquirer.List('connection', message="Connection Type", choices=["app", "user"], default="app"),
        inquirer.Text('endpoint', message="Graph API Endpoint (exclude API version!)", default="https://graph.microsoft.com"),
        inquirer.Text('scope', message="Scope (comma separated)", default="https://graph.microsoft.com/.default"),
    ]

    answers = inquirer.prompt(base_questions)

    if answers['connection'] == 'app':
        app_questions = [
            inquirer.Text('private_key', message="Private Key (if using certificate)"),
            inquirer.Text('thumbprint', message="Thumbprint (if using certificate)"),
            inquirer.Text('secret', message="Client Secret (if not using certificate)"),
        ]
        app_answers = inquirer.prompt(app_questions)
        answers.update(app_answers)
        # print(answers)
        answers['scope'] = answers['scope'].split(",")
        tenant = Tenant(**answers)
        name = input("Enter a name for this tenant: ")
        with open(f"tenants/{name}.json", "w") as f:
            f.write(json.dumps(tenant.model_dump(), indent=4))
            console.print(f"Tenant '{name}' created successfully", style="bold green")
    except Exception as e:
        console.print(f"Failed to create tenant: {e}", style="bold red")

def get_source_tenant_method():

    try:
        console.print("Select SOURCE Tenant to migrate from", style="bold magenta")

        # Get json files from /tenants folder
        tenants = os.listdir("tenants")

        questions = [
            inquirer.List('options',
                        message="Select SOURCE Tenant to migrate from:",
                        choices=tenants,
                    ),
        ]
        answers = inquirer.prompt(questions)
        selection = answers['options']
        console.print(f"You selected {selection}")

        with open(f"tenants/{selection}", "r") as f:
            tenant_data = json.load(f)
            tenant = Tenant(**tenant_data)
            # console.print(tenant) # DEBUG

        # Passes validation checks
        console.print("Tenant data is valid", style="bold green")
        console.print("Getting access token", style="bold green")

        if tenant.connection == "app":
            access_token = get_access_token(dict(tenant.model_dump()))
        else:
            access_token = get_user_access_token(dict(tenant.model_dump()))

        if not access_token:
            console.print("Failed to get access token", style="bold red")
            return None

        console.print("Access token retrieved successfully", style="bold green")
        tenant.access_token = access_token
        tenant.file = selection
        return tenant
    except Exception as e:
        console.print(f"Failed to get tenant: {e}", style="bold red")
        return get_source_tenant_method()
    

def get_destination_tenants_method():
    
    # Get json files from /tenants folder
    tenants = os.listdir("tenants")

    while True:
        console.print("Select DESTINATION Tenants", style="bold magenta")
        questions = [
            inquirer.Checkbox('options',
                        message="Select DESTINATION Tenants to migrate to (Space selects it, Enter to finish):",
                        choices=tenants,
                    ),
        ]
        answers = inquirer.prompt(questions)
        selection = answers['options']
        
        selection = answers['options']
        if not selection:
            console.print("Please select an option", style="bold red")
            continue
        else:
            break
        
    console.print(f"You selected '{', '.join(selection)}'")
    final_selection = []
    # Check and validate tenants
    for tenant_file in selection:
        try:
            with open(f"tenants/{tenant_file}", "r") as f:
                tenant_data = json.load(f)
                tenant = Tenant(**tenant_data)

            access_token = get_access_token(dict(tenant.model_dump()))

            if not access_token:
                raise Exception(f"Failed to get access token for tenant: {tenant_file}")

            final_selection.append(tenant_file)
        except Exception as e:
            console.print(f"Failed to load tenant: {e}", style="bold red")
            return get_destination_tenants_method()

    return final_selection

def delete_all_tenants():
    """Delete all tenant JSON files in the tenants/ directory."""
    try:
        confirm = inquirer.confirm("Are you sure you want to delete all tenant files?", default=False)
        if not confirm:
            console.print("Deletion cancelled.", style="bold yellow")
            return

        tenant_files = glob.glob("tenants/*.json")
        if not tenant_files:
            console.print("No tenant files found to delete.", style="bold yellow")
            return

        for tenant_file in tenant_files:
            os.remove(tenant_file)
            console.print(f"Deleted {tenant_file}", style="bold green")

        console.print("All tenant files deleted successfully.", style="bold green")
    except Exception as e:
        console.print(f"Failed to delete tenant files: {e}", style="bold red")

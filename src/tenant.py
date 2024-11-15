from rich.console import Console
console = Console()
import inquirer, json
from schema.tenant import Tenant
import os
from utils.msapp import get_access_token, get_user_access_token
import glob

def create_or_edit_tenant(tenant_data=None) -> None:
    """Create a new tenant or edit an existing one."""
    base_questions = [
        inquirer.Text('authority', message="Authority URL", default=tenant_data.get('authority', "https://login.microsoftonline.com/") if tenant_data else "https://login.microsoftonline.com/"),
        inquirer.Text('client_id', message="Client ID", default=tenant_data.get('client_id', "") if tenant_data else ""),
        inquirer.List('connection', message="Connection Type", choices=["app", "user"], default=tenant_data.get('connection', "app") if tenant_data else "app"),
        inquirer.Text('endpoint', message="Graph API Endpoint (exclude API version!)", default=tenant_data.get('endpoint', "https://graph.microsoft.com") if tenant_data else "https://graph.microsoft.com"),
        inquirer.Text('scope', message="Scope (comma separated)", default=",".join(tenant_data.get('scope', ["https://graph.microsoft.com/.default"])) if tenant_data else "https://graph.microsoft.com/.default"),
    ]

    try:
        answers = inquirer.prompt(base_questions)

        if answers['connection'] == 'app':
            app_questions = [
                inquirer.Text('private_key', message="Private Key (if using certificate) - File path OR encryption key", default=tenant_data.get('private_key', "") if tenant_data else ""),
                inquirer.Text('thumbprint', message="Thumbprint (if using certificate)", default=tenant_data.get('thumbprint', "") if tenant_data else ""),
                inquirer.Text('secret', message="Client Secret (if NOT using certificate)", default=tenant_data.get('secret', "") if tenant_data else ""),
            ]
            app_answers = inquirer.prompt(app_questions)
            answers.update(app_answers)

        answers['scope'] = answers['scope'].split(",")
        tenant = Tenant(**answers)

        if tenant_data:
            name = tenant_data['name']
            console.print(f"Editing tenant '{name}'", style="bold green")
        else:
            name = input("Enter a name for this tenant: ")

        with open(f"tenants/{name}.json", "w") as f:
            f.write(json.dumps(tenant.model_dump(), indent=4))
            console.print(f"Tenant '{name}' {'edited' if tenant_data else 'created'} successfully", style="bold green")
    except Exception as e:
        console.print(f"Failed to {'edit' if tenant_data else 'create'} tenant: {e}", style="bold red")

def get_source_tenant_method() -> Tenant:

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

def view_edit_tenant():
    """View or edit an existing tenant."""
    try:
        tenants = os.listdir("tenants")
        if not tenants:
            console.print("No tenants available to view or edit.", style="bold yellow")
            return

        questions = [
            inquirer.List('options',
                        message="Select a tenant to view/edit:",
                        choices=tenants,
                    ),
        ]
        answers = inquirer.prompt(questions)
        selection = answers['options']

        with open(f"tenants/{selection}", "r") as f:
            tenant_data = json.load(f)
            console.print(json.dumps(tenant_data, indent=4), style="bold blue")

        if inquirer.confirm("Do you want to edit this tenant?", default=False):
            # Use the create_or_edit_tenant function to edit the tenant
            tenant_data['name'] = selection.split('.')[0]  # Extract name from filename
            create_or_edit_tenant(tenant_data)
    except Exception as e:
        console.print(f"Failed to view/edit tenant: {e}", style="bold red")

def delete_tenant():
    """Delete a tenant."""
    try:
        tenants = os.listdir("tenants")
        if not tenants:
            console.print("No tenants available to delete.", style="bold yellow")
            return

        questions = [
            inquirer.List('options',
                        message="Select a tenant to delete:",
                        choices=tenants,
                    ),
        ]
        answers = inquirer.prompt(questions)
        selection = answers['options']

        if inquirer.confirm(f"Are you sure you want to delete {selection}?", default=False):
            os.remove(f"tenants/{selection}")
            console.print(f"Tenant '{selection}' deleted successfully.", style="bold green")
    except Exception as e:
        console.print(f"Failed to delete tenant: {e}", style="bold red")

def manage_tenants():
    """Manage tenants by creating, viewing/editing, or deleting them."""
    options = [
        "Create New Tenant",
        "View/Edit Tenant",
        "Delete Tenant"
    ]

    questions = [
        inquirer.List('action',
                    message="What would you like to do?",
                    choices=options,
                ),
    ]
    answers = inquirer.prompt(questions)
    action = answers['action']

    if action == "Create New Tenant":
        create_or_edit_tenant()
    elif action == "View/Edit Tenant":
        view_edit_tenant()
    elif action == "Delete Tenant":
        delete_tenant()
        

def clean_up_data():
    """Delete all tenant JSON files in the tenants/ directory."""
    try:
        confirm = inquirer.confirm("Are you sure you want to delete all tenant files and exported data?", default=False)
        if not confirm:
            console.print("Deletion cancelled.", style="bold yellow")
            return

        tenant_files = glob.glob("tenants/*.json")
        exported_files = glob.glob("files/*.json")
        
        if not tenant_files:
            console.print("No tenant files found to delete.", style="bold yellow")
        if not exported_files:
            console.print("No exported files found to delete.", style="bold yellow")
        
        all_files = tenant_files + exported_files

        for f in all_files:
            os.remove(f)
            console.print(f"Deleted {f}", style="bold green")

        console.print("Done cleaning up.", style="bold green")
        
    except Exception as e:
        console.print(f"Failed to delete files: {e}", style="bold red")

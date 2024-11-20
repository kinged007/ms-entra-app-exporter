# Microsoft Entra ID Migration Helper

This application is designed to securely and compliantly export applications and service principals from Microsoft Entra ID tenants. It operates by establishing a tenant connection using an OAuth app for authentication. The required permissions are `Applications.Read.All` for either the application itself (Application access) or the user using the application (Delegated access).

## Features

- **Tenant Connection**: Authenticate and connect using OAuth.
- **Export Options**: Export app data using search and filter or from a CSV file.
- **Data Sanitization**: Ensures sensitive information is not leaked.

## Setup

Create an App Registration (oAuth) app in Microsoft Entra. 

Under Authentication, click "Add a Platform".
Select "Mobile and desktop Applications"
Select the option for "MSAL only".
Click "Configure"

This will allow access via User Authentication.

To allow access via Certificate or Secret Key, you can configure this in the "Certificates and Secrets" section.


## Usage

To run the application, execute the following command:

```bash
sh run.sh
```

or on Windows:

```bash
run.bat
```

## Proxy Configuration

If a proxy is required, specify it in the `.env` file.

```
PROXY_ADDRESS="http://your-proxy-address:port"
```

## Installation

1. Clone the repository.
2. Configure the `.env` file with your proxy settings if needed.
3. Run the application using the provided scripts.

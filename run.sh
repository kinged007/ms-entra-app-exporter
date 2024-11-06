#!/bin/bash

echo

# if ! command -v python3 &> /dev/null;
# then
#     echo Python3 is not installed
#     exit 1
# fi

# Check if python3 is available
if command -v python3 &>/dev/null; then
    PYTHON=python3
# Check if python is available
elif command -v python &>/dev/null; then
    PYTHON=python
else
    echo "Could not find python or python3. Please make sure they are installed."
    exit 1
fi


# Check if pip3 is available
if command -v pip3 &>/dev/null; then
    PIP=pip3
# Check if pip is available
elif command -v pip &>/dev/null; then
    PIP=pip
else
    echo "Could not find pip or pip3. Please make sure they are installed."
    exit 1
fi

# Load configuration from .env file
if [ -f "$(dirname "$0")/.env" ]; then
    export $(grep -v '^#' "$(dirname "$0")/.env" | xargs)
fi

cd "$(dirname "$0")" || exit

# Set proxy for pip
export PIP_PROXY="--proxy $PROXY_ADDRESS"

# Set proxy for Python app
export HTTP_PROXY=$PROXY_ADDRESS
export HTTPS_PROXY=$PROXY_ADDRESS

if [ ! -d "venv" ];
then
    echo Creating virtual environment
    $PYTHON -m venv venv

    . venv/bin/activate

    echo Installing dependencies
    $PIP install $PIP_PROXY -r requirements.txt --upgrade
    # $PIP install -r vendor/gpt-researcher/requirements.txt --upgrade
    
else

    echo Activating virtual environment
    . venv/bin/activate
    
    # Check if "--upgrade" is passed in the arguments
    if [[ "${@}" =~ "--upgrade" ]]; then
        echo "Upgrading dependencies..."
        $PIP install --upgrade -r requirements.txt
        REQUIREMENTS_FILES=$(find modules -type f -name 'requirements.txt')
        for FILE in $REQUIREMENTS_FILES; do
            echo "Installing requirements from $FILE"
            $PIP install $PIP_PROXY --upgrade -r $FILE
        done
        # $PIP install --upgrade -r vendor/gpt-researcher/requirements.txt
        echo "Upgraded dependencies. Please restart the application."
        exit 0
    fi
fi

# streamlit run app.py "$@"
$PYTHON app.py "$@"
# uvicorn app:app --host 0.0.0.0 "$@"

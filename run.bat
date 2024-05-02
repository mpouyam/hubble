@echo off
REM Check if Poetry is installed
poetry --version >nul 2>&1
if %errorlevel% neq 0 (
    REM Poetry is not installed, so install it
    echo Installing Poetry...
    pip install poetry
)

REM Install project dependencies using Poetry
echo Installing project dependencies...
poetry install

REM Run your Python project using Poetry
echo Running Python project...
poetry run python app.py
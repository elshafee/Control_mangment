@echo off
echo Checking for required libraries...

REM Function to check if a library is installed
:check_library
set "library_name=%1"
python -c "try: import %1; print('%1 is installed') ; exit(0) ; except ImportError: print('%1 is not installed') ; exit(1)" > nul 2>&1
if %errorlevel% == 1 (
    echo %library_name% is not installed. Installing...
    pip install %library_name%
    if %errorlevel% neq 0 (
        echo Failed to install %library_name%.  Exiting.
        pause
        exit /b 1
    )
) else (
    echo %library_name% is installed.
)
goto :eof

REM Check for each library
call :check_library Flask
call :check_library Flask-Login
call :check_library Flask-SQLAlchemy

REM Install from requirements.txt if any of the libraries were missing (more robust)
echo Checking requirements.txt...
if exist "requirements.txt" (
    pip show -f requirements.txt > nul 2>&1
    if %errorlevel% neq 0 (
        echo Installing from requirements.txt...
        pip install -r requirements.txt
         if %errorlevel% neq 0 (
            echo Failed to install from requirements.txt.  Exiting.
            pause
            exit /b 1
        )
    ) else (
        echo All libraries in requirements.txt are already installed.
    )
) else (
    echo requirements.txt not found.  Skipping.
)

echo All required libraries are installed.

echo Starting the application...
REM Start the Python application and capture the output
for /f "tokens=*" %%i in ('python main.py ^| findstr /r "http://[0-9\.]\+:[0-9]\+"') do (
  set "flask_url=%%i"
)

echo Flask is running at: %flask_url%

REM Open the URL in the default browser
if not "%flask_url%"=="" (
  echo Opening %flask_url% in your default browser...
  start "" "%flask_url%"
) else (
  echo Could not determine the Flask URL.  Please open your browser and navigate to the address shown above.
)
echo Application stopped. Press any key to close.
pause
exit /b 0

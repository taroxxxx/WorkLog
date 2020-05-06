@REM use git cloned %USERPROFILE%\pythonenv\repos\batchlion

set TARGET=WorkLog

if not exist %TARGET%.py (
    echo "%TARGET% does not exist."
    exit /b 1
)

set REPOSITORY_PATH=%USERPROFILE%\pythonenv\repos\batchlion

set PYTHON_INSTALL_DIR=%USERPROFILE%\pythonenv\projects\batchlion
set PYTHON_EXE=%PYTHON_INSTALL_DIR%\python.exe

%PYTHON_EXE% %REPOSITORY_PATH%\expandZipLib.py

if %ERRORLEVEL% neq 0 (
    REM expandZipLib.py
    pause
    exit /b %ERRORLEVEL%
)

set PYINSTALLER_EXE=%PYTHON_INSTALL_DIR%\scripts\pyinstaller.exe
set PYTHONPATH=%~dp0;%~dp0\zipLib;

%PYINSTALLER_EXE% -y __build.spec --clean

if %ERRORLEVEL% neq 0 (
    REM PYINSTALLER_EXE
    pause
    exit /b %ERRORLEVEL%
)

set TARGET_EXE_DIR=%~dp0\dist\%TARGET%

%PYTHON_EXE% %~dp0__build.py %TARGET% %TARGET_EXE_DIR%

if %ERRORLEVEL% neq 0 (
    REM __build.py
    pause
    exit /b %ERRORLEVEL%
)

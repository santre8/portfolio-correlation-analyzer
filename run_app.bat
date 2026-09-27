@echo off
rem ES: Oculta los comandos para que la consola muestre solamente mensajes utiles.
rem EN: Hides commands so the console displays only useful messages.

setlocal
rem ES: Aisla las variables de entorno creadas por este archivo por lotes.
rem EN: Keeps environment-variable changes made by this batch file local.

rem ES: Cambia a la carpeta donde esta guardado este archivo, aunque se ejecute desde otra ubicacion.
rem EN: Changes to this file's folder, even when it is launched from another location.
cd /d "%~dp0"

rem ES: Comprueba si el entorno virtual ya tiene su propio ejecutable de Python.
rem EN: Checks whether the virtual environment already has its own Python executable.
if not exist ".venv\Scripts\python.exe" (
    rem ES: Informa que se creara un entorno virtual local en la carpeta .venv.
    rem EN: Reports that a local virtual environment will be created in the .venv folder.
    echo [SETUP] Creating the local Python environment...

    rem ES: Busca el lanzador de Python para Windows sin mostrar su salida.
    rem EN: Looks for the Windows Python launcher without displaying its output.
    where py >nul 2>&1

    rem ES: Si se encontro el lanzador py, usa cualquier version instalada de Python 3.
    rem EN: If the py launcher was found, uses any installed Python 3 version.
    if not errorlevel 1 (
        rem ES: Crea el entorno virtual .venv mediante el lanzador py.
        rem EN: Creates the .venv virtual environment through the py launcher.
        py -3 -m venv ".venv"
    ) else (
        rem ES: Si py no existe, busca el comando python como alternativa.
        rem EN: If py is unavailable, looks for the python command as a fallback.
        where python >nul 2>&1

        rem ES: Un codigo de error indica que tampoco se encontro el comando python.
        rem EN: An error code indicates that the python command was not found either.
        if errorlevel 1 (
            rem ES: Muestra un mensaje indicando que Python 3 no esta instalado o accesible.
            rem EN: Displays a message saying Python 3 is not installed or accessible.
            echo [ERROR] Python 3 was not found.

            rem ES: Explica la version minima recomendada y permite leer el mensaje.
            rem EN: Explains the minimum recommended version and lets the user read the message.
            echo Install Python 3.10 or newer and run this file again.
            pause

            rem ES: Finaliza el archivo con codigo 1 para indicar un error.
            rem EN: Ends the batch file with code 1 to indicate an error.
            exit /b 1
        )

        rem ES: Crea el entorno virtual usando directamente el comando python.
        rem EN: Creates the virtual environment by using the python command directly.
        python -m venv ".venv"
    )

    rem ES: Comprueba si alguno de los comandos de creacion del entorno fallo.
    rem EN: Checks whether either virtual-environment creation command failed.
    if errorlevel 1 (
        rem ES: Informa que no fue posible crear el entorno virtual.
        rem EN: Reports that the virtual environment could not be created.
        echo [ERROR] The virtual environment could not be created.

        rem ES: Pausa la consola para que el usuario pueda leer el error.
        rem EN: Pauses the console so the user can read the error.
        pause

        rem ES: Sale con codigo de error y evita continuar con una instalacion incompleta.
        rem EN: Exits with an error code and prevents continuing with an incomplete setup.
        exit /b 1
    )
)

rem ES: Activa el entorno virtual para usar su Python y sus paquetes aislados.
rem EN: Activates the virtual environment to use its isolated Python and packages.
call ".venv\Scripts\activate.bat"

rem ES: Si la activacion falla, salta al bloque comun de manejo de errores.
rem EN: If activation fails, jumps to the shared error-handling block.
if errorlevel 1 goto :error

rem ES: Informa que se comprobaran e instalaran las dependencias del proyecto.
rem EN: Reports that the project dependencies will be checked and installed.
echo [SETUP] Checking project dependencies...

rem ES: Instala las versiones definidas en requirements.txt y oculta el aviso de version de pip.
rem EN: Installs the versions defined in requirements.txt and hides pip's version notice.
python -m pip install --disable-pip-version-check -r "requirements.txt"

rem ES: Si pip no pudo instalar algun paquete, salta al bloque de errores.
rem EN: If pip could not install a package, jumps to the error block.
if errorlevel 1 goto :error

rem ES: Informa que la aplicacion financiera esta a punto de iniciarse.
rem EN: Reports that the financial application is about to start.
echo [START] Opening the Financial Portfolio Analyzer...

rem ES: Inicia matriz_s4.py como una aplicacion web de Streamlit.
rem EN: Starts matriz_s4.py as a Streamlit web application.
python -m streamlit run "matriz_s4.py"

rem ES: Si Streamlit termina con un error, salta al bloque de errores.
rem EN: If Streamlit exits with an error, jumps to the error block.
if errorlevel 1 goto :error

rem ES: Finaliza correctamente cuando Streamlit se cierra sin errores.
rem EN: Finishes successfully when Streamlit closes without errors.
exit /b 0

rem ES: Define el bloque al que se salta cuando ocurre un error.
rem EN: Defines the block used when an error occurs.
:error

rem ES: Imprime una linea vacia para separar visualmente el mensaje de error.
rem EN: Prints a blank line to visually separate the error message.
echo.

rem ES: Muestra el mensaje general de que la aplicacion no pudo iniciarse.
rem EN: Displays the general message that the application could not be started.
echo [ERROR] The application could not be started.

rem ES: Mantiene la ventana abierta para que el usuario pueda leer el mensaje.
rem EN: Keeps the window open so the user can read the message.
pause

rem ES: Finaliza el archivo con codigo 1 para comunicar el fallo al sistema.
rem EN: Ends the batch file with code 1 to report the failure to the system.
exit /b 1

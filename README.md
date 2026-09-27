# Financial Portfolio & Correlation Analyzer

Aplicacion web en Streamlit para consultar precios historicos de Yahoo Finance,
calcular retornos y correlaciones, y explorar grupos de activos mediante
clustering jerarquico.

## Inicio rapido en Windows

1. Instala Python 3.10 o posterior desde <https://www.python.org/downloads/>.
   Durante la instalacion, activa la opcion **Add Python to PATH**.
2. Haz doble clic en `run_app.bat`.
3. La primera ejecucion crea el entorno aislado `.venv` e instala las
   dependencias. Las siguientes ejecuciones reutilizan ese entorno.
4. Streamlit abrira la aplicacion en el navegador. Si no lo hace, abre la URL
   local que aparece en la consola, normalmente <http://localhost:8501>.

No es necesario instalar Anaconda ni activar un entorno manualmente.

## Inicio desde una terminal

En PowerShell o CMD:

```bat
cd /d "D:\Backup\develop\carmen projects"
run_app.bat
```

## Instalacion manual

Si prefieres controlar el entorno:

```bat
cd /d "D:\Backup\develop\carmen projects"
py -3 -m venv .venv
call .venv\Scripts\activate.bat
python -m pip install -r requirements.txt
python -m streamlit run matriz_s4.py
```

En macOS o Linux, cambia la activacion por:

```bash
source .venv/bin/activate
```

## Archivos del proyecto

- `matriz_s4.py`: aplicacion Streamlit.
- `requirements.txt`: versiones exactas de las dependencias probadas.
- `run_app.bat`: instalador y lanzador automatico para Windows.
- `.gitignore`: excluye el entorno virtual y archivos temporales.

## Compartir o reproducir

Comparte la carpeta completa, pero omite `.venv` si ya existe. La otra persona
solo necesita Python y debe ejecutar `run_app.bat`; el entorno se reconstruye a
partir de `requirements.txt`.

La aplicacion necesita conexion a Internet para descargar datos de mercado y
datos de empresas desde Yahoo Finance.

## Solucion de problemas

- **Python no encontrado:** reinstala Python y activa `Add Python to PATH`.
- **El puerto 8501 esta ocupado:** ejecuta
  `python -m streamlit run matriz_s4.py --server.port 8502` con el entorno
  activado.
- **Dependencias danadas:** elimina solo la carpeta `.venv` y vuelve a ejecutar
  `run_app.bat` para reconstruirla.
- **Yahoo Finance no devuelve un ticker:** verifica el simbolo y la conexion a
  Internet; algunos simbolos pueden cambiar o dejar de estar disponibles.

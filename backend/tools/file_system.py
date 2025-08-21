import os

def list_project_files(directory: str = '.') -> list[str]:
    """Devuelve una lista de archivos y carpetas en el directorio especificado."""
    print(f"--- [Herramienta FS]: Listando archivos en '{directory}' ---")
    try:
        return os.listdir(directory)
    except FileNotFoundError:
        return ["Error: El directorio no fue encontrado."]

def read_file_content(filepath: str) -> str:
    """Lee y devuelve el contenido de un archivo de texto específico."""
    print(f"--- [Herramienta FS]: Leyendo el archivo '{filepath}' ---")
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return "Error: El archivo no fue encontrado."
    except Exception as e:
        return f"Error al leer el archivo: {e}"

def write_file_content(filepath: str, content: str) -> str:
    """Escribe o sobrescribe el contenido de un archivo de texto específico."""
    print(f"--- [Herramienta FS]: Escribiendo en el archivo '{filepath}' ---")
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Archivo '{filepath}' guardado exitosamente."
    except Exception as e:
        return f"Error al escribir en el archivo: {e}"
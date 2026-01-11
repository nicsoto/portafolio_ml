import os
from pathlib import Path

output = []
output.append("# Portafolio ML - Código Completo\n\n")
output.append("Este archivo contiene todo el código fuente del proyecto.\n\n")
output.append("---\n\n")

# Archivos a incluir
include_extensions = {'.py', '.md', '.toml'}
exclude_dirs = {'.venv', '.git', '__pycache__', '.pytest_cache', 'data'}
exclude_files = {'uv.lock', 'portafolio_ml_completo.md'}

for root, dirs, files in os.walk('.'):
    # Filtrar directorios excluidos
    dirs[:] = [d for d in dirs if d not in exclude_dirs]
    
    for file in sorted(files):
        if file in exclude_files:
            continue
        
        ext = Path(file).suffix
        if ext not in include_extensions:
            continue
        
        filepath = os.path.join(root, file)
        rel_path = filepath[2:]  # Quitar ./
        
        try:
            with open(filepath, 'r') as f:
                content = f.read()
            
            # Determinar lenguaje para syntax highlighting
            lang = 'python' if ext == '.py' else 'toml' if ext == '.toml' else 'markdown'
            
            output.append(f"## `{rel_path}`\n\n")
            output.append(f"```{lang}\n{content}\n```\n\n")
            output.append("---\n\n")
        except:
            pass

with open('../portafolio_ml_completo.md', 'w') as f:
    f.write(''.join(output))

print("✅ Archivo creado: ../portafolio_ml_completo.md")

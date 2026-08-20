import json
from pathlib import Path

# Los directorios que contienen traducciones
ALLOWED_DIRS = [
    "allied_society", "chronicles", "city_intro", "class_job", 
    "combat_actions_traits", "msq", "other", "sidequests", "ui", "ui_menus"
]

def main():
    catalog = []
    base_path = Path(".")

    for dir_name in ALLOWED_DIRS:
        folder = base_path / dir_name
        if not folder.exists():
            continue

        # Encontrar todos los archivos _en.json en el directorio
        for en_file in sorted(folder.rglob("*_en.json")):
            es_file = en_file.parent / en_file.name.replace("_en.json", "_es.json")
            
            # Leer total de líneas originales
            try:
                en_data = json.loads(en_file.read_text(encoding="utf-8"))
                total_keys = len(en_data)
            except Exception:
                continue
            
            translated_keys = 0
            has_es = False
            
            # Contar líneas traducidas si existe el archivo _es.json
            if es_file.exists():
                has_es = True
                try:
                    es_data = json.loads(es_file.read_text(encoding="utf-8"))
                    # Cuenta solo los valores que no están en blanco
                    translated_keys = sum(1 for v in es_data.values() if str(v).strip())
                except Exception:
                    pass
            
            progress = round((translated_keys / total_keys * 100), 1) if total_keys > 0 else 0.0
            
            catalog.append({
                "path": en_file.as_posix(),
                "es_path": es_file.as_posix(),
                "total_keys": total_keys,
                "translated_keys": translated_keys,
                "progress": progress,
                "has_es": has_es
            })

    # Guardar el nuevo catálogo
    catalog_path = base_path / "file_catalog.json"
    catalog_path.write_text(json.dumps(catalog, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Catálogo actualizado: {len(catalog)} archivos procesados.")

if __name__ == "__main__":
    main()
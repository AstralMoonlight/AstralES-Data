import json
from pathlib import Path

BASE = Path(__file__).parent.parent  # raiz del repo

EXCLUDE_NAMES = {"all_texts"}
EXCLUDE_DIRS  = {"GLOSSARY"}

def main():
    catalog = []

    for en_file in sorted(BASE.rglob("*_en.json")):
        # Excluir all_texts y GLOSSARY
        if any(p in EXCLUDE_DIRS for p in en_file.parts):
            continue
        if any(en_file.stem.startswith(ex) for ex in EXCLUDE_NAMES):
            continue

        es_file = en_file.with_name(en_file.name.replace("_en.json", "_es.json"))

        try:
            en_data = json.loads(en_file.read_text(encoding="utf-8"))
            total_keys = len(en_data)
        except Exception as e:
            print(f"Error leyendo {en_file}: {e}")
            continue

        translated_keys = 0
        has_es = es_file.exists()

        if has_es:
            try:
                es_data = json.loads(es_file.read_text(encoding="utf-8"))
                translated_keys = sum(1 for v in es_data.values() if str(v).strip())
            except Exception:
                pass

        progress = round(translated_keys / total_keys * 100, 1) if total_keys > 0 else 0.0

        # Ruta relativa a la raiz del repo, con separador /
        rel_en = en_file.relative_to(BASE).as_posix()
        rel_es = es_file.relative_to(BASE).as_posix()

        catalog.append({
            "path":            rel_en,
            "es_path":         rel_es,
            "total_keys":      total_keys,
            "translated_keys": translated_keys,
            "progress":        progress,
            "has_es":          has_es
        })

    output = BASE / "file_catalog.json"
    output.write_text(json.dumps(catalog, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Catalogo actualizado: {len(catalog)} archivos procesados.")

if __name__ == "__main__":
    main()
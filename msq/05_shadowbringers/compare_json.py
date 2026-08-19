import argparse
import json
import re
import sys
from pathlib import Path


def detect_duplicate_keys(ordered_pairs):
    """Lanza un ValueError si un objeto contiene claves duplicadas en el mismo nivel."""
    d = {}
    for key, value in ordered_pairs:
        if key in d:
            raise ValueError(f"Clave duplicada encontrada en el mismo nivel: '{key}'")
        d[key] = value
    return d


def extract_placeholders(text):
    """Extrae patrones comunes de variables e interpolación (ej: {name}, {0}, %s, <tag>)."""
    if not isinstance(text, str):
        return []
    # Captura llaves {var}, formato printf %s/%d y etiquetas <tag>
    patterns = r"(\{[^{}]*\}|%[a-zA-Z]|<[^>]+>)"
    return sorted(re.findall(patterns, text))


def deep_inspect_translations(data1, data2, path=""):
    """Revisa estructura, claves, orden, placeholders e inconsistencias de tipos."""
    errors = []
    warnings = []

    # 1. Validación de tipos
    if type(data1) is not type(data2):
        errors.append(
            f"Tipo incompatible en '{path or 'root'}': {type(data1).__name__} != {type(data2).__name__}"
        )
        return errors, warnings

    # 2. Diccionarios (Objetos)
    if isinstance(data1, dict):
        keys1 = list(data1.keys())
        keys2 = list(data2.keys())

        if keys1 != keys2:
            missing_in_2 = set(keys1) - set(keys2)
            missing_in_1 = set(keys2) - set(keys1)

            if missing_in_2:
                errors.append(f"Claves faltantes en Archivo 2 en '{path or 'root'}': {list(missing_in_2)}")
            if missing_in_1:
                errors.append(f"Claves sobrantes en Archivo 2 en '{path or 'root'}': {list(missing_in_1)}")

            if not missing_in_1 and not missing_in_2:
                errors.append(
                    f"Orden desalineado en '{path or 'root'}':\n"
                    f"  - Archivo 1: {keys1}\n"
                    f"  - Archivo 2: {keys2}"
                )

        common_keys = [k for k in keys1 if k in data2]
        for key in common_keys:
            current_path = f"{path}.{key}" if path else key
            sub_err, sub_warn = deep_inspect_translations(data1[key], data2[key], current_path)
            errors.extend(sub_err)
            warnings.extend(sub_warn)

    # 3. Listas (Arrays)
    elif isinstance(data1, list):
        if len(data1) != len(data2):
            errors.append(f"Longitud de array diferente en '{path}': {len(data1)} vs {len(data2)}")

        for idx, (item1, item2) in enumerate(zip(data1, data2)):
            current_path = f"{path}[{idx}]"
            sub_err, sub_warn = deep_inspect_translations(item1, item2, current_path)
            errors.extend(sub_err)
            warnings.extend(sub_warn)

    # 4. Strings (Valores de traducción)
    elif isinstance(data1, str):
        # Alerta por texto vacío
        if not data1.strip() and data2.strip():
            warnings.append(f"Texto vacío en Archivo 1 en '{path}' pero con contenido en Archivo 2")
        elif data1.strip() and not data2.strip():
            warnings.append(f"Texto vacío en Archivo 2 en '{path}' pero con contenido en Archivo 1")

        # Inconsistencia en variables / placeholders / tags
        tags1 = extract_placeholders(data1)
        tags2 = extract_placeholders(data2)
        if tags1 != tags2:
            warnings.append(
                f"Discrepancia de variables/tags en '{path}':\n"
                f"    - Archivo 1 tiene: {tags1}\n"
                f"    - Archivo 2 tiene: {tags2}"
            )

    return errors, warnings


def parse_json_file(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f, object_pairs_hook=detect_duplicate_keys)


def main():
    parser = argparse.ArgumentParser(
        description="Audita claves duplicadas, estructura y consistencia de strings JSON."
    )
    parser.add_argument("file1", type=str, help="Primer archivo JSON")
    parser.add_argument("file2", type=str, help="Segundo archivo JSON")
    args = parser.parse_args()

    base_dir = Path.cwd()
    p1, p2 = base_dir / args.file1, base_dir / args.file2

    # Parseo y detección de duplicados directos
    data = {}
    for path, name in [(p1, args.file1), (p2, args.file2)]:
        if not path.is_file():
            print(f"Error: No se encontró '{name}' en {base_dir}")
            sys.exit(1)
        try:
            data[name] = parse_json_file(path)
        except ValueError as e:
            print(f"✗ Error de duplicado en '{name}': {e}")
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"✗ Error de sintaxis JSON en '{name}': {e}")
            sys.exit(1)

    errors, warnings = deep_inspect_translations(data[args.file1], data[args.file2])

    if warnings:
        print(f"⚠ Se detectaron {len(warnings)} advertencia(s) en las cadenas de traducción:")
        for w in warnings:
            print(f"  • {w}")
        print()

    if errors:
        print(f"✗ Se detectaron {len(errors)} error(es) estructurales críticos:")
        for err in errors:
            print(f"  • {err}")
        sys.exit(1)

    if not errors and not warnings:
        print("✓ Todo impecable: Sin claves duplicadas, estructura idéntica y variables alineadas.")


if __name__ == "__main__":
    main()
import argparse
import csv
from collections import Counter
from pathlib import Path

from fetch_entidades import download_entidades


REQUIRED_FIELDS = {
    "id_tipo_entidad",
    "id_nivel_institucional",
    "id_padre",
}


def normalize_key(value):
    if value is None:
        return ""
    return str(value).strip()


def read_entidades(input_path: str):
    input_file = Path(input_path)

    with input_file.open("r", newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        fieldnames = set(reader.fieldnames or [])
        missing_fields = REQUIRED_FIELDS - fieldnames
        if missing_fields:
            missing = ", ".join(sorted(missing_fields))
            raise ValueError(f"Faltan campos requeridos en el CSV: {missing}")
        return list(reader)


def write_resumen(rows, output_path: str):
    counts = Counter()
    parent_ids = set()

    for row in rows:
        entity_type = normalize_key(row.get("id_tipo_entidad"))
        institutional_level = normalize_key(row.get("id_nivel_institucional"))
        parent_id = normalize_key(row.get("id_padre"))
        counts[(entity_type, institutional_level, parent_id)] += 1
        parent_ids.add(parent_id)

    ordered_parents = sorted(parent_ids)
    grouped_keys = sorted({
        (entity_type, institutional_level)
        for entity_type, institutional_level, _ in counts
    })

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with output_file.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([
            "id_tipo_entidad",
            "id_nivel_institucional",
            *ordered_parents,
        ])
        for entity_type, institutional_level in grouped_keys:
            writer.writerow([
                entity_type,
                institutional_level,
                *[
                    counts[(entity_type, institutional_level, parent_id)]
                    for parent_id in ordered_parents
                ],
            ])

    print(
        f"Resumen generado: {output_file} | "
        f"{len(grouped_keys)} grupos | {len(ordered_parents)} padres"
    )


def resumen_entidades(input_path: str, output_path: str):
    input_file = Path(input_path)
    if not input_file.exists():
        print(f"No existe {input_file}; descargando el CSV crudo.")
        download_entidades(str(input_file))

    rows = read_entidades(str(input_file))
    write_resumen(rows, output_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Genera una matriz de entidades por tipo, nivel y padre"
    )
    parser.add_argument(
        "--input",
        default="results/entidades_maestro.csv",
        help="CSV crudo de entidades",
    )
    parser.add_argument(
        "--output",
        default="results/resumen_entidades.csv",
        help="CSV resumen de entidades",
    )
    args = parser.parse_args()

    resumen_entidades(args.input, args.output)
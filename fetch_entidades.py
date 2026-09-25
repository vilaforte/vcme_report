import argparse
import csv
import json
from pathlib import Path

import requests


API_URL = "https://www.gob.bo/ws/api/publico/entidades"


def fetch_entidades(api_url: str = API_URL):
    response = requests.get(
        api_url,
        headers={"Accept": "application/json"},
        timeout=60,
    )
    response.raise_for_status()

    try:
        payload = response.json()
    except ValueError as exc:
        raise ValueError(
            f"La respuesta no es JSON válido: {response.text[:300]}"
        ) from exc

    if isinstance(payload, list):
        return payload

    if isinstance(payload, dict) and isinstance(payload.get("datos"), list):
        return payload["datos"]

    raise ValueError("La respuesta no contiene una lista de registros en 'datos'")


def normalize_csv_value(value):
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return value


def write_entidades_csv(rows, output_path: str):
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = []

    for row in rows:
        if isinstance(row, dict):
            for key in row:
                if key not in fieldnames:
                    fieldnames.append(key)

    with output_file.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(
            csvfile,
            fieldnames=fieldnames,
            extrasaction="ignore",
        )
        if fieldnames:
            writer.writeheader()
            for row in rows:
                if isinstance(row, dict):
                    writer.writerow({
                        key: normalize_csv_value(value)
                        for key, value in row.items()
                    })

    print(f"Se guardaron {len(rows)} registros en {output_file}")


def download_entidades(output_path: str, api_url: str = API_URL):
    rows = fetch_entidades(api_url)
    write_entidades_csv(rows, output_path)
    return rows


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Descarga las entidades y las guarda en un CSV"
    )
    parser.add_argument(
        "--output",
        default="results/entidades_maestro.csv",
        help="Ruta del CSV crudo de entidades",
    )
    parser.add_argument(
        "--url",
        default=API_URL,
        help="URL del endpoint de entidades",
    )
    args = parser.parse_args()

    download_entidades(args.output, api_url=args.url)
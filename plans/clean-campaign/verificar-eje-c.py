#!/usr/bin/env python3
"""Comprueba que la sección del eje C de MARCO-DECLARADO.md dice lo que dice el
almacén.

Existe porque un documento que cita cifras puede desviarse de ellas sin que nada
lo grite, y esta campaña ya perdió un día por una corrección que vivía en una
conversación y no en un fichero. Aquí las cifras se re-derivan de `job_event` en
cada ejecución y se comparan carácter a carácter con lo escrito.

Falla con exit 1 si cualquier celda de la rejilla, cualquier fila de la tabla de
resumen o cualquiera de los recuentos agregados difiere. Se prueba a sí mismo:
`--autoprueba` altera una cifra en memoria y confirma que el fallo salta.
"""
from __future__ import annotations

import argparse
import os
import pathlib
import re
import subprocess
import sys

DOC = pathlib.Path(__file__).with_name("MARCO-DECLARADO.md")

#: (job, eje, sustrato, variante). La identidad de cada comparación va aquí y no
#: se deduce de la base: un job se localiza por su id, no por parecerse.
TRABAJOS = [
    ("8d7e1a9e-2a47-4ce3-9fcf-a26f78adccc0", "autoexclusion", "ankh_large", "B"),
    ("76199173-8ba8-4537-9355-601fe2ab8214", "autoexclusion", "ankh_large", "A"),
    ("4a4983e8-0eb7-4191-a420-d2d4fecd6cf8", "autoexclusion", "protst", "B"),
    ("bbc57c0b-5606-49e8-8830-aad5bdf02fbf", "autoexclusion", "protst", "A"),
    ("09f3b01b-a403-415b-a021-b999a2e643e6", "autoexclusion", "prot_t5", "B"),
    ("26bb49b5-57f7-4c6d-bd22-bf8cf48ff82f", "autoexclusion", "prot_t5", "A"),
    ("331b7b78-5ebb-4e2a-a306-c883b22ad580", "aspecto", "ankh_large", "B"),
    ("c344f26c-8abd-49fa-9a2f-aef6b6ee6371", "aspecto", "ankh_large", "A"),
    ("d2874f2a-1870-4fe7-b377-4ce9ed4a6d92", "aspecto", "protst", "B"),
    ("bffa80e4-3c46-4405-9c17-6c257a6ed23a", "aspecto", "protst", "A"),
    ("26669632-fe40-4574-9139-58cc8f89aab8", "aspecto", "prot_t5", "B"),
    ("4c75d29d-b7f2-48dd-ba49-b88ab4ee8c0f", "aspecto", "prot_t5", "A"),
    # Las otras dos perillas, 2026-09-09.
    ("5e8a26ec-b199-411a-8570-a2be6d14ddc1", "donante", "ankh_large", "B"),
    ("5e1a31ed-2902-4272-b973-5e3c3fb30348", "donante", "ankh_large", "A"),
    ("9ad0ae6e-0b2d-4bf4-a2cc-202abc14bfc6", "donante", "protst", "B"),
    ("526dfca8-75a9-46d8-aa98-cc3457bf2491", "donante", "protst", "A"),
    ("2e8c56f4-9399-49f6-81af-9ffe9df7f863", "donante", "prot_t5", "B"),
    ("782dc933-f8a9-422b-aa19-81ecd1af96b8", "donante", "prot_t5", "A"),
    ("552002f3-fb37-409e-9630-593d619afe86", "ancestros", "ankh_large", "B"),
    ("81a766e8-0d7b-4b1f-84d8-07e42aa1b933", "ancestros", "ankh_large", "A"),
    ("67d7f31f-78ae-4e7c-b5fd-bbca7f18fb17", "ancestros", "protst", "B"),
    ("0f246c23-5354-436a-80ca-63de427ed0b2", "ancestros", "protst", "A"),
    ("60cbbc8b-3ab9-45e4-befe-8692cd9476c4", "ancestros", "prot_t5", "B"),
    ("021fba32-137b-4f0c-a0d9-73ff93200a20", "ancestros", "prot_t5", "A"),
]

PANELES = ["LK:BPO", "LK:CCO", "LK:MFO", "NK:BPO", "NK:CCO", "NK:MFO",
           "PK:BPO", "PK:CCO", "PK:MFO"]


def url() -> str:
    env = pathlib.Path(__file__).resolve().parents[3] / "PROTEA" / ".env"
    for line in env.read_text().splitlines():
        if line.startswith("PROTEA_DB_URL="):
            return line.split("=", 1)[1].strip().strip('"\'').replace(
                "postgresql+psycopg://", "postgresql://")
    raise SystemExit("no encuentro PROTEA_DB_URL")


def paneles(dsn: str) -> dict:
    """(job, panel) -> (delta, resuelve, estado). Una consulta, sin agregar."""
    ids = ",".join(f"'{j}'" for j, *_ in TRABAJOS)
    sql = (
        "SELECT job_id::text, fields->>'panel', "
        "       to_char((fields->>'delta')::numeric,'0.0000'), "
        "       (fields->>'resolves')::text, fields->>'status' "
        f"  FROM job_event WHERE job_id IN ({ids}) "
        "   AND event='compare_paired_panels.panel' ORDER BY 1,2"
    )
    out = subprocess.run(["psql", dsn, "-qAt", "-F", "\t", "-c", sql],
                         capture_output=True, text=True, check=True).stdout
    filas = {}
    for ln in out.strip().split("\n"):
        job, panel, delta, resuelve, estado = ln.split("\t")
        filas[(job, panel)] = (delta.strip(), resuelve == "true", estado)
    return filas


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--autoprueba", action="store_true",
                    help="altera una cifra en memoria y confirma que el fallo salta")
    a = ap.parse_args()

    doc = DOC.read_text()
    filas = paneles(url())

    esperados = 9 * len(TRABAJOS)
    if len(filas) != esperados:
        print(f"el almacen da {len(filas)} paneles y se esperaban {esperados}",
              file=sys.stderr)
        return 1

    fallos = []

    # 1. La rejilla panel a panel de la variante B de auto-exclusion.
    B = {s: j for j, e, s, v in TRABAJOS if e == "autoexclusion" and v == "B"}
    for panel in PANELES:
        cols = [filas[(B[s], panel)][0].replace("-", "−")
                for s in ("ankh_large", "protst", "prot_t5")]
        if a.autoprueba and panel == "LK:CCO":
            cols[0] = "−0,9999"
        fila = "| " + panel + " | " + " | ".join(c.replace(".", ",") for c in cols) + " |"
        if fila not in doc:
            fallos.append(f"la rejilla no lleva esta fila:\n  {fila}")

    # 2. La tabla de resumen del eje de aspecto.
    for j, eje, s, v in TRABAJOS:
        if eje != "aspecto":
            continue
        p = [filas[(j, k)] for k in PANELES]
        res = sum(1 for d, r, _ in p if r)
        pos = sum(1 for d, r, _ in p if float(d.replace(",", ".")) > 0)
        fila = f"| {s} | {v} | {res}/9 | {pos} |"
        if fila not in doc:
            fallos.append(f"la tabla de resumen no lleva esta fila:\n  {fila}")

    # 2-bis. Las rejillas de las otras dos perillas. Llevan signo explicito
    # porque una de ellas es la primera que GANA, y un signo perdido en el
    # documento invertiria el veredicto sin cambiar ninguna cifra.
    for eje in ("donante", "ancestros"):
        B2 = {s: j for j, e, s, v in TRABAJOS if e == eje and v == "B"}
        if not B2:
            continue
        for panel in PANELES:
            cols = []
            for s in ("ankh_large", "protst", "prot_t5"):
                d = filas[(B2[s], panel)][0]
                # El signo se escribe SIEMPRE, tambien el mas: una de estas dos
                # perillas es la unica que gana, y un signo perdido invierte el
                # veredicto sin cambiar ninguna cifra.
                cols.append(("\u2212" + d[1:]) if d.startswith("-") else ("+" + d))
            if a.autoprueba and eje == "ancestros" and panel == "NK:MFO":
                cols[0] = "\u22120,0400"
            fila = "| " + panel + " | " + " | ".join(
                c.replace(".", ",") for c in cols) + " |"
            if fila not in doc:
                fallos.append(f"la rejilla de {eje} no lleva esta fila:\n  {fila}")

    # 3. Los agregados que el texto afirma en prosa.
    auto = [filas[(j, k)] for j, e, *_ in TRABAJOS if e == "autoexclusion"
            for k in PANELES if (j, k) in filas]
    n_res = sum(1 for d, r, _ in auto if r)
    n_ok = sum(1 for d, r, st in auto if st == "ok")
    if (n_res, n_ok) != (54, 54):
        fallos.append(f"auto-exclusion: {n_res} resuelven y {n_ok} con estado ok, "
                      "y el texto dice 54 y 54")
    asp = [filas[(j, k)] for j, e, *_ in TRABAJOS if e == "aspecto"
           for k in PANELES if (j, k) in filas]
    a_res = sum(1 for d, r, _ in asp if r)
    a_nul = sum(1 for d, r, st in asp if st == "null_with_power")
    if (a_res, a_nul) != (31, 23):
        fallos.append(f"aspecto: {a_res} resuelven y {a_nul} son null_with_power, "
                      "y el texto dice 31 y 23")
    if any(float(d.replace(",", ".")) > 0 for d, _, _ in auto + asp):
        fallos.append("hay un delta positivo, y el texto dice que ninguno lo es")

    don = [filas[(j, k)] for j, e, *_ in TRABAJOS if e == "donante"
           for k in PANELES if (j, k) in filas]
    if don:
        d_res = sum(1 for d, r, _ in don if r)
        d_pos = sum(1 for d, _, _ in don if float(d.replace(",", ".")) > 0)
        if (d_res, d_pos) != (54, 0):
            fallos.append(f"donante: {d_res} resuelven y {d_pos} positivos, "
                          "y el texto dice 54 y ninguno")
    anc = [filas[(j, k)] for j, e, *_ in TRABAJOS if e == "ancestros"
           for k in PANELES if (j, k) in filas]
    if anc:
        a_res = sum(1 for d, r, _ in anc if r)
        a_pos = sum(1 for d, _, _ in anc if float(d.replace(",", ".")) > 0)
        if (a_res, a_pos) != (54, 54):
            fallos.append(f"ancestros: {a_res} resuelven y {a_pos} positivos, "
                          "y el texto dice 54 y 54 -- es la unica perilla que gana, "
                          "asi que un signo perdido aqui invierte el veredicto")

    if fallos:
        print("EL DOCUMENTO Y EL ALMACEN NO COINCIDEN", file=sys.stderr)
        for f in fallos:
            print("  " + f, file=sys.stderr)
        return 1
    print(f"eje C: {len(filas)} paneles de {len(TRABAJOS)} trabajos coinciden "
          "con el almacen")
    return 0


if __name__ == "__main__":
    sys.exit(main())

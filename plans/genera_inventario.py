"""Generate the window inventory from the database. Read-only.

Not written by hand: an inventory somebody maintains by hand is an inventory
that lies the moment one more window is generated. Re-run it instead.
"""
import os
import sys
from sqlalchemy import create_engine, text

PERFIL = {
    ("as_closed", "pivot_terms", "any"): "viejo",
    ("projected", "live_in_both_ends", "experimental"): "campana",
}

SQL = """
SELECT es.id::text, aso.source_version AS t0, asn.source_version AS t1,
       es.truth_profile, es.toi_rule, es.not_codes,
       es.pivot_snapshot_id::text, piv.obo_version,
       es.old_native_snapshot_id::text, es.new_native_snapshot_id::text,
       aso.ontology_snapshot_id::text, asn.ontology_snapshot_id::text,
       es.window_role, es.created_at::date,
       (es.stats->>'delta_proteins')::int AS delta,
       (SELECT count(*) FROM evaluation_result er WHERE er.evaluation_set_id=es.id) AS res,
       (SELECT e.fields->>'code_revision' FROM job_event e
         WHERE e.job_id=es.job_id AND e.event='job.started' LIMIT 1) AS rev
FROM evaluation_set es
JOIN annotation_set aso ON aso.id=es.old_annotation_set_id
JOIN annotation_set asn ON asn.id=es.new_annotation_set_id
JOIN ontology_snapshot piv ON piv.id=es.pivot_snapshot_id
ORDER BY (regexp_replace(aso.source_version,'[^0-9]','','g'))::int,
         (regexp_replace(asn.source_version,'[^0-9]','','g'))::int,
         es.created_at
"""


def construccion(f):
    """(A) closes both ends under the pivot; (B) each end under its own era."""
    if f[8] == f[6] and f[9] == f[6]:
        return "A"
    if f[8] == f[10] and f[9] == f[11]:
        return "B"
    return f"{f[8][:4]}-{f[9][:4]}"


def etiqueta(f):
    perfil = PERFIL.get((f[3], f[4], f[5]), f"{f[3][:4]}-{f[4][:4]}-{f[5][:3]}")
    return f"{f[1]}-{f[2]}.{perfil}.{f[6][:8]}.{construccion(f)}"


QUE_ES = {
    "ea0f4334": "**LA ventana de validacion larga.** El laboratorio la reproduce al bit; sus "
                "9 `replaced_by` y su proyeccion 2.610/3.821 son numeros publicados",
    "44cd7a5b": "**La banda PROSPECTIVA.** Empieza despues del holdout y no selecciona nada; "
                "sus cuatro puntuaciones llevan `PROSPECTIVE_DECLARATION`",
    "cb46395a": "**EL HOLDOUT. Su pase se gasto el 2026-10-26 EN EL LABORATORIO** (0,4471 "
                "contra 0,2605), no aqui, por eso tiene cero resultados en PROTEA. El "
                "silencio de esta tabla no dice nada sobre el mundo. NO se reconstruye y NO "
                "se borra",
    "ea94e57e": "La MISMA 211->227 con el marco viejo, tambien marcada `valid`. Quien lea "
                "\"la de validacion\" sin mirar el perfil puede coger esta",
    "7aa37929": "Otra 211->227 vieja marcada `valid`, `as_closed` a 39.885, y **nunca fue "
                "el titular**. Cero resultados, y aun asi lleva papel: no se borra",
    "c35ee267": "Serie vieja con tres resultados pegados. La unica `viejo` sin papel que "
                "tiene evidencia, asi que **no entra en ningun borrado**",
    "3bd720c9": "La (A) de 160->177, construida con el remapeo ROTO (revision 8ab6487f). Su "
                "verdad es la vieja y **no se puede reconstruir en su sitio**: los ocho "
                "campos de identidad son los mismos y la restriccion unica la rechaza",
    "e84dfec8": "La (B) gemela de 160->177, para la comparacion (A)/(B). Su verdad es "
                "identica al byte con el arreglo del remapeo",
    "56225292": "La primera construida con el remapeo ARREGLADO (revision 637b3517), para "
                "validar el despliegue de punta a punta y medir el coste real: 173 s",
}


def main() -> None:
    with create_engine(os.environ["PROTEA_DB_URL"]).connect() as c:
        filas = c.execute(text(SQL)).fetchall()
    out = sys.stdout.write

    etqs = [etiqueta(f) for f in filas]
    colisiones = len(etqs) - len(set(etqs))

    out("# Inventario de las ventanas de evaluacion: nombradas y descritas\n\n")
    out(f"**{len(filas)} ventanas, generadas desde la base el 2026-11-08** por "
        "`plans/genera_inventario.py`. No se escribe a mano: un inventario que alguien "
        "mantiene a mano es un inventario que miente en cuanto se genera una ventana mas.\n\n")
    out("## Por que hace falta nombrarlas\n\n")
    out("El par de conjuntos de anotaciones **dejo de identificar una ventana**: los tres "
        "grafos de propagacion y las tres reglas de verdad entraron en la clave. Hoy **62 "
        "de 69 pares distintos llevan mas de una**, asi que la exportacion se niega en 62 "
        "de 69 pares, y no hay forma de decir \"la ventana de 204->205\" sin decir cual.\n\n")
    out("La etiqueta es `<t0>-<t1>.<perfil>.<pivote>.<construccion>`:\n\n"
        "* `perfil`: **`campana`** es el marco vivo "
        "(`projected`/`live_in_both_ends`/`experimental`) y **`viejo`** el superado "
        "(`as_closed`/`pivot_terms`/`any`);\n"
        "* `construccion`: **A** cierra los dos extremos bajo el pivote, **B** cada "
        "extremo bajo su propia era. La primera version de esta etiqueta no lo llevaba y "
        "colisionaba en dos casos, que son justo la (A) y la (B) de 160->177.\n\n")
    out(f"Colisiones ahora: **{colisiones}**"
        f"{' (la etiqueta identifica)' if not colisiones else ' -- USAR EL ID'}.\n\n")

    con_papel = [f for f in filas if f[12]]
    out("## Las que NO se tocan: las cinco con papel declarado\n\n")
    out("**El recuento de resultados NO sirve para decidir si una ventana es desechable**, "
        "y esta es la prueba: el holdout tiene cero. Su unica mirada se tomo en el "
        "laboratorio, y las tablas de la plataforma no ven el laboratorio. Un filtro de "
        "\"sin resultados\" lo habria incluido en un borrado.\n\n")
    out("| etiqueta | id | tramo | papel | resultados | delta | que es |\n")
    out("|---|---|---|---|---|---|---|\n")
    for f in con_papel:
        out(f"| `{etiqueta(f)}` | `{f[0][:8]}` | {f[1]}->{f[2]} | **{f[12]}** | {f[15]} "
            f"| {f[14]:,} | {QUE_ES.get(f[0][:8],'')} |\n")

    camp = [f for f in filas if PERFIL.get((f[3], f[4], f[5])) == "campana"]
    out(f"\n## El marco vivo: {len(camp)} ventanas `campana`\n\n")
    out("| etiqueta | id | tramo | pivote | constr. | papel | delta | revision | dia | que es |\n")
    out("|---|---|---|---|---|---|---|---|---|---|\n")
    for f in camp:
        out(f"| `{etiqueta(f)}` | `{f[0][:8]}` | {f[1]}->{f[2]} | {f[7]} "
            f"| {construccion(f)} | {f[12] or '-'} | {f[14]:,} "
            f"| `{(f[16] or 'NULL')[:8]}` | {f[13]} | {QUE_ES.get(f[0][:8],'')} |\n")

    viejo = [f for f in filas if PERFIL.get((f[3], f[4], f[5])) == "viejo"]
    borrables = [f for f in viejo if f[15] == 0 and not f[12]]
    out(f"\n## El marco superado: {len(viejo)} ventanas `viejo`\n\n")
    out("Construidas del 8 al 11 de octubre con el codigo que tardaba **74 minutos por "
        "ventana**, cada una pivotando en **su propia era** en vez de en un pivote comun, "
        "con `as_closed` (un termino que el pivote no puede nombrar lo tira el cierre) y "
        "`not_codes = any` (un `NOT|IBA` quita verdad a positivos experimentales).\n\n")
    out(f"**Ninguna corrida de la campana debe nombrar una de estas.** De las {len(viejo)}, "
        f"**{len(borrables)} no tienen ni resultados ni papel** y serian las candidatas si "
        "alguna vez se decide limpiar. Borrarlas es una decision aparte: deja sus parquets "
        "huerfanos en MinIO y cuesta unas 6 horas deshacer con el codigo de hoy.\n\n")
    out("| etiqueta | id | tramo | pivote | papel | resultados | delta | dia |\n")
    out("|---|---|---|---|---|---|---|---|\n")
    for f in viejo:
        marca = "**NO BORRAR**" if (f[12] or f[15]) else ""
        out(f"| `{etiqueta(f)}` | `{f[0][:8]}` | {f[1]}->{f[2]} | {f[7]} "
            f"| {f[12] or '-'} | {f[15]} | {f[14]:,} | {f[13]} | {marca}\n".replace(" | \n", " |\n"))

    otros = [f for f in filas if PERFIL.get((f[3], f[4], f[5])) is None]
    if otros:
        out(f"\n## Ni uno ni otro: {len(otros)} con reglas mezcladas\n\n")
        out("| etiqueta | id | tramo | perfil | toi | not_codes | resultados |\n")
        out("|---|---|---|---|---|---|---|\n")
        for f in otros:
            out(f"| `{etiqueta(f)}` | `{f[0][:8]}` | {f[1]}->{f[2]} | {f[3]} | {f[4]} "
                f"| {f[5]} | {f[15]} |\n")

    sin_rev = sum(1 for f in filas if not f[16])
    out("\n## Y lo que el inventario no puede decir\n\n")
    out(f"**{sin_rev} de {len(filas)} ventanas no dicen con que codigo se construyeron.** El "
        "sello de revision aterrizo en el trabajador despues del 27 de octubre, asi que para "
        "esas la unica via es casar su fecha contra los bloques de `DECLARED-REVISION.txt`, "
        "que es arqueologia. PROTEA #1140 anade la columna y rellena las que se pueden "
        "rellenar; las demas se quedan NULL en vez de inferirse de la fecha, porque una "
        "fecha mapea a una declaracion y no a un proceso.\n")


if __name__ == "__main__":
    main()

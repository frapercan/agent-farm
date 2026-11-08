# Inventario de las ventanas de evaluacion: nombradas y descritas

**87 ventanas, generadas desde la base el 2026-11-08** por `plans/genera_inventario.py`. No se escribe a mano: un inventario que alguien mantiene a mano es un inventario que miente en cuanto se genera una ventana mas.

## Por que hace falta nombrarlas

El par de conjuntos de anotaciones **dejo de identificar una ventana**: los tres grafos de propagacion y las tres reglas de verdad entraron en la clave. Hoy **62 de 69 pares distintos llevan mas de una**, asi que la exportacion se niega en 62 de 69 pares, y no hay forma de decir "la ventana de 204->205" sin decir cual.

La etiqueta es `<t0>-<t1>.<perfil>.<pivote>.<construccion>`:

* `perfil`: **`campana`** es el marco vivo (`projected`/`live_in_both_ends`/`experimental`) y **`viejo`** el superado (`as_closed`/`pivot_terms`/`any`);
* `construccion`: **A** cierra los dos extremos bajo el pivote, **B** cada extremo bajo su propia era. La primera version de esta etiqueta no lo llevaba y colisionaba en dos casos, que son justo la (A) y la (B) de 160->177.

Colisiones ahora: **0** (la etiqueta identifica).

## Las que NO se tocan: las cinco con papel declarado

**El recuento de resultados NO sirve para decidir si una ventana es desechable**, y esta es la prueba: el holdout tiene cero. Su unica mirada se tomo en el laboratorio, y las tablas de la plataforma no ven el laboratorio. Un filtro de "sin resultados" lo habria incluido en un borrado.

| etiqueta | id | tramo | papel | resultados | delta | que es |
|---|---|---|---|---|---|---|
| `211-227.viejo.15f002ea.B` | `ea94e57e` | 211->227 | **valid** | 2 | 63,734 | La MISMA 211->227 con el marco viejo, tambien marcada `valid`. Quien lea "la de validacion" sin mirar el perfil puede coger esta |
| `211-227.viejo.15f002ea.A` | `7aa37929` | 211->227 | **valid** | 0 | 39,885 | Otra 211->227 vieja marcada `valid`, `as_closed` a 39.885, y **nunca fue el titular**. Cero resultados, y aun asi lleva papel: no se borra |
| `211-227.campana.15f002ea.A` | `ea0f4334` | 211->227 | **valid** | 12 | 40,531 | **LA ventana de validacion larga.** El laboratorio la reproduce al bit; sus 9 `replaced_by` y su proyeccion 2.610/3.821 son numeros publicados |
| `227-230.viejo.28c785ca.B` | `cb46395a` | 227->230 | **test** | 0 | 21,996 | **EL HOLDOUT. Su pase se gasto el 2026-10-26 EN EL LABORATORIO** (0,4471 contra 0,2605), no aqui, por eso tiene cero resultados en PROTEA. El silencio de esta tabla no dice nada sobre el mundo. NO se reconstruye y NO se borra |
| `230-235.campana.2146c369.A` | `44cd7a5b` | 230->235 | **test** | 4 | 28,220 | **La banda PROSPECTIVA.** Empieza despues del holdout y no selecciona nada; sus cuatro puntuaciones llevan `PROSPECTIVE_DECLARATION` |

## El marco vivo: 83 ventanas `campana`

| etiqueta | id | tramo | pivote | constr. | papel | delta | revision | dia | que es |
|---|---|---|---|---|---|---|---|---|---|
| `156-157.campana.15f002ea.A` | `d87aa1e7` | 156->157 | releases/2022-07-01 | A | - | 5,399 | `d5416224` | 2026-11-08 |  |
| `157-158.campana.15f002ea.A` | `2170cc93` | 157->158 | releases/2022-07-01 | A | - | 6,553 | `d5416224` | 2026-11-08 |  |
| `158-159.campana.15f002ea.A` | `e3639c55` | 158->159 | releases/2022-07-01 | A | - | 4,910 | `d5416224` | 2026-11-08 |  |
| `159-160.campana.15f002ea.A` | `96646bb4` | 159->160 | releases/2022-07-01 | A | - | 8,469 | `d5416224` | 2026-11-08 |  |
| `160-161.campana.15f002ea.A` | `983f3a65` | 160->161 | releases/2022-07-01 | A | - | 5,369 | `d5416224` | 2026-11-08 |  |
| `160-177.campana.15f002ea.B` | `e84dfec8` | 160->177 | releases/2022-07-01 | B | - | 57,232 | `8ab6487f` | 2026-11-07 | La (B) gemela de 160->177, para la comparacion (A)/(B). Su verdad es identica al byte con el arreglo del remapeo |
| `160-177.campana.15f002ea.A` | `d3c8cd2e` | 160->177 | releases/2022-07-01 | A | - | 31,871 | `d5416224` | 2026-11-08 |  |
| `161-162.campana.15f002ea.A` | `a5933668` | 161->162 | releases/2022-07-01 | A | - | 12,564 | `d5416224` | 2026-11-08 |  |
| `162-163.campana.15f002ea.A` | `d82e9b2f` | 162->163 | releases/2022-07-01 | A | - | 5,127 | `d5416224` | 2026-11-08 |  |
| `163-164.campana.15f002ea.A` | `fa7ea497` | 163->164 | releases/2022-07-01 | A | - | 7,580 | `d5416224` | 2026-11-08 |  |
| `164-165.campana.15f002ea.A` | `c197ba4b` | 164->165 | releases/2022-07-01 | A | - | 7,148 | `d5416224` | 2026-11-08 |  |
| `165-166.campana.15f002ea.A` | `b4533108` | 165->166 | releases/2022-07-01 | A | - | 6,769 | `d5416224` | 2026-11-08 |  |
| `166-167.campana.15f002ea.A` | `40136294` | 166->167 | releases/2022-07-01 | A | - | 5,360 | `d5416224` | 2026-11-08 |  |
| `167-168.campana.15f002ea.A` | `4a9f58ae` | 167->168 | releases/2022-07-01 | A | - | 5,374 | `d5416224` | 2026-11-08 |  |
| `168-169.campana.15f002ea.A` | `72ea69b1` | 168->169 | releases/2022-07-01 | A | - | 6,378 | `d5416224` | 2026-11-08 |  |
| `169-170.campana.15f002ea.A` | `56dfa71c` | 169->170 | releases/2022-07-01 | A | - | 5,189 | `d5416224` | 2026-11-08 |  |
| `170-171.campana.15f002ea.A` | `522d02bc` | 170->171 | releases/2022-07-01 | A | - | 6,741 | `d5416224` | 2026-11-08 |  |
| `171-172.campana.15f002ea.A` | `f845afdf` | 171->172 | releases/2022-07-01 | A | - | 4,942 | `d5416224` | 2026-11-08 |  |
| `172-173.campana.15f002ea.A` | `f986e445` | 172->173 | releases/2022-07-01 | A | - | 5,793 | `d5416224` | 2026-11-08 |  |
| `173-174.campana.15f002ea.A` | `2feada67` | 173->174 | releases/2022-07-01 | A | - | 5,103 | `d5416224` | 2026-11-08 |  |
| `174-175.campana.15f002ea.A` | `2cd5f200` | 174->175 | releases/2022-07-01 | A | - | 5,775 | `d5416224` | 2026-11-08 |  |
| `174-202.campana.15f002ea.A` | `899cba71` | 174->202 | releases/2022-07-01 | A | - | 41,863 | `8cc344b0` | 2026-11-08 |  |
| `175-176.campana.15f002ea.A` | `73252908` | 175->176 | releases/2022-07-01 | A | - | 5,369 | `d5416224` | 2026-11-08 |  |
| `176-177.campana.15f002ea.A` | `597715b2` | 176->177 | releases/2022-07-01 | A | - | 5,794 | `d5416224` | 2026-11-08 |  |
| `177-178.campana.15f002ea.A` | `16e315b9` | 177->178 | releases/2022-07-01 | A | - | 4,979 | `d5416224` | 2026-11-08 |  |
| `178-179.campana.15f002ea.A` | `7369e486` | 178->179 | releases/2022-07-01 | A | - | 8,131 | `d5416224` | 2026-11-08 |  |
| `178-204.campana.15f002ea.A` | `2a74f7cb` | 178->204 | releases/2022-07-01 | A | - | 40,561 | `8cc344b0` | 2026-11-08 |  |
| `179-180.campana.15f002ea.A` | `16a80269` | 179->180 | releases/2022-07-01 | A | - | 6,263 | `d5416224` | 2026-11-08 |  |
| `180-181.campana.15f002ea.A` | `1a9148a0` | 180->181 | releases/2022-07-01 | A | - | 6,357 | `d5416224` | 2026-11-08 |  |
| `181-182.campana.15f002ea.A` | `4220a313` | 181->182 | releases/2022-07-01 | A | - | 8,308 | `d5416224` | 2026-11-08 |  |
| `182-183.campana.15f002ea.A` | `c5277415` | 182->183 | releases/2022-07-01 | A | - | 3,976 | `d5416224` | 2026-11-08 |  |
| `183-184.campana.15f002ea.A` | `2337fd69` | 183->184 | releases/2022-07-01 | A | - | 6,866 | `d5416224` | 2026-11-08 |  |
| `183-205.campana.15f002ea.A` | `1d61bbad` | 183->205 | releases/2022-07-01 | A | - | 34,974 | `8cc344b0` | 2026-11-08 |  |
| `184-185.campana.15f002ea.A` | `d75e0e4d` | 184->185 | releases/2022-07-01 | A | - | 5,217 | `d5416224` | 2026-11-08 |  |
| `185-186.campana.15f002ea.A` | `63218b38` | 185->186 | releases/2022-07-01 | A | - | 4,051 | `d5416224` | 2026-11-08 |  |
| `186-187.campana.15f002ea.A` | `fa0ed627` | 186->187 | releases/2022-07-01 | A | - | 4,219 | `d5416224` | 2026-11-08 |  |
| `186-202.campana.15f002ea.A` | `e448eef6` | 186->202 | releases/2022-07-01 | A | - | 26,913 | `8cc344b0` | 2026-11-08 |  |
| `187-188.campana.15f002ea.A` | `76d9ada6` | 187->188 | releases/2022-07-01 | A | - | 3,612 | `d5416224` | 2026-11-08 |  |
| `187-189.campana.15f002ea.A` | `1a915dca` | 187->189 | releases/2022-07-01 | A | - | 4,250 | `d5416224` | 2026-11-08 |  |
| `189-190.campana.15f002ea.A` | `3351388b` | 189->190 | releases/2022-07-01 | A | - | 4,420 | `d5416224` | 2026-11-08 |  |
| `189-204.campana.15f002ea.A` | `0c5f1b8c` | 189->204 | releases/2022-07-01 | A | - | 26,419 | `8cc344b0` | 2026-11-08 |  |
| `190-191.campana.15f002ea.A` | `bdb3ceb4` | 190->191 | releases/2022-07-01 | A | - | 7,351 | `d5416224` | 2026-11-08 |  |
| `191-192.campana.15f002ea.A` | `1f59f9f5` | 191->192 | releases/2022-07-01 | A | - | 8,206 | `d5416224` | 2026-11-08 |  |
| `191-211.campana.15f002ea.A` | `7ada11d7` | 191->211 | releases/2022-07-01 | A | - | 37,950 | `8cc344b0` | 2026-11-08 |  |
| `193-194.campana.15f002ea.A` | `9f1942d7` | 193->194 | releases/2022-07-01 | A | - | 4,265 | `d5416224` | 2026-11-08 |  |
| `193-205.campana.15f002ea.A` | `56f21264` | 193->205 | releases/2022-07-01 | A | - | 22,076 | `8cc344b0` | 2026-11-08 |  |
| `194-195.campana.15f002ea.A` | `cdbedf8b` | 194->195 | releases/2022-07-01 | A | - | 3,995 | `d5416224` | 2026-11-08 |  |
| `195-196.campana.15f002ea.A` | `ae9809b3` | 195->196 | releases/2022-07-01 | A | - | 3,987 | `d5416224` | 2026-11-08 |  |
| `195-202.campana.15f002ea.A` | `661950db` | 195->202 | releases/2022-07-01 | A | - | 14,623 | `8cc344b0` | 2026-11-08 |  |
| `196-197.campana.15f002ea.A` | `23e42ae9` | 196->197 | releases/2022-07-01 | A | - | 4,728 | `d5416224` | 2026-11-08 |  |
| `197-198.campana.15f002ea.A` | `2f4974f6` | 197->198 | releases/2022-07-01 | A | - | 4,910 | `d5416224` | 2026-11-08 |  |
| `198-199.campana.15f002ea.A` | `6f00b1aa` | 198->199 | releases/2022-07-01 | A | - | 3,365 | `d5416224` | 2026-11-08 |  |
| `198-204.campana.15f002ea.A` | `dad7a713` | 198->204 | releases/2022-07-01 | A | - | 11,654 | `8cc344b0` | 2026-11-08 |  |
| `199-200.campana.15f002ea.A` | `7efccd22` | 199->200 | releases/2022-07-01 | A | - | 5,788 | `d5416224` | 2026-11-08 |  |
| `199-202.campana.15f002ea.A` | `c3b83501` | 199->202 | releases/2022-07-01 | A | - | 10,336 | `8cc344b0` | 2026-11-08 |  |
| `199-211.campana.15f002ea.A` | `bb3fabc4` | 199->211 | releases/2022-07-01 | A | - | 29,103 | `8cc344b0` | 2026-11-08 |  |
| `200-201.campana.15f002ea.A` | `f74a3fe4` | 200->201 | releases/2022-07-01 | A | - | 3,993 | `d5416224` | 2026-11-08 |  |
| `200-205.campana.15f002ea.A` | `ef4249b0` | 200->205 | releases/2022-07-01 | A | - | 14,447 | `8cc344b0` | 2026-11-08 |  |
| `201-202.campana.15f002ea.A` | `f6a2c36a` | 201->202 | releases/2022-07-01 | A | - | 6,296 | `d5416224` | 2026-11-08 |  |
| `201-204.campana.15f002ea.A` | `275c73bd` | 201->204 | releases/2022-07-01 | A | - | 8,050 | `8cc344b0` | 2026-11-08 |  |
| `202-203.campana.15f002ea.A` | `ac49aad5` | 202->203 | releases/2022-07-01 | A | - | 2,866 | `d5416224` | 2026-11-08 |  |
| `203-204.campana.15f002ea.A` | `02c5a33e` | 203->204 | releases/2022-07-01 | A | - | 6,169 | `d5416224` | 2026-11-08 |  |
| `203-205.campana.15f002ea.A` | `e44d718b` | 203->205 | releases/2022-07-01 | A | - | 11,450 | `8cc344b0` | 2026-11-08 |  |
| `204-205.campana.15f002ea.A` | `56225292` | 204->205 | releases/2022-07-01 | A | - | 6,882 | `637b3517` | 2026-11-07 | La primera construida con el remapeo ARREGLADO (revision 637b3517), para validar el despliegue de punta a punta y medir el coste real: 173 s |
| `204-211.campana.15f002ea.A` | `f8d418e0` | 204->211 | releases/2022-07-01 | A | - | 20,722 | `8cc344b0` | 2026-11-08 |  |
| `205-211.campana.15f002ea.A` | `b2606202` | 205->211 | releases/2022-07-01 | A | - | 16,159 | `d5416224` | 2026-11-08 |  |
| `211-212.campana.15f002ea.A` | `227dcc1e` | 211->212 | releases/2022-07-01 | A | - | 1,695 | `d5416224` | 2026-11-08 |  |
| `211-227.campana.15f002ea.A` | `ea0f4334` | 211->227 | releases/2022-07-01 | A | valid | 40,531 | `NULL` | 2026-10-27 | **LA ventana de validacion larga.** El laboratorio la reproduce al bit; sus 9 `replaced_by` y su proyeccion 2.610/3.821 son numeros publicados |
| `212-213.campana.15f002ea.A` | `8ab5c889` | 212->213 | releases/2022-07-01 | A | - | 2,336 | `d5416224` | 2026-11-08 |  |
| `213-214.campana.15f002ea.A` | `871366da` | 213->214 | releases/2022-07-01 | A | - | 3,409 | `d5416224` | 2026-11-08 |  |
| `214-215.campana.15f002ea.A` | `26d21ed5` | 214->215 | releases/2022-07-01 | A | - | 1,638 | `d5416224` | 2026-11-08 |  |
| `215-216.campana.15f002ea.A` | `f5658bd6` | 215->216 | releases/2022-07-01 | A | - | 3,618 | `d5416224` | 2026-11-08 |  |
| `216-217.campana.15f002ea.A` | `74402a31` | 216->217 | releases/2022-07-01 | A | - | 2,545 | `d5416224` | 2026-11-08 |  |
| `217-218.campana.15f002ea.A` | `f43e8e3b` | 217->218 | releases/2022-07-01 | A | - | 6,007 | `d5416224` | 2026-11-08 |  |
| `218-219.campana.15f002ea.A` | `f1e9ee88` | 218->219 | releases/2022-07-01 | A | - | 2,685 | `d5416224` | 2026-11-08 |  |
| `219-220.campana.15f002ea.A` | `d12540d6` | 219->220 | releases/2022-07-01 | A | - | 3,996 | `d5416224` | 2026-11-08 |  |
| `220-221.campana.15f002ea.A` | `0f617b2c` | 220->221 | releases/2022-07-01 | A | - | 2,963 | `d5416224` | 2026-11-08 |  |
| `221-222.campana.15f002ea.A` | `5d905a76` | 221->222 | releases/2022-07-01 | A | - | 3,014 | `d5416224` | 2026-11-08 |  |
| `222-223.campana.15f002ea.A` | `d128db33` | 222->223 | releases/2022-07-01 | A | - | 3,809 | `d5416224` | 2026-11-08 |  |
| `223-224.campana.15f002ea.A` | `06b58140` | 223->224 | releases/2022-07-01 | A | - | 4,200 | `d5416224` | 2026-11-08 |  |
| `224-225.campana.15f002ea.A` | `a9685579` | 224->225 | releases/2022-07-01 | A | - | 3,498 | `d5416224` | 2026-11-08 |  |
| `225-226.campana.15f002ea.A` | `5d44f0aa` | 225->226 | releases/2022-07-01 | A | - | 11,683 | `d5416224` | 2026-11-08 |  |
| `230-235.campana.2146c369.A` | `44cd7a5b` | 230->235 | releases/2026-01-23 | A | test | 28,220 | `NULL` | 2026-10-27 | **La banda PROSPECTIVA.** Empieza despues del holdout y no selecciona nada; sus cuatro puntuaciones llevan `PROSPECTIVE_DECLARATION` |

## El marco superado: 4 ventanas `viejo`

Construidas del 8 al 11 de octubre con el codigo que tardaba **74 minutos por ventana**, cada una pivotando en **su propia era** en vez de en un pivote comun, con `as_closed` (un termino que el pivote no puede nombrar lo tira el cierre) y `not_codes = any` (un `NOT|IBA` quita verdad a positivos experimentales).

**Ninguna corrida de la campana debe nombrar una de estas.** De las 4, **0 no tienen ni resultados ni papel** y serian las candidatas si alguna vez se decide limpiar. Borrarlas es una decision aparte: deja sus parquets huerfanos en MinIO y cuesta unas 6 horas deshacer con el codigo de hoy.

| etiqueta | id | tramo | pivote | papel | resultados | delta | dia |
|---|---|---|---|---|---|---|---|
| `211-227.viejo.15f002ea.B` | `ea94e57e` | 211->227 | releases/2022-07-01 | valid | 2 | 63,734 | 2026-10-27 | **NO BORRAR**
| `211-227.viejo.15f002ea.A` | `7aa37929` | 211->227 | releases/2022-07-01 | valid | 0 | 39,885 | 2026-10-27 | **NO BORRAR**
| `219-220.viejo.2ba77c97.B` | `c35ee267` | 219->220 | releases/2024-01-17 | - | 3 | 5,810 | 2026-10-11 | **NO BORRAR**
| `227-230.viejo.28c785ca.B` | `cb46395a` | 227->230 | releases/2025-07-22 | test | 0 | 21,996 | 2026-10-27 | **NO BORRAR**

## Y lo que el inventario no puede decir

**6 de 87 ventanas no dicen con que codigo se construyeron.** El sello de revision aterrizo en el trabajador despues del 27 de octubre, asi que para esas la unica via es casar su fecha contra los bloques de `DECLARED-REVISION.txt`, que es arqueologia. PROTEA #1140 anade la columna y rellena las que se pueden rellenar; las demas se quedan NULL en vez de inferirse de la fecha, porque una fecha mapea a una declaracion y no a un proceso.

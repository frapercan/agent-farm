# Inventario de las ventanas de evaluacion: nombradas y descritas

**196 ventanas, generadas desde la base el 2026-11-08** por `plans/genera_inventario.py`. No se escribe a mano: un inventario que alguien mantiene a mano es un inventario que miente en cuanto se genera una ventana mas.

## Por que hace falta nombrarlas

El par de conjuntos de anotaciones **dejo de identificar una ventana**: los tres grafos de propagacion y las tres reglas de verdad entraron en la clave. Hoy **62 de 69 pares distintos llevan mas de una**, asi que la exportacion se niega en 62 de 69 pares, y no hay forma de decir "la ventana de 204->205" sin decir cual.

La etiqueta es `<t0>-<t1>.<perfil>.<pivote>.<construccion>`:

* `perfil`: **`campana`** es el marco vivo (`projected`/`live_in_both_ends`/`experimental`) y **`viejo`** el superado (`as_closed`/`pivot_terms`/`any`);
* `construccion`: **A** cierra los dos extremos bajo el pivote, **B** cada extremo bajo su propia era. La primera version de esta etiqueta no lo llevaba y colisionaba en dos casos, que son justo la (A) y la (B) de 160->177.

**El NOMBRE es como se habla de una ventana**, y la etiqueta es su identidad tecnica. `validacion-larga`, `holdout-227-230`, `serie-204-205`, `serie-vieja-204-205`. Existe porque el investigador lo pidio el 2026-11-08: llevaba horas refiriendome a las ventanas por ocho caracteres de su uuid, que no dicen nada, y el holdout merece llamarse holdout.

Colisiones ahora: **0** (la etiqueta identifica).

## Las que NO se tocan: las cinco con papel declarado

**El recuento de resultados NO sirve para decidir si una ventana es desechable**, y esta es la prueba: el holdout tiene cero. Su unica mirada se tomo en el laboratorio, y las tablas de la plataforma no ven el laboratorio. Un filtro de "sin resultados" lo habria incluido en un borrado.

| nombre | etiqueta | id | tramo | papel | resultados | delta | que es |
|---|---|---|---|---|---|---|---|
| **validacion-larga-marco-viejo** | `211-227.viejo.15f002ea.B` | `ea94e57e` | 211->227 | **valid** | 2 | 63,734 | La MISMA 211->227 con el marco viejo, tambien marcada `valid`. Quien lea "la de validacion" sin mirar el perfil puede coger esta |
| **validacion-larga-descartada** | `211-227.viejo.15f002ea.A` | `7aa37929` | 211->227 | **valid** | 0 | 39,885 | Otra 211->227 vieja marcada `valid`, `as_closed` a 39.885, y **nunca fue el titular**. Cero resultados, y aun asi lleva papel: no se borra |
| **validacion-larga** | `211-227.campana.15f002ea.A` | `ea0f4334` | 211->227 | **valid** | 12 | 40,531 | **LA ventana de validacion larga.** El laboratorio la reproduce al bit; sus 9 `replaced_by` y su proyeccion 2.610/3.821 son numeros publicados |
| **holdout-227-230** | `227-230.viejo.28c785ca.B` | `cb46395a` | 227->230 | **test** | 0 | 21,996 | **EL HOLDOUT. Su pase se gasto el 2026-10-26 EN EL LABORATORIO** (0,4471 contra 0,2605), no aqui, por eso tiene cero resultados en PROTEA. El silencio de esta tabla no dice nada sobre el mundo. NO se reconstruye y NO se borra |
| **banda-prospectiva** | `230-235.campana.2146c369.A` | `44cd7a5b` | 230->235 | **test** | 4 | 28,220 | **La banda PROSPECTIVA.** Empieza despues del holdout y no selecciona nada; sus cuatro puntuaciones llevan `PROSPECTIVE_DECLARATION` |

## El marco vivo: 68 ventanas `campana`

| nombre | id | tramo | pivote | constr. | papel | delta | revision | dia |
|---|---|---|---|---|---|---|---|---|
| **serie-156-157** | `d87aa1e7` | 156->157 | releases/2022-07-01 | A | - | 5,399 | `d5416224` | 2026-11-08 |
| **serie-157-158** | `2170cc93` | 157->158 | releases/2022-07-01 | A | - | 6,553 | `d5416224` | 2026-11-08 |
| **serie-158-159** | `e3639c55` | 158->159 | releases/2022-07-01 | A | - | 4,910 | `d5416224` | 2026-11-08 |
| **serie-159-160** | `96646bb4` | 159->160 | releases/2022-07-01 | A | - | 8,469 | `d5416224` | 2026-11-08 |
| **serie-160-161** | `983f3a65` | 160->161 | releases/2022-07-01 | A | - | 5,369 | `d5416224` | 2026-11-08 |
| **serie-160-177** | `e84dfec8` | 160->177 | releases/2022-07-01 | B | - | 57,232 | `8ab6487f` | 2026-11-07 |
| **serie-160-177** | `d3c8cd2e` | 160->177 | releases/2022-07-01 | A | - | 31,871 | `d5416224` | 2026-11-08 |
| **serie-161-162** | `a5933668` | 161->162 | releases/2022-07-01 | A | - | 12,564 | `d5416224` | 2026-11-08 |
| **serie-162-163** | `d82e9b2f` | 162->163 | releases/2022-07-01 | A | - | 5,127 | `d5416224` | 2026-11-08 |
| **serie-163-164** | `fa7ea497` | 163->164 | releases/2022-07-01 | A | - | 7,580 | `d5416224` | 2026-11-08 |
| **serie-164-165** | `c197ba4b` | 164->165 | releases/2022-07-01 | A | - | 7,148 | `d5416224` | 2026-11-08 |
| **serie-165-166** | `b4533108` | 165->166 | releases/2022-07-01 | A | - | 6,769 | `d5416224` | 2026-11-08 |
| **serie-166-167** | `40136294` | 166->167 | releases/2022-07-01 | A | - | 5,360 | `d5416224` | 2026-11-08 |
| **serie-167-168** | `4a9f58ae` | 167->168 | releases/2022-07-01 | A | - | 5,374 | `d5416224` | 2026-11-08 |
| **serie-168-169** | `72ea69b1` | 168->169 | releases/2022-07-01 | A | - | 6,378 | `d5416224` | 2026-11-08 |
| **serie-169-170** | `56dfa71c` | 169->170 | releases/2022-07-01 | A | - | 5,189 | `d5416224` | 2026-11-08 |
| **serie-170-171** | `522d02bc` | 170->171 | releases/2022-07-01 | A | - | 6,741 | `d5416224` | 2026-11-08 |
| **serie-171-172** | `f845afdf` | 171->172 | releases/2022-07-01 | A | - | 4,942 | `d5416224` | 2026-11-08 |
| **serie-172-173** | `f986e445` | 172->173 | releases/2022-07-01 | A | - | 5,793 | `d5416224` | 2026-11-08 |
| **serie-173-174** | `2feada67` | 173->174 | releases/2022-07-01 | A | - | 5,103 | `d5416224` | 2026-11-08 |
| **serie-174-175** | `2cd5f200` | 174->175 | releases/2022-07-01 | A | - | 5,775 | `d5416224` | 2026-11-08 |
| **serie-175-176** | `73252908` | 175->176 | releases/2022-07-01 | A | - | 5,369 | `d5416224` | 2026-11-08 |
| **serie-176-177** | `597715b2` | 176->177 | releases/2022-07-01 | A | - | 5,794 | `d5416224` | 2026-11-08 |
| **serie-177-178** | `16e315b9` | 177->178 | releases/2022-07-01 | A | - | 4,979 | `d5416224` | 2026-11-08 |
| **serie-178-179** | `7369e486` | 178->179 | releases/2022-07-01 | A | - | 8,131 | `d5416224` | 2026-11-08 |
| **serie-179-180** | `16a80269` | 179->180 | releases/2022-07-01 | A | - | 6,263 | `d5416224` | 2026-11-08 |
| **serie-180-181** | `1a9148a0` | 180->181 | releases/2022-07-01 | A | - | 6,357 | `d5416224` | 2026-11-08 |
| **serie-181-182** | `4220a313` | 181->182 | releases/2022-07-01 | A | - | 8,308 | `d5416224` | 2026-11-08 |
| **serie-182-183** | `c5277415` | 182->183 | releases/2022-07-01 | A | - | 3,976 | `d5416224` | 2026-11-08 |
| **serie-183-184** | `2337fd69` | 183->184 | releases/2022-07-01 | A | - | 6,866 | `d5416224` | 2026-11-08 |
| **serie-184-185** | `d75e0e4d` | 184->185 | releases/2022-07-01 | A | - | 5,217 | `d5416224` | 2026-11-08 |
| **serie-185-186** | `63218b38` | 185->186 | releases/2022-07-01 | A | - | 4,051 | `d5416224` | 2026-11-08 |
| **serie-186-187** | `fa0ed627` | 186->187 | releases/2022-07-01 | A | - | 4,219 | `d5416224` | 2026-11-08 |
| **serie-187-188** | `76d9ada6` | 187->188 | releases/2022-07-01 | A | - | 3,612 | `d5416224` | 2026-11-08 |
| **serie-187-189** | `1a915dca` | 187->189 | releases/2022-07-01 | A | - | 4,250 | `d5416224` | 2026-11-08 |
| **serie-189-190** | `3351388b` | 189->190 | releases/2022-07-01 | A | - | 4,420 | `d5416224` | 2026-11-08 |
| **serie-190-191** | `bdb3ceb4` | 190->191 | releases/2022-07-01 | A | - | 7,351 | `d5416224` | 2026-11-08 |
| **serie-191-192** | `1f59f9f5` | 191->192 | releases/2022-07-01 | A | - | 8,206 | `d5416224` | 2026-11-08 |
| **serie-193-194** | `9f1942d7` | 193->194 | releases/2022-07-01 | A | - | 4,265 | `d5416224` | 2026-11-08 |
| **serie-194-195** | `cdbedf8b` | 194->195 | releases/2022-07-01 | A | - | 3,995 | `d5416224` | 2026-11-08 |
| **serie-195-196** | `ae9809b3` | 195->196 | releases/2022-07-01 | A | - | 3,987 | `d5416224` | 2026-11-08 |
| **serie-196-197** | `23e42ae9` | 196->197 | releases/2022-07-01 | A | - | 4,728 | `d5416224` | 2026-11-08 |
| **serie-197-198** | `2f4974f6` | 197->198 | releases/2022-07-01 | A | - | 4,910 | `d5416224` | 2026-11-08 |
| **serie-198-199** | `6f00b1aa` | 198->199 | releases/2022-07-01 | A | - | 3,365 | `d5416224` | 2026-11-08 |
| **serie-199-200** | `7efccd22` | 199->200 | releases/2022-07-01 | A | - | 5,788 | `d5416224` | 2026-11-08 |
| **serie-200-201** | `f74a3fe4` | 200->201 | releases/2022-07-01 | A | - | 3,993 | `d5416224` | 2026-11-08 |
| **serie-201-202** | `f6a2c36a` | 201->202 | releases/2022-07-01 | A | - | 6,296 | `d5416224` | 2026-11-08 |
| **serie-202-203** | `ac49aad5` | 202->203 | releases/2022-07-01 | A | - | 2,866 | `d5416224` | 2026-11-08 |
| **serie-203-204** | `02c5a33e` | 203->204 | releases/2022-07-01 | A | - | 6,169 | `d5416224` | 2026-11-08 |
| **serie-204-205** | `56225292` | 204->205 | releases/2022-07-01 | A | - | 6,882 | `637b3517` | 2026-11-07 |
| **serie-205-211** | `b2606202` | 205->211 | releases/2022-07-01 | A | - | 16,159 | `d5416224` | 2026-11-08 |
| **serie-211-212** | `227dcc1e` | 211->212 | releases/2022-07-01 | A | - | 1,695 | `d5416224` | 2026-11-08 |
| **validacion-larga** | `ea0f4334` | 211->227 | releases/2022-07-01 | A | valid | 40,531 | `NULL` | 2026-10-27 |
| **serie-212-213** | `8ab5c889` | 212->213 | releases/2022-07-01 | A | - | 2,336 | `d5416224` | 2026-11-08 |
| **serie-213-214** | `871366da` | 213->214 | releases/2022-07-01 | A | - | 3,409 | `d5416224` | 2026-11-08 |
| **serie-214-215** | `26d21ed5` | 214->215 | releases/2022-07-01 | A | - | 1,638 | `d5416224` | 2026-11-08 |
| **serie-215-216** | `f5658bd6` | 215->216 | releases/2022-07-01 | A | - | 3,618 | `d5416224` | 2026-11-08 |
| **serie-216-217** | `74402a31` | 216->217 | releases/2022-07-01 | A | - | 2,545 | `d5416224` | 2026-11-08 |
| **serie-217-218** | `f43e8e3b` | 217->218 | releases/2022-07-01 | A | - | 6,007 | `d5416224` | 2026-11-08 |
| **serie-218-219** | `f1e9ee88` | 218->219 | releases/2022-07-01 | A | - | 2,685 | `d5416224` | 2026-11-08 |
| **serie-219-220** | `d12540d6` | 219->220 | releases/2022-07-01 | A | - | 3,996 | `d5416224` | 2026-11-08 |
| **serie-220-221** | `0f617b2c` | 220->221 | releases/2022-07-01 | A | - | 2,963 | `d5416224` | 2026-11-08 |
| **serie-221-222** | `5d905a76` | 221->222 | releases/2022-07-01 | A | - | 3,014 | `d5416224` | 2026-11-08 |
| **serie-222-223** | `d128db33` | 222->223 | releases/2022-07-01 | A | - | 3,809 | `d5416224` | 2026-11-08 |
| **serie-223-224** | `06b58140` | 223->224 | releases/2022-07-01 | A | - | 4,200 | `d5416224` | 2026-11-08 |
| **serie-224-225** | `a9685579` | 224->225 | releases/2022-07-01 | A | - | 3,498 | `d5416224` | 2026-11-08 |
| **serie-225-226** | `5d44f0aa` | 225->226 | releases/2022-07-01 | A | - | 11,683 | `d5416224` | 2026-11-08 |
| **banda-prospectiva** | `44cd7a5b` | 230->235 | releases/2026-01-23 | A | test | 28,220 | `NULL` | 2026-10-27 |

## El marco superado: 128 ventanas `viejo`

Construidas del 8 al 11 de octubre con el codigo que tardaba **74 minutos por ventana**, cada una pivotando en **su propia era** en vez de en un pivote comun, con `as_closed` (un termino que el pivote no puede nombrar lo tira el cierre) y `not_codes = any` (un `NOT|IBA` quita verdad a positivos experimentales).

**Ninguna corrida de la campana debe nombrar una de estas.** De las 128, **124 no tienen ni resultados ni papel** y serian las candidatas si alguna vez se decide limpiar. Borrarlas es una decision aparte: deja sus parquets huerfanos en MinIO y cuesta unas 6 horas deshacer con el codigo de hoy.

| nombre | id | tramo | pivote | papel | resultados | delta | dia |
|---|---|---|---|---|---|---|---|
| **serie-vieja-156-157** | `df9a9dd2` | 156->157 | releases/2016-05-31 | - | 0 | 1,646 | 2026-10-08 |
| **serie-vieja-157-158** | `435f8fa8` | 157->158 | releases/2016-08-31 | - | 0 | 9,750 | 2026-10-08 |
| **serie-vieja-157-158** | `5c66d592` | 157->158 | releases/2016-05-31 | - | 0 | 7,962 | 2026-10-11 |
| **serie-vieja-158-159** | `3c812e86` | 158->159 | releases/2016-09-30 | - | 0 | 3,365 | 2026-10-08 |
| **serie-vieja-158-159** | `83796b3e` | 158->159 | releases/2016-08-31 | - | 0 | 1,562 | 2026-10-11 |
| **serie-vieja-159-160** | `ed6338eb` | 159->160 | releases/2016-09-30 | - | 0 | 10,902 | 2026-10-08 |
| **serie-vieja-160-161** | `6e3f7bf9` | 160->161 | releases/2016-10-29 | - | 0 | 4,976 | 2026-10-08 |
| **serie-vieja-160-161** | `25f4f0aa` | 160->161 | releases/2016-09-30 | - | 0 | 4,631 | 2026-10-11 |
| **serie-vieja-161-162** | `bc8e810b` | 161->162 | releases/2016-12-24 | - | 0 | 21,970 | 2026-10-08 |
| **serie-vieja-161-162** | `35a8e07b` | 161->162 | releases/2016-10-29 | - | 0 | 21,196 | 2026-10-11 |
| **serie-vieja-162-163** | `b8d11a2c` | 162->163 | releases/2017-01-31 | - | 0 | 4,570 | 2026-10-08 |
| **serie-vieja-162-163** | `a24f4f0f` | 162->163 | releases/2016-12-24 | - | 0 | 4,127 | 2026-10-11 |
| **serie-vieja-163-164** | `d28df026` | 163->164 | releases/2017-02-28 | - | 0 | 12,639 | 2026-10-08 |
| **serie-vieja-163-164** | `3b0734ae` | 163->164 | releases/2017-01-31 | - | 0 | 11,793 | 2026-10-11 |
| **serie-vieja-164-165** | `fb15a431` | 164->165 | releases/2017-03-31 | - | 0 | 9,711 | 2026-10-08 |
| **serie-vieja-164-165** | `faab8d9e` | 164->165 | releases/2017-02-28 | - | 0 | 4,097 | 2026-10-11 |
| **serie-vieja-165-166** | `4d7890be` | 165->166 | releases/2017-04-28 | - | 0 | 18,451 | 2026-10-08 |
| **serie-vieja-165-166** | `cd60f96f` | 165->166 | releases/2017-03-31 | - | 0 | 15,840 | 2026-10-11 |
| **serie-vieja-166-167** | `d134786a` | 166->167 | releases/2017-05-30 | - | 0 | 8,108 | 2026-10-08 |
| **serie-vieja-166-167** | `3087c906` | 166->167 | releases/2017-04-28 | - | 0 | 7,790 | 2026-10-11 |
| **serie-vieja-167-168** | `df4d598d` | 167->168 | releases/2017-06-29 | - | 0 | 3,673 | 2026-10-10 |
| **serie-vieja-167-168** | `13f42d98` | 167->168 | releases/2017-05-30 | - | 0 | 2,828 | 2026-10-11 |
| **serie-vieja-168-169** | `f9247408` | 168->169 | releases/2017-07-31 | - | 0 | 4,205 | 2026-10-08 |
| **serie-vieja-168-169** | `1be1487b` | 168->169 | releases/2017-06-29 | - | 0 | 3,595 | 2026-10-11 |
| **serie-vieja-169-170** | `6af476a1` | 169->170 | releases/2017-08-31 | - | 0 | 2,053 | 2026-10-08 |
| **serie-vieja-169-170** | `3cb40b83` | 169->170 | releases/2017-07-31 | - | 0 | 2,027 | 2026-10-11 |
| **serie-vieja-170-171** | `5c67eefe` | 170->171 | releases/2017-09-30 | - | 0 | 13,531 | 2026-10-08 |
| **serie-vieja-170-171** | `3e9f717b` | 170->171 | releases/2017-08-31 | - | 0 | 4,190 | 2026-10-11 |
| **serie-vieja-171-172** | `6a7b4c8b` | 171->172 | releases/2017-10-31 | - | 0 | 6,788 | 2026-10-08 |
| **serie-vieja-171-172** | `6d9018fd` | 171->172 | releases/2017-09-30 | - | 0 | 2,913 | 2026-10-11 |
| **serie-vieja-172-173** | `6a67bc43` | 172->173 | releases/2017-11-30 | - | 0 | 13,243 | 2026-10-08 |
| **serie-vieja-172-173** | `e24773ed` | 172->173 | releases/2017-10-31 | - | 0 | 12,364 | 2026-10-11 |
| **serie-vieja-173-174** | `f9ed812a` | 173->174 | releases/2017-12-29 | - | 0 | 2,792 | 2026-10-10 |
| **serie-vieja-173-174** | `82f6a6b1` | 173->174 | releases/2017-11-30 | - | 0 | 2,792 | 2026-10-11 |
| **serie-vieja-174-175** | `dab841bd` | 174->175 | releases/2018-02-01 | - | 0 | 2,192 | 2026-10-08 |
| **serie-vieja-174-175** | `27bdeabd` | 174->175 | releases/2017-12-29 | - | 0 | 2,192 | 2026-10-11 |
| **serie-vieja-175-176** | `433266a9` | 175->176 | releases/2018-03-10 | - | 0 | 8,829 | 2026-10-08 |
| **serie-vieja-175-176** | `b0e13c98` | 175->176 | releases/2018-02-01 | - | 0 | 7,712 | 2026-10-11 |
| **serie-vieja-176-177** | `7c60135d` | 176->177 | releases/2018-04-02 | - | 0 | 4,986 | 2026-10-08 |
| **serie-vieja-176-177** | `598bb27f` | 176->177 | releases/2018-03-10 | - | 0 | 4,049 | 2026-10-11 |
| **serie-vieja-177-178** | `ef5f62cf` | 177->178 | releases/2018-04-02 | - | 0 | 2,356 | 2026-10-08 |
| **serie-vieja-178-179** | `997d4089` | 178->179 | releases/2018-06-01 | - | 0 | 6,215 | 2026-10-08 |
| **serie-vieja-178-179** | `708fabb0` | 178->179 | releases/2018-04-02 | - | 0 | 5,628 | 2026-10-11 |
| **serie-vieja-179-180** | `45c0b1b7` | 179->180 | releases/2018-07-02 | - | 0 | 2,885 | 2026-10-08 |
| **serie-vieja-179-180** | `4265a3f9` | 179->180 | releases/2018-06-01 | - | 0 | 2,852 | 2026-10-11 |
| **serie-vieja-180-181** | `b8b89de3` | 180->181 | releases/2018-09-05 | - | 0 | 5,992 | 2026-10-08 |
| **serie-vieja-180-181** | `014fc4a6` | 180->181 | releases/2018-07-02 | - | 0 | 5,276 | 2026-10-11 |
| **serie-vieja-181-182** | `f952e961` | 181->182 | releases/2018-10-01 | - | 0 | 5,243 | 2026-10-08 |
| **serie-vieja-181-182** | `75bdbf9d` | 181->182 | releases/2018-09-05 | - | 0 | 5,224 | 2026-10-11 |
| **serie-vieja-182-183** | `91bac32d` | 182->183 | releases/2018-10-08 | - | 0 | 694 | 2026-10-08 |
| **serie-vieja-182-183** | `0623c713` | 182->183 | releases/2018-10-01 | - | 0 | 666 | 2026-10-11 |
| **serie-vieja-183-184** | `92ee5561` | 183->184 | releases/2018-11-15 | - | 0 | 4,158 | 2026-10-08 |
| **serie-vieja-183-184** | `7140f9dc` | 183->184 | releases/2018-10-08 | - | 0 | 4,153 | 2026-10-11 |
| **serie-vieja-184-185** | `9906633c` | 184->185 | releases/2019-01-01 | - | 0 | 3,628 | 2026-10-08 |
| **serie-vieja-184-185** | `ef190d51` | 184->185 | releases/2018-11-15 | - | 0 | 3,332 | 2026-10-11 |
| **serie-vieja-185-186** | `11a94bdb` | 185->186 | releases/2019-02-01 | - | 0 | 704 | 2026-10-10 |
| **serie-vieja-185-186** | `8835c008` | 185->186 | releases/2019-01-01 | - | 0 | 683 | 2026-10-11 |
| **serie-vieja-186-187** | `2148e8be` | 186->187 | releases/2019-03-19 | - | 0 | 3,962 | 2026-10-08 |
| **serie-vieja-186-187** | `e4230f33` | 186->187 | releases/2019-02-01 | - | 0 | 3,957 | 2026-10-11 |
| **serie-vieja-187-188** | `26417c3c` | 187->188 | releases/2019-04-17 | - | 0 | 1,265 | 2026-10-08 |
| **serie-vieja-187-188** | `9f34963e` | 187->188 | releases/2019-03-19 | - | 0 | 1,195 | 2026-10-11 |
| **serie-vieja-187-189** | `bc60cc3a` | 187->189 | releases/2019-06-01 | - | 0 | 5,261 | 2026-10-08 |
| **serie-vieja-187-189** | `4c27c2f3` | 187->189 | releases/2019-03-19 | - | 0 | 3,797 | 2026-10-11 |
| **serie-vieja-189-190** | `a1a2a212` | 189->190 | releases/2019-06-10 | - | 0 | 2,265 | 2026-10-08 |
| **serie-vieja-189-190** | `9cdb01ce` | 189->190 | releases/2019-06-01 | - | 0 | 2,264 | 2026-10-11 |
| **serie-vieja-190-191** | `a63b7331` | 190->191 | releases/2019-07-01 | - | 0 | 5,119 | 2026-10-09 |
| **serie-vieja-190-191** | `a0b19d78` | 190->191 | releases/2019-06-10 | - | 0 | 4,826 | 2026-10-11 |
| **serie-vieja-191-192** | `697845e7` | 191->192 | releases/2019-07-01 | - | 0 | 5,904 | 2026-10-09 |
| **serie-vieja-193-194** | `ff2fab77` | 193->194 | releases/2019-11-02 | - | 0 | 88,666 | 2026-10-10 |
| **serie-vieja-193-194** | `872447ae` | 193->194 | releases/2019-07-01 | - | 0 | 4,772 | 2026-10-11 |
| **serie-vieja-194-195** | `d9b69958` | 194->195 | releases/2019-12-09 | - | 0 | 3,232 | 2026-10-09 |
| **serie-vieja-194-195** | `822c4c3e` | 194->195 | releases/2019-11-02 | - | 0 | 3,068 | 2026-10-11 |
| **serie-vieja-195-196** | `a2095e46` | 195->196 | releases/2020-01-01 | - | 0 | 2,183 | 2026-10-09 |
| **serie-vieja-195-196** | `9fb7399f` | 195->196 | releases/2019-12-09 | - | 0 | 1,338 | 2026-10-11 |
| **serie-vieja-196-197** | `12ed0793` | 196->197 | releases/2020-03-23 | - | 0 | 17,737 | 2026-10-09 |
| **serie-vieja-196-197** | `6272c7d5` | 196->197 | releases/2020-01-01 | - | 0 | 17,609 | 2026-10-11 |
| **serie-vieja-197-198** | `a2db101c` | 197->198 | releases/2020-06-01 | - | 0 | 5,795 | 2026-10-09 |
| **serie-vieja-197-198** | `60749252` | 197->198 | releases/2020-03-23 | - | 0 | 5,476 | 2026-10-11 |
| **serie-vieja-198-199** | `ef18a458` | 198->199 | releases/2020-07-16 | - | 0 | 5,303 | 2026-10-09 |
| **serie-vieja-198-199** | `6375575a` | 198->199 | releases/2020-06-01 | - | 0 | 5,303 | 2026-10-11 |
| **serie-vieja-199-200** | `9676a2c8` | 199->200 | releases/2020-09-10 | - | 0 | 4,903 | 2026-10-10 |
| **serie-vieja-199-200** | `ce32256b` | 199->200 | releases/2020-07-16 | - | 0 | 4,441 | 2026-10-11 |
| **serie-vieja-200-201** | `42edc25e` | 200->201 | releases/2020-11-18 | - | 0 | 15,884 | 2026-10-09 |
| **serie-vieja-200-201** | `6025bc8c` | 200->201 | releases/2020-09-10 | - | 0 | 10,766 | 2026-10-11 |
| **serie-vieja-201-202** | `d5c1d837` | 201->202 | releases/2021-02-01 | - | 0 | 7,554 | 2026-10-09 |
| **serie-vieja-201-202** | `c1af2e1c` | 201->202 | releases/2020-11-18 | - | 0 | 7,517 | 2026-10-11 |
| **serie-vieja-202-203** | `ba9c763b` | 202->203 | releases/2021-02-01 | - | 0 | 2,618 | 2026-10-09 |
| **serie-vieja-203-204** | `aee6aecf` | 203->204 | releases/2021-05-01 | - | 0 | 17,302 | 2026-10-10 |
| **serie-vieja-203-204** | `bf5a36a3` | 203->204 | releases/2021-02-01 | - | 0 | 17,176 | 2026-10-11 |
| **serie-vieja-204-205** | `b8af9fc1` | 204->205 | releases/2021-10-26 | - | 0 | 15,550 | 2026-10-09 |
| **serie-vieja-204-205** | `d24d982a` | 204->205 | releases/2021-05-01 | - | 0 | 12,038 | 2026-10-11 |
| **serie-vieja-205-211** | `22f603da` | 205->211 | releases/2022-07-01 | - | 0 | 22,764 | 2026-10-09 |
| **serie-vieja-205-211** | `f90f0b53` | 205->211 | releases/2021-10-26 | - | 0 | 22,508 | 2026-10-11 |
| **serie-vieja-211-212** | `4fad58ba` | 211->212 | releases/2022-11-03 | - | 0 | 8,921 | 2026-10-09 |
| **serie-vieja-211-212** | `b3a44819` | 211->212 | releases/2022-07-01 | - | 0 | 8,727 | 2026-10-11 |
| **validacion-larga-marco-viejo** | `ea94e57e` | 211->227 | releases/2022-07-01 | valid | 2 | 63,734 | 2026-10-27 | **NO BORRAR**
| **validacion-larga-descartada** | `7aa37929` | 211->227 | releases/2022-07-01 | valid | 0 | 39,885 | 2026-10-27 | **NO BORRAR**
| **serie-vieja-212-213** | `d4a0acc4` | 212->213 | releases/2023-01-01 | - | 0 | 9,375 | 2026-10-09 |
| **serie-vieja-212-213** | `6dfa3203` | 212->213 | releases/2022-11-03 | - | 0 | 9,310 | 2026-10-11 |
| **serie-vieja-213-214** | `4d0acd56` | 213->214 | releases/2023-03-06 | - | 0 | 7,747 | 2026-10-09 |
| **serie-vieja-213-214** | `6f59f509` | 213->214 | releases/2023-01-01 | - | 0 | 7,222 | 2026-10-11 |
| **serie-vieja-214-215** | `e2829c97` | 214->215 | releases/2023-05-10 | - | 0 | 7,015 | 2026-10-09 |
| **serie-vieja-214-215** | `f97a040e` | 214->215 | releases/2023-03-06 | - | 0 | 7,011 | 2026-10-11 |
| **serie-vieja-215-216** | `16c12b05` | 215->216 | releases/2023-06-11 | - | 0 | 4,504 | 2026-10-09 |
| **serie-vieja-215-216** | `8f019b8c` | 215->216 | releases/2023-05-10 | - | 0 | 4,005 | 2026-10-11 |
| **serie-vieja-216-217** | `966676b9` | 216->217 | releases/2023-07-27 | - | 0 | 18,260 | 2026-10-10 |
| **serie-vieja-216-217** | `383cd830` | 216->217 | releases/2023-06-11 | - | 0 | 18,213 | 2026-10-11 |
| **serie-vieja-217-218** | `793a69e9` | 217->218 | releases/2023-10-09 | - | 0 | 6,572 | 2026-10-09 |
| **serie-vieja-217-218** | `03590591` | 217->218 | releases/2023-07-27 | - | 0 | 6,221 | 2026-10-11 |
| **serie-vieja-218-219** | `57ad2cdc` | 218->219 | releases/2024-01-17 | - | 0 | 11,055 | 2026-10-09 |
| **serie-vieja-218-219** | `4d308764` | 218->219 | releases/2023-10-09 | - | 0 | 8,636 | 2026-10-11 |
| **serie-vieja-219-220** | `cd5d2a70` | 219->220 | releases/2024-03-28 | - | 0 | 9,258 | 2026-10-09 |
| **serie-vieja-219-220** | `c35ee267` | 219->220 | releases/2024-01-17 | - | 3 | 5,810 | 2026-10-11 | **NO BORRAR**
| **serie-vieja-220-221** | `94a7561e` | 220->221 | releases/2024-06-10 | - | 0 | 7,878 | 2026-10-09 |
| **serie-vieja-220-221** | `4adc03df` | 220->221 | releases/2024-03-28 | - | 0 | 7,806 | 2026-10-11 |
| **serie-vieja-221-222** | `5a39b763` | 221->222 | releases/2024-06-17 | - | 0 | 2,233 | 2026-10-09 |
| **serie-vieja-221-222** | `b841d275` | 221->222 | releases/2024-06-10 | - | 0 | 2,233 | 2026-10-11 |
| **serie-vieja-222-223** | `db9cd64e` | 222->223 | releases/2024-09-08 | - | 0 | 5,258 | 2026-10-09 |
| **serie-vieja-222-223** | `23bc252f` | 222->223 | releases/2024-06-17 | - | 0 | 5,146 | 2026-10-11 |
| **serie-vieja-223-224** | `5d4772ae` | 223->224 | releases/2024-10-27 | - | 0 | 10,020 | 2026-10-09 |
| **serie-vieja-223-224** | `26c67e7d` | 223->224 | releases/2024-09-08 | - | 0 | 9,785 | 2026-10-11 |
| **serie-vieja-224-225** | `880688c8` | 224->225 | releases/2025-02-06 | - | 0 | 4,782 | 2026-10-10 |
| **serie-vieja-224-225** | `e945ad04` | 224->225 | releases/2024-10-27 | - | 0 | 3,781 | 2026-10-11 |
| **serie-vieja-225-226** | `81fb0a18` | 225->226 | releases/2025-03-16 | - | 0 | 11,713 | 2026-10-09 |
| **serie-vieja-225-226** | `30298ed2` | 225->226 | releases/2025-02-06 | - | 0 | 11,594 | 2026-10-11 |
| **serie-vieja-226-227** | `3a8776b9` | 226->227 | releases/2025-07-22 | - | 0 | 12,540 | 2026-10-09 |
| **serie-vieja-226-227** | `2f5ec8dd` | 226->227 | releases/2025-03-16 | - | 0 | 12,132 | 2026-10-11 |
| **holdout-227-230** | `cb46395a` | 227->230 | releases/2025-07-22 | test | 0 | 21,996 | 2026-10-27 | **NO BORRAR**

## Y lo que el inventario no puede decir

**130 de 196 ventanas no dicen con que codigo se construyeron.** El sello de revision aterrizo en el trabajador despues del 27 de octubre, asi que para esas la unica via es casar su fecha contra los bloques de `DECLARED-REVISION.txt`, que es arqueologia. PROTEA #1140 anade la columna y rellena las que se pueden rellenar; las demas se quedan NULL en vez de inferirse de la fecha, porque una fecha mapea a una declaracion y no a un proceso.

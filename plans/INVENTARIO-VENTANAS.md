# Inventario de las ventanas de evaluacion: nombradas y descritas

**144 ventanas, generadas desde la base el 2026-11-08** por `plans/genera_inventario.py`. No se escribe a mano: un inventario que alguien mantiene a mano es un inventario que miente en cuanto se genera una ventana mas.

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

## El marco vivo: 16 ventanas `campana`

| etiqueta | id | tramo | pivote | constr. | papel | delta | revision | dia | que es |
|---|---|---|---|---|---|---|---|---|---|
| `156-157.campana.15f002ea.A` | `d87aa1e7` | 156->157 | releases/2022-07-01 | A | - | 5,399 | `d5416224` | 2026-11-08 |  |
| `157-158.campana.15f002ea.A` | `2170cc93` | 157->158 | releases/2022-07-01 | A | - | 6,553 | `d5416224` | 2026-11-08 |  |
| `158-159.campana.15f002ea.A` | `e3639c55` | 158->159 | releases/2022-07-01 | A | - | 4,910 | `d5416224` | 2026-11-08 |  |
| `159-160.campana.15f002ea.A` | `96646bb4` | 159->160 | releases/2022-07-01 | A | - | 8,469 | `d5416224` | 2026-11-08 |  |
| `160-161.campana.15f002ea.A` | `983f3a65` | 160->161 | releases/2022-07-01 | A | - | 5,369 | `d5416224` | 2026-11-08 |  |
| `160-177.campana.15f002ea.A` | `3bd720c9` | 160->177 | releases/2022-07-01 | A | - | 31,801 | `8ab6487f` | 2026-11-07 | La (A) de 160->177, construida con el remapeo ROTO (revision 8ab6487f). Su verdad es la vieja. **Pedirla otra vez NO da una nueva y tampoco falla**: `_maybe_reuse_existing` sirve ESTA fila bajo la misma identidad sin mirar `code_revision`, con un evento `idempotent_reuse` de nivel info. La restriccion unica no llega a rechazarla porque la operacion no llega a insertar. Yo escribi lo contrario y era falso |
| `160-177.campana.15f002ea.B` | `e84dfec8` | 160->177 | releases/2022-07-01 | B | - | 57,232 | `8ab6487f` | 2026-11-07 | La (B) gemela de 160->177, para la comparacion (A)/(B). Su verdad es identica al byte con el arreglo del remapeo |
| `161-162.campana.15f002ea.A` | `a5933668` | 161->162 | releases/2022-07-01 | A | - | 12,564 | `d5416224` | 2026-11-08 |  |
| `162-163.campana.15f002ea.A` | `d82e9b2f` | 162->163 | releases/2022-07-01 | A | - | 5,127 | `d5416224` | 2026-11-08 |  |
| `163-164.campana.15f002ea.A` | `fa7ea497` | 163->164 | releases/2022-07-01 | A | - | 7,580 | `d5416224` | 2026-11-08 |  |
| `164-165.campana.15f002ea.A` | `c197ba4b` | 164->165 | releases/2022-07-01 | A | - | 7,148 | `d5416224` | 2026-11-08 |  |
| `165-166.campana.15f002ea.A` | `b4533108` | 165->166 | releases/2022-07-01 | A | - | 6,769 | `d5416224` | 2026-11-08 |  |
| `166-167.campana.15f002ea.A` | `40136294` | 166->167 | releases/2022-07-01 | A | - | 5,360 | `d5416224` | 2026-11-08 |  |
| `204-205.campana.15f002ea.A` | `56225292` | 204->205 | releases/2022-07-01 | A | - | 6,882 | `637b3517` | 2026-11-07 | La primera construida con el remapeo ARREGLADO (revision 637b3517), para validar el despliegue de punta a punta y medir el coste real: 173 s |
| `211-227.campana.15f002ea.A` | `ea0f4334` | 211->227 | releases/2022-07-01 | A | valid | 40,531 | `NULL` | 2026-10-27 | **LA ventana de validacion larga.** El laboratorio la reproduce al bit; sus 9 `replaced_by` y su proyeccion 2.610/3.821 son numeros publicados |
| `230-235.campana.2146c369.A` | `44cd7a5b` | 230->235 | releases/2026-01-23 | A | test | 28,220 | `NULL` | 2026-10-27 | **La banda PROSPECTIVA.** Empieza despues del holdout y no selecciona nada; sus cuatro puntuaciones llevan `PROSPECTIVE_DECLARATION` |

## El marco superado: 128 ventanas `viejo`

Construidas del 8 al 11 de octubre con el codigo que tardaba **74 minutos por ventana**, cada una pivotando en **su propia era** en vez de en un pivote comun, con `as_closed` (un termino que el pivote no puede nombrar lo tira el cierre) y `not_codes = any` (un `NOT|IBA` quita verdad a positivos experimentales).

**Ninguna corrida de la campana debe nombrar una de estas.** De las 128, **124 no tienen ni resultados ni papel** y serian las candidatas si alguna vez se decide limpiar. Borrarlas es una decision aparte: deja sus parquets huerfanos en MinIO y cuesta unas 6 horas deshacer con el codigo de hoy.

| etiqueta | id | tramo | pivote | papel | resultados | delta | dia |
|---|---|---|---|---|---|---|---|
| `156-157.viejo.625863f5.A` | `df9a9dd2` | 156->157 | releases/2016-05-31 | - | 0 | 1,646 | 2026-10-08 |
| `157-158.viejo.25c5015d.B` | `435f8fa8` | 157->158 | releases/2016-08-31 | - | 0 | 9,750 | 2026-10-08 |
| `157-158.viejo.625863f5.B` | `5c66d592` | 157->158 | releases/2016-05-31 | - | 0 | 7,962 | 2026-10-11 |
| `158-159.viejo.c15c24bb.B` | `3c812e86` | 158->159 | releases/2016-09-30 | - | 0 | 3,365 | 2026-10-08 |
| `158-159.viejo.25c5015d.B` | `83796b3e` | 158->159 | releases/2016-08-31 | - | 0 | 1,562 | 2026-10-11 |
| `159-160.viejo.c15c24bb.A` | `ed6338eb` | 159->160 | releases/2016-09-30 | - | 0 | 10,902 | 2026-10-08 |
| `160-161.viejo.e803c5a0.B` | `6e3f7bf9` | 160->161 | releases/2016-10-29 | - | 0 | 4,976 | 2026-10-08 |
| `160-161.viejo.c15c24bb.B` | `25f4f0aa` | 160->161 | releases/2016-09-30 | - | 0 | 4,631 | 2026-10-11 |
| `161-162.viejo.0a497d38.B` | `bc8e810b` | 161->162 | releases/2016-12-24 | - | 0 | 21,970 | 2026-10-08 |
| `161-162.viejo.e803c5a0.B` | `35a8e07b` | 161->162 | releases/2016-10-29 | - | 0 | 21,196 | 2026-10-11 |
| `162-163.viejo.40e3b5f4.B` | `b8d11a2c` | 162->163 | releases/2017-01-31 | - | 0 | 4,570 | 2026-10-08 |
| `162-163.viejo.0a497d38.B` | `a24f4f0f` | 162->163 | releases/2016-12-24 | - | 0 | 4,127 | 2026-10-11 |
| `163-164.viejo.49ff92da.B` | `d28df026` | 163->164 | releases/2017-02-28 | - | 0 | 12,639 | 2026-10-08 |
| `163-164.viejo.40e3b5f4.B` | `3b0734ae` | 163->164 | releases/2017-01-31 | - | 0 | 11,793 | 2026-10-11 |
| `164-165.viejo.8affb525.B` | `fb15a431` | 164->165 | releases/2017-03-31 | - | 0 | 9,711 | 2026-10-08 |
| `164-165.viejo.49ff92da.B` | `faab8d9e` | 164->165 | releases/2017-02-28 | - | 0 | 4,097 | 2026-10-11 |
| `165-166.viejo.59fbb483.B` | `4d7890be` | 165->166 | releases/2017-04-28 | - | 0 | 18,451 | 2026-10-08 |
| `165-166.viejo.8affb525.B` | `cd60f96f` | 165->166 | releases/2017-03-31 | - | 0 | 15,840 | 2026-10-11 |
| `166-167.viejo.8447d1b3.B` | `d134786a` | 166->167 | releases/2017-05-30 | - | 0 | 8,108 | 2026-10-08 |
| `166-167.viejo.59fbb483.B` | `3087c906` | 166->167 | releases/2017-04-28 | - | 0 | 7,790 | 2026-10-11 |
| `167-168.viejo.b374c2c5.B` | `df4d598d` | 167->168 | releases/2017-06-29 | - | 0 | 3,673 | 2026-10-10 |
| `167-168.viejo.8447d1b3.B` | `13f42d98` | 167->168 | releases/2017-05-30 | - | 0 | 2,828 | 2026-10-11 |
| `168-169.viejo.a5499f63.B` | `f9247408` | 168->169 | releases/2017-07-31 | - | 0 | 4,205 | 2026-10-08 |
| `168-169.viejo.b374c2c5.B` | `1be1487b` | 168->169 | releases/2017-06-29 | - | 0 | 3,595 | 2026-10-11 |
| `169-170.viejo.f2f32356.B` | `6af476a1` | 169->170 | releases/2017-08-31 | - | 0 | 2,053 | 2026-10-08 |
| `169-170.viejo.a5499f63.B` | `3cb40b83` | 169->170 | releases/2017-07-31 | - | 0 | 2,027 | 2026-10-11 |
| `170-171.viejo.1585f60b.B` | `5c67eefe` | 170->171 | releases/2017-09-30 | - | 0 | 13,531 | 2026-10-08 |
| `170-171.viejo.f2f32356.B` | `3e9f717b` | 170->171 | releases/2017-08-31 | - | 0 | 4,190 | 2026-10-11 |
| `171-172.viejo.93654a02.B` | `6a7b4c8b` | 171->172 | releases/2017-10-31 | - | 0 | 6,788 | 2026-10-08 |
| `171-172.viejo.1585f60b.B` | `6d9018fd` | 171->172 | releases/2017-09-30 | - | 0 | 2,913 | 2026-10-11 |
| `172-173.viejo.82fb8001.B` | `6a67bc43` | 172->173 | releases/2017-11-30 | - | 0 | 13,243 | 2026-10-08 |
| `172-173.viejo.93654a02.B` | `e24773ed` | 172->173 | releases/2017-10-31 | - | 0 | 12,364 | 2026-10-11 |
| `173-174.viejo.b74eabc2.B` | `f9ed812a` | 173->174 | releases/2017-12-29 | - | 0 | 2,792 | 2026-10-10 |
| `173-174.viejo.82fb8001.B` | `82f6a6b1` | 173->174 | releases/2017-11-30 | - | 0 | 2,792 | 2026-10-11 |
| `174-175.viejo.4548ea99.B` | `dab841bd` | 174->175 | releases/2018-02-01 | - | 0 | 2,192 | 2026-10-08 |
| `174-175.viejo.b74eabc2.B` | `27bdeabd` | 174->175 | releases/2017-12-29 | - | 0 | 2,192 | 2026-10-11 |
| `175-176.viejo.f2c4928a.B` | `433266a9` | 175->176 | releases/2018-03-10 | - | 0 | 8,829 | 2026-10-08 |
| `175-176.viejo.4548ea99.B` | `b0e13c98` | 175->176 | releases/2018-02-01 | - | 0 | 7,712 | 2026-10-11 |
| `176-177.viejo.2d2ca421.B` | `7c60135d` | 176->177 | releases/2018-04-02 | - | 0 | 4,986 | 2026-10-08 |
| `176-177.viejo.f2c4928a.B` | `598bb27f` | 176->177 | releases/2018-03-10 | - | 0 | 4,049 | 2026-10-11 |
| `177-178.viejo.2d2ca421.A` | `ef5f62cf` | 177->178 | releases/2018-04-02 | - | 0 | 2,356 | 2026-10-08 |
| `178-179.viejo.f385071a.B` | `997d4089` | 178->179 | releases/2018-06-01 | - | 0 | 6,215 | 2026-10-08 |
| `178-179.viejo.2d2ca421.B` | `708fabb0` | 178->179 | releases/2018-04-02 | - | 0 | 5,628 | 2026-10-11 |
| `179-180.viejo.788833da.B` | `45c0b1b7` | 179->180 | releases/2018-07-02 | - | 0 | 2,885 | 2026-10-08 |
| `179-180.viejo.f385071a.B` | `4265a3f9` | 179->180 | releases/2018-06-01 | - | 0 | 2,852 | 2026-10-11 |
| `180-181.viejo.e2cb08ca.B` | `b8b89de3` | 180->181 | releases/2018-09-05 | - | 0 | 5,992 | 2026-10-08 |
| `180-181.viejo.788833da.B` | `014fc4a6` | 180->181 | releases/2018-07-02 | - | 0 | 5,276 | 2026-10-11 |
| `181-182.viejo.6dd1c8e7.B` | `f952e961` | 181->182 | releases/2018-10-01 | - | 0 | 5,243 | 2026-10-08 |
| `181-182.viejo.e2cb08ca.B` | `75bdbf9d` | 181->182 | releases/2018-09-05 | - | 0 | 5,224 | 2026-10-11 |
| `182-183.viejo.2194b0ea.B` | `91bac32d` | 182->183 | releases/2018-10-08 | - | 0 | 694 | 2026-10-08 |
| `182-183.viejo.6dd1c8e7.B` | `0623c713` | 182->183 | releases/2018-10-01 | - | 0 | 666 | 2026-10-11 |
| `183-184.viejo.425e2853.B` | `92ee5561` | 183->184 | releases/2018-11-15 | - | 0 | 4,158 | 2026-10-08 |
| `183-184.viejo.2194b0ea.B` | `7140f9dc` | 183->184 | releases/2018-10-08 | - | 0 | 4,153 | 2026-10-11 |
| `184-185.viejo.77c3b385.B` | `9906633c` | 184->185 | releases/2019-01-01 | - | 0 | 3,628 | 2026-10-08 |
| `184-185.viejo.425e2853.B` | `ef190d51` | 184->185 | releases/2018-11-15 | - | 0 | 3,332 | 2026-10-11 |
| `185-186.viejo.efa7e4df.B` | `11a94bdb` | 185->186 | releases/2019-02-01 | - | 0 | 704 | 2026-10-10 |
| `185-186.viejo.77c3b385.B` | `8835c008` | 185->186 | releases/2019-01-01 | - | 0 | 683 | 2026-10-11 |
| `186-187.viejo.d28cec7f.B` | `2148e8be` | 186->187 | releases/2019-03-19 | - | 0 | 3,962 | 2026-10-08 |
| `186-187.viejo.efa7e4df.B` | `e4230f33` | 186->187 | releases/2019-02-01 | - | 0 | 3,957 | 2026-10-11 |
| `187-188.viejo.47771a52.B` | `26417c3c` | 187->188 | releases/2019-04-17 | - | 0 | 1,265 | 2026-10-08 |
| `187-188.viejo.d28cec7f.B` | `9f34963e` | 187->188 | releases/2019-03-19 | - | 0 | 1,195 | 2026-10-11 |
| `187-189.viejo.3e1c99c6.B` | `bc60cc3a` | 187->189 | releases/2019-06-01 | - | 0 | 5,261 | 2026-10-08 |
| `187-189.viejo.d28cec7f.B` | `4c27c2f3` | 187->189 | releases/2019-03-19 | - | 0 | 3,797 | 2026-10-11 |
| `189-190.viejo.97d1cfc5.B` | `a1a2a212` | 189->190 | releases/2019-06-10 | - | 0 | 2,265 | 2026-10-08 |
| `189-190.viejo.3e1c99c6.B` | `9cdb01ce` | 189->190 | releases/2019-06-01 | - | 0 | 2,264 | 2026-10-11 |
| `190-191.viejo.d3a7dc9e.B` | `a63b7331` | 190->191 | releases/2019-07-01 | - | 0 | 5,119 | 2026-10-09 |
| `190-191.viejo.97d1cfc5.B` | `a0b19d78` | 190->191 | releases/2019-06-10 | - | 0 | 4,826 | 2026-10-11 |
| `191-192.viejo.d3a7dc9e.A` | `697845e7` | 191->192 | releases/2019-07-01 | - | 0 | 5,904 | 2026-10-09 |
| `193-194.viejo.4710dc13.B` | `ff2fab77` | 193->194 | releases/2019-11-02 | - | 0 | 88,666 | 2026-10-10 |
| `193-194.viejo.d3a7dc9e.B` | `872447ae` | 193->194 | releases/2019-07-01 | - | 0 | 4,772 | 2026-10-11 |
| `194-195.viejo.b8cc7515.B` | `d9b69958` | 194->195 | releases/2019-12-09 | - | 0 | 3,232 | 2026-10-09 |
| `194-195.viejo.4710dc13.B` | `822c4c3e` | 194->195 | releases/2019-11-02 | - | 0 | 3,068 | 2026-10-11 |
| `195-196.viejo.07802c38.B` | `a2095e46` | 195->196 | releases/2020-01-01 | - | 0 | 2,183 | 2026-10-09 |
| `195-196.viejo.b8cc7515.B` | `9fb7399f` | 195->196 | releases/2019-12-09 | - | 0 | 1,338 | 2026-10-11 |
| `196-197.viejo.ffa050f7.B` | `12ed0793` | 196->197 | releases/2020-03-23 | - | 0 | 17,737 | 2026-10-09 |
| `196-197.viejo.07802c38.B` | `6272c7d5` | 196->197 | releases/2020-01-01 | - | 0 | 17,609 | 2026-10-11 |
| `197-198.viejo.1640e0fb.B` | `a2db101c` | 197->198 | releases/2020-06-01 | - | 0 | 5,795 | 2026-10-09 |
| `197-198.viejo.ffa050f7.B` | `60749252` | 197->198 | releases/2020-03-23 | - | 0 | 5,476 | 2026-10-11 |
| `198-199.viejo.e7d5d24b.B` | `ef18a458` | 198->199 | releases/2020-07-16 | - | 0 | 5,303 | 2026-10-09 |
| `198-199.viejo.1640e0fb.B` | `6375575a` | 198->199 | releases/2020-06-01 | - | 0 | 5,303 | 2026-10-11 |
| `199-200.viejo.2cbd5df7.B` | `9676a2c8` | 199->200 | releases/2020-09-10 | - | 0 | 4,903 | 2026-10-10 |
| `199-200.viejo.e7d5d24b.B` | `ce32256b` | 199->200 | releases/2020-07-16 | - | 0 | 4,441 | 2026-10-11 |
| `200-201.viejo.4d9c4783.B` | `42edc25e` | 200->201 | releases/2020-11-18 | - | 0 | 15,884 | 2026-10-09 |
| `200-201.viejo.2cbd5df7.B` | `6025bc8c` | 200->201 | releases/2020-09-10 | - | 0 | 10,766 | 2026-10-11 |
| `201-202.viejo.a1f5f5a4.B` | `d5c1d837` | 201->202 | releases/2021-02-01 | - | 0 | 7,554 | 2026-10-09 |
| `201-202.viejo.4d9c4783.B` | `c1af2e1c` | 201->202 | releases/2020-11-18 | - | 0 | 7,517 | 2026-10-11 |
| `202-203.viejo.a1f5f5a4.A` | `ba9c763b` | 202->203 | releases/2021-02-01 | - | 0 | 2,618 | 2026-10-09 |
| `203-204.viejo.4ce8c11c.B` | `aee6aecf` | 203->204 | releases/2021-05-01 | - | 0 | 17,302 | 2026-10-10 |
| `203-204.viejo.a1f5f5a4.B` | `bf5a36a3` | 203->204 | releases/2021-02-01 | - | 0 | 17,176 | 2026-10-11 |
| `204-205.viejo.28db4cd1.B` | `b8af9fc1` | 204->205 | releases/2021-10-26 | - | 0 | 15,550 | 2026-10-09 |
| `204-205.viejo.4ce8c11c.B` | `d24d982a` | 204->205 | releases/2021-05-01 | - | 0 | 12,038 | 2026-10-11 |
| `205-211.viejo.15f002ea.B` | `22f603da` | 205->211 | releases/2022-07-01 | - | 0 | 22,764 | 2026-10-09 |
| `205-211.viejo.28db4cd1.B` | `f90f0b53` | 205->211 | releases/2021-10-26 | - | 0 | 22,508 | 2026-10-11 |
| `211-212.viejo.d0e53de5.B` | `4fad58ba` | 211->212 | releases/2022-11-03 | - | 0 | 8,921 | 2026-10-09 |
| `211-212.viejo.15f002ea.B` | `b3a44819` | 211->212 | releases/2022-07-01 | - | 0 | 8,727 | 2026-10-11 |
| `211-227.viejo.15f002ea.B` | `ea94e57e` | 211->227 | releases/2022-07-01 | valid | 2 | 63,734 | 2026-10-27 | **NO BORRAR**
| `211-227.viejo.15f002ea.A` | `7aa37929` | 211->227 | releases/2022-07-01 | valid | 0 | 39,885 | 2026-10-27 | **NO BORRAR**
| `212-213.viejo.0e1cba96.B` | `d4a0acc4` | 212->213 | releases/2023-01-01 | - | 0 | 9,375 | 2026-10-09 |
| `212-213.viejo.d0e53de5.B` | `6dfa3203` | 212->213 | releases/2022-11-03 | - | 0 | 9,310 | 2026-10-11 |
| `213-214.viejo.fb1f20f5.B` | `4d0acd56` | 213->214 | releases/2023-03-06 | - | 0 | 7,747 | 2026-10-09 |
| `213-214.viejo.0e1cba96.B` | `6f59f509` | 213->214 | releases/2023-01-01 | - | 0 | 7,222 | 2026-10-11 |
| `214-215.viejo.046e0d03.B` | `e2829c97` | 214->215 | releases/2023-05-10 | - | 0 | 7,015 | 2026-10-09 |
| `214-215.viejo.fb1f20f5.B` | `f97a040e` | 214->215 | releases/2023-03-06 | - | 0 | 7,011 | 2026-10-11 |
| `215-216.viejo.cc0c572b.B` | `16c12b05` | 215->216 | releases/2023-06-11 | - | 0 | 4,504 | 2026-10-09 |
| `215-216.viejo.046e0d03.B` | `8f019b8c` | 215->216 | releases/2023-05-10 | - | 0 | 4,005 | 2026-10-11 |
| `216-217.viejo.07e72843.B` | `966676b9` | 216->217 | releases/2023-07-27 | - | 0 | 18,260 | 2026-10-10 |
| `216-217.viejo.cc0c572b.B` | `383cd830` | 216->217 | releases/2023-06-11 | - | 0 | 18,213 | 2026-10-11 |
| `217-218.viejo.b0745ea0.B` | `793a69e9` | 217->218 | releases/2023-10-09 | - | 0 | 6,572 | 2026-10-09 |
| `217-218.viejo.07e72843.B` | `03590591` | 217->218 | releases/2023-07-27 | - | 0 | 6,221 | 2026-10-11 |
| `218-219.viejo.2ba77c97.B` | `57ad2cdc` | 218->219 | releases/2024-01-17 | - | 0 | 11,055 | 2026-10-09 |
| `218-219.viejo.b0745ea0.B` | `4d308764` | 218->219 | releases/2023-10-09 | - | 0 | 8,636 | 2026-10-11 |
| `219-220.viejo.bca3e800.B` | `cd5d2a70` | 219->220 | releases/2024-03-28 | - | 0 | 9,258 | 2026-10-09 |
| `219-220.viejo.2ba77c97.B` | `c35ee267` | 219->220 | releases/2024-01-17 | - | 3 | 5,810 | 2026-10-11 | **NO BORRAR**
| `220-221.viejo.f813b31c.B` | `94a7561e` | 220->221 | releases/2024-06-10 | - | 0 | 7,878 | 2026-10-09 |
| `220-221.viejo.bca3e800.B` | `4adc03df` | 220->221 | releases/2024-03-28 | - | 0 | 7,806 | 2026-10-11 |
| `221-222.viejo.6e44e1b6.B` | `5a39b763` | 221->222 | releases/2024-06-17 | - | 0 | 2,233 | 2026-10-09 |
| `221-222.viejo.f813b31c.B` | `b841d275` | 221->222 | releases/2024-06-10 | - | 0 | 2,233 | 2026-10-11 |
| `222-223.viejo.950ff8af.B` | `db9cd64e` | 222->223 | releases/2024-09-08 | - | 0 | 5,258 | 2026-10-09 |
| `222-223.viejo.6e44e1b6.B` | `23bc252f` | 222->223 | releases/2024-06-17 | - | 0 | 5,146 | 2026-10-11 |
| `223-224.viejo.3b8d6831.B` | `5d4772ae` | 223->224 | releases/2024-10-27 | - | 0 | 10,020 | 2026-10-09 |
| `223-224.viejo.950ff8af.B` | `26c67e7d` | 223->224 | releases/2024-09-08 | - | 0 | 9,785 | 2026-10-11 |
| `224-225.viejo.a748634a.B` | `880688c8` | 224->225 | releases/2025-02-06 | - | 0 | 4,782 | 2026-10-10 |
| `224-225.viejo.3b8d6831.B` | `e945ad04` | 224->225 | releases/2024-10-27 | - | 0 | 3,781 | 2026-10-11 |
| `225-226.viejo.6a7453c1.B` | `81fb0a18` | 225->226 | releases/2025-03-16 | - | 0 | 11,713 | 2026-10-09 |
| `225-226.viejo.a748634a.B` | `30298ed2` | 225->226 | releases/2025-02-06 | - | 0 | 11,594 | 2026-10-11 |
| `226-227.viejo.28c785ca.B` | `3a8776b9` | 226->227 | releases/2025-07-22 | - | 0 | 12,540 | 2026-10-09 |
| `226-227.viejo.6a7453c1.B` | `2f5ec8dd` | 226->227 | releases/2025-03-16 | - | 0 | 12,132 | 2026-10-11 |
| `227-230.viejo.28c785ca.B` | `cb46395a` | 227->230 | releases/2025-07-22 | test | 0 | 21,996 | 2026-10-27 | **NO BORRAR**

## Y lo que el inventario no puede decir

**130 de 144 ventanas no dicen con que codigo se construyeron.** El sello de revision aterrizo en el trabajador despues del 27 de octubre, asi que para esas la unica via es casar su fecha contra los bloques de `DECLARED-REVISION.txt`, que es arqueologia. PROTEA #1140 anade la columna y rellena las que se pueden rellenar; las demas se quedan NULL en vez de inferirse de la fecha, porque una fecha mapea a una declaracion y no a un proceso.

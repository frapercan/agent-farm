# El resto de reproducibilidad del kNN es la forma del ultimo trozo

Escrito el 2026-11-05, **antes de que corrieran los dos brazos del servidor** de la
exploracion 3 (`149b06f4-d2a7-44b3-b106-b67a76f74fd9`, reglas `fcc27bb9`). Esta aqui
y no en los eventos de la exploracion porque esos solo se aceptan sobre una
exploracion ya informada, y una prediccion escrita despues de ver el resultado no
es una prediccion. El sello de git es la fecha.

## Lo medido en el par del nodo

El desempate de `protea-method#66` funciono, y funciono completo:

| | |
|---|---|
| claves en cada conjunto | 1.145.504, cuenta exacta en los dos |
| solo en un lado | 0 |
| filas que difieren | **64** (0,0056%, contra 110.950 y 9,7% en la exploracion 1) |
| donante de referencia | 0 difieren |
| recuento de votos | 0 |
| posicion k | 0 |
| libro de donantes | 0 |
| distancia y distancias del libro | 64 |

**La seleccion es estable al bit.** Las 64 son autovotos
(`ref_protein_accession = protein_accession`) de dos proteinas: `Q8CIG8` con 48
filas y `Q8IXI1` con 16.

La exploracion 1 era la misma clase, comprobado: sus 7 claves con distancia
distinta eran 7 de 7 autovotos, en 2 proteinas, con diferencia maxima
`1,7763568394002505e-15`, el mismo valor al digito. Asi que la prediccion
preinscrita que nombraba un empate en la frontera del k-esimo vecino **pierde**
contra la de la cancelacion.

## Por que cerca de cero, y no en el resto

`cosine_distance_f64` SI esta en uso (`ORDER_INVARIANT_BACKENDS` es `{numpy}`), asi
que la acumulacion va en float64. Pero:

```
ulp de float32 en 2,8523698958338173e-08   1,77635683940025046e-15
diferencia observada A contra B            1,77635683940025050e-15
```

Los dos brazos produjeron **float32 adyacentes**. A distancia 0,5 el ulp de float32
es 5,96e-08, **33,6 millones de veces** la dispersion de float64, y el redondeo la
borra. Cerca de cero el ulp se encoge hasta el tamano de la dispersion y el
redondeo deja de proteger. No es que float32 sea grueso ahi: es fino, y por eso
falla. El docstring de `_order_invariance` dice que bajar a float32 borra siempre
la dispersion de float64, y cerca de cero eso es falso.

Lo unico que esta cerca de cero es el autovoto: la distancia de una proteina a si
misma, que deberia ser 0 y sale entre -2,7e-07 y +2,4e-07 por cancelacion al
restar `1 - dot`. Hay distancias negativas, que en coseno no significan nada.

## La causa: el resto de M en el kernel dgemm

Medido en el nodo con el banco del brazo y 8 hilos. 40.506 consultas hacen 39
lotes de 1024 y uno de 570; un lote de 1024 se parte en 500 + 500 + 24 y el de
570 en 500 + 70.

- En un trozo de **70**, las filas **66 y 69** salen con el otro redondeo.
- Las filas 0, 35 y de 63 a 68 menos la 66 salen con el valor normal.
- En trozos de 24 y de 500 no aparecio ninguna.

No lo cambian: la posicion dentro de un trozo de 500, los companeros de trozo,
repetir la cuenta, subconjuntos del banco, los hilos BLAS de 1 a 12, ni la
alineacion del buffer. Es el manejo del resto de M en el kernel.

**Y por que son siempre dos proteinas:** las filas 66 y 69 son dos filas, y
`_coordinator.py:434` carga las accesiones de consulta con `.all()` sin
`order_by`, y las corta en lotes en la linea 187. Asi que QUIEN cae en esas filas
lo decide el plan de consulta y cambia de corrida a corrida. El banco si esta
ordenado (`_batch_op_reference.py:525`): es la misma clase de defecto, en el lado
que nunca se arreglo.

## La prediccion para los dos brazos del servidor

Las dos maquinas corren el kernel Haswell con `OPENBLAS_NUM_THREADS` 8. Asi que
**portatil-A contra portatil-B, y el par cruzado portatil-A contra sobremesa-A,
deberian diferir SOLO en esta clase**: autovotos, a distancia cerca de cero, de
exactamente las dos proteinas que caigan en las filas 66 y 69 del trozo final de
70, por exactamente un ulp de float32, con donante de referencia, recuento de
votos, posicion k y libro de donantes identicos.

Falsarian esta explicacion: cualquier diferencia en la seleccion, un numero de
proteinas afectadas distinto de dos, o una diferencia mayor que un ulp.

## Los dos arreglos, los dos despues de esta exploracion

1. **Ordenar las consultas** en `_coordinator.py` de PROTEA, el espejo del #66.
   Hace que dos corridas repitan al bit, que es lo que mide este instrumento.
2. **Rellenar el ultimo trozo** hasta la forma completa, en protea-method, para
   que todas las consultas pasen por la misma forma de GEMM. Mas fuerte: asi la
   distancia de una proteina tampoco depende del conjunto de consultas en que
   vaya, y cubre dos secuencias identicas con accesiones distintas.

Ninguno se aplica aqui: los dos cambian filas. Se descarto como arreglo principal
poner la autodistancia a 0 por definicion, porque tapa un caso especial en vez de
quitar la dispersion en origen.

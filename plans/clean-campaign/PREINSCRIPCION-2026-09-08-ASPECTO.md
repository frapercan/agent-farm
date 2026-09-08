# Preinscripción: la separación por aspecto, medida donde puede moverse

**Escrita el 2026-09-08 a las 10:37 CEST, con los tres brazos a 0/24, 1/24 y
0/24.** Ninguna predicción se escribe después de ver un número; ése es el punto
del fichero y es la razón por la que existe separado.

## Por qué hace falta

El 2026-09-08 se midió la separación por aspecto y salió: 27 deltas negativos,
veinte resolviendo, magnitudes de 0,0001 a 0,0032. Se reportó como veredicto y
**se retiró horas después**, por dos defectos del par comparado:

- los dos brazos corrieron en revisiones distintas, `8699bfd` con época de caché
  2 contra `5674c933` con época 3, y entre ellas está #941, que subió la época
  justamente para invalidar caché;
- y, lo que de verdad lo invalida, **la medida entera está dentro de
  `exclude_self_neighbour=false`**, el régimen que el otro sub-eje acababa de
  mostrar dominado por auto-recuperación.

La medición anterior no era un veredicto. Era, como mucho, un techo.

## El mecanismo que se pone a prueba

Con `selfx=false`, el vecino más cercano es la propia proteína en el **95,0 %**
de las filas a profundidad 1, y el **81,8 %** de las 14.032 consultas no tiene
ningún otro vecino a esa profundidad (medido el 2026-08-28, en el docstring de
`_self_neighbour`). Así que el pool que la separación por aspecto particiona
está hecho en su mayoría de las anotaciones de la **propia proteína**, que ya
contienen el aspecto que se puntúa. Separarlas por aspecto o no hacerlo es casi
la misma operación **por construcción**.

Eso no dice que el efecto quedara tapado: **predice que fuera cercano a cero**,
que es lo que se midió. Y por eso la medida vieja es consistente a la vez con
«el eje no importa» y con «el eje no se pudo mover», sin distinguirlas.

## La predicción, del nodo de cómputo, antes de los datos

> El efecto de la separación por aspecto medido con `selfx=true` será **mayor en
> magnitud** que el medido con `selfx=false`, porque el pool de donantes pasa a
> ser vecinos reales cuyos conjuntos de anotación sí difieren por aspecto.

Con la expectativa declarada y apostada en contra: **espera (B)**, que el efecto
siga siendo de milésimas, porque las vistas por aspecto siguen siendo índices
`int32` sobre un pool unificado y separar sigue recortando sin añadir.

## Los cuatro desenlaces, nombrados antes

| | qué se mide | qué significa |
|---|---|---|
| **A** | magnitud >2× la anterior, misma dirección | el eje **sí** se movía y lo anterior estaba enmascarado; la medida vieja era un techo |
| **B** | magnitud del mismo orden, milésimas | la separación por aspecto **no importa**, ahora establecido, porque se midió donde podía moverse |
| **C** | magnitud mayor, dirección **invertida** | el mecanismo del pool compartido no explicaba la dirección; hay que buscar otra cosa |
| **D** | magnitud **menor** con `selfx=true` | refuta el mecanismo entero: si el pool propio explicaba el cero, quitarlo no puede reducir el efecto |

**(D) es la que deja mal a la explicación de esta tarde**, y por eso está en la
tabla. Una explicación que no puede salir refutada por ningún desenlace no es
una predicción, es una expectativa.

## Cómo se contrasta

Comparación pareada `compare_paired_panels` sobre `f_micro_w`, 2000 remuestreos,
BCa, τ reelegido dentro de cada remuestreo, `ia_weighted`, poblaciones
intersectadas — entre:

    aspsep=true,  selfx=true   (a738e942, 7a049478, 2148fb9e)
    aspsep=false, selfx=true   (e6463d3a, 4021e082, 3941c6c2)

**Un solo campo, y la misma revisión de código en los dos lados**, porque los
seis brazos se despacharon sobre `087fefe`. Eso es lo que faltaba en la medición
retirada, y es lo que hay que comprobar en la fila y no dar por supuesto: el
defecto que la tumbó fue leer `code_revision` como si fuera constante.

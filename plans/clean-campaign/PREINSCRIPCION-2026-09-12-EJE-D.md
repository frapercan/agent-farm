# Preinscripción del eje D: rasgos, sobre la escalera histórica

Escrita el 2026-09-12 en el nodo de cómputo, antes de despachar ningún brazo.
Una vez la escalera corra, preinscribir ya no es posible: sólo es racionalizar.

## Lo que este documento compromete, y lo que no

Compromete cuatro cosas y nada más:

1. **Una predicción**, sobre una observación y no sobre un desenlace.
2. **Una regla de decisión**, con el orden fijado: la potencia primero, las
   comparaciones después.
3. **Un registro de confundidos**, cada uno con su disposición.
4. **Una condición de cancelación**, que se lee tras un peldaño y no tras doce.

**No** compromete una predicción sobre lo que la escalera comprará, ni sobre
dónde estará el codo, ni sobre qué familias usará el combinador en qué celdas.
Esas tres partes son exploratorias y se declaran exploratorias. Un eje
honestamente etiquetado como exploratorio vale más que tres apuestas que no
pueden perder, y el borrador de esta misma preinscripción escribió tres de ésas
antes de que dos pasadas adversariales las cortaran.

## Por qué existe el eje

El eje D pregunta si añadir historia del lado de entrenamiento mejora la
transferencia, y con qué rasgos. Lo que el registro ya cerró y el eje no
reabre está en la tabla del final. Lo que hace que la pregunta siga abierta es
que el valor del re-ranking está en **re-ponderar** y no en **re-ordenar**:
permutar un conjunto fijo de candidatos vale exactamente cero, porque el
puntuador es una suma conmutativa. Así que un eje de rasgos no puede
justificarse como «más rasgos ordenan mejor». Sólo puede justificarse si los
rasgos cambian el peso, y eso es lo que se mide.

## La predicción

**P1.** La tasa de resolución de accesiones cae al menos diez puntos
porcentuales entre el peldaño de prueba y el duodécimo, y no crece más de un
punto en ningún paso.

La refutan una caída menor, o dos subidas por encima de la tolerancia, **haga
lo que haga la curva de rendimiento**. Ésa es la razón de preferirla: se
contrasta sobre una observación del corpus, no sobre un desenlace del eje, así
que un eje que no compre nada no la confirma por defecto.

Los diez puntos son un **juicio, no una medida**. No existe en este disco
ninguna medida de esta tasa sobre una población que coincida. Se declara como
juicio, con su razón: el corpus histórico está atado a una tabla de proteínas
contemporánea sin historia de accesiones, así que la resolución tiene que
degradarse al retroceder, y diez puntos es el menor descenso que distinguiría
degradación de ruido de carga. Si alguien mide la tasa sobre una población que
coincida antes del primer despacho, este número se sustituye por el medido y se
anota la sustitución.

## La regla de decisión

**El veredicto es por celda.** Las nueve celdas, categoría por aspecto, son
nueve poblaciones: un aspecto puntúa sólo las proteínas que ganaron ese
aspecto, y las fracciones medidas son 31, 55 y 34 por ciento, así que las
celdas no comparten ni denominador. Sus tamaños van de 821 a 13.876.

**No se cuentan celdas.** Ni para sellar, ni para confirmar, ni para decidir si
algo hace falta. La regla declarada del plan experimental sella «si un nivel
gana en mayoría de las nueve celdas», y este eje no la usa, por una razón que
no es la agregación sino la ceguera a la potencia: con esa dispersión de
tamaños, una mayoría la puede sostener el subconjunto que menos resuelve,
mientras las celdas grandes resuelven con holgura y pierden la votación.
Cambiar esa regla en el plan es decisión del autor y no se toma aquí.

**La decisión se toma sólo sobre las celdas con potencia declarada, y el
conjunto con potencia se fija antes de leer ninguna comparación.** Tres
estados, y son totales:

| Estado | Cuándo | Qué se hace |
|---|---|---|
| **Sella** | todas las celdas con potencia resuelven en la misma dirección | el suelo es el **mínimo por celda**, nunca una media |
| **Abierto por desacuerdo** | las celdas con potencia resuelven en direcciones opuestas | el desacuerdo *es* el resultado: el efecto depende de la celda, y eso es un hallazgo |
| **Abierto por potencia** | ninguna celda resuelve el efecto de interés | se publica el n requerido por celda |

No es una media, porque no se agrega ningún estimador. No es un voto, porque
las celdas sin potencia no participan. Es total, porque todo caso recibe un
estado, y el grafo de la campaña necesita que un eje reñido reciba un estado y
no nueve respuestas sin decisión.

Una celda que no resuelve se informa **sin potencia**. Nunca como nula, y nunca
promediada con las demás.

## El instrumento, y el orden

El eje se juzga sobre `f_micro_w`, que es un **máximo sobre el umbral de un
cociente de sumas ponderadas** agrupadas a un umbral compartido. Por tanto
`σ/√n` no es su error estándar: no es una media, sus unidades no están
igualmente ponderadas, y la cantidad reportada es un máximo sobre una
superficie estimada. Cualquier tabla de efecto mínimo detectable construida
sobre un multiplicador de cobertura por un error estándar queda excluida de
este eje. Esa construcción se retiró el 2026-09-07 y el primer borrador de esta
preinscripción la reprodujo entera, que es la razón de que este párrafo exista.

El único instrumento admisible es el **remuestreo pareado**, con base de
percentil recentrado, restringido a la clave del panel de cada celda.

**El orden queda pre-comprometido y es la mitad del compromiso:** la potencia
por celda se obtiene de los paneles del propio eje D, **antes** de leer
cualquier comparación entre brazos. No se declara aquí un número de potencia
por celda, porque los datos del eje D no existen y por tanto su potencia no se
puede conocer. Fijar un número que no se puede tener es exactamente cómo el
primer borrador llegó a tener desenlaces refutadores inalcanzables.

Las sigmas de cohortes anteriores no se usan, por dos motivos independientes:
el instrumento no aplica, y esa cohorte mezcla el holdout competitivo.

## Ningún suelo heredado

El eje D **no hereda suelo** para decir si un brazo hizo algo. El suelo del
re-ranker que estaba disponible está enmarcado en la ventana que esta campaña
veda, así que sale del argumento entero: no como umbral, no como comparador, no
como previo y no como magnitud. Un suelo ausente y declarado ausente es
honesto; uno traído de una ventana prohibida no lo es, y una preinscripción no
puede vedar una ventana y apoyarse en un número medido en ella.

Antes de llamar útil a ningún brazo hay que medir un suelo sobre la ventana
declarada. Eso es trabajo del eje, no un supuesto del eje.

## La condición de cancelación, leída tras UN peldaño

Se lee sobre el peldaño de prueba, antes de cargar los once restantes. Cualquiera
de estas tres cancela la escalera: no la deja abierta, la cancela, y el disco no
se gasta.

| | Condición | Por qué cancela |
|---|---|---|
| K1 | la resolución de accesiones del peldaño cae por debajo de nueve décimas | un peldaño que no resuelve no aporta consultas, aporta disco |
| K2 | la resolución de términos en espacio de texto cae por debajo de 95 centésimas | los identificadores de término son por instantánea, así que un peldaño mal atado transfiere contra una ontología que su conjunto ya no declara |
| K3 | alguna de las nueve celdas queda por debajo de doscientos positivos | una celda así no resuelve nada y el eje no puede informarla ni como nula |

K1 y K2 son juicios declarados, no medidas trasladadas: las cifras disponibles
de cobertura están medidas del lado de las proteínas y no del lado de las
accesiones, y las de resolución de términos están medidas sobre entregas
modernas cuya época no coincide con la de la escalera. Usar cualquiera de las
dos como si coincidiera es el defecto que este proyecto corrige más veces, así
que se declaran como juicio con su razón en vez de heredar un número que no
mide lo que se afirma.

**Lo que se sabe hoy, y es buena noticia para la escalera:** el impuesto de
ocho años de deriva es de **2,58 puntos**, no de sesenta.

| Entrega | Filas | Proteínas | Cobertura de 575.503 |
|---|---|---|---|
| 160 | 5.285.072 | 541.604 | 94,11 % |
| 219 | 6.153.651 | 556.447 | 96,69 % |
| 220 | 5.317.051 | 556.306 | 96,66 % |
| 227 | 5.880.402 | 557.071 | 96,80 % |

Población: la tabla de proteínas de esta campaña, 575.503 entradas, instantánea
contemporánea sin historia de accesiones. El par de dos meses es el control: 219
y 220 son indistinguibles, así que el filtro no pierde nada por deriva reciente
y lo que se mide entre 160 y 220 es deriva y no artefacto de carga.

## La ablación: por columnas, nunca por nombres de familia

El esquema de rasgos declara 21 familias sobre 78 columnas. Una de ellas,
`knn`, es la **unión exacta** de `knn_distance` y `knn_vote`, y es el único caso:
sólo dos pares comparten columnas en todo el esquema y los dos involucran a
`knn`. Así que los 21 nombres cubren **20 conjuntos independientes**.

Consecuencia, y es la razón de este apartado: **dejar una familia fuera no puede
aislar esas siete columnas.** Quitar `knn` las deja entrar por las dos
subfamilias, y quitar una subfamilia las deja entrar por `knn`. Una ablación
sobre nombres de familia produciría tres brazos que no quitan nada y nadie lo
notaría en el resultado.

La ablación se hace **quitando columnas**, por el argumento de exclusión del
sellador de esquema, que está documentado para eso y ya existe. No se implementa
la versión por familias. El sellador de familias y el de columnas son dos
huellas distintas a propósito: el primero ata nombres y columnas juntos y da
digests distintos al mismo conjunto de columnas, y eso es su contrato, no un
defecto.

Cada resultado de la ablación recibe uno de cuatro estados por celda, simétricos
en signo:

| | Estado |
|---|---|
| A1 | resuelta y con magnitud en el efecto de interés o por encima |
| A2 | **resuelta y por debajo del efecto de interés**: existe, no sella nada |
| A3 | sin resolver, con potencia |
| A4 | sin resolver, sin potencia, con el n requerido declarado |

A2 existe en los dos signos. Un efecto cuyo intervalo excluye el cero pero cuya
magnitud queda por debajo del interés es un estado con nombre propio, no un
hueco de la tabla: los huecos de tabla son cómo un resultado se reinterpreta
después.

## Confundidos, con disposición

| Confundido | Disposición |
|---|---|
| `prediction_set.meta` no registra la máquina que computó el brazo, y dos máquinas sirven las colas | **medir**: el rol de la topología ya viaja en cada evento de trabajo hijo, así que el cruce es posible hoy y hay que hacerlo antes de declarar el eje |
| la clave de la caché de reservorio nombró un puntero y no un contenido, y los identificadores de término son por instantánea | **excluir**: la época de caché está por delante de la reparación, verificado antes de despachar |
| el índice de embeddings de ontología declara una sola época contra una escalera de doce, y un término desconocido se enmascara a cero sin levantar nada | **excluir**: sus familias no entran en el eje mientras no haya productor registrado por época |
| el guardia de ontología rechaza sólo lo posterior, y para una escalera hacia atrás importa la magnitud del desfase y no su signo | **medir**: se registra el desfase por peldaño. Medido hoy: exacto en el 160, once días en el 219 |
| el disparo automático de conjuntos de evaluación comprueba la existencia sobre dos columnas mientras la restricción tiene cinco, así que el primer conjunto de una pareja bloquea su propio reemplazo | **limitación bloqueante**: ningún brazo se despacha hasta que esté resuelto. No es del eje, es de la plataforma |
| la tabla de conjuntos de anotación no tiene marca de completitud, así que un conjunto a medio cargar es indistinguible de uno terminado | **limitación bloqueante**, por lo mismo |
| el contador de anotaciones insertadas cuenta candidatos construidos y no filas escritas | **declarar**: el exceso medido es 0,004 por ciento en el 160 y 0,33 en el 219. La diferencia de ochenta veces entre las dos entregas no está explicada y merece una frase antes de cargar doce |
| el nodo de cómputo pierde su conexión de mensajería durante cada carga larga y no aparece como consumidor mientras trabaja | **declarar**: medido, noventa y dos minutos contra un latido de diez, y se recupera solo en cinco segundos. No pierde trabajo, hace ilegible el estado de la cola |

## Lo que el eje D no reabre

| Resultado | Población | Por qué no se remide |
|---|---|---|
| re-ponderar vale, re-ordenar vale exactamente cero | el puntuador, por construcción | es una propiedad algebraica de una suma conmutativa, no una medida que pueda salir distinta |
| el número de vecinos útil está entre tres y diez, y treinta es demasiado | dos poblaciones, dos codificadores, 16 de 18 comparaciones | el eje D no varía el número de vecinos |
| el eje de corpus está cerrado por aritmética | el reservorio completo | alcanzar un ajuste en dominio exigiría un corpus que no existe |
| la última capa gana, y ninguna combinación de capas la mejora | cuatro profundidades, tres medidas | el eje D no varía la capa |
| las estadísticas de la ontología no explican la frontera | el grafo, idéntico en las tres categorías | no es un candidato de rasgo |

## Apéndice: lo que las pasadas adversariales cambiaron

Esta preinscripción se escribió tres veces y se cortó la cuarta parte. La
primera versión tenía 610 líneas, la segunda 1.206 y la tercera 1.597, y el
recuento de defectos enumerados se mantuvo plano mientras el documento se
triplicaba: tres predicciones infalsables y cuatro huecos de desenlace en la
segunda y en la tercera, y los apoyos en ventanas vedadas subiendo de dos a
cuatro. Dos de los defectos de la tercera pasada nacieron de arreglos de la
segunda, uno de ellos por adoptar dos correcciones a la vez, que es un defecto
que ninguna de las dos pasadas podía ver por separado.

Lo que eso enseña, y es la razón de que esta versión sea corta: **la longitud
era el defecto.** La tercera versión vedaba una ventana en su línea 131 y
derivaba de esa misma ventana un umbral universal en la 1.120. Novecientas
ochenta y nueve líneas de distancia. En un documento de este tamaño esa
contradicción no se puede escribir.

Lo que las pasadas sí encontraron, y se conserva:

- El primer borrador reprodujo entera la construcción de efecto mínimo
  detectable retirada el 2026-09-07, en el mismo párrafo donde decía respetar su
  retirada. Buscando por qué, se encontró que el tronco la seguía ofreciendo: la
  retirada quitó la tabla y dejó vivo el criterio que la consume.
- Los desenlaces del primer borrador exigían mayoría de cinco sobre nueve
  celdas, mientras su propia lectura de potencia daba entre tres y cuatro, así
  que el desenlace refutador era inalcanzable y el predicho automático.
- El segundo borrador cortó su predicción cabecera por estar satisfecha por su
  propio nulo, y escribió dos reemplazos con la misma forma. De ahí la decisión
  de degradar en vez de reemplazar: una predicción infalsable no mejora
  reescribiéndola el mismo día.

La evidencia completa de las tres pasadas queda en este directorio: seis
informes de superficie con su verificación, dos ataques, dos cierres y una
certificación. Las versiones largas están en `descartes/`, no borradas, porque
el recuento de defectos que no baja es en sí mismo el resultado.

# score-ablation — Plan

Sustituye los scores triviales del grid SELECT (embedding_only / vote_fraction /
composite, pesos 0/1 a mano) por una EXPLORACION DE SCORE SENSATA, DERIVADA
IN-SITU PARA CADA CATEGORIA (NK/LK/PK x BPO/MFO/CCO), sobre el modelo ganador
ligero, en la ventana SELECT 220->227 (LAFA-frame, full-GT `f_micro_w`).
Track A del ROADMAP-THESIS-10.

El score se EXPLORA y AJUSTA por (categoria, aspecto), no global: la K de
retrieval (A-SCORE.0), los pesos de features (A-SCORE.1) y la temperatura /
prior / calibracion (A-SCORE.2) se fijan por celda. El entregable es una TABLA
DE SCORE POR CATEGORIA (que celda usa que knobs), no un unico juego colapsado.

Disciplina (NO rompe el rigor): sigue siendo UN solo metodo principiado, una
familia `scoring_config` condicionada por categoria, vista en `/benchmark`; no
son scores rivales ni `vN`. Cada especializacion por categoria debe BATIR al
ajuste agrupado (pooled) en CV interno held-out de 220->227 (k-fold por
proteina) o se REVIERTE al pooled (anti winner's-curse: NK tiene pocas
proteinas y sobre-ajusta facil). La ventana FINAL 227->230 no se toca en este
loop.

Motivacion (medido sobre 220->227, embedding_only, media de 8 PLMs):
- El KNN esta limitado por PRECISION, no por recall (R_w casi dobla a P_w en
  las 9 celdas; el techo de recall del ref-pool es ~0.99).
- El fallo se concentra en terminos profundos de alta IA: la precision sin
  pesar cae fuerte al pesar por IA (CCO -0.22), senal de que propagamos los
  terminos hoja del vecino, que no transfieren.
- El embedding casi no mueve la aguja (8 PLMs dentro de 0.03); el SCORE si
  (stages dentro de 0.02-0.04). Hemos optimizado el eje equivocado.

## Invariantes (todas las slices)

- MODELO FIJO: Ankh-base (450M, ganador ligero; dentro del CI del top).
  ProtT5-XL como control. Se elimina el eje PLM y se aisla el eje score.
- VENTANAS (sin ambiguedad). VALIDACION = delta 220->227 (eval_set
  817c6b9f, `window_role='valid'`): aqui se deriva, ajusta y rankea el
  score. PROMOCION/HELD-OUT = 227->230: lo que se sube a LAFA, SELLADO,
  no se toca en este loop (el numero insesgado final sale ahi). El reranker
  se entrena con datos PREVIOS a 220, pero eso queda FUERA de scope ahora.
  No hay sub-split 226: 220->227 es la ventana de validacion completa.
- SIN LEAKAGE, SIN VARIANTES. Los parametros del score (T, prior, K) se
  ajustan sobre 220->227; 227->230 sellado; un solo score final, sin `vN`.
- PRIOR KNOWLEDGE NO ES LEAKAGE. Ponderar o excluir por `evidence_code`
  (descontar IEA por su circularidad homologica) es prior biologico valido,
  decidido a priori sobre el pool de referencia t0, sobre la evidencia de
  ENTRADA del vecino, nunca sobre las etiquetas held-out. NO es leakage: un
  executor NO debe marcarlo como tal. De hecho lo arriesgado es no descontar
  IEA (transferencia circular que infla).
- UI ES LA FUENTE DE VERDAD. El score elegido se registra como `scoring_config`
  y sus numeros se ven en `/benchmark`. Nada de CSV sueltos.
- FEATURES YA MATERIALIZADAS. El `score.tsv` ya trae por (proteina, termino,
  vecino): `embedding_similarity` (1 - cos/2), `identity_nw` (global, NW),
  `identity_sw` (local, SW), cobertura/gaps del alineamiento,
  `taxonomic_distance`, `evidence_code`, `neighbor_vote_fraction`. Re-puntuar
  y re-ajustar sobre esa matriz; NO recomputar KNN ni alineamientos. Acceso
  read-only por API, nunca DB directa, nunca curl ad-hoc a endpoints de
  operacion (dispatch por POST /jobs).
- METRICA: full-GT `f_micro_w` (NO candidate-set, que infla con un score
  fuerte). Reportar P_w / R_w / F_w por (categoria, aspecto).

## A-SCORE — derivacion del score por ablation

### A-SCORE.0 — K ablation (retrieval)

```yaml
id: A-SCORE.0
phase: A-SCORE
loop: score-ablation
status: pending
deps: [F-EVAL-PROTOCOL.valid]
```

K ablation sobre SELECT 220->227, modelo Ankh-base, las 9 celdas.
Serie K = [3, 5, 10, 30]. (Tramo alto 100-1000 PARADO como configuracion
alternativa, fuera de scope de esta slice.)

- Curva por aspecto de `recall_w` / `precision_w` / `f_micro_w` vs K.
- Localizar la saturacion de recall por aspecto (techo ref-pool ~0.99).
  Esperado: BPO se beneficia de K30; MFO/CCO prefieren K bajo.
- K3/5/10 ya materializadas; solo completar K30 donde falte (a K<=30 el
  alineamiento por vecino es asumible).
- Analisis JUNTO con el score: K alto solo paga con agregacion similarity-
  weighted; con max-sim o vote es plano o peor. Cruzar con A-SCORE.2.

Exit: K optima por aspecto; input para fijar K en A-SCORE.2.
Suggested agent: claude (data/eval)

### A-SCORE.1 — Ablation completa de features

```yaml
id: A-SCORE.1
phase: A-SCORE
loop: score-ablation
status: pending
deps: [F-EVAL-PROTOCOL.valid]
```

Modelo Ankh-base, K=3, las 9 celdas (NK/LK/PK x BPO/MFO/CCO).
Features: `embedding_similarity`, `identity_nw` (global), `identity_sw`
(local), cobertura/gaps del alineamiento (descuento de confianza),
`taxonomic_distance`, `evidence_code` (tier EXP vs IEA), `neighbor_vote_fraction`.

Procedimiento:
1. Matriz de correlacion de las features (exponer redundancia ANTES de nada;
   embedding_sim e identity_nw/sw seran colineales).
2. Leave-one-in (senal en solitario) Y leave-one-out (valor marginal dado el
   resto). El hueco entre ambos separa redundancia de senal unica.
3. Pesos AJUSTADOS (logistica o LightGBM ligero) sobre 220->227 (validacion),
   NO pesos 0/1 a mano. Control de overfitting DENTRO del loop = CV interno
   sobre 220->227 (k-fold por proteina, sin que un mismo accession caiga en
   train y test del fold). 227->230 NO se toca aqui; el numero insesgado final
   sale ahi en la promocion del campeon, FUERA de este loop.
4. Estratificar por bin de identidad de secuencia Y por bin de LONGITUD de
   query (el valor de embedding vs alineamiento es CONDICIONAL a ambas: la
   identidad cruda infla en secuencias cortas; el mean-pool del embedding es
   no monotono en longitud, ruidoso en cortas y difuminado en multidominio).
5. Brazo `evidence_code`: comparar (a) sin pesar, (b) ponderado por tier,
   (c) IEA excluido. Etiquetar como prior-knowledge, NO leakage.

Hipotesis a confirmar o refutar:
- embedding gana al alineamiento a baja identidad (twilight zone).
- SW (local) > NW (global) en MFO (dominio = funcion molecular).
- gaps/cobertura recortan sobre-prediccion (palanca de precision).
- evidence-tier sube precision; IEA-excluido limpia circularidad.
- taxonomic_distance ~0 (memoria reranker LM.3), reconfirmar en full-GT.

Exit: tabla valor-marginal + valor-solo por feature y celda; veredicto
survive/muere por feature; hipotesis resueltas.
Suggested agent: claude (data/eval)

### A-SCORE.2 — Score posterior calibrado (el del grid SELECT)

```yaml
id: A-SCORE.2
phase: A-SCORE
loop: score-ablation
status: pending
deps: [A-SCORE.0, A-SCORE.1]
```

Con las features supervivientes de A-SCORE.1 y la K por aspecto de A-SCORE.0,
construir UN score tipo log-odds naive-Bayes sobre vecinos:

```
logit P(t) = log( prior_t / (1 - prior_t) ) + beta * sum_{vecinos con t} k(sim_n)
  k(sim) = exp(sim / T)          (soft-vote con temperatura)
  prior_t = IA / frecuencia      (GO-IDF; penaliza terminos someros frecuentes)
  peso del vecino incluye evidence-tier (EXP > IEA)
```

- Calibracion isotonica por aspecto y bin de IA sobre 220->227 (validacion),
  de modo que el score sea una PROBABILIDAD comparable entre terminos y
  aspectos (un unico umbral global pasa a ser principiado).
- Barrido conjunto (T, exponente del prior, K en {3,5,10,30}) en validacion.
- Registrar el resultado como UN `scoring_config` nuevo (frozen, sin `vN`),
  surfaced en `/benchmark`.

Exit: un score; el grid SELECT (PLM x K x score) rankeable con el; numeros
verificables en la UI; los stages triviales quedan como dos extremos (T->0 y
T->inf) del mismo score parametrizado.
Suggested agent: claude

### A-SCORE.3 — Drill termino-a-termino (justifica el prior IA)

```yaml
id: A-SCORE.3
phase: A-SCORE
loop: score-ablation
status: pending
deps: []
```

PK-BPO (P_w=0.033) + NK-MFO (control bueno): extraer los GO sobre-predichos
(predichos pero fuera del delta GT) vs el delta real; distribucion de IA,
frecuencia y profundidad. Datos via API read-only:
`GET /scoring/prediction-sets/{id}/score.tsv` +
`GET /evaluation-sets/817c6b9f-62cc-42bc-afac-6f72a21525f6/ground-truth-PK.tsv`,
IA en `data/benchmarks/IA_cafa6.tsv`.

Exit: evidencia empirica de que lo sobre-predicho es de baja IA / alta
frecuencia (justifica el GO-IDF de A-SCORE.2) + material de redaccion Ch6.
Puede correr en paralelo a A-SCORE.0 / A-SCORE.1.
Suggested agent: Explore / claude

### A-SCORE.4 — Scoring instance-conditional (gating por priors de la query)

```yaml
id: A-SCORE.4
phase: A-SCORE
loop: score-ablation
status: pending
deps: [A-SCORE.2]
```

Generaliza el score por-celda a un score que se ADAPTA por proteina segun sus
caracteristicas prior (no las etiquetas: sin leakage). NK/LK/PK ya es un
conditioning de 3 buckets sobre el estado de anotacion previo; esto lo sube a
conditioning continuo sobre priors robustas de la query.

LINEA QUE NO SE CRUZA: condicionar sobre FEATURES prior (generaliza) SI;
heuristica bespoke por proteina concreta (overfitting, no validable) NO.

Priors de conditioning (pocas y robustas, NO un saco). Marco unificador: todas
estiman una sola cosa latente, la CONFIANZA DE TRANSFERENCIA por homologia para
ESTA proteina, que gatea cuan agresivo es el score:
- Confianza de homologia = identidad / distancia al vecino mas cercano (la
  variable estrella: orphan -> conservador; homologo 90% experimental ->
  transferencia agresiva). Ataca el modo de fallo en su raiz (sobre-commit de
  terminos profundos arrastrados por UN vecino lejano).
- Longitud de la query (no monotona): cortas -> identidad de alineamiento
  espuria + mean-pool ruidoso; largas/multidominio -> mean-pool difuminado +
  NW global engaña (manda SW local) + mas terminos esperados. Sugiere
  presupuesto de terminos escalado por longitud y/o bit-score en vez de
  identidad cruda.
- Densidad de vecinos (familia densa caracterizada vs proteina dark/huerfana).
- Presencia / nº de dominios InterPro (multidominio -> transferir por dominio,
  SW local manda). Camino FALLBACK para proteinas sin dominio.
- Distancia taxonomica al vecino (riesgo de convergencia -> descuento).
- [PRIORIDAD ALTA] Entropia / acuerdo de los vecinos: si los K vecinos coinciden
  en terminos (baja entropia -> confianza) o se dispersan (alta -> ambiguedad).
  La senal de confianza per-query mas barata, sale directa del candidate-set
  sin computar nada nuevo.
- [PRIORIDAD ALTA] Anotaciones t0 que la query YA tiene, como conditioning
  (prior legitimo: <= t0, conocido al predecir, define LK/PK; NO es leakage).
  Acoplamiento funcional: un MFO conocido restringe los BPO plausibles
  (correlaciones GO cross-aspecto). Unica via para arañar en PK sin evidencia
  externa: usar las funciones ya conocidas para priorizar el incremento novedoso
  (no rompe el techo info-teorico, lo sube algo donde el score solo no llega).
- Desorden / baja complejidad (fraccion IDR, predecible a priori): las proteinas
  intrinsecamente desordenadas rompen el supuesto funcion=local; embedding y
  alineamiento poco fiables -> conservador. Cubre un modo de fallo que ninguna
  otra prior toca.
- Candidatas de segunda ronda (solo si la lista corta no satura la mejora en
  held-out): contenido TM / signal-peptide (lever dirigido a CCO), margen
  1o-vs-2o vecino, evidencia EXP del mejor vecino, densidad de referencia del
  taxon de la query, composicion aminoacidica sesgada.

Realizacion: NO es un eje magico nuevo. Es "añadir las priors de la query como
features de conditioning y dejar que un modelo (el reranker GBM, o T(x)/beta(x)
parametrico) aprenda el gating por interacciones". El reranker ya hace una
version debil; falta alimentarlo explicito con estas priors.

Coste de features (a diferencia de A-SCORE.0/.1/.2, que re-puntuan sobre el
score.tsv ya materializado): longitud, entropia-de-vecinos, anotaciones t0 y
distancia taxonomica son baratas o ya disponibles (join sobre datos existentes);
desorden (IUPred/flDPnn) y cobertura InterPro requieren computo extra ->
presupuestar o dejarlas para la 2a ronda.

Disciplina anti-winner's-curse:
- Pocas priors robustas; gating simple.
- La mejora debe SOBREVIVIR en CV interno held-out de 220->227 (k-fold por
  proteina), no solo en el ajuste. 227->230 NO se toca aqui: su unico toque es
  la promocion final del campeon congelado, fuera de este loop.
- Gated DETRAS de A-SCORE.2: primero se valida el score por-celda; si saltas al
  instance-adaptive antes, no puedes atribuir si la ganancia viene del prior-IA
  o del gating.

Exit: veredicto de si el scoring condicional por priors bate al score por-celda
de A-SCORE.2, con la ganancia confirmada en held-out; taxonomia de regimenes de
prediccion (homologo-cercano / twilight / multidominio / dark / convergencia)
documentada para Ch6. Suggested agent: claude

## Secuencia

```
A-SCORE.0 (K)        \
A-SCORE.1 (features)  >-- en paralelo --> A-SCORE.2 (score) --> A-SCORE.4 (instance-conditional)
A-SCORE.3 (drill)    /                          |                        |
                                                v                        v
                                          ranking grid SELECT     confirmar en CV interno (220->227)
```

A-SCORE.2 depende de .0 y .1. A-SCORE.3 es independiente y alimenta la
justificacion del prior. A-SCORE.4 cuelga de .2 (instance-conditional solo
tras validar el score por-celda). Todo cuelga del protocolo no-leakage de
Track A (select en 220->227, 227->230 intacto).

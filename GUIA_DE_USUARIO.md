# Guía de usuario — Programa MOORA

Guía de uso del programa, paso a paso. La instalación, las pruebas y la estructura del código están en el [README](README.md).

## Introducción

MOORA ordena un conjunto de alternativas según varios criterios y muestra todo el cálculo, paso a paso. Resuelve cada problema con dos métodos a la vez y los compara:

- **Sistema de Razones (SR):** es compensatorio. Suma los aportes de todos los criterios, así que una fortaleza puede compensar una debilidad. Gana el mayor yᵢ.
- **Punto de Referencia (PR):** es no compensatorio. Juzga a cada alternativa por su peor desvío respecto del ideal. Gana el menor dᵢ.

### Cómo abrir y cerrar el programa

1. Haga doble clic en **Iniciar MOORA.bat**. Necesita Python 3.10 o superior instalado en el equipo.
2. Espere a que termine la preparación. La primera vez crea el entorno e instala los paquetes, lo que requiere internet y puede tardar unos minutos.
3. El programa se abre solo en el navegador, en `http://localhost:8501`. Si ese puerto está ocupado, usa el siguiente libre.
4. Para cerrarlo, cierre la ventana negra de la consola. Cerrar solo la pestaña del navegador deja el servidor en marcha.

### Recorrido general

El trabajo sigue seis pasos, en este orden. Al abrir el programa ya hay un ejemplo cargado («Selección de proveedores»), de modo que puede recorrer todos los pasos antes de cargar sus datos.

| Paso | Para qué sirve |
| --- | --- |
| 1 · Datos del problema | Cargar alternativas, criterios y valores |
| 2 · Criterios y pesos | Definir el sentido de cada criterio y su peso |
| 3 · Resultados paso a paso | Elegir la normalización y ver cada tabla del cálculo |
| 4 · Comparación y gráficos | Contrastar los dos rankings y ver por qué gana cada alternativa |
| 5 · Análisis de sensibilidad | Probar qué pasa si cambia el peso de un criterio |
| 6 · Exportación | Descargar resultados y guardar el problema |

## Barra lateral izquierda

La barra lateral está siempre visible y cumple dos funciones: moverse entre los pasos y ver el estado del problema sin salir de la pantalla actual. Sus elementos son, de arriba hacia abajo:

| Elemento | Qué muestra o hace |
| --- | --- |
| **Lista de pasos** | Lleva a cualquiera de los seis pasos con un clic, en cualquier orden. El punto marcado indica el paso actual. |
| **Nombre del problema** | Repite el nombre escrito en el paso 1. Si está vacío, dice «Problema sin nombre». |
| **Datos del problema** | Indica el tamaño de la matriz, el método de pesos y la normalización en uso. Por ejemplo: «4 alternativas × 4 criterios · pesos: asignación directa · normalización vectorial». |
| **Ganadores (SR y PR)** | Muestra la mejor alternativa de cada método. Se actualiza con cada cambio. Si hay empate, aparecen los nombres separados por «/». |
| **Decimales a mostrar** | Fija cuántos decimales se ven en tablas, métricas y etiquetas de gráficos, de 2 a 10. El valor inicial es 4. Solo cambia la vista: no altera el cálculo. |
| **Acerca de** | Se despliega con un clic y describe brevemente el método y el origen del trabajo práctico. |

### Cómo leer el aviso de estado

Debajo de los ganadores aparece uno de estos tres avisos:

- **Marca verde, «Ambos métodos coinciden en la mejor alternativa»:** SR y PR eligen la misma opción.
- **Advertencia, «Los métodos difieren en la mejor alternativa»:** no es un error. Cada método eligió una opción distinta, y el paso 4 explica por qué.
- **Prohibido, «N problema(s) por corregir antes de calcular»:** faltan datos o hay datos inválidos. Los pasos 3 a 6 muestran la lista de errores y ofrecen botones para volver a corregirlos.

## 1 · Datos del problema

Este paso define qué se compara: las alternativas (filas), los criterios (columnas) y sus valores. Hay tres formas de cargarlos, una por pestaña, y las tres terminan en las mismas tablas editables al pie de la pantalla.

El campo **Nombre del problema** es el primero de la pantalla. Ese nombre aparece en la barra lateral y se usa para nombrar los archivos exportados.

### Pestaña Ejemplos precargados

Elija un ejemplo de la lista y presione **Cargar ejemplo**. El ejemplo reemplaza al problema actual.

| Ejemplo | Tamaño | Para qué sirve |
| --- | --- | --- |
| Selección de proveedores (ejemplo del TP) | 4 × 4 | Ver un caso en que los métodos difieren: SR elige al Proveedor C y PR al Proveedor A |
| Ubicación de una planta | 5 × 6 | Practicar con más criterios, entre costos y beneficios |
| Selección de candidatos | 6 × 5 | Ver un caso en que ambos métodos coinciden |
| Inversión en robots (actividad de la cátedra) | 6 × 6 | Contrastar el resultado con la resolución en Excel de la actividad |

### Pestaña Carga manual

Use esta pestaña para escribir los datos directamente en el programa.

1. Indique **Alternativas (m)** y **Criterios (n)**, de 1 a 50 cada uno. Cambiar estos números no hace nada hasta presionar uno de los botones del paso siguiente.
2. Presione uno de los dos botones:
   - **Nueva matriz vacía** borra el problema actual y crea una tabla vacía, con nombres provisorios A1, A2… y C1, C2…
   - **Aplicar dimensión (conserva datos)** cambia el tamaño y mantiene lo que entra. Si achica la tabla, se pierden las últimas filas o columnas.
3. En la tabla **Nombres de los criterios**, reemplace C1, C2… por los nombres reales.
4. Si quiere, elija una unidad para cada criterio en **Unidades de medida**.
5. En la tabla **Matriz de decisión**, escriba el nombre de cada alternativa en la primera columna y sus valores en las demás.

Para editar una celda, selecciónela con un clic, presione Enter, escriba y confirme con Enter. Al confirmar, la selección baja a la celda de abajo, lo que agiliza la carga por columnas. Las celdas vacías muestran la palabra «None».

**Atención con los decimales al escribir en las tablas.** Con el navegador en español, el separador decimal es la coma: `7,25` queda bien y la tabla lo muestra como 7.25. En cambio, `5.5` queda como **55**, porque el punto se descarta. El separador depende del idioma del navegador, así que compruebe la primera celda que cargue.

### Pestaña Importar Excel / CSV

Use esta pestaña si ya tiene los datos en una planilla.

1. Presione **Upload** y elija un archivo `.xlsx`, `.xls` o `.csv` de hasta 20 MB.
2. Si el libro de Excel tiene varias hojas, elija la correcta en **Hoja**. Si no elige, se lee la primera.
3. Revise la **Vista previa**: la cantidad de alternativas y criterios, los valores y la leyenda que indica si se encontraron sentidos y pesos.
4. Presione **Usar estos datos**. Hasta ese momento, el problema actual no cambia. Al confirmar, los datos lo reemplazan y el problema toma el nombre del archivo.

### Forma que debe tener el archivo

El archivo debe contener una sola tabla, con los criterios en la primera fila y las alternativas en la primera columna. Excel y CSV usan exactamente la misma estructura:

| Alternativa | Precio | Calidad | Plazo | Capacidad |
| --- | --- | --- | --- | --- |
| Proveedor A | 120 | 8 | 10 | 5000 |
| Proveedor B | 100 | 7 | 15 | 4000 |
| Proveedor C | 135 | 9 | 7 | 6000 |
| Proveedor D | 110 | 6 | 12 | 4500 |
| Sentido | Costo | Beneficio | Costo | Beneficio |
| Peso | 0,35 | 0,30 | 0,15 | 0,20 |

| Parte de la tabla | Contenido | ¿Obligatoria? | Si falta |
| --- | --- | --- | --- |
| Primera fila | Nombres de los criterios. La primera celda puede tener cualquier texto o estar vacía, salvo una de las palabras reservadas para las filas Sentido o Peso. | Sí | El archivo se rechaza |
| Primera columna | Nombres de las alternativas | Sí | Se completan con A1, A2… y se avisa |
| Resto de las celdas | Valores numéricos | Sí | La celda queda vacía y debe completarse en la matriz |
| Fila **Sentido** | Beneficio o Costo de cada criterio | No | Todos los criterios se toman como Beneficio |
| Fila **Peso** | Peso de cada criterio, en cualquier escala | No | Todos los criterios reciben el mismo peso |

Las filas Sentido y Peso pueden ir antes o después de los datos. Los pesos no necesitan sumar 1: `35; 30; 15; 20` es válido y se normaliza después.

**En Excel:** coloque cada dato en su propia celda. La tabla puede empezar en cualquier celda de la hoja, no solo en A1.

**En CSV:** escriba una fila por línea. Son válidas estas dos formas:

Punto y coma como separador y coma decimal (la más cómoda con Excel en español):

```text
Alternativa;Precio;Calidad;Plazo;Capacidad
Proveedor A;120;8;10;5000
Proveedor B;100;7;15;4000
Proveedor C;135;9;7;6000
Proveedor D;110;6;12;4500
Sentido;Costo;Beneficio;Costo;Beneficio
Peso;0,35;0,30;0,15;0,20
```

Coma como separador y punto decimal:

```text
Alternativa,Precio,Calidad,Plazo,Capacidad
Proveedor A,120,8,10,5000
Proveedor B,100,7,15,4000
Proveedor C,135,9,7,6000
Proveedor D,110,6,12,4500
Sentido,Costo,Beneficio,Costo,Beneficio
Peso,0.35,0.30,0.15,0.20
```

No combine coma como separador con coma decimal: el archivo se rechaza con un error como «Error tokenizing data». También se acepta el tabulador como separador, y los acentos se leen bien.

**Palabras que reconoce el programa** (no distingue mayúsculas de minúsculas):

| Uso | Palabras aceptadas |
| --- | --- |
| Rótulo de la fila de sentidos | Sentido, Sentidos, Tipo, Dirección, Objetivo, Max/Min, Optimización |
| Criterio de beneficio | Beneficio, Max, Máximo, Maximizar, Mayor, Benefit, Maximize, + |
| Criterio de costo | Costo, Coste, Min, Mínimo, Minimizar, Menor, Cost, Minimize, - |
| Rótulo de la fila de pesos | Peso, Pesos, W, Wj, W\_j, Ponderación, Ponderaciones, Importancia |

Una fila sin rótulo también se toma como sentidos si todos sus valores son palabras de esta lista. Un sentido no reconocido se toma como Beneficio y el programa lo avisa.

**Cómo se leen los números.** Evite los separadores de miles, porque un número como `5.000` se lee como 5 sin ningún aviso:

| En el archivo | Se lee como | Resultado |
| --- | --- | --- |
| `120,5` o `120.5` | 120,5 | Correcto |
| `5.000,50` o `5,000.50` | 5000,5 | Correcto, porque tiene ambos signos |
| `35%` | 0,35 | Correcto |
| `5000` | 5000 | Correcto y recomendado |
| `5.000` | **5** | Incorrecto, sin aviso |
| `1,234` | **1,234** | Incorrecto si quería decir mil doscientos, sin aviso |
| `1.234.567` | Celda vacía | Se avisa como valor no numérico |

**Otros detalles de la lectura:**

- **Fila en blanco:** corta la lectura de alternativas, sin aviso. Si hay una fila vacía en medio de los datos, se pierden las siguientes. Controle la cantidad en la Vista previa.
- **Debajo de la tabla:** después de una fila en blanco solo se leen las filas Sentido y Peso. Cualquier otra cosa se ignora, así que puede importar planillas con otras tablas abajo.
- **Columna sin nombre:** se ignora por completo.
- **Alternativa sin valores:** se ignora y el programa avisa.
- **Nombres repetidos:** se renombran y el programa avisa. Por ejemplo, un segundo «C1» pasa a ser «C1 (2)».
- **Unidades de medida:** no se leen del archivo. El texto del encabezado se conserva tal cual, como en `Precio ($/u)`, y las unidades se eligen después.
- **Archivos `.xls`** (Excel 97-2003): se importan igual que los `.xlsx`, incluida la elección de hoja.

**El camino más seguro es partir de una plantilla.** Los botones **Plantilla Excel** y **Plantilla CSV (;)** descargan el problema actual con este mismo formato. Reemplace los datos en ese archivo y súbalo.

### Tablas al pie de la pantalla

Estas tablas aparecen con cualquiera de las tres formas de carga, y sirven para revisar o corregir los datos:

- **Nombres de los criterios:** una fila con el nombre de cada criterio.
- **Unidades de medida:** una lista por criterio con sugerencias como `$`, kg, km o días, donde también puede escribir una unidad propia. Es solo informativa y no interviene en el cálculo. Desde ese momento, el criterio se muestra con la unidad entre corchetes, como en `Precio [$]`.
- **Matriz de decisión:** la tabla de valores. No admite agregar filas o columnas por sí sola: eso se hace con la pestaña Carga manual.

Debajo de la matriz, un mensaje verde confirma «La matriz está completa y es válida». Si hay algo para corregir, aparece en rojo o en amarillo.

## 2 · Criterios y pesos

Este paso define dos cosas de cada criterio: si conviene que su valor sea alto o bajo (el sentido) y cuánto importa en la decisión (el peso).

### Tabla de criterios

| Columna | Qué se carga |
| --- | --- |
| **Criterio** | El nombre. También puede corregirse aquí. La unidad entre corchetes se define en el paso 1. |
| **Sentido** | Una lista con dos opciones. **Beneficio**: más es mejor, como calidad o capacidad. **Costo**: menos es mejor, como precio o plazo. |
| **Peso asignado** | El peso de cada criterio. Solo aparece con el método Asignación directa. |

Revise siempre los sentidos después de importar un archivo. Si el archivo no tenía fila Sentido, todos los criterios llegan como Beneficio.

### Métodos de asignación de pesos

Elija el método en la fila de opciones superior. Debajo aparece su fórmula.

| Método | Quién define los pesos | Cuándo conviene | Requisitos |
| --- | --- | --- | --- |
| **Asignación directa** | Usted, criterio por criterio | Cuando el decisor tiene preferencias claras | Ningún peso negativo ni vacío, y al menos uno mayor que 0 |
| **Pesos iguales (1/n)** | El programa: todos valen lo mismo | Cuando no hay información para preferir un criterio | Ninguno |
| **Entropía (objetivo)** | El programa, según cuánto varían los valores de cada criterio entre alternativas | Cuando se quiere un peso basado solo en los datos | Al menos 2 alternativas, sin valores negativos ni columnas que sumen 0 |
| **CRITIC (objetivo)** | El programa, según el contraste de cada criterio y su conflicto con los demás | Cuando hay criterios parecidos entre sí que no se quiere contar dos veces | Al menos 2 alternativas y todos los sentidos definidos |

Cambiar de método puede cambiar el ganador. En el ejemplo de proveedores, la entropía le da el 55,6 % del peso al Plazo, y entonces ambos métodos eligen al Proveedor C.

Los pesos que usted escribió en Asignación directa quedan guardados al cambiar de método. Si vuelve a esa opción, reaparecen.

### Asignación directa en detalle

Puede escribir los pesos en cualquier escala: `0,35; 0,30; 0,15; 0,20` y `35; 30; 15; 20` dan el mismo resultado. El indicador **Suma de los pesos ingresados** muestra el total. Si no da 1, el programa divide cada peso por la suma y lo avisa en amarillo:

```math
w_j \leftarrow \frac{w_j}{\sum_k w_k}
```

Un criterio con peso 0 se acepta, pero no influye en el resultado y el programa lo avisa.

### Pesos utilizados en el cálculo

Debajo de la tabla se muestran los pesos finales, ya normalizados, que usan todos los pasos siguientes. Hay una tabla con el peso en tanto por uno y en porcentaje, y un gráfico de barras ordenado de mayor a menor.

Con Entropía o CRITIC aparece además un desplegable de **Pasos intermedios**:

- **Entropía:** la matriz de proporciones pᵢⱼ y, por criterio, la entropía Eⱼ, la diversificación dⱼ = 1 − Eⱼ y el peso wⱼ.
- **CRITIC:** la matriz normalizada rᵢⱼ, la matriz de correlación entre criterios y, por criterio, el desvío σⱼ, el conflicto Σ(1 − ρⱼₖ), la información Cⱼ y el peso wⱼ. Un criterio con el mismo valor en todas las alternativas recibe peso 0.

## 3 · Resultados paso a paso

Este paso muestra todo el cálculo de MOORA, tabla por tabla, para poder seguirlo o controlarlo a mano. Arriba se elige la normalización, y dos tarjetas anticipan qué alternativa gana en cada método.

### Método de normalización

La lista desplegable superior ofrece cuatro métodos. La elección se aplica también a los pasos 4, 5 y 6, y queda indicada en la barra lateral.

| Método | Fórmula | Requisito de los datos |
| --- | --- | --- |
| **Normalización vectorial** (predeterminada, la propia de MOORA) | x / √(Σ x²) | Ninguna columna con todos sus valores en 0 |
| **Normalización lineal** | x / máx x | El máximo de cada columna debe ser mayor que 0 |
| **Normalización lineal basada en la suma** | x / Σ x | La suma de cada columna debe ser mayor que 0 |
| **Normalización logarítmica** | ln x / ln(Π x) | Todos los valores mayores que 0, y el producto de cada columna mayor que 1 |

La misma fórmula se aplica a criterios de beneficio y de costo. El sentido se tiene en cuenta después, al agregar.

### Tarjetas de resumen

- **Mejor según Sistema de Razones:** la alternativa ganadora y su valor y.
- **Mejor según Punto de Referencia:** la alternativa ganadora y su valor d.

Si hay empate en el primer lugar, la tarjeta muestra los nombres separados por «/».

### Las tablas del cálculo, en orden

1. **Paso 1 · Matriz de decisión original:** los datos tal como se cargaron, más una tabla con el sentido y el peso final de cada criterio.
2. **Paso 2 · Normalización:** la fórmula elegida, una fila con el divisor de cada columna y la matriz normalizada x\*.
3. **Paso 3 · Matriz normalizada ponderada:** cada valor normalizado multiplicado por el peso de su criterio, v = w · x\*.
4. **Paso 4 · Aplicación de los métodos MOORA:** dos paneles, uno al lado del otro, descritos abajo.
5. **Resultados finales:** dos rankings, uno por método, ordenados del primero al último. El del Punto de Referencia indica además el criterio crítico de cada alternativa.

### Panel izquierdo: Sistema de Razones

Es el enfoque compensatorio. La tabla muestra el aporte de cada criterio con signo: positivo si es de beneficio y negativo si es de costo. Luego vienen las columnas Σ Beneficio, Σ Costo, yᵢ y Posición. **Mayor yᵢ es mejor.**

```math
y_i = \sum_{j \in Max} w_j\, x^*_{ij} - \sum_{j \in Min} w_j\, x^*_{ij}
```

El valor yᵢ puede ser negativo cuando los costos pesan más que los beneficios. Eso no es un error: solo importa el orden.

### Panel derecho: Punto de Referencia

Es el enfoque no compensatorio. Primero muestra el punto de referencia rⱼ, que es el mejor valor normalizado de cada criterio: el máximo si es de beneficio y el mínimo si es de costo. Luego muestra la tabla de desviaciones ponderadas, con dᵢ, Posición y Criterio crítico. **Menor dᵢ es mejor.**

```math
d_i = \max_j \left\{ w_j \left| r_j - x^*_{ij} \right| \right\}
```

En cada fila se resalta el desvío más grande. Ese valor es dᵢ, y su columna es el criterio crítico de la alternativa. El desplegable **Ver desviaciones sin ponderar** muestra las mismas desviaciones antes de multiplicarlas por los pesos.

### Cómo leer las tablas

- **Resaltado azul:** marca la posición 1 de cada ranking y el desvío máximo de cada fila.
- **Empates:** dos alternativas con el mismo puntaje comparten posición, y la siguiente salta un lugar (1, 2, 2, 4).
- **Columnas fijas:** en los paneles del paso 4, yᵢ, dᵢ y Posición quedan fijas a la izquierda al desplazar la tabla hacia los costados.
- **Decimales:** se controlan desde la barra lateral.

## 4 · Comparación y gráficos

Este paso responde si los dos métodos están de acuerdo y, si no lo están, por qué. Combina indicadores, una tabla comparativa, una interpretación escrita y cinco gráficos.

### Indicador de coincidencia y métricas

Arriba aparece un aviso verde, «Coinciden en la mejor alternativa», o uno amarillo, «Los métodos difieren en la mejor alternativa», con el ganador de cada método. Debajo hay tres métricas:

| Métrica | Qué indica |
| --- | --- |
| **Correlación de Spearman (ρ)** | Cuánto se parecen los dos rankings completos. Vale 1 si son idénticos y −1 si están invertidos. |
| **Posiciones coincidentes** | Cuántas alternativas ocupan el mismo lugar en ambos métodos, por ejemplo «4 de 4». |
| **Mayor cambio de posición** | El salto más grande de una alternativa entre un ranking y el otro. |

Debajo del valor de ρ aparece su interpretación:

| Valor de ρ | Interpretación |
| --- | --- |
| 0,9 o más | Concordancia muy alta |
| De 0,7 a 0,9 | Concordancia alta |
| De 0,4 a 0,7 | Concordancia moderada |
| De 0 a 0,4 | Concordancia baja |
| Menor que 0 | Los rankings tienden a ser opuestos |

Con una sola alternativa, o si un ranking es todo empates, ρ no está definido y se muestra «—».

### Tabla comparativa de rankings

Cada fila es una alternativa, ordenada según su posición en el Sistema de Razones. Muestra yᵢ y su posición, dᵢ y su posición, la **Diferencia (PR − SR)** y la columna **Coincide**, con ✔ o ✘. Una diferencia positiva significa que la alternativa queda peor ubicada en el Punto de Referencia.

### Interpretación

El recuadro **Interpretación** redacta las conclusiones automáticamente:

- **Si los métodos coinciden:** indica que la recomendación es robusta frente al enfoque usado.
- **Si difieren:** explica en qué criterios la ganadora del SR compensa sus debilidades, cuál es el peor desvío de cada ganadora y qué elegiría un decisor que acepta compensar y uno que no. También sugiere sobre qué criterio conviene hacer el análisis de sensibilidad.
- **Siempre:** lista los cambios de posición (por ejemplo, «Proveedor A (2° → 1°)»), informa los empates en el primer lugar y repite el valor de ρ.

### Gráficos

| Gráfico | Qué muestra | Cómo leerlo |
| --- | --- | --- |
| **Puntajes: Sistema de Razones** | Barras horizontales con el yᵢ de cada alternativa | La mejor queda arriba y en azul. Mayor es mejor. Cada barra indica su valor y su posición. |
| **Puntajes: Punto de Referencia** | Barras horizontales con el dᵢ de cada alternativa | La mejor queda arriba y en azul. Menor es mejor. |
| **Comparación de posiciones** | Una línea por alternativa, que une su posición en SR (izquierda) con su posición en PR (derecha) | Las líneas horizontales indican que la posición se mantiene. Las líneas que se cruzan indican discrepancias. |
| **Aportes al Sistema de Razones** (pestaña) | Barras apiladas con el aporte de cada criterio. Los beneficios van a la derecha y los costos a la izquierda. El rombo marca el yᵢ neto. | Muestra cómo las fortalezas de una alternativa compensan sus debilidades. |
| **Desvíos respecto del punto de referencia** (pestaña) | Mapa de calor con el desvío ponderado de cada alternativa en cada criterio | Cuanto más intenso el color, mayor el desvío. El número en negrita de cada fila es el máximo, es decir, el dᵢ. |

Los colores identifican siempre a la misma alternativa o criterio en todos los gráficos. La paleta es apta para daltonismo y tiene ocho colores: a partir de la novena serie, el resto se muestra en gris. Con más de ocho criterios, el gráfico de aportes agrupa los últimos en «Otros criterios».

### Interacción con los gráficos

- **Pasar el cursor** sobre una barra, punto o celda muestra su valor exacto.
- **Barra de herramientas:** aparece arriba a la derecha al pasar el cursor. La cámara descarga el gráfico como imagen PNG. También hay botones para ampliar una zona, desplazar, acercar, alejar, volver a la vista inicial (la casa) y ver en pantalla completa.
- **Leyenda:** un clic en un nombre de la leyenda oculta o muestra esa serie.

## 5 · Análisis de sensibilidad

Este paso mide qué tan firme es la recomendación: cambia el peso de un criterio y muestra en el momento cómo cambian los dos rankings. Requiere al menos 2 criterios.

La simulación no modifica el problema. La barra lateral y los pasos 2, 3 y 4 siguen usando los pesos originales.

### Controles

| Control | Para qué sirve |
| --- | --- |
| **Criterio a modificar** | Elige el criterio. La lista muestra el peso actual de cada uno. |
| **Peso simulado** (deslizador) | Mueve el peso entre 0 y 1, de a 0,01. |
| **Valor exacto** | Permite escribir el peso con tantos decimales como indique «Decimales a mostrar». |
| **− / +** | Restan o suman el valor elegido en Paso. |
| **Paso** | Define cuánto mueven los botones − y +: 0,1, 0,01, 0,001 y así hasta la cantidad de decimales configurada. |
| **↺ Restablecer** | Vuelve al peso original. Está desactivado mientras no haya cambios. |

### Cómo se reparten los demás pesos

Al cambiar el peso de un criterio k, los demás se ajustan para que la suma siga siendo 1, y conservan sus proporciones entre sí:

```math
w'_j = w_j \cdot \frac{1 - w'_k}{1 - w_k} \qquad (j \neq k)
```

Debajo de la tabla de pesos se muestra el factor exacto aplicado. Si el criterio tenía todo el peso (w = 1), el resto se reparte en partes iguales.

### Tarjetas y tablas

- **Tarjetas:** muestran el peso simulado con su variación, y el ganador de cada método. Si el ganador cambió, la tarjeta indica cuál era antes.
- **Pesos de los criterios:** compara el peso original con el simulado y muestra la variación con ▲ o ▼. La fila marcada es el criterio modificado.
- **Resultados recalculados:** compara yᵢ y dᵢ originales y simulados. La posición se lee «anterior → nueva»: ▲ en verde si la alternativa sube y ▼ en rojo si baja. En azul aparece la mejor de cada método.
- **Matriz normalizada ponderada simulada:** un desplegable con la matriz recalculada. Al pasar el cursor sobre una celda se ve su valor original.

Las celdas que cambian se iluminan en verde por un instante, para que se note qué se movió.

### Gráficos

Tres selectores definen qué se ve: **Gráfico** (Estabilidad o Heatmap), **Método** (Sistema de Razones o Punto de Referencia) y, solo para Estabilidad, **Escala**.

| Gráfico | Qué muestra | Cómo leerlo |
| --- | --- | --- |
| **Estabilidad (líneas)** | El puntaje de cada alternativa para cada peso del criterio, de 0 a 1 | La línea gris continua es el peso original y la verde a trazos, el simulado. Los círculos marcan cada **cruce**: el peso exacto en que otra alternativa pasa al 1.º lugar. |
| **Heatmap** | La posición de cada alternativa (filas) para pesos de 0 a 1, de a 0,05 (columnas) | Cuanto más intenso el azul, mejor la posición. El 1.º lugar aparece en azul pleno. |

La escala **Relativa al promedio** resta a cada puntaje el promedio de todas las alternativas. Así las líneas se separan mejor, sin cambiar el orden ni dónde se cruzan. La escala **Puntaje absoluto** muestra los valores reales.

### Cómo interpretar el resultado

- **Sin cruces entre 0 y 1:** el ganador se mantiene para cualquier peso de ese criterio. La recomendación es robusta frente a él.
- **Un cruce cerca del peso original:** un cambio chico de opinión sobre ese criterio cambia la recomendación. Conviene justificar bien ese peso.
- **Un cruce lejos del peso original:** hace falta un cambio grande para alterar la decisión.

Por ejemplo, en el problema de proveedores con pesos por entropía, Precio pesa 0,0953 y el Sistema de Razones elige al Proveedor C. El gráfico marca cruces en 0,639 y 0,662. Con un peso simulado de 0,70, el SR pasa a elegir al Proveedor B y el PR al Proveedor D. Como los cruces están lejos del peso original, la elección de C es estable frente al Precio.

El último criterio analizado se puede incluir en la exportación del paso 6.

## 6 · Exportación

Este paso descarga los resultados y guarda el problema para retomarlo después. Cada botón descarga un archivo directamente a la carpeta de descargas del navegador.

### Opciones previas

- **Incluir el último análisis de sensibilidad:** aparece si se visitó el paso 5. Agrega el análisis del último criterio elegido allí, con su peso recorrido de 0 a 1 en 201 puntos. No guarda el peso simulado puntual. Si no se visitó el paso 5, o si después se cargó otro problema, la opción no aparece.
- **Formato CSV:** elige entre «Coma (,) y punto decimal» y «Punto y coma (;) y coma decimal», que es la opción predeterminada y la que mejor abre Excel en español. Afecta a todos los archivos CSV de esta pantalla.

A la derecha se listan las hojas que tendrá el libro de Excel.

### Resultados completos

| Botón | Archivo | Contenido |
| --- | --- | --- |
| **Excel con todos los pasos** | `<nombre>_resultados.xlsx` | Un libro con una hoja por tabla del cálculo |
| **ZIP con un CSV por tabla** | `<nombre>_resultados_csv.zip` | Las mismas tablas del Excel, numeradas: `01_resumen.csv`, `02_problema.csv` y así sucesivamente |
| **CSV de resultados finales** | `<nombre>_ranking.csv` | Una sola tabla con yᵢ, dᵢ, las dos posiciones, la diferencia y si coinciden |

El `<nombre>` sale del nombre del problema, en minúsculas y con guiones bajos.

**Hojas del libro Excel, en orden:**

1. **Resumen:** problema, normalización, ganador de cada método, si coinciden, ρ de Spearman y posiciones coincidentes.
2. **Problema:** la matriz con sus filas Sentido y Peso.
3. **Criterios:** sentido, peso y divisor de normalización de cada criterio.
4. **Pesos entropia** o **Pesos CRITIC** y **Correlacion CRITIC:** solo si se usó uno de esos métodos.
5. **Normalizada** y **Ponderada:** las matrices de los pasos 2 y 3.
6. **Sistema de Razones**, **Punto de referencia**, **Desviaciones** y **Desviaciones ponderadas:** las tablas del paso 4.
7. **Resultados** y **Comparacion:** los rankings finales y la tabla comparativa.
8. **Sensibilidad**, **Sensibilidad detalle** y **Puntos de cambio:** solo si se incluyó el análisis de sensibilidad. La última hoja aparece solo si hubo cruces.

En el Excel, los encabezados tienen fondo azul oscuro, los números se muestran con 6 decimales y la primera fila y columna quedan fijas. Los valores se guardan con precisión completa, sin importar la opción «Decimales a mostrar».

### Matriz de datos del problema

Los botones **Problema (Excel)** y **Problema (CSV)** guardan el problema en el mismo formato que se importa en el paso 1, con filas Sentido y Peso. Sirven para retomar el trabajo más tarde, ya que el programa no guarda nada por sí solo.

Al volver a importar ese archivo, tenga en cuenta dos cosas:

- **Pesos:** se guardan los pesos finales del cálculo. Si se usaron Entropía o CRITIC, al reimportar llegan como Asignación directa, con esos mismos valores.
- **Unidades y normalización:** no se guardan. Las unidades vuelven a quedar vacías y la normalización vuelve a ser vectorial.

### Vista previa

El desplegable **Vista previa de las tablas exportadas** permite elegir cualquier hoja del libro y verla antes de descargar.

## Pequeños detalles

Estos detalles no son parte del método, pero hacen más cómodo el trabajo.

### Modo claro y modo oscuro

1. Haga clic en el menú **⋮** (tres puntos), arriba a la derecha.
2. En la primera fila del menú, elija una de las tres opciones:
   - **System:** sigue el tema del sistema operativo. Es la opción inicial.
   - **Light:** modo claro, con fondo gris muy claro y barra lateral blanca.
   - **Dark:** modo oscuro, con fondo azul casi negro.
3. Haga clic fuera del menú para cerrarlo.

El cambio es instantáneo y alcanza también a tablas y gráficos, sin recalcular nada. El navegador recuerda la elección, incluso después de recargar la página. Los colores de los gráficos son aptos para daltonismo y se leen bien en ambos modos.

### Otras opciones del menú ⋮

| Opción | Para qué sirve |
| --- | --- |
| **Print** | Abre la impresión del navegador, útil para guardar la pantalla actual como PDF. |
| **Record screen** | Graba un video de la pantalla, por ejemplo para una presentación. |
| **Rerun**, **Auto rerun** y **Clear cache** | Herramientas de Streamlit, la plataforma sobre la que funciona el programa. No hacen falta para el uso normal. |

El botón **Deploy**, junto al menú, también es de Streamlit: sirve para publicar aplicaciones en internet y no es necesario usarlo.

### Ocultar la barra lateral

Para ganar espacio, pase el cursor por la barra lateral y haga clic en **«** (arriba a la derecha de la barra). Para volver a mostrarla, haga clic en **»**, arriba a la izquierda de la pantalla.

### El programa no guarda el trabajo por sí solo

Recargar la página (F5), cerrar la pestaña o abrir el programa en otra pestaña vuelve al ejemplo inicial, y se pierden los datos cargados. Para conservar un problema, descárguelo con **Problema (Excel)** en el paso 6 y vuélvalo a importar en el paso 1.

### Navegación y ayudas

- **Botones al pie de cada paso:** «← paso anterior» y «paso siguiente →», este último en azul. Son equivalentes a la lista de la barra lateral.
- **Íconos de ayuda (?):** al pasar el cursor muestran una explicación breve. Aparecen, por ejemplo, junto a Método de normalización, Correlación de Spearman, Paso, Escala y Formato CSV.
- **Fórmulas:** cada método muestra su fórmula escrita en notación matemática, justo donde se aplica.

### Herramientas de las tablas

Al pasar el cursor sobre una tabla aparece una pequeña barra arriba a la derecha. Permite elegir qué columnas ver (el ojo), descargar esa tabla sola como CSV, buscar un valor (la lupa) y verla en pantalla completa.

### Colores de los avisos

| Color | Significado | ¿Se puede calcular? |
| --- | --- | --- |
| Verde | Todo está correcto | Sí |
| Azul | Información, por ejemplo cuándo se calcularán los pesos por entropía | Sí |
| Amarillo | Advertencia: conviene revisar, por ejemplo pesos que no suman 1 | Sí |
| Rojo | Error: falta un dato o hay un dato inválido | No, hasta corregirlo |

## Problemas frecuentes

Los mensajes en rojo impiden calcular hasta que se corrigen. Los de esta tabla son los más habituales, con el texto que muestra el programa.

### Mensajes de datos y pesos

| Mensaje | Causa | Solución |
| --- | --- | --- |
| «Hay N celda(s) vacía(s): …» | Faltan valores en la matriz | Complete las celdas indicadas en el paso 1 |
| «Hay N valor(es) no numérico(s): …» | Una celda tiene texto en lugar de un número | Corríjala en el paso 1 |
| «Hay alternativas sin nombre» o «Hay criterios sin nombre» | Un nombre quedó vacío | Escríbalo en la matriz o en Nombres de los criterios |
| «Hay nombres de alternativa repetidos» (o de criterio) | Dos filas o columnas se llaman igual | Cambie uno de los nombres |
| «La suma de cuadrados es 0 en …» | Un criterio tiene todos sus valores en 0 | Corrija los datos o elimine el criterio |
| «Falta indicar el sentido (Beneficio / Costo) de: …» | Un criterio no tiene sentido asignado | Elija Beneficio o Costo en el paso 2 |
| «Falta el peso de: …» | Un peso quedó vacío en Asignación directa | Escriba el peso en el paso 2 |
| «Los pesos no pueden ser negativos» | Hay un peso menor que 0 | Use pesos de 0 en adelante |
| «La suma de los pesos es 0» | Todos los pesos valen 0 | Asigne un peso positivo a al menos un criterio |
| «Método de entropía: …» | Hay valores negativos, una sola alternativa o columnas que suman 0 | Use otro método de pesos o revise los datos |
| «Método CRITIC: …» | Los criterios no varían o están perfectamente correlacionados | Use otro método de pesos |
| «La normalización logarítmica requiere valores mayores que 0» | Hay valores en 0 o negativos | Elija otra normalización en el paso 3 |

Las advertencias en amarillo no impiden calcular. Las más comunes avisan que los pesos no suman 1 y se normalizaron, que un criterio tiene el mismo valor en todas las alternativas y no discrimina, o que hay valores negativos.

### Mensajes al importar

| Mensaje | Causa | Solución |
| --- | --- | --- |
| «Error tokenizing data» | El CSV usa coma como separador y también como decimal | Use punto y coma como separador, o punto como decimal |
| «No se encontró el encabezado con los nombres de los criterios» | La primera fila no tiene nombres de criterios | Agregue una primera fila con los nombres |
| «No se encontraron filas de alternativas debajo del encabezado» | El archivo tiene una sola fila útil, que se tomó como encabezado | Agregue las filas de alternativas debajo del encabezado |
| «El archivo está vacío» | La hoja elegida no tiene datos | Elija otra hoja en Hoja |
| «No se pudo abrir el libro de Excel: …» | El archivo está dañado o no es un libro de Excel válido. Si menciona «xlrd», falta el paquete que lee los `.xls` | Ábralo en Excel y guárdelo de nuevo. Si menciona «xlrd», abra el programa con Iniciar MOORA.bat, que instala lo que falta |

### Síntomas sin mensaje

| Síntoma | Causa probable | Solución |
| --- | --- | --- |
| Un valor quedó 10 o 1000 veces más grande o más chico | Separador decimal o de miles equivocado | Revise la sección de decimales del paso 1 y corrija la celda |
| Faltan alternativas después de importar | Hay una fila en blanco en medio de los datos | Borre la fila vacía y vuelva a importar |
| Todo volvió al ejemplo inicial | Se recargó la página o se abrió otra pestaña | Reimporte el problema guardado con Problema (Excel) |
| No aparece la columna Peso en el paso 2 | El método elegido no es Asignación directa | Elija Asignación directa |
| No aparece la opción de sensibilidad en el paso 6 | No se visitó el paso 5 desde que se cargó el problema | Abra el paso 5, elija el criterio y vuelva al paso 6 |
| Todos los criterios aparecen como Beneficio | El archivo importado no tenía fila Sentido | Ajuste los sentidos en el paso 2 |

### Problemas al abrir el programa

- **«No se encontró Python en este equipo»:** instale Python 3.10 o superior desde python.org, marque la opción «Add python.exe to PATH» y vuelva a abrir Iniciar MOORA.bat.
- **La primera vez falla la instalación:** revise la conexión a internet, que solo se necesita para instalar los paquetes, y vuelva a intentar.
- **«El servidor no respondió en 90 s»:** abra manualmente en el navegador la dirección que muestra la consola, por ejemplo `http://localhost:8501`.

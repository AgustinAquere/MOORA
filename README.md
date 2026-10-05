# MOORA

Aplicación web local (Python + Streamlit) para resolver problemas de decisión multicriterio con
**MOORA – Sistema de Razones** y **MOORA con Punto de Referencia** (métrica min-max de Tchebycheff).
Trabajo práctico de *Decisiones en Escenarios Complejos*.

## Instalación y ejecución

Requiere Python 3.10 o superior.

### Con doble clic (Windows)

Abrir **`Iniciar MOORA.bat`**. En cada inicio:

1. crea el entorno `.venv` si no existe (o lo recrea si quedó dañado);
2. verifica que estén instalados todos los paquetes de `requirements.txt` con la versión pedida
   e instala los que falten o estén desactualizados (necesita internet solo en ese caso);
3. inicia el servidor en un puerto libre y abre el navegador cuando la aplicación está lista.

Para cerrar la aplicación, cerrar la ventana negra de la consola.

### Manualmente

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows  (Linux/macOS: source .venv/bin/activate)
pip install -r requirements.txt
streamlit run app.py
```

La aplicación se abre en el navegador en `http://localhost:8501`.

Pruebas unitarias:

```bash
python -m pytest
```

## Flujo de uso

| Paso | Contenido |
|---|---|
| 1 · Datos del problema | Ejemplos precargados, carga manual con dimensión m × n configurable (nombres de criterios y alternativas editables), importación desde Excel/CSV. |
| 2 · Criterios y pesos | Nombre y sentido (Beneficio/Costo) de cada criterio; pesos por asignación directa (con normalización automática), iguales (1/n) o entropía. |
| 3 · Resultados paso a paso | Matriz original, normas, matriz normalizada, matriz ponderada, Sistema de Razones, punto de referencia, desviaciones, desviaciones ponderadas y resultados finales. |
| 4 · Comparación y gráficos | Tabla comparativa, Spearman, indicador de coincidencia, notas interpretativas (compensatorio vs. no compensatorio) y gráficos Plotly. |
| 5 · Análisis de sensibilidad | Variación del peso de un criterio con renormalización proporcional; puntos de cambio de la mejor alternativa (refinados por bisección) e intervalos de estabilidad. |
| 6 · Exportación | Libro Excel con una hoja por paso, ZIP con un CSV por tabla, CSV de resultados y el problema en formato reimportable. |

## Estructura del proyecto

```
MOORA/
├─ Iniciar MOORA.bat       # Doble clic: crea .venv si hace falta y ejecuta launcher.py
├─ launcher.py             # Verifica/instala requirements.txt, inicia Streamlit y abre el navegador
├─ app.py                  # Punto de entrada de Streamlit (navegación y resumen lateral)
├─ engine/                 # Núcleo de cálculo: funciones puras, sin dependencias de la interfaz
│   ├─ moora.py            # Normalización, Sistema de Razones, Punto de Referencia, rankings, Spearman, comparación
│   ├─ weights.py          # Normalización de pesos, pesos iguales, entropía de Shannon
│   └─ sensitivity.py      # Redistribución de pesos, análisis de sensibilidad, puntos de cambio, estabilidad
├─ data_io/                # Entrada/salida (no se llama «io» para no ocultar el módulo io de Python)
│   ├─ validators.py       # Validación de matriz, nombres, sentidos y pesos con mensajes en español
│   ├─ serializers.py      # Lectura de Excel/CSV y exportación de problema y resultados
│   └─ examples.py         # Ejemplos precargados
├─ ui/                     # Interfaz Streamlit
│   ├─ state.py            # Estado de la sesión y cálculo del análisis completo
│   ├─ components.py       # Componentes reutilizables (tablas, alertas, navegación)
│   ├─ charts.py           # Gráficos Plotly
│   ├─ theme.py            # Paleta (modo claro/oscuro, apta para daltonismo)
│   └─ step_*.py           # Un módulo por paso del flujo
└─ tests/                  # Pruebas con pytest
```

## Formato de importación

Primera fila: nombres de los criterios; primera columna: alternativas. Las filas **Sentido**
(Beneficio/Costo o MAX/MIN) y **Peso** son opcionales y pueden ir antes o después de los datos.
Se aceptan coma o punto decimal y CSV separado por `,` o `;`. Ejemplo:

```
Alternativa;Precio ($/u);Calidad (1-10);Plazo (días);Capacidad (u/mes)
Proveedor A;120;8;10;5000
Proveedor B;100;7;15;4000
Proveedor C;135;9;7;6000
Proveedor D;110;6;12;4500
Sentido;Costo;Beneficio;Costo;Beneficio
Peso;0,35;0,30;0,15;0,20
```

El paso 1 permite descargar una plantilla con el problema actual en este formato.

## Validación del núcleo

Las pruebas contrastan el motor con:

* el ejemplo ilustrativo del informe del TP (Sección 4.6, Tablas 2 y 3): y = (0,0142; −0,0289; 0,0516; −0,0337),
  d = (0,0299; 0,0527; 0,0524; 0,0593);
* la actividad MOORA de la cátedra (inversión en robots, García Alcaraz et al. 2007) resuelta en Excel,
  incluyendo normas y matriz normalizada;
* casos calculados a mano (2×2, Spearman con y sin empates, entropía, punto de cambio de la sensibilidad
  en forma cerrada);
* casos límite: pesos que no suman 1, todos los criterios del mismo sentido, columna de ceros, valores
  negativos o vacíos, una sola alternativa o un solo criterio.

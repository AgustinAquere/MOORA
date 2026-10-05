"""Ejemplos precargados de distintos dominios."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Example:
    name: str
    description: str
    alternatives: list[str]
    criteria: list[str]
    values: list[list[float]]
    directions: list[str]
    weights: list[float]


EXAMPLES: dict[str, Example] = {
    ex.name: ex
    for ex in [
        Example(
            name="Selección de proveedores (ejemplo del TP)",
            description=(
                "Ejemplo ilustrativo de la Sección 4.6 del informe (Tablas 2 y 3). El Sistema de Razones "
                "prefiere al Proveedor C y el Punto de Referencia al Proveedor A: sirve para ver la diferencia "
                "entre un enfoque compensatorio y uno no compensatorio."
            ),
            alternatives=["Proveedor A", "Proveedor B", "Proveedor C", "Proveedor D"],
            criteria=["Precio ($/u)", "Calidad (1-10)", "Plazo (días)", "Capacidad (u/mes)"],
            values=[
                [120, 8, 10, 5000],
                [100, 7, 15, 4000],
                [135, 9, 7, 6000],
                [110, 6, 12, 4500],
            ],
            directions=["Costo", "Beneficio", "Costo", "Beneficio"],
            weights=[0.35, 0.30, 0.15, 0.20],
        ),
        Example(
            name="Ubicación de una planta",
            description=(
                "Elección de la localidad para una nueva planta industrial. Combina costos (terreno, "
                "mano de obra, distancia al mercado) con beneficios (infraestructura, incentivos, "
                "disponibilidad de personal calificado)."
            ),
            alternatives=["Córdoba", "Rosario", "Mendoza", "Tucumán", "Neuquén"],
            criteria=[
                "Costo del terreno (USD/m²)",
                "Costo laboral (USD/h)",
                "Distancia al mercado (km)",
                "Infraestructura (1-10)",
                "Incentivos fiscales (%)",
                "Personal calificado (1-10)",
            ],
            values=[
                [45, 9.5, 700, 8, 10, 8],
                [60, 10.2, 300, 9, 5, 9],
                [35, 8.8, 1050, 7, 15, 7],
                [25, 7.9, 1250, 5, 20, 6],
                [40, 11.5, 1150, 7, 25, 6],
            ],
            directions=["Costo", "Costo", "Costo", "Beneficio", "Beneficio", "Beneficio"],
            weights=[0.15, 0.20, 0.25, 0.15, 0.10, 0.15],
        ),
        Example(
            name="Selección de candidatos",
            description=(
                "Selección de un candidato para un puesto de analista. Se valoran la experiencia, la "
                "formación, la entrevista y la prueba técnica, y se penaliza la expectativa salarial. "
                "Aquí ambos métodos coinciden en la mejor alternativa."
            ),
            alternatives=["Candidato 1", "Candidato 2", "Candidato 3", "Candidato 4", "Candidato 5", "Candidato 6"],
            criteria=[
                "Experiencia (años)",
                "Formación (1-5)",
                "Entrevista (1-10)",
                "Prueba técnica (0-100)",
                "Expectativa salarial (miles $)",
            ],
            values=[
                [5, 4, 8, 82, 1400],
                [2, 5, 8, 85, 1200],
                [8, 3, 6, 70, 1900],
                [6, 4, 9, 90, 1450],
                [1, 3, 7, 92, 1050],
                [6, 5, 5, 74, 1700],
            ],
            directions=["Beneficio", "Beneficio", "Beneficio", "Beneficio", "Costo"],
            weights=[0.20, 0.15, 0.20, 0.25, 0.20],
        ),
        Example(
            name="Inversión en robots (actividad MOORA de la cátedra)",
            description=(
                "García Alcaraz et al. (2007), «Justificación multicriterio y multiatributos de inversiones "
                "en robots». Datos y pesos de la actividad MOORA; permite contrastar con la resolución en Excel."
            ),
            alternatives=["A1", "A2", "A3", "A4", "A5", "A6"],
            criteria=[
                "X1 Costo (US$)",
                "X2 Capacidad de carga (kg)",
                "X3 Velocidad (m/s)",
                "X4 Calidad de servicio",
                "X5 Facilidad de programación",
                "X6 Integración",
            ],
            values=[
                [8500, 90, 1.4, 5.2, 7.0, 6.2],
                [4750, 85, 1.3, 5.4, 6.2, 5.8],
                [7200, 98, 1.6, 7.0, 5.6, 6.8],
                [4800, 95, 1.3, 6.4, 4.8, 6.6],
                [6300, 105, 0.9, 4.2, 6.4, 5.0],
                [9400, 93, 1.9, 8.4, 5.0, 7.0],
            ],
            directions=["Costo", "Beneficio", "Beneficio", "Beneficio", "Beneficio", "Beneficio"],
            weights=[0.17051, 0.17512, 0.15668, 0.16590, 0.15668, 0.17512],
        ),
    ]
}

DEFAULT_EXAMPLE = next(iter(EXAMPLES))

"""Generación de ejercicios variables para las actividades existentes."""
from __future__ import annotations

import hashlib
import json
import random
from typing import Any

from app.infrastructure.database import get_recent_activity_fingerprints, record_activity_item


CONTENT_BANK = {
    "empresas": ["la cooperativa local", "el equipo de finanzas", "la empresa logística", "la junta directiva", "la oficina regional", "la asociación comercial", "el área de calidad", "la firma consultora", "el comité de ventas", "la red de proveedores", "la planta de producción", "la incubadora de negocios"],
    "educación": ["la biblioteca escolar", "el grupo de docentes", "la universidad pública", "el laboratorio de idiomas", "la coordinación académica", "la comunidad estudiantil", "la escuela rural", "el centro de formación", "la clase de ciencias", "la tutoría virtual", "la asociación de familias", "el equipo pedagógico"],
    "ciencia": ["el observatorio climático", "la investigadora principal", "el equipo de biología", "el centro de datos", "la expedición marina", "el laboratorio clínico", "la revista científica", "la estación espacial", "el instituto de física", "la red de investigadores", "el museo de ciencias", "la unidad de análisis"],
    "tecnología": ["la plataforma digital", "el equipo de desarrollo", "la comunidad de usuarios", "el laboratorio de innovación", "la empresa de software", "la red de ciberseguridad", "el centro de soporte", "el grupo de diseño", "la aplicación móvil", "el equipo de producto", "la infraestructura en nube", "la startup local"],
    "deporte": ["el cuerpo técnico", "la liga universitaria", "el club deportivo", "la selección juvenil", "el equipo de entrenamiento", "la federación regional", "el comité olímpico", "la escuela de atletismo", "la afición local", "el grupo de arbitraje", "la academia deportiva", "el centro de rendimiento"],
    "salud": ["el hospital comunitario", "el equipo médico", "la campaña de prevención", "el centro de salud", "la red de enfermería", "el laboratorio farmacéutico", "la unidad de bienestar", "la clínica universitaria", "el programa de vacunación", "la asociación de pacientes", "el servicio de urgencias", "la brigada sanitaria"],
    "marketing": ["la campaña de marca", "el equipo creativo", "la agencia digital", "la comunidad de clientes", "el estudio de mercado", "la estrategia comercial", "el canal de contenidos", "la identidad visual", "el lanzamiento regional", "la encuesta de consumidores", "el equipo de comunicación", "la campaña informativa"],
    "redes sociales": ["la comunidad en línea", "el equipo de contenidos", "la conversación digital", "la cuenta institucional", "la red de creadores", "el canal de noticias", "la audiencia internacional", "el foro ciudadano", "la plataforma educativa", "el grupo de moderación", "la campaña colaborativa", "el boletín digital"],
    "política": ["el concejo municipal", "la mesa de diálogo", "la comisión ciudadana", "el equipo de gobierno", "la audiencia pública", "la propuesta normativa", "el comité electoral", "la asamblea local", "la oficina de participación", "el acuerdo comunitario", "la sesión plenaria", "el observatorio cívico"],
    "medio ambiente": ["la reserva natural", "el grupo de reciclaje", "la campaña de reforestación", "el río urbano", "la comunidad costera", "el centro ambiental", "la red de huertas", "el parque regional", "la alianza climática", "el programa de energía limpia", "la brigada ecológica", "el vivero comunitario"],
}

VERBS = ["presentó", "analizó", "coordinó", "propuso", "documentó", "compartió", "revisó", "priorizó", "comunicó", "diseñó", "validó", "impulsó"]
OBJECTS = ["un plan de mejora", "los resultados del trimestre", "una propuesta colaborativa", "el informe de avance", "una estrategia de respuesta", "los datos recopilados", "un calendario de acciones", "la evaluación del proyecto", "un acuerdo de trabajo", "la iniciativa regional", "la evidencia disponible", "un nuevo protocolo"]
CONNECTORS = ["durante la reunión semanal", "para el próximo ciclo", "con la comunidad involucrada", "antes del cierre del mes", "a partir de los hallazgos", "con criterios transparentes", "en una sesión abierta", "para mejorar la coordinación", "tras revisar los datos", "con enfoque en el bienestar"]
ADJECTIVES = ["claro", "preciso", "colaborativo", "sostenible", "responsable", "oportuno", "inclusivo", "medible", "estratégico", "coherente"]
LINGUISTIC_PAIRS = [("prefijo", "Elemento que se agrega antes de la raíz"), ("sufijo", "Elemento que se agrega después de la raíz"), ("conector", "Palabra que relaciona ideas"), ("sujeto", "Quien realiza la acción"), ("predicado", "Información que se dice del sujeto"), ("adjetivo", "Palabra que califica un sustantivo"), ("verbo", "Palabra que expresa acción o estado"), ("sustantivo", "Palabra que nombra entidades o conceptos")]


def _difficulty(activity: dict[str, Any]) -> int:
    return min(4, max(1, int(activity["level_id"])))


def _difficulty_label(value: int) -> str:
    return ("Fácil", "Intermedio", "Difícil", "Experto")[value - 1]


def _context(rng: random.Random) -> dict[str, str]:
    category = rng.choice(list(CONTENT_BANK))
    subject = rng.choice(CONTENT_BANK[category])
    verb, obj, connector = rng.choice(VERBS), rng.choice(OBJECTS), rng.choice(CONNECTORS)
    return {"category": category, "subject": subject, "verb": verb, "object": obj, "connector": connector, "sentence": f"{subject.capitalize()} {verb} {obj} {connector}."}


def _order_payload(ctx: dict[str, str], rng: random.Random) -> dict[str, Any]:
    ordered = [
        ("a", f"{ctx['subject'].capitalize()} identificó una necesidad en {ctx['category']}"),
        ("b", f"Después, {ctx['verb']} {ctx['object']}"),
        ("c", f"Finalmente, compartió un mensaje {rng.choice(ADJECTIVES)} {ctx['connector']}"),
    ]
    shown = ordered[:]
    rng.shuffle(shown)
    return {"hint": "Busca el contexto, luego la acción y al final el cierre.", "items": [{"id": key, "text": text} for key, text in shown], "correct_order": [key for key, _ in ordered]}


def _payload_for(activity: dict[str, Any], ctx: dict[str, str], rng: random.Random) -> dict[str, Any]:
    kind = activity["activity_type"]
    if kind == "hotspot":
        words = [ctx["subject"], ctx["verb"], ctx["object"], rng.choice(CONNECTORS), "la", "y"]
        return {"hint": "Selecciona las piezas que contienen la acción y la información central.", "items": [{"text": word, "correct": index < 3} for index, word in enumerate(words)]}
    if kind in {"order", "drag_drop", "sentence_editor"}:
        return _order_payload(ctx, rng)
    if kind == "simulation":
        return _order_payload(ctx, rng) | {"blocks": _order_payload(ctx, rng)["items"]}
    if kind == "matching":
        pairs = rng.sample(LINGUISTIC_PAIRS, 3)
        return {"hint": "Relaciona cada concepto con la definición que explica su función.", "pairs": [{"left": left, "right": right} for left, right in pairs]}
    if kind == "classification":
        adjectives = rng.sample(ADJECTIVES, 2)
        return {"hint": "Decide si cada palabra nombra, expresa una acción o califica.", "categories": [{"id": "sustantivo", "label": "Sustantivo"}, {"id": "verbo", "label": "Verbo"}, {"id": "adjetivo", "label": "Adjetivo"}], "items": [{"id": "n", "text": ctx["object"], "category": "sustantivo"}, {"id": "v", "text": ctx["verb"], "category": "verbo"}, *[{"id": f"a{i}", "text": value, "category": "adjetivo"} for i, value in enumerate(adjectives)] ]}
    if kind == "inference":
        return {"hint": "Observa qué acción y propósito se sugieren, no solo las palabras literales.", "items": [{"id": "correct", "text": f"{ctx['subject'].capitalize()} busca avanzar con una acción coordinada.", "correct": True}, {"id": "one", "text": "No se requiere ningún seguimiento adicional.", "correct": False}, {"id": "two", "text": "El tema ya fue cancelado definitivamente.", "correct": False}]}
    if kind == "error_spot":
        return {"hint": "Revisa la concordancia entre el sujeto y el verbo.", "items": [{"id": "bad", "text": f"{ctx['subject'].capitalize()} presentaron el informe.", "correct": False}, {"id": "good", "text": f"{ctx['subject'].capitalize()} {ctx['verb']} {ctx['object']}.", "correct": True}, {"id": "bad2", "text": "Los propuesta fue revisada.", "correct": False}]}
    if kind == "decision":
        return {"hint": "Las palabras de certeza, posibilidad y duda señalan cada nivel.", "items": [{"id": "sure", "text": f"Sin duda, {ctx['sentence'].lower()}", "correct": "verde"}, {"id": "likely", "text": f"Probablemente, {ctx['sentence'].lower()}", "correct": "amarillo"}, {"id": "uncertain", "text": f"Quizá, {ctx['sentence'].lower()}", "correct": "rojo"}]}
    if kind == "concept_choice":
        payload = activity.get("payload") or {}
        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except Exception:
                payload = {}
        if isinstance(payload, dict) and payload.get("items"):
            return payload
        return {"hint": "Selecciona la opción que explique mejor el concepto.", "items": [{"id": "a", "text": "La idea general del concepto es correcta y la forma concreta de pronunciarlo puede cambiar según el contexto.", "correct": True}, {"id": "b", "text": "El concepto se aplica solo a la escritura, no a la pronunciación.", "correct": False}, {"id": "c", "text": "Es la misma realidad en todas las palabras, sin cambios.", "correct": False}]}
    return activity["payload"]


def _authored_payload(activity: dict[str, Any]) -> dict[str, Any]:
    payload = activity.get("payload") or {}
    if isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except json.JSONDecodeError:
            payload = {}
    embedded_answer = payload.get("answer") if isinstance(payload, dict) else None
    if isinstance(payload, dict) and payload.get("items"):
        return payload

    answer = activity.get("answer") or embedded_answer
    kind = activity.get("activity_type")
    if kind == "classification" and isinstance(answer, dict):
        categories = [{"id": category, "label": category.replace("_", " ").title()} for category in answer]
        items = [
            {"id": f"item-{index}", "text": item, "category": category}
            for category, values in answer.items()
            for index, item in enumerate(values)
        ]
        return {"hint": "Clasifica cada elemento según el criterio indicado en la instrucción.", "categories": categories, "items": items}
    if kind == "order" and isinstance(answer, list):
        items = [{"id": f"sentence-{index}", "text": sentence} for index, sentence in enumerate(answer)]
        return {"hint": "Ordena los fragmentos para reconstruir la secuencia indicada.", "items": items, "correct_order": [item["id"] for item in items]}
    return {}


def generate_activity_payload(user_id: int, activity: dict[str, Any]) -> dict[str, Any]:
    difficulty = _difficulty(activity)
    payload = _authored_payload(activity)
    return {**payload, "meta": {"difficulty": difficulty, "difficulty_label": _difficulty_label(difficulty), "dynamic": False}}

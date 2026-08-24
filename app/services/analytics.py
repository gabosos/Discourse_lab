from __future__ import annotations

from typing import Dict, List, Any


class AnalyticsService:
    """Servicio de métricas, progreso y experiencia del estudiante."""

    def get_student(self) -> Dict[str, Any]:
        return {
            "name": "Estudiante",
            "initials": "E",
            "level": 1,
            "xp": 0,
            "xp_to_next": 200,
            "streak": 0,
            "coins": 0,
        }

    def get_dashboard_metrics(self) -> Dict[str, int]:
        return {
            "xp": 1840,
            "streak": 12,
            "completion": 72,
            "levels": 6,
            "daily_minutes": 18,
            "daily_goal": 25,
            "missions_done": 8,
            "achievements": 14,
        }

    def get_level_summary(self) -> List[Dict[str, object]]:
        return [
            {"id": 1, "title": "Fonética y Fonología", "progress": 82, "status": "completed"},
            {"id": 2, "title": "Morfología", "progress": 65, "status": "active"},
            {"id": 3, "title": "Sintaxis", "progress": 72, "status": "active"},
            {"id": 4, "title": "Semántica", "progress": 58, "status": "active"},
            {"id": 5, "title": "Pragmática", "progress": 44, "status": "locked"},
            {"id": 6, "title": "Discurso Organizacional", "progress": 31, "status": "locked"},
        ]

    def get_continue_learning(self) -> Dict[str, Any]:
        return {
            "title": "Constructor de Mensajes",
            "level": "Sintaxis",
            "level_id": 3,
            "progress": 48,
            "xp_reward": 120,
        }

    def get_daily_goal(self) -> Dict[str, Any]:
        return {
            "current": 18,
            "target": 25,
            "unit": "min",
            "percent": 72,
        }

    def get_missions(self) -> List[Dict[str, Any]]:
        return [
            {"title": "Detective Fonético", "level": "Fonética", "status": "done", "xp": 150},
            {"title": "Arrastra la Prosodia", "level": "Fonética", "status": "done", "xp": 100},
            {"title": "Construye Oraciones", "level": "Sintaxis", "status": "active", "xp": 120},
            {"title": "Clasificador Morfológico", "level": "Morfología", "status": "active", "xp": 130},
            {"title": "Análisis de Textos Organizacionales", "level": "Discurso Organizacional", "status": "locked", "xp": 200},
            {"title": "Revisión de Pragmática", "level": "Pragmática", "status": "locked", "xp": 180},
        ]

    def get_notifications(self) -> List[Dict[str, Any]]:
        return [
            {"id": 1, "type": "achievement", "icon": "achievement", "title": "Nuevo logro desbloqueado", "body": "Completaste 10 actividades seguidas", "time": "Hace 2h", "unread": True},
            {"id": 2, "type": "streak", "icon": "streak", "title": "Racha de 12 días", "body": "Sigue así. Tu racha está en marcha", "time": "Hace 5h", "unread": True},
            {"id": 3, "type": "mission", "icon": "mission", "title": "Nueva misión disponible", "body": "Clasificador Morfológico te espera", "time": "Ayer", "unread": False},
            {"id": 4, "type": "xp", "icon": "xp", "title": "+120 XP ganados", "body": "Detective Fonético completado", "time": "Ayer", "unread": False},
        ]

    def get_achievements(self) -> List[Dict[str, Any]]:
        return [
            {"icon": "🎯", "name": "Primer paso", "desc": "Completa tu primera actividad", "unlocked": True},
            {"icon": "🔥", "name": "En llamas", "desc": "Racha de 7 días", "unlocked": True},
            {"icon": "📚", "name": "Lector voraz", "desc": "5 niveles iniciados", "unlocked": True},
            {"icon": "🧠", "name": "Analista", "desc": "Domina sintaxis al 80%", "unlocked": True},
            {"icon": "💎", "name": "Perfeccionista", "desc": "100% en una actividad", "unlocked": False},
            {"icon": "🌟", "name": "Estrella", "desc": "Top 10 del ranking", "unlocked": False},
        ]

    def get_leaderboard(self) -> List[Dict[str, Any]]:
        return [
            {"rank": 1, "name": "Andrés M.", "initials": "AM", "xp": 2340, "you": False},
            {"rank": 2, "name": "Laura P.", "initials": "LP", "xp": 2100, "you": False},
            {"rank": 3, "name": "Tu Progreso", "initials": "TP", "xp": 1840, "you": True},
            {"rank": 4, "name": "Diego R.", "initials": "DR", "xp": 1720, "you": False},
            {"rank": 5, "name": "Sofía L.", "initials": "SL", "xp": 1580, "you": False},
        ]

    def get_streak_calendar(self) -> List[int]:
        return [0, 1, 2, 3, 4, 2, 1, 3, 4, 3, 2, 4, 4, 3, 1, 0, 2, 3, 4, 4, 3, 2, 4, 3, 4, 4, 3, 2]

    def get_weekly_activity(self) -> List[Dict[str, Any]]:
        return [
            {"day": "Lun", "minutes": 22},
            {"day": "Mar", "minutes": 35},
            {"day": "Mié", "minutes": 18},
            {"day": "Jue", "minutes": 42},
            {"day": "Vie", "minutes": 28},
            {"day": "Sáb", "minutes": 15},
            {"day": "Dom", "minutes": 18},
        ]

    def get_recommendations(self) -> List[Dict[str, Any]]:
        return [
            {"title": "Refuerza Pragmática", "reason": "Tu progreso está por debajo del promedio del grupo", "action": "Lee entre Líneas"},
            {"title": "Completa tu meta diaria", "reason": "Te faltan 7 minutos para alcanzar tu objetivo", "action": "Continuar estudio"},
        ]

    def get_learning_history(self) -> List[Dict[str, Any]]:
        return [
            {"date": "Hoy", "activity": "Constructor de Mensajes", "xp": 45, "score": 88},
            {"date": "Ayer", "activity": "Detective Fonético", "xp": 120, "score": 95},
            {"date": "Ayer", "activity": "Mapa Conceptual", "xp": 80, "score": 82},
            {"date": "12 Jul", "activity": "Arrastra la Prosodia", "xp": 100, "score": 91},
        ]

    def get_search_index(self) -> List[Dict[str, str]]:
        return [
            {"type": "nivel", "title": "Fonética y Fonología", "url": "/levels/1"},
            {"type": "nivel", "title": "Morfología", "url": "/levels/2"},
            {"type": "nivel", "title": "Sintaxis", "url": "/levels/3"},
            {"type": "nivel", "title": "Semántica", "url": "/levels/4"},
            {"type": "nivel", "title": "Pragmática", "url": "/levels/5"},
            {"type": "nivel", "title": "Discurso Organizacional", "url": "/levels/6"},
            {"type": "actividad", "title": "Detective Fonético", "url": "/levels/1"},
            {"type": "actividad", "title": "Constructor de Mensajes", "url": "/levels/3"},
            {"type": "página", "title": "Panel del estudiante", "url": "/dashboard"},
            {"type": "página", "title": "Proyecto final", "url": "/final-project"},
            {"type": "página", "title": "Diploma digital", "url": "/certificate"},
        ]

    def get_level_detail(self, level_id: int) -> Dict[str, Any]:
        summary = {item["id"]: item for item in self.get_level_summary()}
        info = summary.get(level_id, {"progress": 0, "status": "locked"})
        from app.infrastructure.database import get_activities_by_level

        activities = get_activities_by_level(level_id)
        return {
            "progress": info["progress"],
            "status": info["status"],
            "activities_detail": [
                {"name": act.get("name"), "duration": "12 min", "xp": act.get("xp_reward", 80), "slug": act.get("slug"), "unlocked": True, "type": act.get("activity_type", "written")}
                for act in activities
            ],
        }

    def _activities_for_level(self, level_id: int) -> List[str]:
        from app.infrastructure.database import get_activities_by_level
        activities = get_activities_by_level(level_id)
        return [act.get("name") for act in activities]

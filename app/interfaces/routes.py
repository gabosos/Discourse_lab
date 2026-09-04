from flask import Blueprint, g, render_template, redirect, url_for, flash, request, session, jsonify, Response
from functools import wraps
import csv
import io
from werkzeug.security import generate_password_hash, check_password_hash
from app.core.config import LEVELS
from app.infrastructure.database import (
    create_user,
    get_user_by_username,
    get_user_by_id,
    get_user_progress,
    get_activities_by_level,
    get_activity_by_slug,
    get_activity_by_id,
    get_activity_progress,
    get_level_overview,
    is_activity_unlocked,
    save_activity_progress,
    create_student,
    get_user_by_email,
    update_last_login,
    record_audit_event,
    get_teacher_dashboard,
    get_student_teacher_view,
    add_teacher_note,
    get_student_live_data,
    get_route_mode,
    set_route_mode,
)
from app.services.analytics import AnalyticsService
from app.services.activity_generator import generate_activity_payload
from app.logging.logger import get_logger
import os
import json

main_bp = Blueprint("main", __name__)
analytics = AnalyticsService()


def register_routes(app) -> None:
    app.register_blueprint(main_bp)


@main_bp.route("/api/client_log", methods=["POST"])
def client_log():
    payload = request.get_json(silent=True) or {}
    level = (payload.get("level") or "INFO").upper()
    message = payload.get("message") or "client_event"
    meta = payload.get("meta") or {}
    logger = get_logger("frontend.client")
    log_method = getattr(logger, level.lower(), logger.info)
    try:
        log_method(message, extra={"context": {"category": "FRONTEND", "metadata": meta}})
    except Exception:
        logger.exception("Failed to log client event")
    return jsonify({"ok": True}), 200


@main_bp.route('/cuadernillo', methods=['GET'])
def cuadernillo_index():
    # Return list of blocks available (reads metadata from data/cuadernillo.json when present)
    data_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'cuadernillo.json')
    data_path = os.path.normpath(data_path)
    blocks = []
    if os.path.exists(data_path):
        try:
            with open(data_path, 'r', encoding='utf-8') as fh:
                data = json.load(fh)
            for b in data.get('blocks', []):
                blocks.append({
                    'level_id': b.get('level_id'),
                    'name': b.get('name'),
                    'description': b.get('description'),
                    'source': b.get('source'),
                    'exercise_count': len(b.get('exercises', []))
                })
        except Exception:
            pass
    return jsonify({'blocks': blocks})


@main_bp.route('/cuadernillo/<int:level_id>', methods=['GET'])
def cuadernillo_block(level_id: int):
    # Return exercises for a given block (level)
    activities = get_activities_by_level(level_id)
    exercises = []
    for a in activities:
        payload = a.get('payload')
        try:
            payload = json.loads(payload) if isinstance(payload, str) else payload
        except Exception:
            payload = {}
        exercises.append({
            'id': a.get('id'),
            'number': a.get('order_index'),
            'slug': a.get('slug'),
            'title': a.get('name'),
            'enunciado': payload.get('enunciado') or a.get('instructions'),
            'type': a.get('activity_type'),
            'status': a.get('status')
        })
    return jsonify({'level_id': level_id, 'exercises': exercises})


@main_bp.route('/cuadernillo/view', methods=['GET'])
def cuadernillo_view():
    data_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'cuadernillo.json')
    data_path = os.path.normpath(data_path)
    blocks = []
    total_exercises = 0
    if os.path.exists(data_path):
        with open(data_path, 'r', encoding='utf-8') as fh:
            blocks = json.load(fh).get('blocks', [])
        total_exercises = sum(len(b.get('exercises', [])) for b in blocks)
    return render_template('cuadernillo.html', **_context(active_page='cuadernillo', blocks=blocks, total_exercises=total_exercises))


@main_bp.route('/cuadernillo/view/<int:level_id>', methods=['GET'])
def cuadernillo_view_level(level_id: int):
    data_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'cuadernillo.json')
    data_path = os.path.normpath(data_path)
    block = None
    if os.path.exists(data_path):
        with open(data_path, 'r', encoding='utf-8') as fh:
            blocks = json.load(fh).get('blocks', [])
        block = next((b for b in blocks if int(b.get('level_id', 0)) == level_id), None)
    if not block:
        flash('Bloque no encontrado.', 'danger')
        return redirect(url_for('main.cuadernillo_view'))
    exercises = block.get('exercises', [])
    return render_template('cuadernillo_level.html', **_context(active_page='cuadernillo', block=block, exercises=exercises, level_id=level_id))


@main_bp.before_app_request
def preserve_teacher_context():
    """A teacher never enters the student experience through a manual URL."""
    current = session.get("student") or {}
    if current.get("role") != "teacher":
        return None
    allowed = {"main.teacher_dashboard", "main.teacher_student_detail", "main.teacher_student_note", "main.teacher_export", "main.logout"}
    if request.endpoint and request.endpoint not in allowed and not request.endpoint.startswith("static"):
        return redirect(url_for("main.teacher_dashboard"))
    return None


def _default_student():
    return {
        "name": "Estudiante",
        "initials": "E",
        "level": 1,
        "xp": 0,
        "xp_in_level": 0,
        "xp_to_next": 200,
        "xp_remaining": 200,
        "streak": 0,
        "coins": 0,
    }


def _set_session_user(user: dict) -> None:
    xp = user.get("xp", 0)
    level = (xp // 200) + 1
    session["student"] = {
        "id": user["id"], "name": user["username"], "initials": user["username"][0].upper() if user["username"] else "U",
        "level": level, "xp": xp, "xp_in_level": xp % 200, "xp_to_next": 200, "xp_remaining": 200 - (xp % 200), "streak": 0,
        "coins": user.get("coins", 0), "role": user.get("role", "student"),
        "route_mode": bool(user.get("route_mode", 1)),
    }


def teacher_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        user = _load_student()
        if not user or user.get("role") != "teacher":
            return render_template("403.html", **_context(active_page=""), error_message="Acceso denegado."), 403
        return view(*args, **kwargs)
    return wrapped


def _simple_pdf(lines: list) -> bytes:
    """Small dependency-free PDF export for the institutional summary."""
    safe_lines = [str(line).encode("latin-1", "replace").decode("latin-1").replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)") for line in lines]
    text = "BT /F1 10 Tf 50 790 Td " + " ".join(f"({line}) Tj 0 -15 Td" for line in safe_lines) + " ET"
    objects = ["<< /Type /Catalog /Pages 2 0 R >>", "<< /Type /Pages /Kids [3 0 R] /Count 1 >>", "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>", f"<< /Length {len(text.encode('latin-1'))} >>\nstream\n{text}\nendstream", "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"]
    result = "%PDF-1.4\n"
    offsets = [0]
    for index, obj in enumerate(objects, 1):
        offsets.append(len(result.encode("latin-1")))
        result += f"{index} 0 obj\n{obj}\nendobj\n"
    xref = len(result.encode("latin-1"))
    result += f"xref\n0 {len(objects)+1}\n0000000000 65535 f \n" + "".join(f"{offset:010d} 00000 n \n" for offset in offsets[1:])
    result += f"trailer << /Size {len(objects)+1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF"
    return result.encode("latin-1")


def _load_student():
    if hasattr(g, "loaded_student"):
        return g.loaded_student
    session_student = session.get("student")
    if not session_student:
        g.loaded_student = None
        return None
    if session_student.get("id"):
        user = get_user_by_id(session_student["id"])
    else:
        user = get_user_by_username(session_student.get("name", ""))
    if user:
        xp = user.get("xp", 0)
        session["student"] = {
            "id": user["id"],
            "name": user["username"],
            "initials": user["username"][0].upper() if user["username"] else "U",
            "level": (xp // 200) + 1, "xp": xp, "xp_in_level": xp % 200, "xp_to_next": 200, "xp_remaining": 200 - (xp % 200),
            "streak": session_student.get("streak", 0),
            "coins": user.get("coins", 0),
            "role": user.get("role", "student"),
            "route_mode": get_route_mode(user["id"]),
        }
        g.loaded_student = user
        return user
    g.loaded_student = None
    return None


def _dashboard_metrics(student: dict) -> dict:
    if student.get("id"):
        return get_student_live_data(student["id"])["metrics"]
    return {"xp": 0, "streak": 0, "completion": 0, "levels": len(LEVELS), "daily_minutes": 0, "daily_goal": 25, "missions_done": 0, "achievements": 0}


def _context(**extra):
    # Ensure session reflects the persisted user record when possible
    loaded_student = _load_student()
    student = session.get("student", _default_student())
    if "xp_in_level" not in student or "xp_remaining" not in student:
        xp = student.get("xp", 0)
        student = {**student, "level": (xp // 200) + 1, "xp_in_level": xp % 200, "xp_to_next": 200, "xp_remaining": 200 - (xp % 200)}
        session["student"] = student

    ctx = {
        "student": student,
        "metrics": _dashboard_metrics(student),
        "notifications": analytics.get_notifications(),
        "search_index": analytics.get_search_index(),
    }
    ctx.update(extra)
    return ctx


def _get_level(level_id: int):
    level = next((item for item in LEVELS if item["id"] == level_id), None)
    if not level:
        return None
    db_activities = get_activities_by_level(level_id)
    return {**level, "activities": db_activities, "activity_count": len(db_activities)}


@main_bp.route("/", methods=["GET", "POST"])
def home():
    if request.method == 'POST':
        username = request.form.get("username", "")[:32].strip()
        if username:
            user = get_user_by_username(username)
            if not user:
                user = create_user(username)
            if not user:
                flash("No fue posible crear el usuario. Intenta de nuevo.", "danger")
                return redirect(url_for("main.home"))
            student_name = user.get("username", username)
            session["student"] = {
                "id": user.get("id"),
                "name": student_name,
                "initials": student_name[0].upper() if student_name else "U",
                "level": 1,
                "xp": user.get("xp", 0),
                "xp_in_level": user.get("xp", 0) % 200,
                "xp_to_next": 200,
                "xp_remaining": 200 - (user.get("xp", 0) % 200),
                "streak": 0,
                "coins": user.get("coins", 0),
                "role": user.get("role", "student"),
            }
            flash("Usuario creado con éxito. Bienvenido a la plataforma.", "success")
            return redirect(url_for("main.home"))
        flash("Por favor ingresa un nombre de usuario válido.", "danger")
        return redirect(url_for("main.home"))

    user = session.get("student", _default_student())
    route_mode = get_route_mode(user["id"]) if user.get("id") else True
    live = get_student_live_data(user["id"]) if user.get("id") else None
    level_summary = {item["id"]: item for item in (live["levels"] if live else [])}
    levels_enriched = []
    for level in LEVELS:
        db_activities = get_activities_by_level(level["id"])
        default_status = "active" if not route_mode or level["id"] == 1 else "locked"
        info = level_summary.get(level["id"], {"progress": 0, "status": default_status})
        if not route_mode and info.get("status") == "locked":
            info = {**info, "status": "active"}
        levels_enriched.append({**level, "activities": db_activities, "activity_count": len(db_activities), **info})
    return render_template(
        "home.html",
        **_context(
            active_page="home",
            levels=levels_enriched,
            continue_learning=live["continue_learning"] if live else {"title": "Detective Fonético", "level": "Fonética", "level_id": 1, "progress": 0, "xp_reward": 120},
            daily_goal=live["daily_goal"] if live else {"current": 0, "target": 25, "unit": "min", "percent": 0},
            user_registered=bool(session.get("student")),
            route_mode=route_mode,
        ),
    )


@main_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()[:32]
        email = request.form.get("email", "").strip().lower()[:120]
        password = request.form.get("password", "")
        if len(username) < 3 or "@" not in email or len(password) < 8:
            flash("Ingresa nombre, correo válido y una contraseña de al menos 8 caracteres.", "danger")
            return redirect(url_for("main.register"))
        if get_user_by_email(email):
            flash("Ese correo ya está registrado.", "danger")
            return redirect(url_for("main.login"))
        user = create_student(username, email, generate_password_hash(password, method="pbkdf2:sha256:600000"))
        _set_session_user(user)
        record_audit_event(user["id"], "register", "public student registration")
        return redirect(url_for("main.home"))
    return render_template("auth.html", **_context(active_page=""), mode="register")


@main_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = get_user_by_email(email)
        if not user or not user.get("password_hash") or not check_password_hash(user["password_hash"], password):
            flash("Correo o contraseña incorrectos.", "danger")
            return redirect(url_for("main.login"))
        if user.get("status", "active") != "active":
            flash("Esta cuenta no está activa.", "danger")
            return redirect(url_for("main.login"))
        _set_session_user(user)
        update_last_login(user["id"])
        record_audit_event(user["id"], "login", "successful login")
        return redirect(url_for("main.teacher_dashboard") if user.get("role") == "teacher" else url_for("main.home"))
    return render_template("auth.html", **_context(active_page=""), mode="login")


@main_bp.route("/logout")
def logout():
    user = _load_student()
    if user:
        record_audit_event(user["id"], "logout", "session closed")
    session.clear()
    return redirect(url_for("main.login"))


@main_bp.route("/levels/<int:level_id>")
def level_detail(level_id: int):
    level = next((item for item in LEVELS if item["id"] == level_id), None)
    if not level:
        flash("Nivel no encontrado", "danger")
        return redirect(url_for("main.home"))
    user = _load_student()
    if user:
        route_mode = get_route_mode(user["id"])
        detail = get_level_overview(user["id"], level_id, route_mode)
        level = {**level, "activity_count": len(detail["activities_detail"])}
    else:
        level = _get_level(level_id)
        activities = level["activities"]
        detail = {
            "progress": 0,
            "status": "active" if level_id == 1 else "locked",
            "activities_detail": [
                {
                    "id": item["id"],
                    "slug": item["slug"],
                    "name": item["name"],
                    "xp": item["xp_reward"],
                    "progress": 0,
                    "status": "pending",
                    "unlocked": item["order_index"] == 1,
                    "type": item["activity_type"],
                }
                for item in activities
            ],
        }
    detail["has_unlocked_activity"] = any(
        item.get("unlocked") and item.get("slug")
        for item in detail.get("activities_detail", [])
    )
    return render_template(
        "level.html",
        **_context(active_page="levels", level=level, detail=detail, route_mode=get_route_mode(user["id"]) if user else True),
    )


@main_bp.route("/api/route-mode", methods=["POST"])
def update_route_mode():
    user = _load_student()
    if not user:
        return jsonify({"success": False, "message": "Sesión no iniciada."}), 401
    payload = request.get_json(silent=True) or {}
    if not isinstance(payload.get("enabled"), bool):
        return jsonify({"success": False, "message": "El estado del modo no es válido."}), 400
    try:
        enabled = set_route_mode(user["id"], payload["enabled"])
    except Exception:
        get_logger("app.route_mode").exception("Unable to persist route mode")
        return jsonify({"success": False, "message": "No se pudo guardar el modo en el servidor."}), 500
    session["student"]["route_mode"] = enabled
    try:
        record_audit_event(user["id"], "route_mode_changed", "enabled" if enabled else "disabled")
    except Exception:
        get_logger("app.route_mode").exception("Unable to record route mode audit event")
    return jsonify({"success": True, "route_mode": enabled})


@main_bp.route("/activities/<slug>")
def activity(slug: str):
    user = _load_student()
    if not user:
        flash("Por favor ingresa para acceder a las actividades.", "info")
        return redirect(url_for("main.home"))
    activity = get_activity_by_slug(slug)
    if not activity:
        fallback = None
        for level_id in range(1, 7):
            items = get_activities_by_level(level_id)
            for item in items:
                if is_activity_unlocked(user["id"], item["id"]):
                    fallback = item
                    break
            if fallback:
                break
        if fallback:
            flash("La actividad solicitada ya no está disponible. Se abrió la siguiente actividad válida.", "warning")
            return redirect(url_for("main.activity", slug=fallback["slug"]))
        flash("Actividad no encontrada.", "danger")
        return redirect(url_for("main.home"))
    route_mode = get_route_mode(user["id"])
    if not is_activity_unlocked(user["id"], activity["id"], route_mode):
        flash("Debes completar actividades previas para desbloquear esta actividad.", "info")
        return redirect(url_for("main.level_detail", level_id=activity["level_id"]))
    activity["payload"] = generate_activity_payload(user["id"], activity)
    activity["interaction_prompt"] = activity["payload"].get("interaction_prompt")
    progress = get_activity_progress(user["id"], activity["id"])
    level_overview = get_level_overview(user["id"], activity["level_id"], route_mode)
    level_activities = get_activities_by_level(activity["level_id"])
    current_index = next((index for index, item in enumerate(level_activities) if item["id"] == activity["id"]), -1)
    next_activity = None
    if activity["level_id"] in (1, 2) and current_index >= 0 and current_index + 1 < len(level_activities):
        candidate = level_activities[current_index + 1]
        next_activity = {"slug": candidate["slug"], "name": candidate["name"], "xp": candidate["xp_reward"]}
    return render_template(
        "activity.html",
        **_context(
            active_page="levels",
            activity=activity,
            progress=progress,
            level_overview=level_overview,
            next_activity=next_activity,
        ),
    )


@main_bp.route("/activities/<slug>/submit", methods=["POST"])
def activity_submit(slug: str):
    user = _load_student()
    if not user:
        return jsonify({"success": False, "message": "Sesión no iniciada."}), 401
    activity = get_activity_by_slug(slug)
    if not activity:
        return jsonify({"success": False, "message": "Actividad no encontrada."}), 404
    if not is_activity_unlocked(user["id"], activity["id"], get_route_mode(user["id"])):
        return jsonify({"success": False, "message": "Debes completar las actividades previas."}), 403
    payload = request.get_json(silent=True) or {}
    if not isinstance(payload, dict) or not isinstance(payload.get("completed", False), bool):
        return jsonify({"success": False, "message": "La respuesta enviada no es válida."}), 400

    def parse_score_value(name: str, minimum: int, maximum: int) -> int:
        value = payload.get(name, 0)
        # bool is technically an int in Python, but never a valid score.
        if isinstance(value, bool):
            raise ValueError
        parsed = int(value)
        if not minimum <= parsed <= maximum:
            raise ValueError
        return parsed

    try:
        completed = payload["completed"]
        correct = parse_score_value("correct", 0, 10_000)
        incorrect = parse_score_value("incorrect", 0, 10_000)
        score = parse_score_value("score", 0, 100)
        hints_used = parse_score_value("hints_used", 0, 1_000)
    except (TypeError, ValueError):
        return jsonify({"success": False, "message": "Puntaje o conteos inválidos."}), 400
    feedback = str(payload.get("feedback", ""))[:2_000]
    previous_progress = get_activity_progress(user["id"], activity["id"])
    previous_level = (user.get("xp", 0) // 200) + 1
    xp = activity.get("xp_reward", 0) if completed else 0
    earned_now = xp if completed and not previous_progress.get("completed") else 0
    progress = save_activity_progress(
        user["id"],
        activity["id"],
        completed,
        correct,
        incorrect,
        score,
        xp,
        hints_used=hints_used,
        feedback=feedback,
    )
    current_user = get_user_by_id(user["id"])
    _set_session_user(current_user)
    current_level = (current_user.get("xp", 0) // 200) + 1
    if completed:
        record_audit_event(user["id"], "activity_completed", activity["slug"])
    return jsonify({
        "success": True,
        "completed": completed,
        "xp": earned_now,
        "new_xp": current_user.get("xp", 0),
        "coins": current_user.get("coins", 0),
        "level": current_level,
        "level_up": current_level > previous_level,
        "progress": progress,
        "level_overview": get_level_overview(user["id"], activity["level_id"]),
    })


@main_bp.route("/dashboard")
def dashboard():
    student = session.get("student", _default_student())
    live = get_student_live_data(student["id"]) if student.get("id") else None
    return render_template(
        "dashboard.html",
        **_context(
            active_page="dashboard",
            level_summary=live["levels"] if live else [{"id": lvl["id"], "title": lvl["title"], "progress": 0, "status": "locked" if lvl["id"] != 1 else "active"} for lvl in LEVELS],
            missions=live["missions"] if live else [], achievements=live["achievements"] if live else [], leaderboard=live["leaderboard"] if live else [], streak_calendar=[], weekly_activity=live["weekly_activity"] if live else [], recommendations=live["recommendations"] if live else [], history=live["history"] if live else [], daily_goal=live["daily_goal"] if live else {"current": 0, "target": 25, "unit": "min", "percent": 0}, continue_learning=live["continue_learning"] if live else {"title": "Detective Fonético", "level": "Fonética", "level_id": 1, "progress": 0, "xp_reward": 120},
        ),
    )


@main_bp.route("/teacher")
@teacher_required
def teacher_dashboard():
    return render_template("teacher_dashboard.html", **_context(active_page="teacher", teacher_data=get_teacher_dashboard()))


@main_bp.route("/teacher/students/<int:student_id>")
@teacher_required
def teacher_student_detail(student_id: int):
    view = get_student_teacher_view(student_id)
    if not view:
        return render_template("404.html", **_context(active_page=""), error_message="Estudiante no encontrado."), 404
    return render_template("teacher_student.html", **_context(active_page="teacher", student_view=view))


@main_bp.route("/teacher/students/<int:student_id>/notes", methods=["POST"])
@teacher_required
def teacher_student_note(student_id: int):
    body = request.form.get("body", "").strip()
    if body:
        teacher = _load_student()
        add_teacher_note(teacher["id"], student_id, body[:2000])
        record_audit_event(teacher["id"], "teacher_note", f"student:{student_id}")
    return redirect(url_for("main.teacher_student_detail", student_id=student_id))


@main_bp.route("/teacher/export/<string:format>")
@teacher_required
def teacher_export(format: str):
    if format not in {"csv", "excel", "pdf"}:
        return render_template("403.html", **_context(active_page=""), error_message="Formato no disponible."), 403
    data = get_teacher_dashboard()["students"]
    if format == "pdf":
        lines = ["Discourse Lab - Reporte de estudiantes", ""] + [f"{item['username']} | {item['email']} | XP {item['xp']} | Promedio {item['average']}% | Progreso {item['completion']}%" for item in data]
        return Response(_simple_pdf(lines), mimetype="application/pdf", headers={"Content-Disposition": "attachment; filename=discourse-lab-estudiantes.pdf"})
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Nombre", "Correo", "Registro", "Último acceso", "Estado", "Nivel", "XP", "Monedas", "Promedio", "Completado %"])
    for item in data:
        writer.writerow([item["username"], item["email"], item["created_at"], item.get("last_login") or "", item.get("status", "active"), item["level"], item["xp"], item["coins"], item["average"], item["completion"]])
    filename = "discourse-lab-estudiantes.csv" if format == "csv" else "discourse-lab-estudiantes.xls"
    mimetype = "text/csv" if format == "csv" else "application/vnd.ms-excel"
    return Response(output.getvalue(), mimetype=mimetype, headers={"Content-Disposition": f"attachment; filename={filename}"})


@main_bp.route("/profile")
def profile():
    student = session.get("student", _default_student())
    live = get_student_live_data(student["id"]) if student.get("id") else None
    return render_template(
        "profile.html",
        **_context(
            active_page="profile",
            achievements=live["achievements"] if live else [], level_summary=live["levels"] if live else [], history=live["history"] if live else [], weekly_activity=live["weekly_activity"] if live else [],
        ),
    )


@main_bp.route("/final-project")
def final_project():
    return render_template(
        "final_project.html",
        **_context(active_page="final_project"),
    )


@main_bp.route("/certificate")
def certificate():
    return render_template(
        "certificate.html",
        **_context(active_page="certificate"),
    )


@main_bp.app_errorhandler(404)
def page_not_found(error):
    return render_template(
        "404.html",
        **_context(active_page=""),
        error_message="La página que buscas no existe.",
    ), 404


@main_bp.app_errorhandler(500)
def server_error(error):
    return render_template(
        "500.html",
        **_context(active_page=""),
        error_message="Ha ocurrido un error interno. Intenta de nuevo más tarde.",
    ), 500

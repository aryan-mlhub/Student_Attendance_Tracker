"""
Flask Application for Student Attendance Tracker.
Complete college Python project web application.
Provides:
- Dashboard with key metrics and date selector
- Student Management (CRUD, duplicate validation, search, filter, sort)
- Attendance Management (Mark Present/Absent/Leave, bulk actions, historical logs, edit)
- Bulk Import (CSV, TXT, text-based PDF via pypdf, Excel, preview, duplicate resolution)
- Reports & Analytics (Individual student report, class report, <75% warnings, CSV export)
- Full server-side validation and CSRF protection
"""

import os
import io
import secrets
from pathlib import Path
from datetime import datetime, date
from typing import Optional, Dict, Any, List

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
    send_file,
    Response,
    abort,
)
from werkzeug.utils import secure_filename

from database import (
    Database,
    StudentManager,
    AttendanceManager,
    BulkImportManager,
    ReportsManager,
    DuplicateRollNumberError,
    ValidationError,
    VALID_STATUSES,
    ATTENDANCE_DEFICIT_THRESHOLD,
)

# App Setup & Configuration
app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", secrets.token_hex(32))
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB max upload
app.config["UPLOAD_FOLDER"] = Path(__file__).resolve().parent / "static" / "uploads"
app.config["UPLOAD_FOLDER"].mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {".csv", ".txt", ".pdf", ".xlsx", ".xls"}

# Initialize database and managers
db = Database()
student_mgr = StudentManager(db)
attendance_mgr = AttendanceManager(db)
reports_mgr = ReportsManager(db)
import_mgr = BulkImportManager(db, student_mgr)


# ---------------------------------------------------------------------
# CSRF and Context Processors
# ---------------------------------------------------------------------

@app.before_request
def csrf_protect():
    """Ensure session has a CSRF token and validate state-changing POST requests."""
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_hex(24)

    if request.method == "POST":
        token = request.form.get("csrf_token") or request.headers.get("X-CSRFToken")
        if not token or token != session.get("csrf_token"):
            flash("Invalid or expired session security token. Please try again.", "error")
            return redirect(request.referrer or url_for("dashboard"))


@app.context_processor
def inject_global_vars():
    """Inject commonly used variables across all Jinja templates."""
    return {
        "csrf_token": session.get("csrf_token", ""),
        "current_year": datetime.now().year,
        "today_str": date.today().strftime("%Y-%m-%d"),
        "total_students_count": student_mgr.get_total_students_count(),
        "deficit_threshold": ATTENDANCE_DEFICIT_THRESHOLD,
    }


# ---------------------------------------------------------------------
# Core Navigation Routes
# ---------------------------------------------------------------------

@app.route("/")
def index():
    """Redirect root path to the Dashboard."""
    return redirect(url_for("dashboard"))


@app.route("/dashboard")
def dashboard():
    """Main dashboard displaying attendance statistics for a chosen date, recent logs, and summary cards."""
    selected_date = request.args.get("date", date.today().strftime("%Y-%m-%d")).strip()
    try:
        selected_date = attendance_mgr.validate_date(selected_date)
    except ValueError:
        selected_date = date.today().strftime("%Y-%m-%d")

    # Metrics for chosen date
    stats = attendance_mgr.get_date_stats(selected_date)

    # Recent attendance sessions
    recent_activity = attendance_mgr.get_recent_activity(limit=6)

    # Check for any defaulters (<75%)
    all_reports = reports_mgr.get_attendance_report()
    defaulters = [r for r in all_reports if r["is_low"]]

    # Total registered students
    total_students = student_mgr.get_total_students_count()

    # Classes for quick filter buttons
    classes = student_mgr.get_distinct_classes()

    return render_template(
        "dashboard.html",
        active_page="dashboard",
        selected_date=selected_date,
        stats=stats,
        recent_activity=recent_activity,
        defaulters=defaulters,
        total_students=total_students,
        classes=classes,
    )


# ---------------------------------------------------------------------
# Student Management Routes
# ---------------------------------------------------------------------

@app.route("/students")
def students_list():
    """Display student list with search, class/section filter, and column sorting."""
    search_query = request.args.get("search", "").strip()
    class_filter = request.args.get("class_name", "").strip()
    section_filter = request.args.get("section", "").strip()
    sort_by = request.args.get("sort_by", "roll_no").strip()
    sort_order = request.args.get("sort_order", "ASC").strip().upper()

    students = student_mgr.get_all_students(
        search_query=search_query,
        class_filter=class_filter,
        section_filter=section_filter,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    distinct_classes = student_mgr.get_distinct_classes()
    distinct_sections = student_mgr.get_distinct_sections(class_filter)

    # Simple pagination
    page = request.args.get("page", 1, type=int)
    per_page = 15
    total_items = len(students)
    total_pages = max(1, (total_items + per_page - 1) // per_page)
    page = max(1, min(page, total_pages))
    start_idx = (page - 1) * per_page
    paginated_students = students[start_idx : start_idx + per_page]

    return render_template(
        "students.html",
        active_page="students",
        students=paginated_students,
        total_items=total_items,
        page=page,
        total_pages=total_pages,
        search_query=search_query,
        class_filter=class_filter,
        section_filter=section_filter,
        sort_by=sort_by,
        sort_order=sort_order,
        distinct_classes=distinct_classes,
        distinct_sections=distinct_sections,
    )


@app.route("/students/new", methods=["GET", "POST"])
def student_add():
    """Add a new student with validation against duplicate roll numbers."""
    if request.method == "POST":
        roll_no = request.form.get("roll_no", "").strip()
        name = request.form.get("name", "").strip()
        class_name = request.form.get("class_name", "").strip()
        section = request.form.get("section", "").strip().upper()

        try:
            student_mgr.add_student(roll_no, name, class_name, section)
            flash(f"Student '{name}' ({roll_no}) added successfully!", "success")
            return redirect(url_for("students_list"))
        except (ValidationError, DuplicateRollNumberError) as e:
            flash(str(e), "error")
            return render_template(
                "student_form.html",
                active_page="students",
                mode="add",
                form_data={
                    "roll_no": roll_no,
                    "name": name,
                    "class_name": class_name,
                    "section": section,
                },
                distinct_classes=student_mgr.get_distinct_classes(),
            )

    return render_template(
        "student_form.html",
        active_page="students",
        mode="add",
        form_data={},
        distinct_classes=student_mgr.get_distinct_classes(),
    )


@app.route("/students/<int:student_id>/edit", methods=["GET", "POST"])
def student_edit(student_id: int):
    """Edit student details with duplicate roll-number validation."""
    student = student_mgr.get_student_by_id(student_id)
    if not student:
        flash("Student record not found.", "error")
        return redirect(url_for("students_list"))

    if request.method == "POST":
        roll_no = request.form.get("roll_no", "").strip()
        name = request.form.get("name", "").strip()
        class_name = request.form.get("class_name", "").strip()
        section = request.form.get("section", "").strip().upper()

        try:
            student_mgr.update_student(student_id, roll_no, name, class_name, section)
            flash(f"Student details for '{name}' updated successfully!", "success")
            return redirect(url_for("students_list"))
        except (ValidationError, DuplicateRollNumberError) as e:
            flash(str(e), "error")
            return render_template(
                "student_form.html",
                active_page="students",
                mode="edit",
                student_id=student_id,
                form_data={
                    "roll_no": roll_no,
                    "name": name,
                    "class_name": class_name,
                    "section": section,
                },
                distinct_classes=student_mgr.get_distinct_classes(),
            )

    return render_template(
        "student_form.html",
        active_page="students",
        mode="edit",
        student_id=student_id,
        form_data=student,
        distinct_classes=student_mgr.get_distinct_classes(),
    )


@app.route("/students/<int:student_id>/delete", methods=["POST"])
def student_delete(student_id: int):
    """Delete a student and their attendance history with foreign-key cascade."""
    student = student_mgr.get_student_by_id(student_id)
    if not student:
        flash("Student not found.", "error")
        return redirect(url_for("students_list"))

    student_mgr.delete_student(student_id)
    flash(f"Student '{student['name']}' ({student['roll_no']}) was successfully deleted.", "info")
    return redirect(url_for("students_list"))


@app.route("/students/<int:student_id>/history")
def student_history(student_id: int):
    """Individual student attendance profile: stats and day-by-day record."""
    student = student_mgr.get_student_by_id(student_id)
    if not student:
        flash("Student record not found.", "error")
        return redirect(url_for("students_list"))

    history_records = reports_mgr.get_student_history(student_id)
    total_days = len(history_records)
    present_days = sum(1 for r in history_records if r["status"] == "Present")
    absent_days = sum(1 for r in history_records if r["status"] == "Absent")
    leave_days = sum(1 for r in history_records if r["status"] == "Leave")

    denom = present_days + absent_days
    pct = round((present_days / denom * 100.0), 1) if denom > 0 else (100.0 if total_days > 0 else 0.0)
    is_defaulter = (total_days > 0) and (pct < ATTENDANCE_DEFICIT_THRESHOLD)

    return render_template(
        "student_detail.html",
        active_page="students",
        student=student,
        history=history_records,
        stats={
            "total_days": total_days,
            "present_days": present_days,
            "absent_days": absent_days,
            "leave_days": leave_days,
            "percentage": pct,
            "is_defaulter": is_defaulter,
        },
    )


# ---------------------------------------------------------------------
# Attendance Management Routes
# ---------------------------------------------------------------------

@app.route("/attendance", methods=["GET", "POST"])
def attendance_mark():
    """Mark attendance for students for a specific date, class, and section."""
    if request.method == "POST":
        attendance_date = request.form.get("attendance_date", "").strip()
        class_name = request.form.get("class_name", "").strip()
        section = request.form.get("section", "").strip()

        try:
            valid_date = attendance_mgr.validate_date(attendance_date)
        except ValueError as e:
            flash(str(e), "error")
            return redirect(url_for("attendance_mark"))

        # Extract submitted statuses
        student_ids = request.form.getlist("student_id")
        records_to_save = []
        for sid_str in student_ids:
            try:
                sid = int(sid_str)
                status = request.form.get(f"status_{sid}")
                if status in VALID_STATUSES:
                    records_to_save.append({"student_id": sid, "status": status})
            except (ValueError, TypeError):
                continue

        if not records_to_save:
            flash("No attendance entries were submitted.", "warning")
            return redirect(url_for("attendance_mark", date=valid_date, class_name=class_name, section=section))

        saved_count = attendance_mgr.save_batch_attendance(valid_date, records_to_save, overwrite=True)
        flash(f"Attendance for {saved_count} students recorded for {valid_date} successfully!", "success")
        return redirect(url_for("attendance_mark", date=valid_date, class_name=class_name, section=section))

    # GET Request
    selected_date = request.args.get("date", date.today().strftime("%Y-%m-%d")).strip()
    try:
        selected_date = attendance_mgr.validate_date(selected_date)
    except ValueError:
        selected_date = date.today().strftime("%Y-%m-%d")

    class_filter = request.args.get("class_name", "").strip()
    section_filter = request.args.get("section", "").strip()
    search_query = request.args.get("search", "").strip()

    # Check if attendance already exists for this date/filters
    has_records, recorded_count = attendance_mgr.has_attendance_for_date(
        selected_date, class_filter or None, section_filter or None
    )

    sheet = attendance_mgr.get_attendance_sheet(
        attendance_date=selected_date,
        class_name=class_filter,
        section=section_filter,
        search_query=search_query,
    )

    distinct_classes = student_mgr.get_distinct_classes()
    distinct_sections = student_mgr.get_distinct_sections(class_filter)

    return render_template(
        "attendance.html",
        active_page="attendance",
        selected_date=selected_date,
        class_filter=class_filter,
        section_filter=section_filter,
        search_query=search_query,
        sheet=sheet,
        has_records=has_records,
        recorded_count=recorded_count,
        distinct_classes=distinct_classes,
        distinct_sections=distinct_sections,
    )


@app.route("/history")
def attendance_history():
    """View historical attendance logs grouped by date and class/section."""
    start_date = request.args.get("start_date", "").strip()
    end_date = request.args.get("end_date", "").strip()
    class_filter = request.args.get("class_name", "").strip()

    history_logs = attendance_mgr.get_attendance_history_log(
        start_date=start_date or None,
        end_date=end_date or None,
        class_filter=class_filter or None,
    )

    distinct_classes = student_mgr.get_distinct_classes()

    return render_template(
        "history.html",
        active_page="history",
        history_logs=history_logs,
        start_date=start_date,
        end_date=end_date,
        class_filter=class_filter,
        distinct_classes=distinct_classes,
    )


# ---------------------------------------------------------------------
# Bulk Import Routes
# ---------------------------------------------------------------------

@app.route("/import")
def bulk_import():
    """Bulk import page showing upload card and preview of parsed rows if staged."""
    staged = session.get("staged_import")
    return render_template(
        "bulk_import.html",
        active_page="import",
        staged=staged,
    )


@app.route("/import/upload", methods=["POST"])
def import_upload():
    """Receive uploaded file, parse rows, validate duplicates, and store in session for preview."""
    if "file" not in request.files:
        flash("No file part in request.", "error")
        return redirect(url_for("bulk_import"))

    uploaded_file = request.files["file"]
    if not uploaded_file or uploaded_file.filename == "":
        flash("Please select a file to upload.", "error")
        return redirect(url_for("bulk_import"))

    safe_name = secure_filename(uploaded_file.filename)
    ext = Path(safe_name).suffix.lower()

    if ext not in ALLOWED_EXTENSIONS:
        flash(f"Unsupported file format '{ext}'. Allowed: .csv, .txt, .pdf, .xlsx", "error")
        return redirect(url_for("bulk_import"))

    file_bytes = uploaded_file.read()
    if not file_bytes:
        flash("The uploaded file is empty.", "error")
        return redirect(url_for("bulk_import"))

    result = import_mgr.load_file_content(safe_name, file_bytes)

    if not result.get("success"):
        error_msg = result.get("error", "Failed to parse file.")
        if result.get("is_scanned_pdf"):
            flash(f"Scanned PDF Alert: {error_msg}", "warning")
        else:
            flash(f"Parsing Error: {error_msg}", "error")
        return redirect(url_for("bulk_import"))

    # Stage parsed data into session
    session["staged_import"] = {
        "file_name": safe_name,
        "records": result["records"],
        "summary": result["summary"],
        "unparsed_items": result["unparsed_items"][:20],  # cap for session size
        "raw_text": result.get("raw_text", "")[:1000],
    }

    flash(f"File '{safe_name}' parsed successfully! {len(result['records'])} rows detected. Please review below.", "info")
    return redirect(url_for("bulk_import"))


@app.route("/import/confirm", methods=["POST"])
def import_confirm():
    """Execute the import into the database for selected rows."""
    staged = session.get("staged_import")
    if not staged or not staged.get("records"):
        flash("No parsed import data found in session. Please upload a file first.", "warning")
        return redirect(url_for("bulk_import"))

    selected_ids = set(request.form.getlist("selected_row"))
    duplicate_action = request.form.get("duplicate_action", "skip").strip().lower()

    # Filter records based on user's checkboxes
    records_to_import = []
    for rec in staged["records"]:
        rec_id_str = str(rec.get("id"))
        if rec_id_str in selected_ids:
            records_to_import.append(rec)

    if not records_to_import:
        flash("No records were selected for import. Check the box next to at least one row.", "warning")
        return redirect(url_for("bulk_import"))

    import_result = import_mgr.execute_import(records_to_import, duplicate_action=duplicate_action)

    # Clear staged session
    session.pop("staged_import", None)

    if import_result["success"]:
        flash(
            f"Import complete! {import_result['added']} added, {import_result['updated']} updated, "
            f"{import_result['skipped']} skipped.",
            "success",
        )
    else:
        flash(f"Import failed: {import_result.get('error', 'Unknown error')}", "error")

    return redirect(url_for("students_list"))


@app.route("/import/clear", methods=["POST"])
def import_clear():
    """Clear currently staged upload preview."""
    session.pop("staged_import", None)
    flash("Staged import preview cleared.", "info")
    return redirect(url_for("bulk_import"))


@app.route("/import/sample/<sample_type>")
def download_sample(sample_type: str):
    """Download sample template files for testing imports."""
    samples_dir = Path(__file__).resolve().parent / "static" / "samples"
    file_map = {
        "csv": ("sample_students.csv", "sample_students.csv", "text/csv"),
        "txt_comma": ("sample_students_comma.txt", "sample_students_comma.txt", "text/plain"),
        "txt_pipe": ("sample_students_pipe.txt", "sample_students_pipe.txt", "text/plain"),
        "pdf": ("sample_students.pdf", "sample_students.pdf", "application/pdf"),
        "scanned_pdf": ("sample_scanned.pdf", "sample_scanned.pdf", "application/pdf"),
    }

    if sample_type not in file_map:
        abort(404)

    file_name, download_name, mime = file_map[sample_type]
    file_path = samples_dir / file_name

    if not file_path.exists():
        flash("Sample file not found.", "error")
        return redirect(url_for("bulk_import"))

    return send_file(str(file_path), as_attachment=True, download_name=download_name, mimetype=mime)


# ---------------------------------------------------------------------
# Reports and Analytics Routes
# ---------------------------------------------------------------------

@app.route("/reports")
def reports_view():
    """Attendance reports with date range, class/section filters, and defaulter toggle."""
    class_filter = request.args.get("class_name", "").strip()
    section_filter = request.args.get("section", "").strip()
    start_date = request.args.get("start_date", "").strip()
    end_date = request.args.get("end_date", "").strip()
    search_query = request.args.get("search", "").strip()
    only_defaulters = request.args.get("only_defaulters") == "1"

    report_data = reports_mgr.get_attendance_report(
        class_filter=class_filter,
        section_filter=section_filter,
        start_date=start_date or None,
        end_date=end_date or None,
        search_query=search_query,
        only_defaulters=only_defaulters,
    )

    # Compute overall metrics across this filtered view
    total_students_in_view = len(report_data)
    total_present = sum(r["present_days"] for r in report_data)
    total_absent = sum(r["absent_days"] for r in report_data)
    total_leave = sum(r["leave_days"] for r in report_data)
    defaulters_count = sum(1 for r in report_data if r["is_low"])

    denom = total_present + total_absent
    overall_percentage = round((total_present / denom * 100.0), 1) if denom > 0 else 0.0

    distinct_classes = student_mgr.get_distinct_classes()
    distinct_sections = student_mgr.get_distinct_sections(class_filter)

    return render_template(
        "reports.html",
        active_page="reports",
        report_data=report_data,
        class_filter=class_filter,
        section_filter=section_filter,
        start_date=start_date,
        end_date=end_date,
        search_query=search_query,
        only_defaulters=only_defaulters,
        distinct_classes=distinct_classes,
        distinct_sections=distinct_sections,
        total_students_in_view=total_students_in_view,
        total_present=total_present,
        total_absent=total_absent,
        total_leave=total_leave,
        defaulters_count=defaulters_count,
        overall_percentage=overall_percentage,
    )


@app.route("/reports/export")
def reports_export_csv():
    """Download current report as CSV."""
    class_filter = request.args.get("class_name", "").strip()
    section_filter = request.args.get("section", "").strip()
    start_date = request.args.get("start_date", "").strip()
    end_date = request.args.get("end_date", "").strip()
    search_query = request.args.get("search", "").strip()
    only_defaulters = request.args.get("only_defaulters") == "1"

    report_data = reports_mgr.get_attendance_report(
        class_filter=class_filter,
        section_filter=section_filter,
        start_date=start_date or None,
        end_date=end_date or None,
        search_query=search_query,
        only_defaulters=only_defaulters,
    )

    csv_data = reports_mgr.generate_csv_string(report_data)
    filename = f"attendance_report_{date.today().strftime('%Y%m%d')}.csv"

    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )




# ---------------------------------------------------------------------
# Error Handlers
# ---------------------------------------------------------------------

@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404


@app.errorhandler(413)
def request_entity_too_large(e):
    flash("The uploaded file exceeds the maximum allowed size (16MB).", "error")
    return redirect(url_for("bulk_import"))


@app.errorhandler(500)
def internal_server_error(e):
    return render_template("500.html", error_message=str(e)), 500


# ---------------------------------------------------------------------
# Development Server Runner
# ---------------------------------------------------------------------

if __name__ == "__main__":
    import socket

    def is_port_in_use(p: int) -> bool:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(("127.0.0.1", p)) == 0

    if os.environ.get("PORT"):
        port = int(os.environ.get("PORT"))
    else:
        port = 5001 if is_port_in_use(5000) else 5000

    print(f"\n=======================================================")
    print(f" Student Attendance Tracker (Flask Edition)")
    print(f" Live URL: http://127.0.0.1:{port}")
    print(f"=======================================================\n")
    app.run(host="0.0.0.0", port=port, debug=False)


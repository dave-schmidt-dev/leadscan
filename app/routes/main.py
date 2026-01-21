import json
import logging
import os

from flask import Blueprint, Response, abort, flash, redirect, render_template, request, stream_with_context, url_for
from sqlalchemy import create_engine

from app import Base, db_session
from app.models.config import AppConfig
from app.models.lead import Lead, LeadStatus
from app.services.google_places import search_nearby
from app.services.pipeline import process_lead_analysis

logger = logging.getLogger(__name__)

bp = Blueprint("main", __name__)

# --- Input Validation Constants ---
MIN_RADIUS = 100  # meters
MAX_RADIUS = 50000  # meters (50km)
DEFAULT_RADIUS = 1000

# --- System Routes ---


@bp.route("/reset-db", methods=["GET", "POST"])
def reset_db():
    """Wipes all leads from the database while preserving API usage statistics."""
    if request.method == "GET":
        return redirect(url_for("main.index"))

    # 1. Backup Stats
    backup_stats = {}
    try:
        backup_stats["google_api_nearby"] = AppConfig.get("google_api_nearby", "0")
        backup_stats["google_api_details"] = AppConfig.get("google_api_details", "0")
        backup_stats["last_billing_month"] = AppConfig.get("last_billing_month", None)
    except Exception:
        pass  # If DB is broken, just proceed

    # 2. Wipe DB
    db_session.remove()  # Close session to release file locks for SQLite

    engine = create_engine(os.environ.get("DATABASE_URI", "sqlite:///leadscan.db"))
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    # 3. Restore Stats
    if backup_stats.get("last_billing_month"):
        AppConfig.set("last_billing_month", backup_stats["last_billing_month"])
        AppConfig.set("google_api_nearby", backup_stats["google_api_nearby"])
        AppConfig.set("google_api_details", backup_stats["google_api_details"])

    flash("Database reset! (API Stats preserved)")
    return redirect(url_for("main.index"))


@bp.route("/favicon.ico")
def favicon():
    """Prevents 404 errors in console logs for the missing favicon."""
    return "", 204


# --- Dashboard & Search ---


@bp.route("/")
def index():
    """Main dashboard showing leads grouped by status."""
    db_session.expire_all()  # Ensure fresh data from database

    # Show everything EXCEPT leads marked as Ignored/Hidden
    all_leads = Lead.query.filter(Lead.status != LeadStatus.IGNORED).order_by(Lead.id.desc()).all()

    # Define desired display order
    status_order = [
        LeadStatus.ANALYZED,
        LeadStatus.SCRAPED,
        LeadStatus.CONTACTED,
        LeadStatus.WON,
        LeadStatus.LOST,
        LeadStatus.GOOD_CONDITION,
    ]

    grouped_leads = {status: [] for status in status_order}
    for lead in all_leads:
        if lead.status in grouped_leads:
            grouped_leads[lead.status].append(lead)

    return render_template("index.html", grouped_leads=grouped_leads)


@bp.route("/search", methods=["POST"])
def search():
    """Performs an Omni-Search and streams real-time progress logs to the UI."""
    keyword = request.form.get("keyword", "business").strip()

    # Input validation: radius with bounds checking
    try:
        radius = int(request.form.get("radius", DEFAULT_RADIUS))
        radius = max(MIN_RADIUS, min(radius, MAX_RADIUS))
    except (ValueError, TypeError):
        radius = DEFAULT_RADIUS

    # Input validation: sanitize keyword
    if not keyword or len(keyword) > 100:
        keyword = "business"

    try:
        lat = float(os.environ.get("DEFAULT_LAT", "37.7749"))
        lng = float(os.environ.get("DEFAULT_LNG", "-122.4194"))
    except ValueError:
        lat, lng = 37.7749, -122.4194

    def generate():
        total_found = 0
        total_new = 0

        # Stream results from the Google Places service generator
        for type, data in search_nearby(lat, lng, radius, keyword):
            if type == "log":
                yield json.dumps({"type": "log", "message": data}) + "\n"
            elif type == "result":
                total_found += 1
                # Deduplicate and Save
                existing = Lead.query.filter_by(place_id=data["place_id"]).first()
                if not existing:
                    new_lead = Lead(
                        place_id=data["place_id"], name=data["name"], address=data["address"], status=LeadStatus.SCRAPED
                    )
                    db_session.add(new_lead)
                    total_new += 1

        db_session.commit()
        yield json.dumps({"type": "done", "new_leads": total_new, "total_scanned": total_found}) + "\n"

    return Response(stream_with_context(generate()), mimetype="application/x-ndjson")


# --- Lead Details & Actions ---


@bp.route("/lead/<int:lead_id>")
def lead_detail(lead_id):
    """View detailed analysis metrics and logs for a single lead."""
    lead = db_session.get(Lead, lead_id)
    if not lead:
        abort(404)
    return render_template("lead_detail.html", lead=lead)


@bp.route("/lead/<int:lead_id>/status", methods=["POST"])
def update_status(lead_id):
    """Update the current workflow status of a lead."""
    lead = db_session.get(Lead, lead_id)
    if not lead:
        abort(404)
    new_status = request.form.get("status")
    if new_status in [s.value for s in LeadStatus]:
        lead.status = LeadStatus(new_status)
        db_session.commit()
        flash("Status updated")
    return redirect(url_for("main.lead_detail", lead_id=lead_id))


@bp.route("/lead/<int:lead_id>/notes", methods=["POST"])
def update_notes(lead_id):
    """Save custom user notes for a specific lead."""
    lead = db_session.get(Lead, lead_id)
    if not lead:
        abort(404)
    lead.notes = request.form.get("notes")
    db_session.commit()
    flash("Notes saved")
    return redirect(url_for("main.lead_detail", lead_id=lead_id))


@bp.route("/lead/<int:lead_id>/analyze", methods=["POST"])
def analyze_lead(lead_id):
    """Trigger deep analysis for a specific lead from its detail page."""
    success = process_lead_analysis(lead_id)
    if success:
        flash("Deep analysis complete.")
    else:
        flash("Analysis failed.")
    return redirect(url_for("main.lead_detail", lead_id=lead_id))


@bp.route("/lead/<int:lead_id>/analyze-dashboard", methods=["POST"])
def analyze_lead_dashboard(lead_id):
    """Trigger analysis for a lead directly from the dashboard."""
    success = process_lead_analysis(lead_id)
    if success:
        flash("Analysis complete.")
    else:
        flash("Analysis failed.")
    return redirect(url_for("main.index"))


@bp.route("/bulk-analyze", methods=["POST"])
def bulk_analyze():
    """Trigger analysis for multiple 'Scraped' leads in sequence."""
    analyze_all = request.form.get("analyze_all") == "on"
    try:
        limit = int(request.form.get("limit", 5))
    except ValueError:
        limit = 5

    query = Lead.query.filter(Lead.status == LeadStatus.SCRAPED)
    leads = query.all() if analyze_all else query.limit(limit).all()
    msg_suffix = " (All Pending)" if analyze_all else f" (Limit: {limit})"

    if not leads:
        flash('No "Scraped" leads found to analyze.')
        return redirect(url_for("main.index"))

    count = 0
    errors = 0
    for lead in leads:
        try:
            if process_lead_analysis(lead.id):
                count += 1
            else:
                errors += 1
        except Exception:
            errors += 1

    flash(f"Bulk Analysis Complete: Processed {count} leads{msg_suffix}. Errors: {errors}")
    return redirect(url_for("main.index"))


@bp.route("/lead/<int:lead_id>/hide", methods=["POST"])
def hide_lead(lead_id):
    """Mark a lead as Ignored so it no longer appears in results."""
    lead = db_session.get(Lead, lead_id)
    if not lead:
        abort(404)
    lead.status = LeadStatus.IGNORED
    db_session.commit()
    flash(f"Lead {lead.name} hidden.")
    return redirect(url_for("main.index"))

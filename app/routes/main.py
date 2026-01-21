from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from app import db_session, Base
from sqlalchemy import create_engine
import os

from app.models.lead import Lead, LeadStatus
from app.services.google_places import search_nearby
from app.services.pipeline import process_lead_analysis

bp = Blueprint('main', __name__)

from app.models.config import AppConfig

@bp.route('/reset-db', methods=['GET', 'POST'])
def reset_db():
    if request.method == 'GET':
        return redirect(url_for('main.index'))
        
    # 1. Backup Stats
    backup_stats = {}
    try:
        backup_stats['google_api_nearby'] = AppConfig.get('google_api_nearby', "0")
        backup_stats['google_api_details'] = AppConfig.get('google_api_details', "0")
        backup_stats['last_billing_month'] = AppConfig.get('last_billing_month', None)
    except:
        pass # If DB is broken, just proceed

    # 2. Wipe DB
    # Close session to release file locks for SQLite
    db_session.remove()
    
    engine = create_engine(os.environ.get('DATABASE_URI', 'sqlite:///leadscan.db'))
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    # 3. Restore Stats
    if backup_stats.get('last_billing_month'):
        AppConfig.set('last_billing_month', backup_stats['last_billing_month'])
        AppConfig.set('google_api_nearby', backup_stats['google_api_nearby'])
        AppConfig.set('google_api_details', backup_stats['google_api_details'])

    flash('Database reset! (API Stats preserved)')
    return redirect(url_for('main.index'))

@bp.route('/favicon.ico')
def favicon():
    return '', 204

@bp.route('/')
def index():
    # Force refresh from DB
    db_session.expire_all()
    
    # Show everything EXCEPT Ignored
    all_leads = Lead.query.filter(Lead.status != LeadStatus.IGNORED).order_by(Lead.id.desc()).all()
    
    # Define desired order (Analyzed first so progress is visible)
    status_order = [
        LeadStatus.ANALYZED,
        LeadStatus.SCRAPED,
        LeadStatus.CONTACTED,
        LeadStatus.WON,
        LeadStatus.LOST,
        LeadStatus.GOOD_CONDITION
    ]
    
    grouped_leads = {status: [] for status in status_order}
    
    for lead in all_leads:
        if lead.status in grouped_leads:
            grouped_leads[lead.status].append(lead)
            
    return render_template('index.html', grouped_leads=grouped_leads)

@bp.route('/search', methods=['POST'])
def search():
    keyword = request.form.get('keyword', 'business')
    radius = int(request.form.get('radius', 1000))
    
    # Get coordinates from env or default to generic center (e.g. San Francisco)
    try:
        lat = float(os.environ.get('DEFAULT_LAT', '37.7749'))
        lng = float(os.environ.get('DEFAULT_LNG', '-122.4194'))
    except ValueError:
        lat, lng = 37.7749, -122.4194
    
    try:
        print(f"DEBUG: Searching with keyword '{keyword}', radius {radius} at {lat}, {lng}")
        results = search_nearby(lat, lng, radius, keyword)
        print(f"DEBUG: Found {len(results)} results from API")
        
        # Deduplicate and Save
        count = 0
        for place in results:
            existing = Lead.query.filter_by(place_id=place['place_id']).first()
            if not existing:
                new_lead = Lead(
                    place_id=place['place_id'],
                    name=place['name'],
                    address=place['address'],
                    status=LeadStatus.SCRAPED
                )
                db_session.add(new_lead)
                count += 1
            else:
                print(f"DEBUG: Skipping duplicate lead: {place['name']}")
        
        print(f"DEBUG: Committing {count} new leads")
        db_session.commit()
        
        if count > 0:
            flash(f'Scan complete. Added {count} new leads.')
        else:
            flash('Scan complete. No new leads found (all duplicates).')
            
    except Exception as e:
        print(f"DEBUG: Search error: {e}")
        db_session.rollback()
        flash(f'Error during scan: {str(e)}')
        
    return redirect(url_for('main.index'))

@bp.route('/lead/<int:lead_id>')
def lead_detail(lead_id):
    lead = db_session.get(Lead, lead_id)
    if not lead:
        abort(404)
    return render_template('lead_detail.html', lead=lead)

@bp.route('/lead/<int:lead_id>/status', methods=['POST'])
def update_status(lead_id):
    lead = db_session.get(Lead, lead_id)
    if not lead:
        abort(404)
    new_status = request.form.get('status')
    if new_status in [s.value for s in LeadStatus]:
        lead.status = LeadStatus(new_status)
        db_session.commit()
        flash('Status updated')
    return redirect(url_for('main.lead_detail', lead_id=lead_id))

@bp.route('/lead/<int:lead_id>/notes', methods=['POST'])
def update_notes(lead_id):
    lead = db_session.get(Lead, lead_id)
    if not lead:
        abort(404)
    lead.notes = request.form.get('notes')
    db_session.commit()
    flash('Notes saved')
    return redirect(url_for('main.lead_detail', lead_id=lead_id))

@bp.route('/lead/<int:lead_id>/analyze', methods=['POST'])
def analyze_lead(lead_id):
    success = process_lead_analysis(lead_id)
    if success:
        flash('Deep analysis complete.')
    else:
        flash('Analysis failed (Lead not found).')
    return redirect(url_for('main.lead_detail', lead_id=lead_id))

@bp.route('/lead/<int:lead_id>/analyze-dashboard', methods=['POST'])
def analyze_lead_dashboard(lead_id):
    success = process_lead_analysis(lead_id)
    if success:
        flash(f'Analysis complete.')
    else:
        flash('Analysis failed.')
    return redirect(url_for('main.index'))

@bp.route('/bulk-analyze', methods=['POST'])
def bulk_analyze():
    analyze_all = request.form.get('analyze_all') == 'on'
    try:
        limit = int(request.form.get('limit', 5))
    except ValueError:
        limit = 5
        
    query = Lead.query.filter(Lead.status == LeadStatus.SCRAPED)
    
    if not analyze_all:
        leads = query.limit(limit).all()
        msg_suffix = f" (Limit: {limit})"
    else:
        leads = query.all()
        msg_suffix = " (All Pending)"
        
    if not leads:
        flash('No "Scraped" leads found to analyze.')
        return redirect(url_for('main.index'))
        
    count = 0
    errors = 0
    
    for lead in leads:
        try:
            if process_lead_analysis(lead.id):
                count += 1
            else:
                errors += 1
        except Exception as e:
            print(f"Error analyzing lead {lead.id}: {e}")
            errors += 1
            
    flash(f"Bulk Analysis Complete: Processed {count} leads{msg_suffix}. Errors: {errors}")
    return redirect(url_for('main.index'))

@bp.route('/lead/<int:lead_id>/hide', methods=['POST'])
def hide_lead(lead_id):
    lead = db_session.get(Lead, lead_id)
    if not lead:
        abort(404)
    lead.status = LeadStatus.IGNORED
    db_session.commit()
    flash(f'Lead {lead.name} hidden (will not reappear in scans)')
    return redirect(url_for('main.index'))
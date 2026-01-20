from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from app import db_session, Base
from sqlalchemy import create_engine
import os

from app.models.lead import Lead, LeadStatus
from app.services.google_places import search_nearby
from app.services.pipeline import process_lead_analysis

bp = Blueprint('main', __name__)

from app.models.config import AppConfig

@bp.route('/reset-db', methods=['POST'])
def reset_db():
    # 1. Backup Stats
    backup_stats = {}
    try:
        backup_stats['google_api_nearby'] = AppConfig.get('google_api_nearby', "0")
        backup_stats['google_api_details'] = AppConfig.get('google_api_details', "0")
        backup_stats['last_billing_month'] = AppConfig.get('last_billing_month', None)
    except:
        pass # If DB is broken, just proceed

    # 2. Wipe DB
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

@bp.route('/')
def index():
    # Show everything EXCEPT Ignored
    all_leads = Lead.query.filter(Lead.status != LeadStatus.IGNORED).order_by(Lead.id.desc()).all()
    
    # Define desired order
    status_order = [
        LeadStatus.SCRAPED,
        LeadStatus.ANALYZED,
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
        results = search_nearby(lat, lng, radius, keyword)
    except Exception as e:
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

@bp.route('/lead/<int:lead_id>/delete', methods=['POST'])
def delete_lead(lead_id):
    lead = db_session.get(Lead, lead_id)
    if not lead:
        abort(404)
    lead.status = LeadStatus.IGNORED
    db_session.commit()
    flash(f'Lead {lead.name} ignored (will not reappear in scans)')
    return redirect(url_for('main.index'))
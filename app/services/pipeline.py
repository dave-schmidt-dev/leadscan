from app.models.lead import Lead, LeadStatus
from app.services.google_places import get_place_details
from app.services.analyzer import analyze_url

def process_lead_analysis(lead_id):
    """
    Runs the full enrichment pipeline for a lead:
    1. Fetches deep contact details (website, phone) from Google Places API.
    2. Runs technical heuristic scans on the business website.
    3. Calculates a priority score and updates the record.
    """
    from app import db_session
    
    lead = Lead.query.get(lead_id)
    if not lead:
        return False

    # --- Phase 1: Contact Enrichment ---
    # Refresh core contact data from Google Details API
    details = get_place_details(lead.place_id)
    if details:
        lead.phone = details.get('formatted_phone_number', lead.phone)
        lead.website_url = details.get('website', lead.website_url)
        lead.address = details.get('formatted_address', lead.address)

    # --- Phase 2: Technical Analysis ---
    if lead.website_url:
        analysis = analyze_url(lead.website_url)
        
        # Map analysis metrics
        lead.ssl_active = analysis.get('ssl_active', False)
        lead.mobile_viewport = analysis.get('mobile_viewport', False)
        lead.contact_info_found = analysis.get('contact_info_found', False)
        lead.copyright_year = analysis.get('copyright_year')
        lead.status_code = analysis.get('status_code')
        lead.analysis_error = analysis.get('error')
        lead.tech_stack = analysis.get('tech_stack')
        lead.load_time = analysis.get('load_time')
        
        # Save technical logs
        if analysis.get('logs'):
            lead.analysis_notes = "\n".join(analysis['logs'])
        
        # --- Phase 3: Scoring ---
        # Simple heuristic score (0-100)
        score = 0
        if lead.ssl_active: score += 25
        if lead.mobile_viewport: score += 25
        if lead.contact_info_found: score += 25
        if analysis.get('exists'): score += 25
        lead.content_heuristic_score = score
        
    # --- Phase 4: Workflow Update ---
    # Automatically move from 'Scraped' to 'Analyzed'
    if lead.status == LeadStatus.SCRAPED:
        lead.status = LeadStatus.ANALYZED
        
    try:
        db_session.commit()
    except Exception:
        db_session.rollback()
        return False
        
    return True

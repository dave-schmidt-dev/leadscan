from app.models.lead import Lead, LeadStatus
from app.services.google_places import get_place_details
from app.services.analyzer import analyze_url

def process_lead_analysis(lead_id):
    from app import db_session
    """
    Runs the full analysis pipeline on an existing lead.
    1. Fetches deep details from Google (website, phone)
    2. Analyzes the website (SSL, mobile, etc.)
    3. Updates the Lead record
    """
    lead = Lead.query.get(lead_id)
    if not lead:
        return False

    # Step 1: Enrich with Google Details (if we don't have URL yet)
    # We always refresh just in case
    details = get_place_details(lead.place_id)
    
    if details:
        lead.phone = details.get('formatted_phone_number', lead.phone)
        lead.website_url = details.get('website', lead.website_url)
        lead.address = details.get('formatted_address', lead.address)

    # Step 2: Analyze Website
    if lead.website_url:
        analysis = analyze_url(lead.website_url)
        
        lead.ssl_active = analysis.get('ssl_active', False)
        lead.mobile_viewport = analysis.get('mobile_viewport', False)
        lead.contact_info_found = analysis.get('contact_info_found', False)
        lead.copyright_year = analysis.get('copyright_year')
        
        # Simple scoring
        score = 0
        if lead.ssl_active: score += 25
        if lead.mobile_viewport: score += 25
        if lead.contact_info_found: score += 25
        if analysis.get('exists'): score += 25
        
        lead.content_heuristic_score = score
        
    # Update status to Analyzed if it was just Scraped
    if lead.status == LeadStatus.SCRAPED:
        lead.status = LeadStatus.ANALYZED
        
    try:
        db_session.commit()
    except Exception as e:
        db_session.rollback()
        return False
        
    return True

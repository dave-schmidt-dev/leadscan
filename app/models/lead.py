import enum
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Enum, Integer, String, Text

from app import Base


class LeadStatus(enum.Enum):
    """Enumeration of possible stages in the lead lifecycle."""
    SCRAPED = "Scraped"
    ANALYZED = "Analyzed"
    CONTACTED = "Contacted"
    WON = "Won"
    LOST = "Lost"
    GOOD_CONDITION = "Good Condition"
    IGNORED = "Ignored"

class Lead(Base):
    """
    Main data model for a potential business lead.
    Stores Google Places identity, contact info, and technical analysis metrics.
    """
    __tablename__ = 'leads'

    # --- Identity & Contact ---
    id = Column(Integer, primary_key=True)
    place_id = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    address = Column(String(500))
    phone = Column(String(50))
    website_url = Column(String(500))

    # --- Analysis Metrics ---
    ssl_active = Column(Boolean, default=False)
    mobile_viewport = Column(Boolean, default=False)
    contact_info_found = Column(Boolean, default=False)
    content_heuristic_score = Column(Integer, default=0) # 0-100 score
    status_code = Column(Integer)
    analysis_error = Column(String(500))
    analysis_notes = Column(Text)
    copyright_year = Column(Integer)
    tech_stack = Column(String(100))
    load_time = Column(Integer) # In milliseconds

    # --- Workflow ---
    status = Column(Enum(LeadStatus), default=LeadStatus.SCRAPED)
    notes = Column(Text)

    # --- Timestamps ---
    created_at = Column(DateTime, default=datetime.utcnow)
    analyzed_at = Column(DateTime)

    def __repr__(self):
        return f'<Lead {self.name}>'

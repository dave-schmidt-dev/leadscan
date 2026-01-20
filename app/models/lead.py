from sqlalchemy import Column, Integer, String, Boolean, Enum, Text
from app import Base
import enum

class LeadStatus(enum.Enum):
    SCRAPED = "Scraped"
    ANALYZED = "Analyzed"
    CONTACTED = "Contacted"
    WON = "Won"
    LOST = "Lost"
    GOOD_CONDITION = "Good Condition"
    IGNORED = "Ignored"

class Lead(Base):
    __tablename__ = 'leads'

    id = Column(Integer, primary_key=True)
    place_id = Column(String(255), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    address = Column(String(500))
    phone = Column(String(50))
    website_url = Column(String(500))
    
    # Analysis fields
    ssl_active = Column(Boolean, default=False)
    mobile_viewport = Column(Boolean, default=False)
    contact_info_found = Column(Boolean, default=False)
    content_heuristic_score = Column(Integer, default=0) # Simple 0-100 score
    
    status = Column(Enum(LeadStatus), default=LeadStatus.SCRAPED)
    notes = Column(Text)

    def __repr__(self):
        return f'<Lead {self.name}>'

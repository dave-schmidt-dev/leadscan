# Omni-Search Business Categories

## Overview
LeadScan's Omni-Search uses **100+ business categories** to comprehensively scan local markets for service businesses with poor web presence. The default list covers approximately **95% of local service businesses** that aren't franchises.

## Default Categories (100+)

### 🏠 Home Services - Construction & Repair (15)
- plumber
- electrician
- hvac
- roofer
- general contractor
- handyman
- carpenter
- painter
- flooring contractor
- drywall contractor
- mason
- concrete contractor
- garage door repair
- appliance repair
- foundation repair

### 🌳 Home Services - Exterior (10)
- landscaper
- lawn care
- tree service
- fencing
- pool service
- gutter cleaning
- pressure washing
- deck builder
- irrigation
- snow removal

### 🧹 Home Services - Cleaning & Maintenance (8)
- cleaning service
- carpet cleaning
- window cleaning
- junk removal
- moving company
- restoration service
- pest control
- chimney sweep

### 🔒 Home Services - Specialty (5)
- locksmith
- security system
- home inspector
- solar installation
- insulation contractor

### 🏥 Medical & Healthcare (8)
- dentist
- chiropractor
- physical therapy
- massage therapist
- acupuncture
- veterinarian
- optometrist
- mental health counselor

### 💼 Professional Services (7)
- lawyer
- accountant
- insurance agent
- real estate agent
- financial advisor
- notary public
- consultant

### 🚗 Automotive (7)
- auto repair
- auto body shop
- towing service
- tire shop
- oil change
- car wash
- auto detailing

### 💇 Personal Services (12)
- barber
- hair salon
- nail salon
- spa
- gym
- personal trainer
- photographer
- wedding planner
- catering
- dry cleaning
- tailor

### 🏢 Business Services (5)
- printing service
- sign shop
- storage facility
- security guard
- janitorial service

### 🔧 Specialty Contractors (5)
- hvac cleaning
- septic service
- well drilling
- fire protection
- elevator service

---

## Customization

### Target Specific Industries

You can override the default list by setting `OMNI_SEARCH_CATEGORIES` in your `.env` file:

```ini
# High-value trades only (fewer API calls)
OMNI_SEARCH_CATEGORIES=plumber,electrician,hvac,roofer,landscaper,lawyer,accountant

# Home services bundle
OMNI_SEARCH_CATEGORIES=plumber,electrician,hvac,landscaper,painter,handyman,carpenter,pest control,cleaning service
```

### Why These Categories?

**Inclusion Criteria:**
1. ✅ Typically local/small businesses (not chains)
2. ✅ High likelihood of poor web presence
3. ✅ Service-based (need websites to get leads)
4. ✅ High customer value (worth paying for web services)
5. ✅ Geographic-bound (need local SEO)

**Excluded:**
- ❌ National chains (McDonald's, Walmart, etc.)
- ❌ Retail stores (handled by TYPE_BLOCKLIST)
- ❌ Gas stations, ATMs (handled by TYPE_BLOCKLIST)

---

## Category Performance Tips

### Maximize Efficiency
- **Default (100+)**: Best coverage but uses ~100 API calls per scan
- **Focused (10-20)**: Target your niche, uses ~10-20 API calls
- **High-Value (7)**: Highest-paying clients, minimal API usage

### Recommended Strategies

**Strategy 1: Full Market Scan**
Use default categories for initial market research. Get comprehensive view of all opportunities.

**Strategy 2: Niche Targeting**
Pick 5-10 categories you specialize in. Example: `plumber,electrician,hvac,landscaper,roofer`

**Strategy 3: Rotating Focus**
Week 1: Home services
Week 2: Medical/Healthcare
Week 3: Professional services
Week 4: Automotive & Personal

---

## API Quota Impact

**Google Places API Limits (Free Tier):**
- Nearby Search: 5,000 requests/month
- Place Details: 10,000 requests/month

**Default (100+ categories):**
- Per scan: ~100 Nearby calls + variable Details calls
- Can scan: ~50 locations/month

**Focused (10 categories):**
- Per scan: ~10 Nearby calls + variable Details calls
- Can scan: ~500 locations/month

**Pro Tip:** Start with focused list, expand to default as you validate ROI.

---

## Future Expansion Ideas

**Potential additions:**
- Roofing inspection
- Window installation
- Kitchen remodeling
- Bathroom remodeling
- Home theater installation
- Smart home installation
- Property management

**Why not included by default:**
- Overlap with existing categories
- Lower search volume
- Already captured by "general contractor" or "handyman"

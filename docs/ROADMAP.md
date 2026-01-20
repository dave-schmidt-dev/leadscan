# LeadScan Roadmap

Ideas for future development sessions.

## Phase 2: Enhanced Analysis
- [ ] **Tech Stack Detection**: Detect if they use WordPress, Wix, or custom HTML. (Easier to pitch "Move away from Wix" or "Fix your WP plugins").
- [ ] **Speed Test**: Measure generic page load time (Time to First Byte).
- [ ] **Broken Link Checker**: Scan the landing page for 404 links (high value pitch point).
- [ ] **Analyze All**: Button to run deep analysis on all "Scraped" leads in batch (with progress bar).

## Phase 3: Pitch Generation (LLM Integration)
- [ ] **Pitch Button**: A button on the Lead Detail page that sends the lead data to an LLM (Claude/GPT).
- [ ] **Prompt Engineering**: "Write a friendly email to {name} noting their lack of SSL and mobile support..."
- [ ] **Draft Storage**: Save the generated email draft to `notes` or a new field.

## Phase 4: Workflow Automation
- [ ] **CSV Export**: Download leads to import into Google Sheets/Excel.
- [ ] **Calendar Integration**: "Remind me to call on Tuesday".
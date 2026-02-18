# AntiGravity 1.0

A **DOE (Directive → Observation → Experiment)** system for converting human intent into reliable, repeatable outputs.

## Philosophy

AI is probabilistic. Business logic must be deterministic.  
This system separates those responsibilities to reduce error over time.

## Quick Start

1. **Copy environment template**
   ```bash
   cp .env.template .env
   ```
   Then edit `.env` with your actual API keys and credentials.

2. **Install dependencies**
   ```bash
   pip install -r execution/requirements.txt
   ```

3. **Read the operating manual**
   See `Agents.md` for the complete system architecture and operating principles.

## Directory Structure

```
.
├── Agents.md              # Operating manual (DOE architecture)
├── directives/            # Layer 1: What to do (GMB Scrape, Enrichment)
├── execution/             # Layer 3: Deterministic scripts (Scraper, Enricher)
├── .tmp/                  # Temporary files (safe to delete)
├── .env                   # Environment variables (not in git)
├── README.md              # This file
└── ENRICHED_SUMMARY_REPORT.txt # Latest high-value SEO lead report
```

1. **Directives** define goals, inputs, tools, outputs, and edge cases
2. **Orchestration** (AI agent) interprets directives and routes execution
3. **Execution** scripts handle the actual work:
    - `scrape_gmb_leads.py`: Extracts business listings from Google Maps.
    - `enrich_leads.py`: Scrapes business websites for contact details, scores them, and writes cold emails.

## Operating Principles

- **Check for existing tools** before creating new ones
- **Self-anneal on failure** - fix, improve, test, update directive
- **Improve directives continuously** - they're living documents
- **Deliverables live in the cloud** - local files are intermediates

## Self-Annealing Loop

When something breaks:
1. Fix it
2. Improve the tool
3. Test again
4. Update the directive
5. Continue with a stronger system

---

**Read `Agents.md` for complete operating instructions.**

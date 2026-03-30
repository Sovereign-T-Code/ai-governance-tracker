# AI Governance Tracker

A zero-cost, automated tracker that aggregates AI legislation, regulations, and policy developments across Canada, the United States, and the European Union into one searchable, filterable interface.

Built as a static site with a Python data pipeline — no server, no database, no paid APIs.

## Features

- **Multi-jurisdiction coverage**: Canada (federal + Ontario), United States (federal), European Union
- **8 data sources**: Congress.gov API, Federal Register API, EUR-Lex, LEGISinfo, Canada Gazette, Ontario OLA, TBS directives, Google News RSS
- **Daily automated updates** via GitHub Actions cron
- **Keyword-based classification**: AI relevance filter, 9 domain categories, normalized status taxonomy
- **Three views**: Sortable data table, vertical timeline, news feed
- **Full-text search** with debounce
- **Multi-select filters**: jurisdiction, status, domain, date range — all persisted in URL params
- **Dark mode default** with light mode toggle
- **Email notifications** when new entries are detected (Gmail SMTP)
- **Expandable row details** with summaries and source links

## Architecture

```
GitHub Actions (daily cron)
    → Python pipeline (fetch → classify → deduplicate → write JSON)
    → Commit data if changed + send email notification
    → Build React frontend
    → Deploy to GitHub Pages
```

Everything runs at build time. The frontend is a static site that loads `data/entries.json` and does all filtering/sorting client-side.

## Project Structure

```
ai-governance-tracker/
├── .github/workflows/update-tracker.yml   # Daily cron + deploy
├── pipeline/
│   ├── main.py              # Pipeline orchestrator
│   ├── classify.py           # AI relevance, domain tagging, status normalization
│   ├── notify.py             # Email notifications (Gmail SMTP)
│   ├── requirements.txt
│   └── sources/
│       ├── congress_gov.py   # US — Congress.gov API
│       ├── federal_register.py # US — Federal Register API
│       ├── eurlex.py         # EU — EUR-Lex search
│       ├── legisinfo.py      # Canada — LEGISinfo (parl.ca)
│       ├── canada_gazette.py # Canada — Canada Gazette RSS
│       ├── ontario_ola.py    # Canada — Ontario Legislative Assembly
│       ├── tbs_directive.py  # Canada — Treasury Board directives
│       └── news_rss.py       # Google News RSS
├── data/
│   ├── entries.json          # All tracked entries
│   └── meta.json             # Pipeline health + last run timestamp
├── frontend/                 # Vite + React + Tailwind
│   └── src/
│       ├── App.jsx
│       ├── components/       # DataTable, Timeline, NewsFeed, Filters, etc.
│       ├── hooks/            # useEntries, useFilterParams
│       └── utils/            # Filter logic, constants
├── README.md
└── LICENSE
```

## Local Development

### Prerequisites

- Python 3.10+
- Node.js 18+
- A free Congress.gov API key ([sign up here](https://api.congress.gov/sign-up/))

### Run the pipeline

```bash
pip install -r pipeline/requirements.txt
CONGRESS_GOV_API_KEY=your_key python -m pipeline.main
```

### Run the frontend

```bash
cd frontend
npm install
cp -r ../data public/data    # copy pipeline output for local dev
npm run dev
```

Open `http://localhost:5173/ai-governance-tracker/` in your browser.

## Deployment

The project deploys automatically to GitHub Pages via GitHub Actions.

### Setup

1. Push the repo to GitHub
2. Go to **Settings > Pages** and set source to **GitHub Actions**
3. Add these **repository secrets** (Settings > Secrets > Actions):

| Secret | Required | Purpose |
|--------|----------|---------|
| `CONGRESS_GOV_API_KEY` | Yes | Congress.gov API key (free) |
| `GMAIL_USER` | No | Gmail address for notifications |
| `GMAIL_APP_PASSWORD` | No | Gmail app password (requires 2FA) |
| `NOTIFY_EMAIL` | No | Email to receive notifications |

4. The workflow runs daily at 6:00 AM UTC, or trigger manually from the Actions tab

## Data Schema

Each entry in `entries.json`:

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique identifier (source-specific) |
| `title` | string | Entry title |
| `jurisdiction` | string | Human-readable jurisdiction name |
| `jurisdiction_code` | string | `CA-FED`, `CA-ON`, `US-FED`, or `EU` |
| `source_url` | string | Link to the original source |
| `source_name` | string | Data source name |
| `type` | string | `legislation` or `news` |
| `status` | string | `Proposed`, `In Progress`, `Passed/Adopted`, `In Force`, or `Withdrawn/Defeated` |
| `domains` | array | Domain tags (Healthcare, Privacy, etc.) |
| `date_introduced` | string | ISO date |
| `date_last_action` | string | ISO date of most recent action |
| `last_action_summary` | string | Description of last action |
| `summary` | string | Entry summary text |
| `date_first_seen` | string | When the pipeline first found this entry |
| `date_last_updated` | string | When the pipeline last updated this entry |

## Adding a New Source

1. Create `pipeline/sources/your_source.py`
2. Implement `def fetch() -> list[dict]` returning entries matching the schema above
3. Wrap the entire body in try/except, return `[]` on failure
4. Import and add it to the `SOURCES` dict in `pipeline/main.py`

## Cost

Zero. Everything runs on free tiers:
- GitHub Actions: ~30-60 min/month of the 2,000 min/month free tier
- GitHub Pages: free static hosting
- All APIs: free, no paid tiers required
- Gmail SMTP: free with app password

## License

MIT

# Paciolus

**Trial Balance Diagnostic Intelligence Platform for Financial Professionals**

Paciolus provides instant, zero-storage trial balance analysis with intelligent anomaly detection, ratio analysis, and professional export capabilities.

## Key Features

- **Zero-Storage Architecture** — Financial data is processed in-memory and never persisted. Only aggregate metadata is stored for variance analysis.
- **Intelligent Classification** — 80+ keyword rules automatically categorize accounts (Assets, Liabilities, Equity, Revenue, Expenses)
- **Anomaly Detection** — Identifies sign errors, unusual balances, and classification mismatches
- **Ratio Intelligence** — Current, Quick, Debt-to-Equity, and Gross Margin calculations with trend analysis
- **Multi-Sheet Excel Support** — Process complex workbooks with automatic sheet consolidation
- **Professional Exports** — PDF diagnostic summaries and Excel workpapers with Oat & Obsidian branding

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 20+
- npm or yarn

### Backend Setup
```bash
cd backend
cp .env.example .env
# Edit .env with your configuration
pip install -r requirements.txt
python main.py
```

### Frontend Setup
```bash
cd frontend
cp .env.example .env.local
npm install
npm run dev
```

### Docker (Recommended)
```bash
docker-compose up --build
```
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Architecture

```
paciolus/
├── backend/                 # FastAPI Python backend
│   ├── main.py             # API endpoints
│   ├── audit_engine.py     # Core diagnostic logic
│   ├── flux_engine.py      # Period-over-period analysis
│   ├── recon_engine.py     # Reconciliation scoring
│   ├── ratio_engine.py     # Financial ratio calculations
│   └── models.py           # SQLAlchemy models
├── frontend/               # Next.js React frontend
│   ├── src/app/           # App router pages
│   ├── src/components/    # Reusable UI components
│   ├── src/hooks/         # Custom React hooks
│   └── src/context/       # React context providers
└── docs/                   # Additional documentation
```

## Documentation

- [CLAUDE.md](./CLAUDE.md) — Development protocol and project state
- [DEPLOYMENT.md](./DEPLOYMENT.md) — Production deployment guide
- [tasks/todo.md](./tasks/todo.md) — Sprint planning and progress
- [tasks/lessons.md](./tasks/lessons.md) — Development patterns and learnings

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | Next.js 14, React, TypeScript, Tailwind CSS, Framer Motion |
| Backend | FastAPI, Python 3.11, SQLAlchemy, Pandas |
| Database | SQLite (dev), PostgreSQL (prod) |
| Auth | JWT with bcrypt password hashing |
| Exports | ReportLab (PDF), openpyxl (Excel) |

## Design System: Oat & Obsidian

Paciolus uses a distinctive premium fintech aesthetic:

| Color | Hex | Usage |
|-------|-----|-------|
| Obsidian | `#212121` | Backgrounds, headers |
| Oatmeal | `#EBE9E4` | Light text, secondary elements |
| Sage | `#4A7C59` | Success states, income |
| Clay | `#BC4749` | Error states, expenses |

Typography: Merriweather (headers), Lato (body), JetBrains Mono (financial data)

## License

Proprietary — All rights reserved.

---

*"Without double entry, businessmen would not sleep at night."* — Luca Pacioli, 1494

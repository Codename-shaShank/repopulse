# RepoPulse frontend

React + Vite + TypeScript dashboard for the RepoPulse API.

## Setup

```bash
cp .env.example .env
```

```bash
npm install
```

```bash
npm run dev
```

The dev server runs at <http://localhost:5173>. Point `VITE_API_BASE_URL` at the
backend — `http://localhost:8000` by default.

## Scripts

| Command | What it does |
|---|---|
| `npm run dev` | Start the Vite dev server |
| `npm run build` | Type check and build into `dist/` |
| `npm run preview` | Serve the production build locally |
| `npm run lint` | Type check only |

## Structure

```text
src/
├── api/          Typed fetch client and endpoint wrappers
├── charts/       Recharts history and language charts
├── components/   Form, list, sync history and shared UI pieces
├── pages/        Dashboard, repository detail, analytics help
├── App.tsx       Routes and layout
└── styles.css    All styling
```

All displayed data comes from the backend; nothing is hardcoded. Charts handle
empty and single-point datasets with an explanatory message rather than an empty
plot.

When deploying as a static site, add a rewrite from `/*` to `/index.html` so
client-side routes resolve on refresh.

# CineBook — Repository Polish & Professional Enhancement Plan

> **Goal:** Transform the existing CineBook project from a working technical assessment into a **portfolio-grade, shareable GitHub repository** with polished UI, professional repo scaffolding, and a README that showcases the project with an embedded launch video.

---

## Phase 1: Repository Scaffolding

> [!IMPORTANT]
> These files are **missing entirely** and are critical for a professional open-source presence.

### 1.1 — [NEW] `.gitignore`

Create a comprehensive `.gitignore` for Python projects:

```
# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*$py.class

# Virtual environments
venv/
.venv/
env/

# IDE files
.vscode/
.idea/
*.swp
*.swo

# SQLite database (generated)
database/booking.db

# Distribution / packaging
dist/
build/
*.egg-info/

# OS-generated files
.DS_Store
Thumbs.db
desktop.ini

# Test artifacts
.pytest_cache/
htmlcov/
.coverage

# Hyperframes rendering artifacts
brag-output/composition/
brag-output/*.md
```

### 1.2 — [NEW] `LICENSE`

Add an MIT License file for open-source credibility.

### 1.3 — [NEW] `.github/FUNDING.yml` *(optional)*

Only if the user wants to enable GitHub Sponsors.

### 1.4 — [NEW] `CONTRIBUTING.md`

Short contributing guide with setup instructions and code style expectations.

---

## Phase 2: README Overhaul with Video Embed

> [!IMPORTANT]
> The current README is functional but reads like internal documentation. The new version must be **eye-catching, scannable, and portfolio-grade**.

### 2.1 — [MODIFY] `README.md`

**Key changes:**

1. **Hero section** — Project name, one-liner tagline, shield.io badges (Python version, license, tests passing)
2. **Embedded launch video** — `brag-output/brag.mp4` embedded for immediate visual impact
   - GitHub doesn't natively embed MP4 in READMEs, so we'll use a **clickable poster image** linking to the raw MP4 file in the repo
   - Strategy: `[![Watch the Demo](brag-output/brag.jpg)](brag-output/brag.mp4)`
3. **Feature highlights** — Three pillars with emojis and concise descriptions
4. **Tech stack badges** — Python, MySQL, SQLite, Streamlit, Flask, Plotly, pytest
5. **Quick start** — Condensed from the current verbose setup to a 4-command quick start
6. **Screenshots section** — Real screenshots of the 4 dashboard pages (to be captured)
7. **Architecture diagram** — Mermaid diagram showing the component relationships
8. **API reference** — Keep the existing table, but in a collapsible section
9. **Testing** — Condensed with test counts and a badge
10. **Troubleshooting** — Move the 6 errors to a collapsible section
11. **License** — MIT badge at the bottom

### 2.2 — Capture Dashboard Screenshots

We need actual screenshots of:
- Book Tickets page (with seat map visible)
- My Bookings page
- Admin Analytics page (with charts)
- Schema & Normalisation page

These will be saved to `docs/screenshots/` and embedded in the README.

---

## Phase 3: Streamlit Dashboard UI Enhancements

> [!IMPORTANT]
> The current dashboard uses **default Streamlit styling** throughout. The changes below will make it feel premium and production-grade without breaking any functionality.

### 3.1 — [NEW] `app/.streamlit/config.toml`

Custom Streamlit theme with a curated color palette:

```toml
[theme]
primaryColor = "#6C63FF"        # Indigo accent
backgroundColor = "#0E1117"     # Dark background
secondaryBackgroundColor = "#1A1D23"  # Sidebar/card dark
textColor = "#FAFAFA"
font = "sans serif"
```

### 3.2 — [MODIFY] `app/streamlit_app.py` — Custom CSS Injection

Add a `st.markdown(unsafe_allow_html=True)` block at the top of the app to inject custom CSS for:

| Element | Enhancement |
|---------|-------------|
| **Sidebar** | Gradient background, subtle border-right, rounded nav items |
| **Page title** | Larger font, custom font weight, subtle bottom border |
| **Seat map buttons** | Rounded corners, hover glow effects, shadow transitions |
| **Metric cards** | Glassmorphism card style with backdrop blur |
| **Expanders** | Custom border-left accent color, rounded corners |
| **Form elements** | Consistent border radius, focus ring color |
| **Tables/DataFrames** | Zebra striping, sticky headers, rounded corners |

### 3.3 — [MODIFY] `app/streamlit_app.py` — Seat Map Visual Upgrade

Current seat map uses emoji-prefixed text buttons (`🟥 A1`, `🟩 A2`). Upgrade to:

- **Color-coded button styling** via CSS classes (green for available, red for taken, gold for selected)
- **Row labels** with a cinema-style "SCREEN" indicator at the top
- **Seat legend** with styled color swatches instead of emoji
- **Seat count badge** showing `X/Y seats available`

### 3.4 — [MODIFY] `app/streamlit_app.py` — Analytics Page Chart Theme

Upgrade Plotly chart aesthetics:

| Chart | Enhancement |
|-------|-------------|
| **Occupancy gauge** | Dark template, neon accent colors, drop shadow |
| **Revenue bar chart** | Gradient fill bars, rounded corners, better axis labels |
| **Seat type pie chart** | Custom color sequence matching theme, percentage labels |
| **Grouped bar chart** | Side-by-side with subtle animation on load |

Use `plotly.io.templates["plotly_dark"]` as the base template with custom overrides.

### 3.5 — [MODIFY] `app/streamlit_app.py` — Booking Confirmation UX

After a successful booking:
- Display a styled **ticket card** with movie name, seat, date, and QR-style payment ref
- Add a **"Print Ticket"** expander with formatted ticket details
- Show a success animation with confetti (already using `st.balloons()`, keep this)

### 3.6 — [MODIFY] `app/streamlit_app.py` — My Bookings Page Enhancement

- Add **booking status chips** (CONFIRMED = green, CANCELLED = red) using styled HTML badges
- Add a **booking count summary** at the top (e.g., "3 Active · 1 Cancelled")
- Improve the cancellation confirmation UX with a warning message

### 3.7 — [MODIFY] `app/streamlit_app.py` — Schema Page Enhancement

- Add a **live ER diagram** using Mermaid.js embedded via `st.components.v1.html()`
- Style the 3NF proof expanders with a color-coded progress indicator (1NF ✓ → 2NF ✓ → 3NF ✓)
- Add a **trigger flowchart** showing the BEFORE INSERT → check → SIGNAL/RAISE flow

---

## Phase 4: Feature Additions

### 4.1 — [MODIFY] `app/streamlit_app.py` — Dashboard Home / Landing Page

Add a **5th page** (or make it the default): a Dashboard Home that shows:
- **Quick stats cards**: Total Movies, Total Bookings, Revenue Today, Active Shows
- **Recent bookings ticker** — Last 5 bookings as a styled list
- **System health** — Database engine indicator (MySQL ✓ or SQLite fallback)

### 4.2 — [MODIFY] `app/streamlit_app.py` — Movie Posters

Enhance the Book Tickets page:
- Show **movie poster thumbnails** next to movie titles in the show selector
- We'll generate placeholder poster images using the `generate_image` tool
- Display genre, duration, and rating as styled chips below the movie title

### 4.3 — [NEW] `app/pages/` — Streamlit Multi-Page App *(Optional)*

Consider migrating from the single-file radio-button navigation to Streamlit's native multi-page app structure. This gives:
- Proper URL routing (`/Book_Tickets`, `/Analytics`, etc.)
- Cleaner code organization
- Better performance (only loads the active page)

> [!WARNING]
> This is the most invasive change. It requires splitting `streamlit_app.py` into separate page files. **Only proceed if user approves.**

---

## Phase 5: Code Quality & Documentation

### 5.1 — [NEW] `docs/ARCHITECTURE.md`

High-level architecture document with:
- System architecture diagram (Streamlit ↔ src/ ↔ DB)
- Database ER diagram (Mermaid)
- Data flow for booking, cancellation, and analytics

### 5.2 — [MODIFY] All source files — Docstring consistency

Ensure all public functions have:
- Type hints on all parameters and return values
- One-line summary + detailed description
- Example usage in docstrings for service functions

### 5.3 — [NEW] `pyproject.toml` or `setup.py`

Add proper Python project metadata for installability.

---

## Phase 6: Testing & CI

### 6.1 — [NEW] `.github/workflows/ci.yml`

GitHub Actions CI pipeline:
```yaml
- Checkout
- Setup Python 3.11
- Install dependencies
- Run pytest with SQLite mode
- Report results
```

### 6.2 — Verify existing tests pass

Run `pytest tests/ -v` to confirm all tests pass with the current codebase before making changes.

---

## Open Questions

> [!IMPORTANT]
> **Q1:** Should we split `streamlit_app.py` (742 lines) into a multi-page Streamlit app structure? This is cleaner but requires significant restructuring. **Recommendation:** Keep single file for now, split later if needed.

> [!IMPORTANT]
> **Q2:** Do you want real movie poster images generated (using the `generate_image` tool) for the 10 movies in the sample data? This would make the booking page much more visual but adds asset management complexity.

> [!IMPORTANT]
> **Q3:** Do you have a GitHub account/org name you'd like used in the badges and README? (e.g., `github.com/yourusername/cinebook`)

> [!IMPORTANT]
> **Q4:** Should we keep `ORIGINAL_REQUEST.md` in the repo or move it to a `docs/` folder? It contains internal build specifications that might not be appropriate for a public repo.

---

## Execution Order

| Step | Phase | Description | Est. LOC Changed |
|------|-------|-------------|------------------|
| 1 | P1 | Create `.gitignore`, `LICENSE`, `CONTRIBUTING.md` | ~80 new |
| 2 | P2 | Capture dashboard screenshots | 0 (asset creation) |
| 3 | P2 | Rewrite `README.md` with video embed + screenshots | ~200 rewrite |
| 4 | P3.1 | Create Streamlit theme config | ~10 new |
| 5 | P3.2 | Inject custom CSS into dashboard | ~150 new |
| 6 | P3.3 | Upgrade seat map visuals | ~60 modified |
| 7 | P3.4 | Upgrade chart themes | ~40 modified |
| 8 | P3.5-3.7 | UX enhancements (tickets, bookings, schema) | ~120 modified |
| 9 | P4.1 | Add Dashboard Home page | ~80 new |
| 10 | P5.1 | Create ARCHITECTURE.md | ~100 new |
| 11 | P6.1 | Create GitHub Actions CI | ~30 new |
| 12 | P6.2 | Run test verification | 0 |

**Total estimated effort:** ~870 lines new/modified across 12 steps.

---

## Verification Plan

### Automated Tests
```powershell
# Verify existing tests still pass after all changes
pytest tests/ -v

# Verify Streamlit app starts without errors
streamlit run app/streamlit_app.py --server.port 8501 --server.headless true
```

### Manual Verification
- Launch the dashboard and visually confirm each page looks polished
- Capture final screenshots for the README
- Verify the README renders correctly in GitHub's markdown preview
- Confirm `.gitignore` excludes the right files

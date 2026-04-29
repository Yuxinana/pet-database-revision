# Pet Adoption Center Management System

SQLite-backed course project for managing shelters, pets, adoption applications, completed adoptions, follow-ups, medical history, vaccinations, and volunteer care assignments.

中文说明：本仓库已经统一到一套真实可运行的 SQLite 实现，文档、SQL、前后端和测试现在使用同一套业务口径。

## Delivery Summary

- ER design, table set, field set, and relationships were kept unchanged.
- The schema was hardened with declarative constraints that match the documented design.
- Official SQL deliverables now run directly on SQLite.
- The web prototype uses GLM-generated prompt-to-SQL with backend read-only validation.
- Index recommendations are now applied during database initialization instead of remaining documentation-only.

## Repository Map

| Path | Purpose |
|---|---|
| `backend/` | FastAPI backend wrapper with routers, config, and compatibility layer |
| `frontend/` | Vue/Vite shell that preserves the existing `frontend/legacy/pawtrack_demo.html` UI |
| `docs/ER_DESIGN.md` | Design rationale, functional requirements, cardinalities, FDs, normalization |
| `PROJECT_STRUCTURE.md` | Current project layout and cleanup guidance |
| `docs/diagrams/er_diagram.png` | ER diagram artifact |
| `backend/app/db/data/` | CSV seed data used to rebuild the database |
| `backend/app/db/schema/table.sql` | Full schema definition with PK/FK/`CHECK`/`UNIQUE` constraints |
| `backend/app/db/schema/indexing.sql` | Representative indexes tied to operational and analytical workloads |
| `backend/app/db/queries/operational_queries.sql` | 6 operational read-only SQLite queries |
| `backend/app/db/queries/analytical_queries.sql` | 6 analytical read-only SQLite queries |
| `docs/sql/WORKFLOW_SQL_EXAMPLES.md` | Workflow-oriented mutation examples kept outside the read-only registry |
| `backend/app/services/query_registry.py` | Parser/catalog helper for the 12 official reviewed read-only SQL deliverables |
| `backend/app/services/llm_sql_assistant.py` | GLM prompt-to-SQL generation, prompt construction, SQL validation, and read-only execution |
| `backend/app/services/web_server_legacy.py` | Existing database initialization, validation, and service behavior moved under backend |
| `docs/` | Supporting design, workflow SQL, and diagram documents |
| `frontend/legacy/pawtrack_demo.html` | Preserved full frontend UI served by FastAPI |
| `docs/TEST_CASES.md` | Manual test design and reproducible validation checklist |
| `docs/REQUIREMENT_TRACEABILITY.md` | Requirement-to-evidence mapping for report and presentation use |
| `tests/test_backend.py` | Automated regression tests |

## Data Snapshot

Verified after rebuild on April 23, 2026:

| Table | Rows |
|---|---:|
| `SHELTER` | 3 |
| `PET` | 20 |
| `APPLICANT` | 15 |
| `ADOPTION_APPLICATION` | 15 |
| `ADOPTION_RECORD` | 6 |
| `FOLLOW_UP` | 16 |
| `MEDICAL_RECORD` | 25 |
| `VACCINATION` | 20 |
| `VOLUNTEER` | 10 |
| `CARE_ASSIGNMENT` | 15 |

Status snapshot on April 23, 2026:

- `PET.status`: `available=11`, `reserved=1`, `medical_hold=2`, `adopted=6`
- `ADOPTION_APPLICATION.status`: `Under Review=3`, `Approved=6`, `Rejected=6`
- `FOLLOW_UP.result_status`: `Excellent=2`, `Good=6`, `Satisfactory=2`, `Needs Improvement=6`

## Schema and Enforcement

The implementation preserves the original ER structure while making the documented rules executable:

- Foreign keys enforce entity relationships.
- `CHECK` constraints enforce controlled domains such as:
  - `PET.status`
  - `ADOPTION_APPLICATION.status`
  - `PET.species`
  - `PET.sex`
  - `MEDICAL_RECORD.record_type`
  - `CARE_ASSIGNMENT.shift`, `task_type`, `status`
  - `FOLLOW_UP.followup_type`, `result_status`
- Same-row temporal checks enforce:
  - pet birth date cannot be after intake date
  - application review date cannot be before application date
  - vaccination due date cannot be before vaccination date
- `ADOPTION_RECORD.application_id` is `UNIQUE`, matching the documented 1:0..1 relationship between application and adoption record.
- Cross-row and cross-table workflow rules remain application-enforced and are surfaced in the audit:
  - shelter capacity
  - pet workflow consistency
  - approved application uniqueness per pet
  - care-assignment shelter consistency
  - follow-up timing and adoption workflow ordering

The backend still runs these checks during database initialization so invalid source data fails early instead of producing a broken demo database.

## Official SQL Deliverables

The official query set contains 12 reviewed read-only SQLite queries:

- Operational:
  - shelter pet roster
  - adoptable pets
  - pet health timeline
  - vaccination due list
  - volunteer schedule
  - under-review application queue
- Analytical:
  - shelter occupancy
  - long-stay pets
  - approval outcomes by housing type
  - adoption demand and success by species
  - volunteer workload
  - post-adoption follow-up outcomes

Important changes from the earlier draft:

- MySQL-only functions such as `CURDATE()`, `DATE_ADD()`, and `DATEDIFF()` were removed from the official deliverables.
- The pet-health query no longer creates a vaccination-medical Cartesian product; it now returns one unified event timeline.
- Mutation examples are no longer mixed into the query registry.

## Prototype and API

### Frontend

`frontend/legacy/pawtrack_demo.html` is a single-file prototype covering:

- Dashboard
- Pets
- Applications
- Medical
- Volunteers
- Analytics
- Assistant

The UI uses backend-returned raw values for business logic and display labels for presentation. For example:

- application workflow raw value: `Under Review`
- application display label: `Pending`
- pet workflow raw value: `reserved`
- pet display label: `Reserved`

### Core endpoints

| Endpoint | Purpose |
|---|---|
| `GET /api/health` | Health check and active database path |
| `GET /api/dashboard` | Dashboard metrics, status overview, recent activity |
| `GET /api/analytics` | Analytical query outputs |
| `POST /api/llm-generate-query` | GLM prompt-to-SQL generation guarded by read-only validation |
| `GET /api/pets` | Pet roster with shelter data and status labels |
| `GET /api/applicants` | Applicant data |
| `GET /api/applications` | Adoption applications with raw/display status fields |
| `POST /api/applications` | Create a new application and reserve the pet |
| `PATCH /api/applications/{id}/review` | Approve or reject a pending application |
| `GET /api/adoption-records` | Completed adoption records |
| `GET /api/follow-ups` | Follow-up records |
| `POST /api/follow-ups` | Create a follow-up for a completed adoption |
| `GET /api/medical-records` | Medical history |
| `GET /api/vaccinations?upcoming=true` | Vaccination list or due-soon subset |
| `GET /api/volunteers` | Volunteer roster |
| `GET /api/care-assignments` | Care assignments |

Generic CRUD routes are also available for `shelters`, `pets`, `applicants`, `medical-records`, `vaccinations`, `volunteers`, `care-assignments`, and `follow-ups` through:

- `POST /api/{resource}`
- `PATCH /api/{resource}/{id}`
- `DELETE /api/{resource}/{id}`

## GLM Prompt-To-SQL Assistant

The project exposes one assistant path:

- `POST /api/llm-generate-query`: GLM-generated SQLite SQL with strict read-only validation before execution

The generated path supports four prompt methods:

- `zero_shot`
- `schema_grounded`
- `few_shot`
- `self_check_repair`

Generated SQL is accepted only if it is one `SELECT` or read-only `WITH ... SELECT` statement. The backend strips comments, rejects dangerous keywords, validates with `EXPLAIN QUERY PLAN`, executes through a read-only SQLite connection, installs a SQLite authorizer, and returns at most 50 rows.

Configure GLM access with environment variables:

```bash
export ZAI_API_KEY="your-rotated-key"
export GLM_MODEL="glm-5.1"
export GLM_BASE_URL="https://open.bigmodel.cn/api/paas/v4/"
export LLM_SQL_TIMEOUT_SECONDS="120"
export GLM_TIMEOUT_RETRIES="1"
export GLM_TIMEOUT_BACKOFF_SECONDS="2"
export GLM_MAX_CONCURRENT_REQUESTS="1"
export GLM_MIN_REQUEST_INTERVAL_SECONDS="1"
export GLM_RATE_LIMIT_RETRIES="4"
export GLM_RATE_LIMIT_BACKOFF_SECONDS="2"
```

`LLM_SQL_TIMEOUT_SECONDS` should stay high enough for GLM prompt-to-SQL responses; timeout retries handle transient slow responses but cannot make a consistently unavailable provider respond.
`GLM_MAX_CONCURRENT_REQUESTS` is a local throttle, not a provider quota override. Keep it low if GLM returns HTTP 429; raise it only after the account quota is upgraded.

## How to Run

### Prerequisites

- Python 3.10+
- Node.js 18+ for the Vue frontend

### FastAPI + Vue startup

```powershell
python -m pip install -r requirements.txt
npm install --prefix frontend
npm run api
npm run frontend
```

Then open:

- `http://127.0.0.1:5173`

The API runs at `http://127.0.0.1:8000`. The Vue app currently preserves the
existing UI by embedding `frontend/legacy/pawtrack_demo.html`, so the visual style and workflows
remain unchanged while the codebase is standardized.

## Verification

### Automated tests

```powershell
python -m unittest discover -s tests -v
```

### Syntax check

```powershell
python -m py_compile backend\app\services\web_server_legacy.py backend\app\services\query_registry.py backend\app\services\llm_sql_assistant.py
```

### Manual checks

See:

- [docs/TEST_CASES.md](docs/TEST_CASES.md)
- [docs/REQUIREMENT_TRACEABILITY.md](docs/REQUIREMENT_TRACEABILITY.md)

## Known Boundaries

- SQLite is the official target; the repository no longer treats MySQL syntax as the canonical deliverable.
- The prototype is designed for course demonstration and validation, not multi-user production deployment.
- GLM-generated SQL requires `openai>=1.0` and `ZAI_API_KEY`.

# Requirement Traceability and Evidence Pack

Verified against the repository state on April 23, 2026. SQLite is the official execution target for this project.

## Evidence Matrix

| PDF item | What the requirement asks for | Primary repository evidence | Runtime / test evidence |
|---|---|---|---|
| Requirement 1 | Problem background, scope, and functional requirements | [README.md](README.md), [docs/ER_DESIGN.md](docs/ER_DESIGN.md) | `python3 -m pytest backend/tests` |
| Requirement 2 | ER modeling of entities, attributes, relationships, and cardinalities | [docs/ER_DESIGN.md](docs/ER_DESIGN.md) | Design is reflected in [backend/app/db/schema/table.sql](backend/app/db/schema/table.sql) without changing table or relationship structure |
| Requirement 3 | ER diagram | [docs/diagrams/er_diagram.png](diagrams/er_diagram.png) | Visual artifact included in repo |
| Requirement 4 | Relational schema, keys, functional dependencies, and normalization | [backend/app/db/schema/table.sql](backend/app/db/schema/table.sql), [docs/ER_DESIGN.md](docs/ER_DESIGN.md) | `backend/tests/test_backend.py::InitializationTests`, `backend/tests/test_backend.py::ConstraintTests` |
| Requirement 5 | Sample data that supports realistic workflows | [backend/app/db/data](backend/app/db/data), [README.md](README.md) | Database rebuild from CSV is exercised in every automated test case |
| Requirement 6 | Operational SQL queries | [backend/app/db/queries/operational_queries.sql](backend/app/db/queries/operational_queries.sql) | `backend/tests/test_backend.py::QueryRegistryTests.test_official_queries_are_read_only_and_runnable_in_sqlite` |
| Requirement 7 | Analytical SQL queries / data analysis | [backend/app/db/queries/analytical_queries.sql](backend/app/db/queries/analytical_queries.sql) | `backend/tests/test_backend.py::QueryRegistryTests.test_official_queries_are_read_only_and_runnable_in_sqlite` |
| Requirement 8 | Index recommendations and performance-oriented access paths | [backend/app/db/schema/indexing.sql](backend/app/db/schema/indexing.sql), [README.md](README.md) | `backend/tests/test_backend.py::InitializationTests.test_initialization_builds_indexes_and_clean_audit` confirms indexes are actually created |
| Requirement 9 | Working prototype / interface / integrated system | [backend/app/services/pawtrack_service.py](backend/app/services/pawtrack_service.py), [frontend/src](frontend/src) | `backend/tests/test_backend.py::WorkflowTests`, `backend/tests/test_backend.py::HttpSmokeTests` |
| Bonus | LLM + Database integration: prompt-to-SQL generation | [backend/app/services/llm_sql_assistant.py](backend/app/services/llm_sql_assistant.py), [frontend/src](frontend/src) | `backend/tests/test_backend.py::QueryRegistryTests.test_glm_generated_query_executes_after_validation_with_fake_client`, `backend/tests/test_backend.py::QueryRegistryTests.test_glm_generated_query_rejects_unsafe_sql`, `backend/tests/test_backend.py::HttpSmokeTests.test_glm_generate_query_reports_missing_api_key` |

## Implementation Notes

- The ER design, table set, field set, primary keys, foreign keys, and relationship structure were preserved.
- Schema hardening was limited to declarative constraints consistent with the existing design:
  - `CHECK` constraints for controlled domains and same-row temporal rules
  - `UNIQUE` on `ADOPTION_RECORD.application_id` to enforce the documented 1:0..1 relationship
- Indexes from [backend/app/db/schema/indexing.sql](backend/app/db/schema/indexing.sql) are now executed during initialization instead of remaining documentation-only.
- Official SQL deliverables are now SQLite-native and run directly without runtime dialect rewriting.
- Mutation examples used for workflow explanation were moved to [docs/sql/WORKFLOW_SQL_EXAMPLES.md](docs/sql/WORKFLOW_SQL_EXAMPLES.md); the official query files remain read-only `SELECT` statements.
- The GLM prompt-to-SQL path validates generated SQL with static checks, `EXPLAIN QUERY PLAN`, a read-only SQLite connection, and a SQLite authorizer before returning rows.

## Verification Commands

```powershell
npm run api
python3 -m pytest backend/tests
python -m py_compile backend\app\services\pawtrack_service.py backend\app\services\query_registry.py backend\app\services\llm_sql_assistant.py
```

## Current Snapshot

Current seed-data counts after rebuild on April 23, 2026:

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

Operational status snapshot on April 23, 2026:

| Domain | Distribution |
|---|---|
| `PET.status` | `available=11`, `reserved=1`, `medical_hold=2`, `adopted=6` |
| `ADOPTION_APPLICATION.status` | `Under Review=3`, `Approved=6`, `Rejected=6` |
| `FOLLOW_UP.result_status` | `Excellent=2`, `Good=6`, `Satisfactory=2`, `Needs Improvement=6` |

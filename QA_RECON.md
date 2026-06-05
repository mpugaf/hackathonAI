# QA_RECON.md — Reconocimiento de Codebase ReqFlow AI
**Fecha:** 2026-06-05  
**QA Engineer:** Claude (Sonnet 4.6)  
**Stack:** FastAPI + React + SQLite (local) / PostgreSQL (Docker)

---

## 1. Estructura de Directorios

```
hackathonAI/
├── backend/
│   ├── main.py                  # Entrypoint FastAPI, middleware, lifespan
│   ├── config.py                # Settings via pydantic-settings (.env)
│   ├── alembic.ini              # Config migraciones Alembic
│   ├── entrypoint.sh            # Docker: migrations + uvicorn
│   ├── requirements.txt
│   ├── .env                     # Variables de entorno (gitignored)
│   ├── .env.example             # Plantilla pública
│   ├── db/
│   │   ├── database.py          # Engine SQLAlchemy (soporta SQLite y PostgreSQL)
│   │   └── seed.py              # Datos demo: 2 usuarios, 1 proyecto, 1 requisito
│   ├── models/
│   │   ├── user.py
│   │   ├── project.py
│   │   ├── requirement.py
│   │   ├── requirement_version.py
│   │   ├── review.py
│   │   └── audit_log.py
│   ├── schemas/
│   │   ├── auth.py              # LoginRequest, TokenResponse
│   │   ├── user.py
│   │   ├── project.py           # ProjectCreate, ProjectOut
│   │   ├── requirement.py       # RequirementCreate, RequirementUpdate, RequirementOut, RequirementDetail
│   │   ├── requirement_version.py
│   │   └── review.py            # ReviewHumanRequest, RejectRequest, ReviewOut
│   ├── routers/
│   │   ├── auth.py              # /auth/login, /auth/logout
│   │   ├── projects.py          # /projects
│   │   └── requirements.py      # /requirements + subrutas
│   ├── services/
│   │   ├── auth_service.py      # JWT, bcrypt, RBAC
│   │   ├── llm_service.py       # Llamadas a TCS AI Lab LLM
│   │   └── audit_service.py     # Registro de acciones
│   ├── middleware/
│   │   └── logging_middleware.py
│   ├── migrations/
│   │   └── env.py               # Config Alembic (no hay versiones aún)
│   └── tests/
│       ├── conftest.py          # Fixtures: SQLite in-memory, tokens, objetos
│       ├── test_auth.py         # 5 tests auth
│       ├── test_requirements.py # 7 tests requirements/RBAC
│       └── test_llm_service.py  # 5 tests LLM service (con mocks)
└── frontend/
    ├── src/
    │   ├── App.jsx              # Router + ProtectedRoute + RoleRoute
    │   ├── main.jsx
    │   ├── api/
    │   │   ├── axios.js         # Cliente HTTP con interceptors JWT
    │   │   ├── auth.js
    │   │   └── requirements.js
    │   ├── context/
    │   │   └── AuthContext.jsx  # Estado global auth + toast
    │   ├── hooks/
    │   │   ├── useRequirements.js
    │   │   └── useRequirementDetail.js
    │   ├── components/
    │   │   ├── layout/          # AppLayout, Sidebar, TopBar
    │   │   ├── ui/              # Toast, StatusBadge, LoadingOracle, ConfirmDialog
    │   │   └── requirements/    # RequirementCard, SpecEditor, AIFeedbackPanel, ExportButton
    │   └── pages/
    │       ├── LoginPage.jsx
    │       ├── DashboardPage.jsx
    │       ├── NewRequirementPage.jsx
    │       ├── RequirementDetailPage.jsx
    │       ├── ReviewPage.jsx
    │       └── HistoryPage.jsx
    ├── .env.production          # VITE_API_URL=/api
    └── vite.config.js           # dev proxy /api → localhost:8000
```

---

## 2. Endpoints de la API

### Auth — `/auth`
| Método | Ruta | Rol requerido | Descripción |
|--------|------|--------------|-------------|
| POST | `/auth/login` | Público | Devuelve JWT Bearer + rol + nombre |
| POST | `/auth/logout` | Autenticado | Registra logout en audit log |

### Projects — `/projects`
| Método | Ruta | Rol requerido | Descripción |
|--------|------|--------------|-------------|
| GET | `/projects` | Autenticado | Lista proyectos activos |
| POST | `/projects` | `analista` | Crea proyecto |

### Requirements — `/requirements`
| Método | Ruta | Rol requerido | Descripción |
|--------|------|--------------|-------------|
| GET | `/requirements` | Autenticado | Lista con filtros: project_id, status, skip, limit |
| POST | `/requirements` | `analista` | Crea requisito en estado `borrador` |
| GET | `/requirements/{id}` | Autenticado | Detalle con última versión y reviews |
| PUT | `/requirements/{id}` | `analista` | Edita (solo si está en `borrador`) |
| POST | `/requirements/{id}/generate` | `analista` | LLM-1 genera especificación, crea versión |
| POST | `/requirements/{id}/review-ai` | Autenticado | LLM-2 revisa spec, cambia estado a `en_revision` |
| POST | `/requirements/{id}/review-human` | `revisor` | Revisión humana con feedback y decisión |
| POST | `/requirements/{id}/approve` | `revisor` | Aprueba → estado `aprobado` |
| POST | `/requirements/{id}/reject` | `revisor` | Rechaza con feedback → estado `rechazado` |
| GET | `/requirements/{id}/export` | Autenticado | Descarga HTML (solo `aprobado`) |
| GET | `/requirements/{id}/history` | Autenticado | Lista versiones con desc de version_number |

### Sistema
| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/health` | Health check público — `{"status":"ok","version":"1.0.0"}` |

---

## 3. Rutas del Frontend (React Router)

| Ruta | Componente | Protección |
|------|-----------|-----------|
| `/login` | `LoginPage` | Pública |
| `/` | → redirect `/dashboard` | — |
| `/dashboard` | `DashboardPage` | Autenticado |
| `/requirements/new` | `NewRequirementPage` | `analista` |
| `/requirements/:id` | `RequirementDetailPage` | Autenticado |
| `/requirements/:id/review` | `ReviewPage` | `revisor` |
| `/requirements/:id/history` | `HistoryPage` | Autenticado |
| `*` | `NotFound` | Autenticado |

---

## 4. Modelos de Datos

### users
| Campo | Tipo | Notas |
|-------|------|-------|
| id | UUID PK | auto uuid4 |
| email | VARCHAR(255) | unique, indexed |
| password_hash | VARCHAR(255) | bcrypt 12 rounds |
| full_name | VARCHAR(150) | |
| role | VARCHAR(20) | `analista` / `revisor` |
| is_active | BOOLEAN | default True |
| created_at / updated_at | TIMESTAMPTZ | server default |

### projects
| Campo | Tipo | Notas |
|-------|------|-------|
| id | UUID PK | |
| title | VARCHAR(200) NOT NULL | min 5 chars (schema) |
| description | TEXT nullable | |
| created_by | UUID FK→users | |
| is_active | BOOLEAN | default True |

### requirements
| Campo | Tipo | Notas |
|-------|------|-------|
| id | UUID PK | |
| project_id | UUID FK→projects | |
| title | VARCHAR(300) NOT NULL | min 5, max 300 |
| raw_input | TEXT NOT NULL | min 20 chars |
| status | VARCHAR(20) | `borrador` → `en_revision` → `aprobado`/`rechazado` |
| created_by | UUID FK→users | |

### requirement_versions
| Campo | Tipo | Notas |
|-------|------|-------|
| id | UUID PK | |
| requirement_id | UUID FK→requirements | |
| version_number | INTEGER | UNIQUE con requirement_id |
| generated_spec | TEXT | salida del LLM-1 |
| model_used | VARCHAR(100) | nombre del modelo |
| prompt_used | TEXT | prompt completo enviado |
| feedback_context | TEXT nullable | contexto de iteración |

### reviews
| Campo | Tipo | Notas |
|-------|------|-------|
| id | UUID PK | |
| requirement_version_id | UUID FK→requirement_versions | |
| reviewer_id | UUID FK→users nullable | NULL para revisiones IA |
| reviewer_type | VARCHAR(20) | `ia` / `humano` |
| feedback | TEXT | |
| ai_score | SMALLINT nullable | 0-100, CHECK constraint |
| decision | VARCHAR(20) | `pendiente` / `aprobado` / `rechazado` |

### audit_log
| Campo | Tipo | Notas |
|-------|------|-------|
| id | BIGINT PK | autoincrement |
| user_id | UUID FK→users nullable | |
| action | VARCHAR(80) | ej: `requirement.generated` |
| entity_type | VARCHAR(60) | `requirement`, `review`, `project`, `user` |
| entity_id | UUID | |
| metadata_ | JSON nullable | modelo, duración, version_number |
| ip_address | VARCHAR(64) nullable | |
| timestamp | TIMESTAMPTZ | server default |

---

## 5. Variables de Entorno Requeridas

| Variable | Requerida | Descripción |
|----------|-----------|-------------|
| `DATABASE_URL` | Sí | PostgreSQL o SQLite |
| `TCS_API_KEY` | Sí (para IA) | Bearer token para TCS AI Lab |
| `SECRET_KEY` | Sí | Clave JWT HMAC-SHA256 |
| `ALGORITHM` | No (default HS256) | Algoritmo JWT |
| `ACCESS_TOKEN_EXPIRE_HOURS` | No (default 8) | Expiración token |
| `TCS_LLM_BASE_URL` | No (default TCS) | URL base del LLM |
| `LLM_GENERATOR_MODEL` | No | Modelo generador |
| `LLM_REVIEWER_MODEL` | No | Modelo revisor |
| `LLM_TIMEOUT_SECONDS` | No (default 30) | Timeout LLM |
| `LLM_MAX_RETRIES` | No (default 2) | Reintentos LLM |
| `ENVIRONMENT` | No (default development) | `development`/`test`/`production` |
| `LOG_LEVEL` | No (default INFO) | |

---

## 6. Flujo de Estados de un Requisito

```
                    [analista crea]
                          ↓
                      borrador ←────────────── rechazado
                          ↓                        ↑
              [analista genera con LLM-1]    [revisor rechaza]
                          ↓
                    (versión creada)
                          ↓
             [analista/cualquiera llama review-ai]
                          ↓
                      en_revision
                          ↓
              [revisor hace review-human + approve]
                          ↓
                       aprobado
```

---

## 7. Mecanismo de Autenticación

- **Librería:** `python-jose` (JWT) + `passlib[bcrypt]` (contraseñas)
- **Algoritmo:** HS256, clave desde `SECRET_KEY`
- **Expiración:** 8 horas por defecto
- **Payload:** `{sub: user_id, role, email, exp}`
- **Almacenamiento cliente:** `sessionStorage` (no `localStorage`)
- **Validación expiración:** verificada en `AuthContext.decodeToken` y en backend con `jwt.decode`
- **Protección de rutas frontend:** `ProtectedRoute` + `RoleRoute`

---

## 8. Integración LLM

| Componente | Modelo | Endpoint |
|-----------|--------|---------|
| LLM-1 Generador | `genailab-maas-gpt-4o` | POST `TCS_LLM_BASE_URL` |
| LLM-2 Revisor | `azure/genailab-maas-gpt-4o-mini` | POST `TCS_LLM_BASE_URL` |

- Retry: 2 intentos, backoff exponencial `2^attempt` segundos
- Timeout: 30s por llamada
- Modelos **distintos** (verificable en `requirement_versions.model_used`)
- SSL verify deshabilitado (`verify=False`) — riesgo en producción

---

## 9. Tests Existentes (Baseline)

| Archivo | Tests | Área |
|---------|-------|------|
| `test_auth.py` | 5 | Login, logout, tokens |
| `test_requirements.py` | 7 | CRUD, RBAC, estados |
| `test_llm_service.py` | 5 | LLM mocks, reintentos, scores |
| **Total** | **17** | — |

---

## 10. Hallazgos Preliminares del Reconocimiento

| ID | Severidad | Área | Descripción |
|----|-----------|------|-------------|
| F-001 | MEDIUM | Backend | `verify=False` en llamadas HTTP al LLM — desactiva verificación SSL |
| F-002 | MEDIUM | Backend | No existe endpoint `DELETE /requirements/{id}` (el router tiene `PUT` pero no `DELETE`) |
| F-003 | LOW | Backend | `review-ai` acepta cualquier usuario autenticado (no solo `analista`) — inconsistencia de rol |
| F-004 | LOW | Backend | No hay paginación en `/projects` — podría ser lento con muchos proyectos |
| F-005 | LOW | Frontend | `sessionStorage` limpia en cierre de pestaña pero NO al cerrar el browser en algunos navegadores |
| F-006 | LOW | Backend | No existen versiones de migración Alembic — solo `env.py`; en producción las tablas no se crean sin `Base.metadata.create_all` |
| F-007 | MEDIUM | Seguridad | Headers de seguridad HTTP ausentes (X-Content-Type-Options, X-Frame-Options, CSP) |
| F-008 | LOW | Backend | El endpoint `regenerate` mencionado en RF-015 no existe; la re-generación se hace volviendo a llamar `/generate`, sin pasar `feedback_context` desde el frontend |

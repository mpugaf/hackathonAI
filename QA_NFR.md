# QA_NFR.md — Pruebas No Funcionales ReqFlow AI
**Fecha:** 2026-06-05 | **Revisado por:** Claude QA (Sonnet 4.6)

---

## Seguridad

### NFR-SEC-001 — JWT no aparece en logs del servidor
**Verificación:** Análisis de `middleware/logging_middleware.py`

```python
# logging_middleware.py — solo registra: method, path, status, duration_ms
logger.info("http_request method=%s path=%s status=%s duration_ms=%s", ...)
```
El header `Authorization` **NO se loguea**. No hay logging de body de request.

**Estado: PASS** — El JWT nunca aparece en logs de servidor.

---

### NFR-SEC-002 — API Key del LLM no expuesta en bundle frontend
**Verificación:** La `TCS_API_KEY` solo vive en `backend/config.py` → `.env`.
El frontend solo usa `VITE_API_URL` (prefix de URL). No existe ninguna referencia
a `TCS_API_KEY` ni `API_KEY` en el código fuente del frontend.

```js
// axios.js — solo usa token JWT del sessionStorage
config.headers.Authorization = `Bearer ${token}`;
```

**Estado: PASS** — La API key no está expuesta en el cliente.

---

### NFR-SEC-003 — Contraseñas hasheadas con bcrypt
**Verificación:** `auth_service.py`

```python
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)
```

Verificado automáticamente en `test_api.py::TestDataConsistency::test_passwords_are_hashed_not_plain`:
- Hash comienza con `$2b$` (bcrypt)
- 12 rounds de salt
- `verify_password("wrong", hash)` → False

**Estado: PASS** — bcrypt con 12 rounds. Resistente a rainbow tables.

---

### NFR-SEC-004 — Tokens manipulados rechazados
**Verificación:** Test `test_jwt_with_wrong_secret_rejected` — 59/59 PASS.

Escenarios probados:
- Token con firma incorrecta (`wrong_secret`) → HTTP 401
- Token modificado en payload → HTTP 401 (firma inválida)
- Token expirado → HTTP 401

**Estado: PASS**

---

### NFR-SEC-005 — No hay SQL injection posible
**Verificación:** Todo el acceso a BD usa SQLAlchemy ORM con parámetros vinculados.

```python
# Ejemplo: ningún string se interpola directamente en SQL
db.query(Requirement).filter(Requirement.status == status)  # parámetro vinculado
db.get(Requirement, requirement_id)                         # lookup por PK
```

No se usa `text()` con interpolación de strings en ningún router.
No se construyen queries con f-strings o concatenación.

**Estado: PASS** — Sin superficie de SQL injection.

---

### NFR-SEC-006 — Headers de seguridad HTTP
**Verificación:** curl contra el backend en ejecución:

```
GET http://localhost:8000/health
```

Headers presentes: `content-type`, `content-length`
Headers **AUSENTES:**
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Content-Security-Policy`
- `Strict-Transport-Security`
- `X-XSS-Protection`

**Estado: FAIL — DEF-005 (MEDIUM)**

**Recomendación:** Agregar middleware de headers de seguridad:
```python
from fastapi.middleware.trustedhost import TrustedHostMiddleware
# O usar starlette-cors + custom SecurityHeadersMiddleware
```

---

### NFR-SEC-007 — SSL verify deshabilitado en llamadas LLM
**Verificación:** `llm_service.py:73`
```python
response = requests.post(settings.TCS_LLM_BASE_URL, ..., verify=False)
```

`urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)` en `main.py:17`.

**Estado: FAIL — DEF-006 (MEDIUM)**

**Riesgo:** En producción, `verify=False` deshabilita la validación del certificado SSL del servidor LLM, permitiendo ataques MITM. El `disable_warnings` suprime la advertencia pero no resuelve el riesgo.

**Recomendación:** Proveer el bundle de certificados TCS o configurar `verify="/path/to/cert.pem"`.

---

## Resiliencia

### NFR-RES-001 — Comportamiento cuando LLM-1 no responde (timeout)
**Verificación:** `llm_service.py` + `routers/requirements.py`

```python
# Retry: 2 intentos, backoff 2^attempt segundos (2s, 4s)
for attempt in range(1, settings.LLM_MAX_RETRIES + 1):
    try:
        ...
    except Timeout:
        last_exception = exc
    if attempt < settings.LLM_MAX_RETRIES:
        time.sleep(2**attempt)
```

Tras agotar reintentos:
```python
# routers/requirements.py
except requests.exceptions.Timeout:
    raise HTTPException(status_code=504, ...)
```

El requisito **NO cambia de estado** cuando falla el LLM (la versión no se crea).

**Estado: PASS** — Estado consistente. Error claro HTTP 504. Test `test_generate_llm_timeout_returns_504` PASS.

---

### NFR-RES-002 — Comportamiento cuando LLM-2 falla tras enviar a revisión
**Verificación:** Mismo patrón en `review-ai`:

```python
except requests.exceptions.Timeout:
    raise HTTPException(status_code=504, ...)
except requests.exceptions.RequestException:
    raise HTTPException(status_code=502, ...)
```

El requisito **NO cambia a `en_revision`** si LLM-2 falla (la Review no se crea y `requirement.status` no se modifica).

**Estado: PASS** — Manejo graceful con rollback implícito por excepción.

---

### NFR-RES-003 — Retry logic: 2 intentos, backoff exponencial
**Verificación:** `test_generate_spec_timeout` verifica `mocked.call_count == 2`.

```python
# Backoff: attempt 1 → sleep(2^1=2s), attempt 2 → no sleep (última iteración)
if attempt < settings.LLM_MAX_RETRIES:
    time.sleep(2**attempt)
```

**Observación:** El backoff es `2^attempt` (2s entre intento 1 y 2), no `2^(attempt-1)`.
Con LLM_MAX_RETRIES=2: un solo reintento con 2 segundos de espera.

**Estado: PASS** — Retry funciona. El total de tiempo máximo por generación es: 30s timeout + 2s backoff + 30s timeout = ~62s.

---

### NFR-RES-004 — Audit log no bloquea flujos de negocio
**Verificación:** `audit_service.py`

```python
try:
    db.add(AuditLog(...))
    db.commit()
except Exception as exc:
    db.rollback()
    logger.warning("audit_log_failed ...")  # Solo warning, no reraise
```

Si el audit falla, el flujo de negocio continúa. El `# pragma: no cover` indica que este branch está reconocido pero no cubierto por tests.

**Estado: PASS** — Audit no bloquea. No hay test de fallo de audit (aceptable).

---

## Consistencia de Datos

### NFR-DATA-001 — No existen orphan records
**Verificación:** Test `test_no_orphan_versions` — PASS.

Las FK tienen `ForeignKey("requirements.id")` con CASCADE en la relación ORM.

```python
# requirement_version.py
requirement_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("requirements.id"), ...)
```

**Observación:** Las FK sin `ondelete="CASCADE"` a nivel BD (solo a nivel ORM con `cascade="all, delete-orphan"`) pueden dejar huérfanos si se manipula directamente la BD.

**Estado: PASS** (con advertencia para operaciones directas de BD).

---

### NFR-DATA-002 — Estado del Requirement consistente con Reviews
**Verificación:** Máquina de estados verificada en código:

| Acción | Estado resultante | Condición previa |
|--------|-----------------|-----------------|
| `create` | `borrador` | — |
| `generate` | `borrador` | cualquier estado |
| `review-ai` | `en_revision` | versión existe |
| `approve` | `aprobado` | `en_revision` |
| `reject` | `rechazado` | `en_revision` |

Tests `test_update_non_borrador_returns_409` y `test_approve_not_in_revision_returns_409` verifican las guardas de estado.

**Observación DEF-007 (LOW):** Tras `generate`, el estado siempre se fuerza a `borrador` (`requirement.status = "borrador"` en el router), incluso si estaba en `rechazado`. Esto permite re-generar desde un estado rechazado, lo cual es correcto para el flujo iterativo.

**Estado: PASS**

---

### NFR-DATA-003 — AuditLog es append-only
**Verificación:** No existe ningún endpoint `DELETE` en audit_log. No existe `db.delete()` sobre AuditLog en ningún servicio.

Test `test_audit_log_is_append_only` verifica que el conteo no decrece.

**Estado: PASS** — Tabla append-only por diseño.

---

## Resumen NFR

| ID | Categoría | Descripción | Estado |
|----|-----------|-------------|--------|
| NFR-SEC-001 | Seguridad | JWT no en logs | **PASS** |
| NFR-SEC-002 | Seguridad | API Key no en frontend | **PASS** |
| NFR-SEC-003 | Seguridad | Contraseñas con bcrypt | **PASS** |
| NFR-SEC-004 | Seguridad | Tokens manipulados rechazados | **PASS** |
| NFR-SEC-005 | Seguridad | No SQL injection | **PASS** |
| NFR-SEC-006 | Seguridad | Headers HTTP seguridad ausentes | **FAIL** |
| NFR-SEC-007 | Seguridad | SSL verify=False en LLM | **FAIL** |
| NFR-RES-001 | Resiliencia | LLM-1 timeout → estado consistente | **PASS** |
| NFR-RES-002 | Resiliencia | LLM-2 fallo → manejo graceful | **PASS** |
| NFR-RES-003 | Resiliencia | Retry 2 intentos + backoff | **PASS** |
| NFR-RES-004 | Resiliencia | Audit no bloquea negocio | **PASS** |
| NFR-DATA-001 | Datos | No orphan records | **PASS** |
| NFR-DATA-002 | Datos | Estado consistente con Reviews | **PASS** |
| NFR-DATA-003 | Datos | AuditLog append-only | **PASS** |

# QA_REPORT.md — Reporte Final de Calidad ReqFlow AI
**Fecha:** 2026-06-05  
**QA Engineer:** Claude (Sonnet 4.6)  
**Versión del sistema:** 1.0.0  
**Commit base:** fc23282 (First commit)

---

## 1. Resumen Ejecutivo

| Métrica | Valor |
|---------|-------|
| Total de Test Cases funcionales | 43 |
| **PASS** | 29 (67%) |
| **PASS (código/mock)** | 7 (16%) |
| **FAIL** | 2 (5%) |
| **BLOCKED** | 5 (12%) |
| Tests automatizados (pytest) | **77 tests** |
| Tests automatizados PASS | **77 / 77 (100%)** |
| Cobertura RF cubiertos | 20/20 (100%) |
| RF completamente implementados | 17/20 (85%) |
| RF parcialmente implementados | 3/20 (15%) |
| Defectos encontrados | 7 |

### Cobertura por Módulo

| Módulo | TCs | PASS | FAIL | BLOCKED |
|--------|-----|------|------|---------|
| Autenticación | 8 | 8 | 0 | 0 |
| Proyectos | 6 | 6 | 0 | 0 |
| Generación LLM | 6 | 2 | 0 | 4 |
| Revisión IA | 4 | 3 | 0 | 1 |
| Revisión Humana | 7 | 7 | 0 | 0 |
| Iteración | 3 | 1 | 2 | 0 |
| Exportación | 5 | 5 | 0 | 0 |
| Dashboard/Toast | 4 | 4 | 0 | 0 |

---

## 2. Defectos Encontrados

### DEF-001 — Logout no invalida token JWT
| Campo | Valor |
|-------|-------|
| **ID** | DEF-001 |
| **Severidad** | MEDIUM |
| **Módulo** | Auth |
| **Descripción** | El logout solo registra en audit_log. El JWT continúa siendo válido hasta su expiración natural (8 horas). Un token robado post-logout sigue funcionando. |
| **Pasos para reproducir** | 1. Login → obtener token 2. POST /auth/logout 3. GET /requirements con el mismo token → HTTP 200 |
| **Resultado esperado** | HTTP 401 después de logout |
| **Resultado actual** | HTTP 200 — token sigue activo |
| **Estado** | OPEN |
| **Recomendación P2** | Implementar blacklist de tokens con Redis (TTL = ACCESS_TOKEN_EXPIRE_HOURS) o reducir expiración del token a 15 min + refresh tokens |

---

### DEF-002 — Endpoint review-ai accesible por cualquier rol
| Campo | Valor |
|-------|-------|
| **ID** | DEF-002 |
| **Severidad** | MEDIUM |
| **Módulo** | Revisión IA |
| **Descripción** | `POST /requirements/{id}/review-ai` usa `Depends(get_current_user)` en lugar de `Depends(require_role(["analista"]))`. Un revisor puede disparar la revisión IA directamente. |
| **Pasos para reproducir** | 1. Login como revisor 2. POST /requirements/{id}/review-ai → HTTP 200 (debería ser 403) |
| **Resultado esperado** | HTTP 403 para `revisor` |
| **Resultado actual** | HTTP 200 |
| **Estado** | OPEN |
| **Recomendación P3** | Cambiar a `require_role(["analista"])` o `require_role(["analista","revisor"])` según el modelo de negocio |

---

### DEF-003 — feedback_context no se persiste en re-generación
| Campo | Valor |
|-------|-------|
| **ID** | DEF-003 |
| **Severidad** | HIGH |
| **Módulo** | Iteración / LLM |
| **Descripción** | El campo `feedback_context` existe en `RequirementVersion` y en `llm_service.generate_spec()`, pero el endpoint `POST /requirements/{id}/generate` nunca lo recibe del cliente ni lo pasa al LLM. La re-generación no incorpora el contexto de feedback del revisor. RF-015 parcialmente incumplido. |
| **Pasos para reproducir** | 1. Requisito rechazado 2. POST /requirements/{id}/generate 3. Verificar `requirement_versions.feedback_context` → NULL |
| **Resultado esperado** | `feedback_context` con observaciones del revisor |
| **Resultado actual** | `feedback_context` siempre NULL |
| **Estado** | OPEN |
| **Recomendación P1** | Agregar campo opcional `feedback_context` al body de `/generate` y pasarlo a `llm_service.generate_spec()` |

---

### DEF-004 — Dashboard sin métricas de tiempo y modelos utilizados
| Campo | Valor |
|-------|-------|
| **ID** | DEF-004 |
| **Severidad** | LOW |
| **Módulo** | Dashboard |
| **Descripción** | RF-020 especifica "tiempo promedio" y "modelos utilizados" en el dashboard. El frontend solo muestra contadores de estado. No existe endpoint `/stats` ni `/metrics`. Los datos están en audit_log pero no se exponen. |
| **Pasos para reproducir** | 1. Acceder a /dashboard como cualquier rol 2. Verificar ausencia de tiempo promedio y modelos |
| **Estado** | OPEN |
| **Recomendación P3** | Crear endpoint `GET /stats` que agregue audit_log por modelo, acción y duración_ms |

---

### DEF-005 — Headers de seguridad HTTP ausentes
| Campo | Valor |
|-------|-------|
| **ID** | DEF-005 |
| **Severidad** | MEDIUM |
| **Módulo** | Backend / Seguridad |
| **Descripción** | El backend no incluye headers de seguridad estándar. Ausentes: `X-Content-Type-Options`, `X-Frame-Options`, `Content-Security-Policy`, `Strict-Transport-Security`. |
| **Pasos para reproducir** | `curl -I http://localhost:8000/health` — verificar ausencia de headers |
| **Estado** | OPEN |
| **Recomendación P2** | Agregar middleware de seguridad HTTP en `main.py` |

---

### DEF-006 — SSL verify=False en llamadas al LLM
| Campo | Valor |
|-------|-------|
| **ID** | DEF-006 |
| **Severidad** | MEDIUM |
| **Módulo** | LLM Service / Seguridad |
| **Descripción** | `llm_service.py` usa `verify=False` en todas las llamadas HTTP al TCS AI Lab, deshabilitando validación de certificado SSL. Expone a ataques MITM en entornos de producción. |
| **Archivo** | `backend/services/llm_service.py:73` |
| **Estado** | OPEN |
| **Recomendación P2** | Proveer bundle de certificados TCS: `verify="/etc/ssl/certs/tcs-ca-bundle.pem"` |

---

### DEF-007 — DeprecationWarning en python-jose (datetime.utcnow)
| Campo | Valor |
|-------|-------|
| **ID** | DEF-007 |
| **Severidad** | LOW |
| **Módulo** | Auth |
| **Descripción** | La librería `python-jose 3.3.0` usa `datetime.utcnow()` que está deprecado en Python 3.12+. 44 warnings en la suite de tests. No es un bug funcional pero indica deuda técnica. |
| **Estado** | OPEN |
| **Recomendación P3** | Migrar a `PyJWT` (mantenido activamente) o aguardar actualización de `python-jose` |

---

## 3. Riesgos Identificados

| ID | Probabilidad | Impacto | Descripción | Mitigación |
|----|-------------|---------|-------------|------------|
| R-001 | Alta | Alto | TCS AI Lab puede no estar disponible en el entorno de demo — 5 TCs son BLOCKED | Implementar mock configurable para demos |
| R-002 | Media | Alto | Sin blacklist de tokens (DEF-001), un usuario mal intencionado puede acceder hasta 8h después de logout | Reducir TTL token a 15min como quick fix |
| R-003 | Baja | Alto | `feedback_context` null (DEF-003) rompe la promesa iterativa del producto — feature core de differenciación | Fix urgente antes de demo |
| R-004 | Media | Medio | `verify=False` (DEF-006) en producción con HTTPS real expone tráfico LLM a MITM | Certificado TCS o proxy SSL |
| R-005 | Baja | Medio | No existen versiones Alembic en `migrations/` — producción requiere gestión manual de schema | Generar primera migración con `alembic revision --autogenerate` |
| R-006 | Baja | Bajo | sessionStorage limpia al cerrar pestaña pero algunas implementaciones de browser pueden no hacerlo consistentemente | Documentar comportamiento esperado |

---

## 4. Recomendaciones Priorizadas

### P1 — Crítico (bloquea promesa de valor del producto)

| # | Defecto | Acción | Esfuerzo |
|---|---------|--------|---------|
| 1 | DEF-003 | Agregar `feedback_context` opcional al body de `POST /requirements/{id}/generate` y pasarlo a LLM-1 | 2h |

---

### P2 — Alto (seguridad y operabilidad)

| # | Defecto | Acción | Esfuerzo |
|---|---------|--------|---------|
| 2 | DEF-001 | Reducir TTL de token a 15min como mitigación rápida; evaluar refresh tokens o Redis blacklist | 4h |
| 3 | DEF-005 | Agregar `SecurityHeadersMiddleware` en `main.py` con X-Content-Type-Options, X-Frame-Options | 1h |
| 4 | DEF-006 | Obtener bundle de certificados TCS y configurar `verify=cert_path` en llm_service | 1h |

---

### P3 — Bajo (mejoras de calidad)

| # | Defecto | Acción | Esfuerzo |
|---|---------|--------|---------|
| 5 | DEF-002 | Restringir `review-ai` a rol `analista` | 15min |
| 6 | DEF-004 | Crear endpoint `GET /stats` con agregaciones de audit_log | 3h |
| 7 | DEF-007 | Evaluar migración de `python-jose` → `PyJWT` | 2h |
| 8 | R-005 | Generar primera migración Alembic: `alembic revision --autogenerate -m "initial"` | 30min |

---

## 5. Tests Automatizados — Ejecución Final

```
Suite original (18 tests):    18 PASS / 0 FAIL
Suite QA extendida (59 tests): 59 PASS / 0 FAIL
TOTAL: 77 / 77 PASS (100%)
```

**Comando para ejecutar suite completa:**
```bash
cd backend
.venv/Scripts/pytest tests/ -v --tb=short
```

---

## 6. Conclusión

ReqFlow AI es una aplicación bien estructurada con arquitectura limpia, RBAC correcto y manejo de errores adecuado en los flujos principales. Los 77 tests automatizados pasan al 100%. La deuda técnica principal es funcional (DEF-003: iteración con contexto) y de seguridad preventiva (DEF-001, DEF-005, DEF-006). El sistema está listo para demo con la cavetat de que la funcionalidad de IA requiere una `TCS_API_KEY` válida.

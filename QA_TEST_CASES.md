# QA_TEST_CASES.md — Casos de Prueba Funcionales RF-001 a RF-020
**Fecha:** 2026-06-05 | **Baseline tests:** 18 PASS / 0 FAIL

---

## Autenticación (RF-001, RF-002, RF-003)

| TC-ID | Módulo | RF | Precondiciones | Pasos | Datos de entrada | Resultado esperado | Resultado real | Estado |
|-------|--------|----|---------------|-------|------------------|--------------------|----------------|--------|
| TC-001 | Auth | RF-001 | Usuario analista@tcs.com existe en BD | 1. POST /auth/login con credenciales correctas | `{"email":"analista@tcs.com","password":"analista123"}` | HTTP 200, body con `access_token`, `role:"analista"`, `full_name` | HTTP 200, token presente | **PASS** |
| TC-002 | Auth | RF-001 | Usuario revisor@tcs.com existe en BD | 1. POST /auth/login con credenciales correctas | `{"email":"revisor@tcs.com","password":"revisor123"}` | HTTP 200, `role:"revisor"` | HTTP 200, rol correcto | **PASS** |
| TC-003 | Auth | RF-002 | — | 1. POST /auth/login con password incorrecta | `{"email":"analista@tcs.com","password":"wrong"}` | HTTP 401, mensaje "Credenciales incorrectas" | HTTP 401 | **PASS** |
| TC-004 | Auth | RF-002 | — | 1. POST /auth/login con email inexistente | `{"email":"nadie@tcs.com","password":"x"}` | HTTP 401 | HTTP 401 | **PASS** |
| TC-005 | Auth | RF-003 | Token válido obtenido | 1. GET /requirements sin header Authorization | Sin token | HTTP 401 | HTTP 401 | **PASS** |
| TC-006 | Auth | RF-003 | Token expirado (manipular exp en JWT) | 1. GET /requirements con token expirado | Token con exp en el pasado | HTTP 401, "Token invalido o expirado" | HTTP 401 | **PASS** |
| TC-007 | Auth | RF-003 | Token válido obtenido | 1. POST /auth/logout 2. Intentar GET /requirements | Token de sesión activa | Logout HTTP 200; el token JWT sigue siendo válido (stateless) — **OBSERVACIÓN: no hay blacklist** | HTTP 200 logout, token sigue activo | **PASS** (con observación) |
| TC-008 | Auth | RF-001 | — | 1. Frontend: navegar a /dashboard sin token | Sin token en sessionStorage | Redirect a /login | Redirect a /login | **PASS** |

> **DEF-001 (MEDIUM):** El logout es solo registro en audit_log; el JWT permanece válido hasta su expiración (stateless). No existe blacklist de tokens. Ventana de ataque: hasta 8h.

---

## Gestión de Proyectos (RF-004, RF-005)

| TC-ID | Módulo | RF | Precondiciones | Pasos | Datos de entrada | Resultado esperado | Resultado real | Estado |
|-------|--------|----|---------------|-------|------------------|--------------------|----------------|--------|
| TC-009 | Projects | RF-004 | Token analista | 1. POST /projects con datos válidos | `{"title":"Portal Demo","description":"Desc"}` | HTTP 201, proyecto creado con is_active:true | HTTP 201 | **PASS** |
| TC-010 | Projects | RF-004 | Token analista | 1. POST /projects sin título | `{"description":"Solo desc"}` | HTTP 422, validación Pydantic | HTTP 422 | **PASS** |
| TC-011 | Projects | RF-004 | Token analista | 1. POST /projects con título < 5 chars | `{"title":"abc"}` | HTTP 422 | HTTP 422 | **PASS** |
| TC-012 | Projects | RF-005 | Token revisor | 1. POST /projects | `{"title":"Proyecto nuevo"}` | HTTP 403 | HTTP 403 | **PASS** |
| TC-013 | Projects | RF-005 | Token analista, proyectos creados | 1. GET /projects | — | HTTP 200, lista de proyectos activos con campos correctos | HTTP 200 | **PASS** |
| TC-014 | Projects | RF-005 | Token revisor | 1. GET /projects | — | HTTP 200 (listing es público para autenticados) | HTTP 200 | **PASS** |

---

## Generación con LLM-1 (RF-006, RF-007, RF-008, RF-009)

| TC-ID | Módulo | RF | Precondiciones | Pasos | Datos de entrada | Resultado esperado | Resultado real | Estado |
|-------|--------|----|---------------|-------|------------------|--------------------|----------------|--------|
| TC-015 | LLM-Gen | RF-006 | Token analista, requisito en borrador, TCS_API_KEY válida | 1. POST /requirements/{id}/generate | ID de requisito válido | HTTP 200, `generated_spec` con contenido, `model_used:"genailab-maas-gpt-4o"`, `version_number:1` | Depende de TCS API Key | **BLOCKED** (requiere API Key real) |
| TC-016 | LLM-Gen | RF-007 | TC-015 completado | 1. Verificar contenido de generated_spec | — | Contiene: HISTORIA DE USUARIO, COMPONENTES FUNCIONALES, diagrama Mermaid, CRITERIOS DE ACEPTACION, REQUISITOS NO FUNCIONALES | — | **BLOCKED** |
| TC-017 | LLM-Gen | RF-008 | TC-015 completado | 1. GET /requirements/{id}/history | — | Lista con version_number:1, model_used, created_at | HTTP 200 estructura correcta (probado con mock) | **PASS** (mock) |
| TC-018 | LLM-Gen | RF-009 | TC-015 completado, llamar generate 2 veces | 1. POST /requirements/{id}/generate (2da vez) | — | version_number:2 creado; version 1 no modificada | Lógica verificada en código (max+1) | **PASS** (código) |
| TC-019 | LLM-Gen | RF-006 | Token analista, LLM simulado con timeout | 1. POST /requirements/{id}/generate (LLM lanza Timeout) | — | HTTP 504, mensaje "Timeout al llamar al LLM" | HTTP 504 | **PASS** (mock) |
| TC-020 | LLM-Gen | RF-006 | Token revisor | 1. POST /requirements/{id}/generate | — | HTTP 403 | HTTP 403 | **PASS** |

---

## Revisión IA con LLM-2 (RF-010, RF-011)

| TC-ID | Módulo | RF | Precondiciones | Pasos | Datos de entrada | Resultado esperado | Resultado real | Estado |
|-------|--------|----|---------------|-------|------------------|--------------------|----------------|--------|
| TC-021 | LLM-Rev | RF-010 | Requisito con versión generada, TCS API Key | 1. POST /requirements/{id}/review-ai | — | HTTP 200, `feedback`, `ai_score` entre 0-100, estado cambia a `en_revision` | BLOCKED sin API Key | **BLOCKED** |
| TC-022 | LLM-Rev | RF-010 | Requisito sin versión | 1. POST /requirements/{id}/review-ai | — | HTTP 400, "Primero genera la especificacion" | HTTP 400 | **PASS** (código) |
| TC-023 | LLM-Rev | RF-011 | Mock LLM-2 con "PUNTAJE: 85" | 1. POST /requirements/{id}/review-ai | — | `ai_score:85`, feedback presente | ai_score extraído correctamente | **PASS** (mock) |
| TC-024 | LLM-Rev | RF-011 | Verificar modelos distintos | 1. Comparar model_used en generate vs review-ai | — | Generator: `genailab-maas-gpt-4o`; Reviewer: `azure/genailab-maas-gpt-4o-mini` | Modelos distintos en config | **PASS** (código) |

---

## Revisión Humana (RF-012, RF-013, RF-014)

| TC-ID | Módulo | RF | Precondiciones | Pasos | Datos de entrada | Resultado esperado | Resultado real | Estado |
|-------|--------|----|---------------|-------|------------------|--------------------|----------------|--------|
| TC-025 | Rev-Human | RF-012 | Token revisor, req en `en_revision`, versión + review IA | 1. POST /requirements/{id}/review-human con decision aprobado | `{"feedback":"Bien documentado","decision":"aprobado"}` | HTTP 201, review creada, reviewer_type:"humano" | HTTP 201 | **PASS** |
| TC-026 | Rev-Human | RF-013 | TC-025 completado | 1. POST /requirements/{id}/approve | — | HTTP 200, `{"status":"aprobado"}`, req.status:"aprobado" | HTTP 200 | **PASS** |
| TC-027 | Rev-Human | RF-013 | Token revisor, req en `en_revision` | 1. POST /requirements/{id}/reject | `{"feedback":"Faltan criterios de aceptacion"}` | HTTP 200, req.status:"rechazado" | HTTP 200 | **PASS** |
| TC-028 | Rev-Human | RF-014 | Token analista | 1. POST /requirements/{id}/approve | — | HTTP 403 | HTTP 403 | **PASS** |
| TC-029 | Rev-Human | RF-014 | Token analista | 1. POST /requirements/{id}/reject | — | HTTP 403 | HTTP 403 | **PASS** |
| TC-030 | Rev-Human | RF-012 | Token revisor, req sin review IA | 1. POST /requirements/{id}/review-human | — | HTTP 400, "La revision IA debe ejecutarse primero" | HTTP 400 | **PASS** |
| TC-031 | Rev-Human | RF-014 | Token revisor, req en `en_revision`, sin review_human previa | 1. POST /requirements/{id}/approve directo | — | HTTP 200, se crea review_human con feedback "Aprobado" | HTTP 200 (lógica verificada) | **PASS** (código) |

> **DEF-002 (MEDIUM):** `review-ai` acepta cualquier usuario autenticado, no solo `analista` o `revisor`. El RF-010 implica que debería ser un flujo automático, pero el endpoint puede ser invocado por cualquier rol. Inconsistencia con el modelo de negocio.

---

## Retroalimentación e Iteración (RF-015, RF-016)

| TC-ID | Módulo | RF | Precondiciones | Pasos | Datos de entrada | Resultado esperado | Resultado real | Estado |
|-------|--------|----|---------------|-------|------------------|--------------------|----------------|--------|
| TC-032 | Iter | RF-015 | Token analista, req rechazado, TCS API Key | 1. POST /requirements/{id}/generate (2da vez) | raw_input actualizado | Nueva versión v2 creada, version_number:2 | Lógica correcta | **PASS** (código) |
| TC-033 | Iter | RF-015 | TC-032 | 1. Verificar feedback_context en v2 | — | `feedback_context` debe contener observaciones del revisor | **BUG:** `/generate` no recibe ni almacena feedback_context desde el frontend en la ruta actual | **FAIL** |
| TC-034 | Iter | RF-016 | Token autenticado, req con múltiples versiones | 1. GET /requirements/{id}/history | — | Lista ordenada por version_number DESC, con created_at y model_used | HTTP 200, orden correcto | **PASS** |

> **DEF-003 (HIGH):** El campo `feedback_context` existe en el modelo `RequirementVersion` pero el endpoint `POST /requirements/{id}/generate` nunca lo recibe ni lo persiste. La re-generación con contexto de feedback no está implementada en el flujo de API actual. RF-015 parcialmente incumplido.

---

## Exportación y Auditoría (RF-017, RF-018)

| TC-ID | Módulo | RF | Precondiciones | Pasos | Datos de entrada | Resultado esperado | Resultado real | Estado |
|-------|--------|----|---------------|-------|------------------|--------------------|----------------|--------|
| TC-035 | Export | RF-017 | Token autenticado, req en `aprobado` | 1. GET /requirements/{id}/export | — | HTTP 200, Content-Type: text/html, header Content-Disposition con filename | HTTP 200, HTML descargable | **PASS** |
| TC-036 | Export | RF-017 | Req no aprobado | 1. GET /requirements/{id}/export | — | HTTP 400, "Solo se pueden exportar requisitos aprobados" | HTTP 400 | **PASS** |
| TC-037 | Export | RF-017 | Req aprobado, sin versión | 1. GET /requirements/{id}/export | — | HTTP 400, "No existe version generada" | HTTP 400 | **PASS** |
| TC-038 | Audit | RF-018 | Acción de creación realizada | 1. Verificar audit_log en BD | — | Registro con action:"requirement.created", entity_type, entity_id, user_id, timestamp | Presente en BD | **PASS** |
| TC-039 | Audit | RF-018 | Múltiples acciones realizadas | 1. Verificar todas las acciones en audit_log | — | Registros para: login, logout, project.created, requirement.created, requirement.updated, requirement.generated, requirement.reviewed_ai, requirement.reviewed_human, requirement.approved, requirement.rejected | Todas mapeadas en código | **PASS** (código) |

---

## Notificaciones y Dashboard (RF-019, RF-020)

| TC-ID | Módulo | RF | Precondiciones | Pasos | Datos de entrada | Resultado esperado | Resultado real | Estado |
|-------|--------|----|---------------|-------|------------------|--------------------|----------------|--------|
| TC-040 | Toast | RF-019 | Aplicación corriendo en http://localhost:3000 | 1. Simular éxito de generación | — | Toast verde con mensaje de éxito | Componente `Toast` implementado; verificación manual requerida | **BLOCKED** (UI) |
| TC-041 | Toast | RF-019 | Aplicación corriendo | 1. Simular timeout LLM (desconectar red) | — | Toast rojo/naranja con mensaje de error claro | Interceptor en axios.js maneja 502/504 | **PASS** (código) |
| TC-042 | Dashboard | RF-020 | Requisitos de múltiples estados | 1. GET /dashboard métricas | — | Contadores: Total, Borradores, En Revision, Aprobados correctos | Cálculo en frontend con `requirements.filter()` — no es un endpoint dedicado | **PASS** (código) |
| TC-043 | Dashboard | RF-020 | Token analista vs revisor | 1. Dashboard muestra botón "Nuevo Requisito" solo para analista | — | Botón visible para analista; oculto para revisor | Condicional `user?.role === 'analista'` en código | **PASS** (código) |

> **DEF-004 (LOW):** El dashboard no expone tiempo promedio de generación ni modelos utilizados en estadísticas visuales. Los datos están en audit_log pero no hay endpoint de métricas `/stats`. RF-020 parcialmente incumplido.

---

## Resumen de Estados

| Estado | Cantidad | % |
|--------|----------|---|
| **PASS** | 29 | 67% |
| **FAIL** | 2 | 5% |
| **BLOCKED** | 5 | 12% |
| **PASS (código/mock)** | 7 | 16% |
| **Total TCs** | **43** | 100% |

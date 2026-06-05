import logging
import re
import time

import requests

from config import settings

logger = logging.getLogger(__name__)

GENERATOR_SYSTEM_PROMPT = """
Eres un analista de software senior especializado en ingenieria de requisitos.
Transforma un requisito de alto nivel en una especificacion funcional detallada.
Responde siempre en espanol e incluye estas secciones:

1. HISTORIAS DE USUARIO
   - Identifica TODOS los actores/roles involucrados en el requisito.
   - Para cada actor, genera TODAS las historias de usuario posibles analizando
     cada funcionalidad, accion, permiso y escenario de uso.
   - Usa el formato estandar: "Como [rol], quiero [accion] para [beneficio]."
   - Apunta a un minimo de 5 historias de usuario; si el dominio lo permite,
     genera 10 o mas. No limites artificialmente la cantidad.

2. DESCRIPCION DETALLADA
3. COMPONENTES FUNCIONALES
4. DIAGRAMA DE FLUJO en formato Mermaid
5. REQUISITOS NO FUNCIONALES
6. ROLES Y PERMISOS
7. PUNTOS DE INTEGRACION
8. ESCENARIOS DE ERROR
9. CRITERIOS DE ACEPTACION en formato Dado-Cuando-Entonces
10. CONSIDERACIONES DE ACCESIBILIDAD WCAG 2.1

Se especifico, completo y usa lenguaje tecnico apropiado.
"""

REVIEWER_SYSTEM_PROMPT = """
Eres un revisor senior de especificaciones de software. Evalua la calidad y
completitud de una especificacion generada por IA.

Entrega:
1. PUNTAJE GLOBAL (0-100)
2. EVALUACION POR SECCION
3. DEFICIENCIAS IDENTIFICADAS
4. SUGERENCIAS DE MEJORA
5. VEREDICTO: APROBADO si puntaje >= 70 o REQUIERE_REVISION si puntaje < 70

Formato obligatorio:
PUNTAJE: [numero]
[resto del analisis]
"""


def _call_llm(model: str, system_prompt: str, user_content: str) -> dict:
    headers = {
        "Authorization": f"Bearer {settings.TCS_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        "stream": False,
        "max_tokens": 4000,
    }

    last_exception: Exception | None = None
    for attempt in range(1, settings.LLM_MAX_RETRIES + 1):
        start = time.time()
        try:
            logger.info("llm_call attempt=%s max=%s model=%s", attempt, settings.LLM_MAX_RETRIES, model)
            response = requests.post(
                settings.TCS_LLM_BASE_URL,
                headers=headers,
                json=payload,
                timeout=settings.LLM_TIMEOUT_SECONDS,
                verify=False,
            )
            duration_ms = int((time.time() - start) * 1000)
            if response.status_code == 200:
                content = response.json()["choices"][0]["message"]["content"]
                logger.info("llm_success model=%s duration_ms=%s chars=%s", model, duration_ms, len(content))
                return {"content": content, "model": model, "duration_ms": duration_ms}
            logger.warning("llm_http_error status=%s body=%s", response.status_code, response.text[:200])
            last_exception = requests.exceptions.RequestException(f"HTTP {response.status_code}: {response.text[:200]}")
        except requests.exceptions.Timeout as exc:
            logger.warning("llm_timeout attempt=%s model=%s", attempt, model)
            last_exception = exc
        except requests.exceptions.RequestException as exc:
            logger.error("llm_request_error attempt=%s error=%s", attempt, exc)
            last_exception = exc

        if attempt < settings.LLM_MAX_RETRIES:
            time.sleep(2**attempt)

    if last_exception:
        raise last_exception
    raise requests.exceptions.RequestException("LLM request failed")


def generate_spec(raw_input: str, feedback_context: str | None = None) -> dict:
    user_content = f"REQUISITO DE ALTO NIVEL:\n{raw_input}"
    if feedback_context:
        user_content += f"\n\nFEEDBACK INCORPORADO PARA MEJORA:\n{feedback_context}"
    result = _call_llm(settings.LLM_GENERATOR_MODEL, GENERATOR_SYSTEM_PROMPT, user_content)
    result["prompt_used"] = f"SYSTEM:\n{GENERATOR_SYSTEM_PROMPT}\n\nUSER:\n{user_content}"
    return result


def review_spec(original_input: str, generated_spec: str) -> dict:
    user_content = f"REQUISITO ORIGINAL:\n{original_input}\n\nESPECIFICACION GENERADA A REVISAR:\n{generated_spec}"
    result = _call_llm(settings.LLM_REVIEWER_MODEL, REVIEWER_SYSTEM_PROMPT, user_content)
    result["ai_score"] = _extract_score(result["content"])
    return result


def _extract_score(review_text: str) -> int:
    match = re.search(r"PUNTAJE:\s*(\d{1,3})", review_text, re.IGNORECASE)
    if match:
        return max(0, min(100, int(match.group(1))))
    return 50

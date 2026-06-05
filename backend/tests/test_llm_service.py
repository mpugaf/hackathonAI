from unittest.mock import Mock, patch

import pytest
import requests

from services.llm_service import _extract_score, generate_spec, review_spec


def _mock_response(content: str):
    response = Mock()
    response.status_code = 200
    response.json.return_value = {"choices": [{"message": {"content": content}}]}
    return response


def test_generate_spec_success():
    with patch("services.llm_service.requests.post", return_value=_mock_response("Spec OK")):
        result = generate_spec("Requisito con detalle suficiente para generar una especificacion")
    assert result["content"] == "Spec OK"
    assert result["model"]
    assert "prompt_used" in result


def test_generate_spec_timeout():
    with patch("services.llm_service.requests.post", side_effect=requests.exceptions.Timeout) as mocked:
        with pytest.raises(requests.exceptions.Timeout):
            generate_spec("Requisito con detalle suficiente para generar una especificacion")
    assert mocked.call_count == 2


def test_generate_spec_all_retries_fail():
    with patch("services.llm_service.requests.post", side_effect=requests.exceptions.RequestException("boom")):
        with pytest.raises(requests.exceptions.RequestException):
            generate_spec("Requisito con detalle suficiente para generar una especificacion")


def test_review_spec_extracts_score():
    with patch("services.llm_service.requests.post", return_value=_mock_response("PUNTAJE: 85\nBuen documento")):
        result = review_spec("Input original", "Spec generada")
    assert result["ai_score"] == 85


def test_extract_score_no_match():
    assert _extract_score("Sin puntaje") == 50

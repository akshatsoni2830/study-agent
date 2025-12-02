import json
import pytest
from src.gemini_client import GeminiClient

def test_clean_json_response_simple():
    client = GeminiClient(api_key="test", model_name="test")
    raw = '{"key": "value"}'
    assert client._clean_json_response(raw) == {"key": "value"}

def test_clean_json_response_markdown():
    client = GeminiClient(api_key="test", model_name="test")
    raw = '```json\n{"key": "value"}\n```'
    assert client._clean_json_response(raw) == {"key": "value"}

def test_clean_json_response_markdown_no_lang():
    client = GeminiClient(api_key="test", model_name="test")
    raw = '```\n{"key": "value"}\n```'
    assert client._clean_json_response(raw) == {"key": "value"}

def test_clean_json_response_list():
    client = GeminiClient(api_key="test", model_name="test")
    raw = '```json\n[{"key": "value"}]\n```'
    assert client._clean_json_response(raw) == [{"key": "value"}]

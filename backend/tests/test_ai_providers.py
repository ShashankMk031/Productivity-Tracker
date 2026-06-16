import pytest
import urllib.request
import urllib.error
import json
from unittest.mock import MagicMock, patch

from ai.providers.gemini_provider import GeminiProvider
from ai.providers.groq_provider import GroqProvider
from ai.providers.openrouter_provider import OpenRouterProvider
from ai.providers.lmstudio_provider import LMStudioProvider
from ai.providers.static_provider import StaticProvider
from ai.ai_service import AIService, AI_FAILURE_PLACEHOLDER

# Mock context object for StaticProvider testing
class MockNotesCategory:
    def __init__(self, count, percentage):
        self.count = count
        self.percentage = percentage

class MockNotes:
    def __init__(self):
        self.total_notes_analyzed = 2
        self.dominant_themes = ["focus", "fatigue"]
        self.categories = {
            "Productivity": MockNotesCategory(1, 50),
            "Mood/Energy": MockNotesCategory(1, 50)
        }

class MockBehavioralPatterns:
    def __init__(self):
        self.completion_rate = 75
        self.current_streak = 4
        self.longest_streak = 10
        self.active_tasks_count = 5
        self.weak_weekdays = ["Wednesday"]
        self.productive_weekdays = ["Monday", "Friday"]

class MockGoal:
    def __init__(self, title, category, progress, completed):
        self.title = title
        self.category = category
        self.progress = progress
        self.completed = completed

class MockMilestone:
    def __init__(self, title, completed):
        self.title = title
        self.completed = completed

class MockProject:
    def __init__(self, title, deadline, progress, urgency, milestones):
        self.title = title
        self.deadline = deadline
        self.progress = progress
        self.urgency = urgency
        self.milestones = milestones

class MockAIContext:
    def __init__(self):
        self.period_type = "weekly"
        self.period_start = "2026-06-08"
        self.period_end = "2026-06-14"
        self.behavioral_patterns = MockBehavioralPatterns()
        self.notes = MockNotes()
        self.goals = [
            MockGoal("Learn Go", "Short-Term Goals", 80, False),
            MockGoal("Clean Desk", "Short-Term Goals", 100, True)
        ]
        self.projects = [
            MockProject("Habit Hardening", "2026-06-20", 90, "YELLOW", [
                MockMilestone("Phase 1", True),
                MockMilestone("Phase 2", False)
            ])
        ]
        self.scores = {"consistency": 85, "execution": 78}
        self.focus_stats = {"total_duration_sec": 7200, "total_sessions": 3, "completed_sessions": 2}
        self.reminder_stats = {"total_reminders": 10, "completed_reminders": 8}
        self.prediction_summary_markdown = "High probability of hitting next milestones."


def test_gemini_provider_generate_success():
    provider = GeminiProvider(api_key="fake-gemini-key")
    
    mock_response = MagicMock()
    mock_response.__enter__.return_value = mock_response
    mock_response.read.return_value = b'{"candidates": [{"content": {"parts": [{"text": "Gemini reflection text"}]}}]}'
    mock_response.status = 200
    
    with patch("urllib.request.urlopen", return_value=mock_response):
        res = provider.generate("test prompt")
        assert res == "Gemini reflection text"


def test_gemini_provider_health():
    # Test missing key
    provider_no_key = GeminiProvider(api_key="")
    assert provider_no_key.check_health() == "missing_key"

    # Test healthy connection
    provider = GeminiProvider(api_key="fake-key")
    mock_response = MagicMock()
    mock_response.__enter__.return_value = mock_response
    mock_response.status = 200
    with patch("urllib.request.urlopen", return_value=mock_response):
        assert provider.check_health() == "healthy"

    # Test offline connection
    with patch("urllib.request.urlopen", side_effect=Exception("Connection refused")):
        assert provider.check_health() == "offline"


def test_groq_provider_generate_success():
    provider = GroqProvider(api_key="fake-groq-key")
    
    mock_response = MagicMock()
    mock_response.__enter__.return_value = mock_response
    mock_response.read.return_value = b'{"choices": [{"message": {"content": "Groq reflection text"}}]}'
    mock_response.status = 200
    
    with patch("urllib.request.urlopen", return_value=mock_response):
        res = provider.generate("test prompt")
        assert res == "Groq reflection text"


def test_openrouter_provider_generate_success():
    provider = OpenRouterProvider(api_key="fake-openrouter-key")
    
    mock_response = MagicMock()
    mock_response.__enter__.return_value = mock_response
    mock_response.read.return_value = b'{"choices": [{"message": {"content": "OpenRouter reflection text"}}]}'
    mock_response.status = 200
    
    with patch("urllib.request.urlopen", return_value=mock_response):
        res = provider.generate("test prompt")
        assert res == "OpenRouter reflection text"


# Removed Ollama and OpenAI provider tests to keep codebase clean


def test_lmstudio_provider_generate_success():
    provider = LMStudioProvider(url="http://localhost:1234")
    
    mock_response = MagicMock()
    mock_response.__enter__.return_value = mock_response
    mock_response.read.return_value = b'{"choices": [{"message": {"content": "LM Studio reflection text"}}]}'
    mock_response.status = 200
    
    with patch("urllib.request.urlopen", return_value=mock_response):
        res = provider.generate("test prompt")
        assert res == "LM Studio reflection text"


def test_static_provider_composition():
    provider = StaticProvider()
    context = MockAIContext()
    
    # Verify health
    assert provider.check_health() == "healthy"
    
    # Verify fallback generation
    report = provider.generate("test prompt", context=context)
    
    assert "# Weekly Reflection" in report
    assert "Wins This Week" in report
    assert "Emerging Risks" in report
    assert "Behavioral Patterns" in report
    assert "Goal Progress" in report
    assert "Project Health" in report
    assert "Habit Hardening" in report
    assert "Learn Go" in report
    assert "Clean Desk" in report
    assert "Consistency Score" in report
    assert "High probability of hitting next milestones" in report


def test_ai_service_fallback_chain_success_at_second_provider(monkeypatch):
    # Setup service
    service = AIService()
    service.provider_order = ["gemini", "groq", "static"]
    
    # Configure API keys to prevent skipping
    service.providers["gemini"].api_key = "fake-gemini-key"
    service.providers["groq"].api_key = "fake-groq-key"
    
    # Mock Gemini to fail and Groq to succeed
    monkeypatch.setattr(service.providers["gemini"], "generate", MagicMock(side_effect=RuntimeError("Rate limit 429")))
    monkeypatch.setattr(service.providers["groq"], "generate", MagicMock(return_value="Groq reflection text"))
    
    res, provider, model = service.generate_reflection("test prompt")
    
    assert res == "Groq reflection text"
    assert provider == "groq"
    assert model == service.providers["groq"].model


def test_ai_service_fallback_to_static_on_llm_failure(monkeypatch):
    service = AIService()
    service.provider_order = ["gemini", "groq", "static"]
    
    # Configure API keys to prevent skipping
    service.providers["gemini"].api_key = "fake-gemini-key"
    service.providers["groq"].api_key = "fake-groq-key"
    
    context = MockAIContext()
    
    # Mock all API providers to fail
    monkeypatch.setattr(service.providers["gemini"], "generate", MagicMock(side_effect=RuntimeError("Outage")))
    monkeypatch.setattr(service.providers["groq"], "generate", MagicMock(side_effect=RuntimeError("Outage")))
    
    # Static provider will generate report using context
    res, provider, model = service.generate_reflection("test prompt", context=context)
    
    assert provider == "static"
    assert "# Weekly Reflection" in res
    assert "Wins This Week" in res


def test_ai_service_skips_unconfigured_api_providers():
    service = AIService()
    service.provider_order = ["gemini", "static"]
    
    # Ensure Gemini has no API key
    service.providers["gemini"].api_key = ""
    
    context = MockAIContext()
    res, provider, model = service.generate_reflection("test prompt", context=context)
    
    # Gemini should be skipped, static should run
    assert provider == "static"
    assert "# Weekly Reflection" in res


def test_ai_service_fallback_to_lmstudio(monkeypatch):
    service = AIService()
    service.provider_order = ["gemini", "lmstudio", "static"]
    
    # Configure Gemini API key so it is not skipped
    service.providers["gemini"].api_key = "fake-gemini-key"
    
    # Mock Gemini to fail and LM Studio to succeed
    monkeypatch.setattr(service.providers["gemini"], "generate", MagicMock(side_effect=RuntimeError("Outage")))
    monkeypatch.setattr(service.providers["lmstudio"], "generate", MagicMock(return_value="LM Studio reflection text"))
    
    res, provider, model = service.generate_reflection("test prompt")
    
    assert res == "LM Studio reflection text"
    assert provider == "lmstudio"
    assert model == service.providers["lmstudio"].model

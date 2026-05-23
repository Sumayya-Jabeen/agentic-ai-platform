"""
Unit tests for the Research & Summarization Skill.

Internal LLM and web search calls are mocked so no real API calls are made.
Tests verify the skill's output schema, structure, and data integrity.
"""

import pytest
from unittest.mock import patch
from models import ResearchInput, ResearchOutput, Source
from skills.research import ResearchSkill


# ── Shared mock output ────────────────────────────────────────────────────────

MOCK_RESEARCH_OUTPUT = ResearchOutput(
    summary="Large language models are neural networks trained on large text corpora.",
    key_points=[
        "LLMs use transformer architecture",
        "Training requires massive compute resources",
        "Models like GPT-4 have billions of parameters",
        "Fine-tuning adapts models for specific tasks",
    ],
    sources=[
        Source(url="https://arxiv.org/example", title="Attention Is All You Need", credibility_score=0.95),
        Source(url="https://openai.com/research", title="GPT-4 Technical Report", credibility_score=0.90),
    ],
    gaps=["Real-time training costs were not found"],
    confidence=0.88,
)

MOCK_CONTEXT = "LLMs are transformer-based models trained on large datasets..."


@pytest.fixture
def skill():
    return ResearchSkill()


# ── Output schema ─────────────────────────────────────────────────────────────

def test_research_output_is_correct_type(skill):
    with patch.object(skill, "_gather_information", return_value=MOCK_CONTEXT), \
         patch.object(skill, "_synthesize", return_value=MOCK_RESEARCH_OUTPUT):
        result = skill.run(ResearchInput(query="What are LLMs?"))
    assert isinstance(result, ResearchOutput)


# ── Summary ───────────────────────────────────────────────────────────────────

def test_research_returns_non_empty_summary(skill):
    with patch.object(skill, "_gather_information", return_value=MOCK_CONTEXT), \
         patch.object(skill, "_synthesize", return_value=MOCK_RESEARCH_OUTPUT):
        result = skill.run(ResearchInput(query="What are LLMs?"))
    assert isinstance(result.summary, str)
    assert len(result.summary) > 0


# ── Key points ────────────────────────────────────────────────────────────────

def test_research_returns_key_points(skill):
    with patch.object(skill, "_gather_information", return_value=MOCK_CONTEXT), \
         patch.object(skill, "_synthesize", return_value=MOCK_RESEARCH_OUTPUT):
        result = skill.run(ResearchInput(query="What are LLMs?"))
    assert isinstance(result.key_points, list)
    assert len(result.key_points) > 0


def test_research_key_points_are_strings(skill):
    with patch.object(skill, "_gather_information", return_value=MOCK_CONTEXT), \
         patch.object(skill, "_synthesize", return_value=MOCK_RESEARCH_OUTPUT):
        result = skill.run(ResearchInput(query="What are LLMs?"))
    for point in result.key_points:
        assert isinstance(point, str)
        assert len(point) > 0


# ── Sources ───────────────────────────────────────────────────────────────────

def test_research_returns_sources(skill):
    with patch.object(skill, "_gather_information", return_value=MOCK_CONTEXT), \
         patch.object(skill, "_synthesize", return_value=MOCK_RESEARCH_OUTPUT):
        result = skill.run(ResearchInput(query="What are LLMs?"))
    assert isinstance(result.sources, list)
    assert len(result.sources) > 0


def test_research_sources_have_url_and_title(skill):
    with patch.object(skill, "_gather_information", return_value=MOCK_CONTEXT), \
         patch.object(skill, "_synthesize", return_value=MOCK_RESEARCH_OUTPUT):
        result = skill.run(ResearchInput(query="What are LLMs?"))
    for source in result.sources:
        assert isinstance(source.url, str) and len(source.url) > 0
        assert isinstance(source.title, str) and len(source.title) > 0


def test_research_source_credibility_in_valid_range(skill):
    with patch.object(skill, "_gather_information", return_value=MOCK_CONTEXT), \
         patch.object(skill, "_synthesize", return_value=MOCK_RESEARCH_OUTPUT):
        result = skill.run(ResearchInput(query="What are LLMs?"))
    for source in result.sources:
        assert 0.0 <= source.credibility_score <= 1.0


# ── Confidence ────────────────────────────────────────────────────────────────

def test_research_confidence_in_valid_range(skill):
    with patch.object(skill, "_gather_information", return_value=MOCK_CONTEXT), \
         patch.object(skill, "_synthesize", return_value=MOCK_RESEARCH_OUTPUT):
        result = skill.run(ResearchInput(query="What are LLMs?"))
    assert 0.0 <= result.confidence <= 1.0


# ── Focus areas ───────────────────────────────────────────────────────────────

def test_research_accepts_focus_areas(skill):
    with patch.object(skill, "_gather_information", return_value=MOCK_CONTEXT), \
         patch.object(skill, "_synthesize", return_value=MOCK_RESEARCH_OUTPUT):
        result = skill.run(ResearchInput(
            query="What are LLMs?",
            focus_areas=["fine-tuning", "inference speed"]
        ))
    assert isinstance(result, ResearchOutput)


# ── Error handling ────────────────────────────────────────────────────────────

def test_research_propagates_gather_error(skill):
    with patch.object(skill, "_gather_information", side_effect=RuntimeError("Search failed")):
        with pytest.raises(RuntimeError, match="Search failed"):
            skill.run(ResearchInput(query="test"))


def test_research_propagates_synthesize_error(skill):
    with patch.object(skill, "_gather_information", return_value=MOCK_CONTEXT), \
         patch.object(skill, "_synthesize", side_effect=RuntimeError("LLM failed")):
        with pytest.raises(RuntimeError, match="LLM failed"):
            skill.run(ResearchInput(query="test"))

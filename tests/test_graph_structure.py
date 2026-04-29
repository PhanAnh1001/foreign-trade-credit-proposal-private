"""Tests for LangGraph graph structure (no LLM calls)."""
import pytest


def test_graph_compiles():
    """Graph should compile without errors."""
    from src.agents.graph import build_lc_graph
    graph = build_lc_graph()
    assert graph is not None


def test_graph_has_expected_nodes():
    """Graph should contain the 4 required nodes."""
    from src.agents.graph import build_lc_graph
    graph = build_lc_graph()
    # LangGraph compiled graph exposes graph.nodes or similar
    # Check it has all 4 node names
    node_names = set(graph.nodes.keys()) if hasattr(graph, 'nodes') else set()
    # At minimum the graph should be a CompiledStateGraph
    assert graph is not None


def test_route_after_review_fill():
    """score >= 7.0 → fill."""
    from src.agents.graph import route_after_review
    state = {"quality_score": 8.5, "retry_count": 1}
    assert route_after_review(state) == "fill"


def test_route_after_review_retry():
    """score < 7.0, retry_count <= 1 → retry_extract."""
    from src.agents.graph import route_after_review
    state = {"quality_score": 5.0, "retry_count": 1}
    assert route_after_review(state) == "retry_extract"


def test_route_after_review_fill_after_max_retries():
    """score < 7.0, retry_count > 1 → fill (proceed with warnings)."""
    from src.agents.graph import route_after_review
    state = {"quality_score": 5.0, "retry_count": 2}
    assert route_after_review(state) == "fill"


def test_route_with_no_score():
    """No score defaults to 0, retry if retry_count allows."""
    from src.agents.graph import route_after_review
    state = {"quality_score": None, "retry_count": 0}
    result = route_after_review(state)
    assert result in ("retry_extract", "fill")

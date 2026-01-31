"""
Tests for GraphSpec.validate() — specifically validation of CONDITIONAL edges.

Covers:
- CONDITIONAL edges without condition_expr fail validation
- CONDITIONAL edges with condition_expr pass validation
- Runtime behavior: CONDITIONAL with no expression returns False (fail closed)
"""

from framework.graph.edge import EdgeCondition, EdgeSpec, GraphSpec
from framework.graph.node import NodeSpec


class TestConditionalEdgeValidation:
    """Tests for CONDITIONAL edge validation in GraphSpec."""

    def test_conditional_without_condition_expr_fails_validation(self):
        """CONDITIONAL edge with no condition_expr should fail validation."""
        # Create minimal graph with CONDITIONAL edge but no condition_expr
        graph = GraphSpec(
            id="test-graph",
            goal_id="goal-1",
            entry_node="node1",
            nodes=[
                NodeSpec(id="node1", name="N1", description="n1", node_type="function"),
                NodeSpec(id="node2", name="N2", description="n2", node_type="function"),
            ],
            edges=[
                EdgeSpec(
                    id="invalid-conditional",
                    source="node1",
                    target="node2",
                    condition=EdgeCondition.CONDITIONAL,
                    condition_expr=None,  # Missing!
                ),
            ],
        )

        errors = graph.validate()

        # Should contain error about missing condition_expr
        assert len(errors) > 0
        assert any("condition_expr" in e.lower() for e in errors)
        assert any("invalid-conditional" in e for e in errors)

    def test_conditional_with_empty_string_fails_validation(self):
        """CONDITIONAL edge with empty string condition_expr should fail validation."""
        graph = GraphSpec(
            id="test-graph",
            goal_id="goal-1",
            entry_node="node1",
            nodes=[
                NodeSpec(id="node1", name="N1", description="n1", node_type="function"),
                NodeSpec(id="node2", name="N2", description="n2", node_type="function"),
            ],
            edges=[
                EdgeSpec(
                    id="empty-condition",
                    source="node1",
                    target="node2",
                    condition=EdgeCondition.CONDITIONAL,
                    condition_expr="",  # Empty string
                ),
            ],
        )

        errors = graph.validate()

        # Should contain error about missing condition_expr
        assert len(errors) > 0
        assert any("condition_expr" in e.lower() for e in errors)

    def test_conditional_with_condition_expr_passes_validation(self):
        """CONDITIONAL edge with condition_expr should pass validation."""
        graph = GraphSpec(
            id="test-graph",
            goal_id="goal-1",
            entry_node="node1",
            nodes=[
                NodeSpec(id="node1", name="N1", description="n1", node_type="function"),
                NodeSpec(id="node2", name="N2", description="n2", node_type="function"),
            ],
            edges=[
                EdgeSpec(
                    id="valid-conditional",
                    source="node1",
                    target="node2",
                    condition=EdgeCondition.CONDITIONAL,
                    condition_expr="result == True",
                ),
            ],
        )

        errors = graph.validate()

        # Should NOT contain error about missing condition_expr
        # (other errors may exist, but not about condition_expr)
        assert not any("condition_expr" in e.lower() for e in errors)

    def test_always_edge_no_condition_expr_passes_validation(self):
        """ALWAYS edges do not require condition_expr and should pass."""
        graph = GraphSpec(
            id="test-graph",
            goal_id="goal-1",
            entry_node="node1",
            nodes=[
                NodeSpec(id="node1", name="N1", description="n1", node_type="function"),
                NodeSpec(id="node2", name="N2", description="n2", node_type="function"),
            ],
            edges=[
                EdgeSpec(
                    id="always-edge",
                    source="node1",
                    target="node2",
                    condition=EdgeCondition.ALWAYS,
                    condition_expr=None,  # OK for ALWAYS
                ),
            ],
        )

        errors = graph.validate()

        # Should NOT error about condition_expr (ALWAYS doesn't need it)
        assert not any("condition_expr" in e.lower() for e in errors)

    def test_on_success_edge_no_condition_expr_passes_validation(self):
        """ON_SUCCESS edges do not require condition_expr."""
        graph = GraphSpec(
            id="test-graph",
            goal_id="goal-1",
            entry_node="node1",
            nodes=[
                NodeSpec(id="node1", name="N1", description="n1", node_type="function"),
                NodeSpec(id="node2", name="N2", description="n2", node_type="function"),
            ],
            edges=[
                EdgeSpec(
                    id="on-success-edge",
                    source="node1",
                    target="node2",
                    condition=EdgeCondition.ON_SUCCESS,
                    condition_expr=None,
                ),
            ],
        )

        errors = graph.validate()

        # Should NOT error about condition_expr (ON_SUCCESS doesn't need it)
        assert not any("condition_expr" in e.lower() for e in errors)

    def test_multiple_conditional_edges_validation(self):
        """Multiple CONDITIONAL edges: invalid ones fail, valid ones pass."""
        graph = GraphSpec(
            id="test-graph",
            goal_id="goal-1",
            entry_node="node1",
            nodes=[
                NodeSpec(id="node1", name="N1", description="n1", node_type="function"),
                NodeSpec(id="node2", name="N2", description="n2", node_type="function"),
                NodeSpec(id="node3", name="N3", description="n3", node_type="function"),
            ],
            edges=[
                EdgeSpec(
                    id="valid-cond",
                    source="node1",
                    target="node2",
                    condition=EdgeCondition.CONDITIONAL,
                    condition_expr="result > 0",
                ),
                EdgeSpec(
                    id="invalid-cond",
                    source="node1",
                    target="node3",
                    condition=EdgeCondition.CONDITIONAL,
                    condition_expr=None,  # Invalid
                ),
            ],
        )

        errors = graph.validate()

        # Should have exactly 1 error, for invalid-cond
        condition_expr_errors = [e for e in errors if "condition_expr" in e.lower()]
        assert len(condition_expr_errors) == 1
        assert "invalid-cond" in condition_expr_errors[0]


class TestConditionalEdgeRuntimeBehavior:
    """Tests for runtime behavior of CONDITIONAL edges without expression."""

    def test_evaluate_condition_returns_false_when_expr_missing(self):
        """_evaluate_condition() should return False when condition_expr is missing."""
        edge = EdgeSpec(
            id="test-edge",
            source="node1",
            target="node2",
            condition=EdgeCondition.CONDITIONAL,
            condition_expr=None,  # No expression
        )

        # Call _evaluate_condition directly
        result = edge._evaluate_condition(output={"result": True}, memory={})

        # Should return False (fail closed) instead of True
        assert result is False

    def test_evaluate_condition_returns_false_with_empty_string(self):
        """_evaluate_condition() should return False when condition_expr is empty string."""
        edge = EdgeSpec(
            id="test-edge",
            source="node1",
            target="node2",
            condition=EdgeCondition.CONDITIONAL,
            condition_expr="",  # Empty
        )

        result = edge._evaluate_condition(output={"result": True}, memory={})

        assert result is False

    def test_evaluate_condition_with_valid_expression_true(self):
        """_evaluate_condition() with valid expression should evaluate properly (true case)."""
        edge = EdgeSpec(
            id="test-edge",
            source="node1",
            target="node2",
            condition=EdgeCondition.CONDITIONAL,
            condition_expr="result == True",
        )

        # Should return True (expression evaluates true)
        # Note: context has 'result' key from output.get("result")
        result = edge._evaluate_condition(output={"result": True}, memory={})
        assert result is True

    def test_evaluate_condition_with_valid_expression_false(self):
        """_evaluate_condition() with valid expression should evaluate properly (false case)."""
        edge = EdgeSpec(
            id="test-edge",
            source="node1",
            target="node2",
            condition=EdgeCondition.CONDITIONAL,
            condition_expr="result == True",
        )

        # Should return False (expression evaluates false)
        result = edge._evaluate_condition(output={"result": False}, memory={})
        assert result is False

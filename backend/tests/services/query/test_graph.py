from langgraph.types import Command

from app.services.query.graph.workflow import build_query_graph
from app.services.query.graph.nodes import QueryNodes
from app.services.query.sql_generator import SQLGenerator


def test_query_graph_human_clarification_resume(db_session):
    graph = build_query_graph(db_session)

    config = {
        "configurable": {
            "thread_id": "test-hitl-001",
        }
    }

    initial_state = {
        "question": "Which is the best product?",
        "schema": {
            "table_name": "dataset_4",
            "columns": [
                {"name": "product", "type": "TEXT"},
                {"name": "category", "type": "TEXT"},
                {"name": "region", "type": "TEXT"},
                {"name": "quantity", "type": "BIGINT"},
                {"name": "unit_price", "type": "BIGINT"},
                {"name": "sale_date", "type": "TEXT"},
                {"name": "revenue", "type": "BIGINT"},
            ],
        },
    }

    # ---------------------------------------------
    # STEP 1: Initial request
    # ---------------------------------------------

    result = graph.invoke(
        initial_state,
        config=config,
    )

    assert "__interrupt__" in result

    interrupt_data = result["__interrupt__"][0].value

    assert interrupt_data["type"] == "clarification"
    assert interrupt_data["question"]

    # ---------------------------------------------
    # STEP 2: Human clarification
    # ---------------------------------------------

    result = graph.invoke(
        Command(
            resume="In terms of revenue."
        ),
        config=config,
    )

    # ---------------------------------------------
    # STEP 3: Graph completed
    # ---------------------------------------------

    assert result["execution_error"] is None
    assert result["status"] == "completed"

    assert result["user_clarification"] == (
        "In terms of revenue."
    )

    assert result["sql"]
    assert result["sql_valid"] is True
    assert result["results"] is not None


def test_query_graph_checkpoint_resume(db_session):
    graph = build_query_graph(db_session)

    config = {
        "configurable": {
            "thread_id": "checkpoint-test-001",
        }
    }

    state = {
        "question": "Which is the best product?",
        "schema": {
            "table_name": "dataset_4",
            "columns": [
                {"name": "product", "type": "TEXT"},
                {"name": "category", "type": "TEXT"},
                {"name": "region", "type": "TEXT"},
                {"name": "quantity", "type": "BIGINT"},
                {"name": "unit_price", "type": "BIGINT"},
                {"name": "sale_date", "type": "TEXT"},
                {"name": "revenue", "type": "BIGINT"},
            ],
        },
    }

    # ---------------------------------------------
    # STEP 1: Initial invocation
    # ---------------------------------------------

    result = graph.invoke(
        state,
        config=config,
    )

    assert "__interrupt__" in result

    # ---------------------------------------------
    # STEP 2: Verify checkpoint
    # ---------------------------------------------

    snapshot = graph.get_state(config)

    assert snapshot.values
    assert snapshot.values["question"] == (
        "Which is the best product?"
    )

    # ---------------------------------------------
    # STEP 3: Resume same thread
    # ---------------------------------------------

    result = graph.invoke(
        Command(
            resume="In terms of revenue."
        ),
        config=config,
    )

    assert result["status"] == "completed"
    assert result["execution_error"] is None
    assert result["sql"]
    assert result["sql_valid"] is True
    assert result["results"] is not None


def test_query_graph_repairs_invalid_sql(
    db_session,
    monkeypatch,
):
    # ==================================================
    # IMPORTANT:
    # This test is specifically testing SQL repair.
    # We don't want ambiguity detection to interfere.
    # ==================================================

    monkeypatch.setattr(
        QueryNodes,
        "detect_ambiguity",
        lambda self, state: {
            **state,
            "is_ambiguous": False,
            "ambiguity_reason": (
                "Question is sufficiently specific."
            ),
            "clarification_question": None,
            "status": "question_clear",
        },
    )

    # ==================================================
    # Mock SQL generation
    # ==================================================

    monkeypatch.setattr(
        SQLGenerator,
        "generate_sql",
        lambda self, question, schema: """
            SELECT product, invalid_column
            FROM dataset_4
        """,
    )

    # ==================================================
    # Mock SQL repair
    # ==================================================

    monkeypatch.setattr(
        SQLGenerator,
        "repair_sql",
        lambda self, sql, error, schema: """
            SELECT product, revenue
            FROM dataset_4
            ORDER BY revenue DESC
            LIMIT 1
        """,
    )

    # ==================================================
    # Build graph
    # ==================================================

    graph = build_query_graph(db_session)

    config = {
        "configurable": {
            "thread_id": "test-sql-repair-001",
        }
    }

    initial_state = {
        "question": "Which product generated the most revenue?",
        "schema": {
            "table_name": "dataset_4",
            "columns": [
                {
                    "name": "product",
                    "type": "TEXT",
                },
                {
                    "name": "category",
                    "type": "TEXT",
                },
                {
                    "name": "region",
                    "type": "TEXT",
                },
                {
                    "name": "quantity",
                    "type": "BIGINT",
                },
                {
                    "name": "unit_price",
                    "type": "BIGINT",
                },
                {
                    "name": "sale_date",
                    "type": "TEXT",
                },
                {
                    "name": "revenue",
                    "type": "BIGINT",
                },
            ],
        },
    }

    # ==================================================
    # Invoke graph
    # ==================================================

    result = graph.invoke(
        initial_state,
        config=config,
    )

    # ==================================================
    # Assertions
    # ==================================================

    assert result["status"] == "completed"

    assert result["sql_valid"] is True

    assert result["execution_error"] is None

    assert result["results"] is not None

    assert result["sql_repair_attempts"] == 1

    assert "invalid_column" not in result["sql"]

    assert "ORDER BY revenue DESC" in result["sql"]

def test_query_graph_repair_exhaustion(
    db_session,
    monkeypatch,
):
    # ==================================================
    # Disable ambiguity for this test
    # ==================================================

    monkeypatch.setattr(
        QueryNodes,
        "detect_ambiguity",
        lambda self, state: {
            **state,
            "is_ambiguous": False,
            "ambiguity_reason": "Question is sufficiently specific.",
            "clarification_question": None,
            "status": "question_clear",
        },
    )

    # ==================================================
    # Always generate invalid SQL
    # ==================================================

    monkeypatch.setattr(
        SQLGenerator,
        "generate_sql",
        lambda self, question, schema: """
            SELECT product, invalid_column
            FROM dataset_4
        """,
    )

    # ==================================================
    # Repair also returns invalid SQL
    # ==================================================

    monkeypatch.setattr(
        SQLGenerator,
        "repair_sql",
        lambda self, sql, error, schema: """
            SELECT product, another_invalid_column
            FROM dataset_4
        """,
    )

    graph = build_query_graph(db_session)

    config = {
        "configurable": {
            "thread_id": "test-sql-repair-exhaustion-001",
        }
    }

    initial_state = {
        "question": "Which product generated the most revenue?",
        "schema": {
            "table_name": "dataset_4",
            "columns": [
                {"name": "product", "type": "TEXT"},
                {"name": "category", "type": "TEXT"},
                {"name": "region", "type": "TEXT"},
                {"name": "quantity", "type": "BIGINT"},
                {"name": "unit_price", "type": "BIGINT"},
                {"name": "sale_date", "type": "TEXT"},
                {"name": "revenue", "type": "BIGINT"},
            ],
        },
    }

    result = graph.invoke(
        initial_state,
        config=config,
    )

    # ==================================================
    # Assertions
    # ==================================================

    assert result["status"] == "rejected"

    assert result["sql_valid"] is False

    assert result["sql_repair_attempts"] == 2

    assert result["sql_repair_error"] is not None

    assert result["results"] is None

def test_query_graph_execution_failure(
    db_session,
    monkeypatch,
):
    # Disable ambiguity
    monkeypatch.setattr(
        QueryNodes,
        "detect_ambiguity",
        lambda self, state: {
            **state,
            "is_ambiguous": False,
            "ambiguity_reason": "Question is sufficiently specific.",
            "clarification_question": None,
            "status": "question_clear",
        },
    )

    # Generate valid SQL
    monkeypatch.setattr(
        SQLGenerator,
        "generate_sql",
        lambda self, question, schema: """
            SELECT product, revenue
            FROM dataset_4
            ORDER BY revenue DESC
            LIMIT 1
        """,
    )

    # Force execution failure
    monkeypatch.setattr(
        QueryNodes,
        "execute_sql",
        lambda self, state: {
            **state,
            "results": None,
            "execution_error": "Database execution failed.",
            "status": "execution_failed",
        },
    )

    graph = build_query_graph(db_session)

    config = {
        "configurable": {
            "thread_id": "test-execution-failure-001",
        }
    }

    initial_state = {
        "question": "Which product generated the most revenue?",
        "schema": {
            "table_name": "dataset_4",
            "columns": [
                {"name": "product", "type": "TEXT"},
                {"name": "revenue", "type": "BIGINT"},
            ],
        },
        "results": None,
        "execution_error": None,
    }

    result = graph.invoke(
        initial_state,
        config=config,
    )

    assert result["status"] == "failed"
    assert result["execution_error"] == (
        "Database execution failed."
    )
    assert result["results"] is None
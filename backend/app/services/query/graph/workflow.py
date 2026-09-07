from sqlalchemy.orm import Session

from langgraph.graph import (
    StateGraph,
    START,
    END,
)

from langgraph.checkpoint.memory import MemorySaver

from app.services.query.graph.state import QueryState

from app.services.query.graph.nodes import (
    QueryNodes,
    route_after_policy,
    route_after_ambiguity,
    route_after_validation,
    route_after_execution,
    route_after_repair,
)


# Shared checkpointer for the application process
checkpointer = MemorySaver()


def build_query_graph(
    db: Session,
):

    nodes = QueryNodes(db)

    graph = StateGraph(QueryState)

    # ==================================================
    # NODES
    # ==================================================

    graph.add_node(
        "policy_check",
        nodes.policy_check,
    )

    graph.add_node(
        "detect_ambiguity",
        nodes.detect_ambiguity,
    )

    graph.add_node(
        "request_clarification",
        nodes.request_clarification,
    )

    graph.add_node(
        "generate_sql",
        nodes.generate_sql,
    )

    graph.add_node(
        "validate_sql",
        nodes.validate_sql,
    )

    graph.add_node(
        "repair_sql",
        nodes.repair_sql,
    )

    graph.add_node(
        "execute_sql",
        nodes.execute_sql,
    )

    graph.add_node(
        "build_response",
        nodes.build_response,
    )

    # ==================================================
    # EDGES
    # ==================================================

    graph.add_edge(
        START,
        "policy_check",
    )

    # --------------------------------------------------
    # POLICY ROUTING
    # --------------------------------------------------

    graph.add_conditional_edges(
        "policy_check",
        route_after_policy,
        {
            "generate": "detect_ambiguity",
            "response": "build_response",
        },
    )

    # --------------------------------------------------
    # AMBIGUITY ROUTING
    # --------------------------------------------------

    graph.add_conditional_edges(
        "detect_ambiguity",
        route_after_ambiguity,
        {
            "clarification": "request_clarification",
            "generate": "generate_sql",
        },
    )

    graph.add_edge(
        "request_clarification",
        "generate_sql",
    )

    # --------------------------------------------------
    # SQL GENERATION
    # --------------------------------------------------

    graph.add_edge(
        "generate_sql",
        "validate_sql",
    )

    # --------------------------------------------------
    # SQL VALIDATION
    # --------------------------------------------------

    graph.add_conditional_edges(
        "validate_sql",
        route_after_validation,
        {
            "execute": "execute_sql",
            "repair": "repair_sql",
            "response": "build_response",
        },
    )

    # --------------------------------------------------
    # SQL REPAIR
    # --------------------------------------------------

    graph.add_conditional_edges(
        "repair_sql",
        route_after_repair,
        {
            "validate": "validate_sql",
            "response": "build_response",
        },
    )

    # --------------------------------------------------
    # SQL EXECUTION
    # --------------------------------------------------

    graph.add_conditional_edges(
        "execute_sql",
        route_after_execution,
        {
            "repair": "repair_sql",
            "response": "build_response",
        },
    )

    # --------------------------------------------------
    # RESPONSE
    # --------------------------------------------------

    graph.add_edge(
        "build_response",
        END,
    )

    return graph.compile(
        checkpointer=checkpointer,
    )
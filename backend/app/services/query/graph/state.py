from typing import TypedDict


class QueryState(TypedDict, total=False):
    # ==================================================
    # INPUT
    # ==================================================

    question: str
    schema: dict

    # ==================================================
    # POLICY
    # ==================================================

    policy_allowed: bool
    policy_reason: str | None

    # ==================================================
    # AMBIGUITY / HITL
    # ==================================================

    is_ambiguous: bool
    ambiguity_reason: str | None
    clarification_question: str | None
    user_clarification: str | None

    # ==================================================
    # SQL
    # ==================================================

    sql: str | None
    original_sql: str | None

    sql_valid: bool
    validation_error: str | None

    # ==================================================
    # SQL REPAIR
    # ==================================================

    sql_repair_attempts: int
    sql_repair_error: str | None

    # ==================================================
    # EXECUTION
    # ==================================================

    results: list[dict] | None
    execution_error: str | None

    # ==================================================
    # RESPONSE
    # ==================================================

    final_answer: str | None

    # ==================================================
    # STATUS
    # ==================================================

    status: str
    dataset_id: int

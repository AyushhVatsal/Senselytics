from sqlalchemy.orm import Session

from pydantic import BaseModel, Field

from langgraph.types import interrupt

from app.services.query.sql_generator import SQLGenerator
from app.services.query.sql_validator import SQLValidator
from app.services.query.sql_executor import SQLExecutor
from app.services.query.graph.state import QueryState


# ============================================================
# STRUCTURED OUTPUT
# ============================================================


class AmbiguityDecision(BaseModel):
    is_ambiguous: bool = Field(
        description="Whether the user's question is ambiguous."
    )

    reason: str = Field(
        description="Why the question is ambiguous, or why it is clear."
    )

    clarification_question: str | None = Field(
        default=None,
        description=(
            "Question to ask the user if clarification is required."
        ),
    )


# ============================================================
# QUERY NODES
# ============================================================


class QueryNodes:

    def __init__(self, db: Session):
        self.db = db

        self.sql_generator = SQLGenerator()
        self.sql_validator = SQLValidator()
        self.sql_executor = SQLExecutor()

        self.intent_llm = (
            self.sql_generator.llm.with_structured_output(
                AmbiguityDecision
            )
        )

    # ========================================================
    # POLICY CHECK
    # ========================================================

    def policy_check(
        self,
        state: QueryState,
    ) -> QueryState:

        question = state["question"].lower().strip()

        destructive_keywords = [
            "delete",
            "drop",
            "truncate",
            "alter",
            "insert",
            "update",
            "create table",
        ]

        for keyword in destructive_keywords:

            if keyword in question:

                return {
                    **state,
                    "policy_allowed": False,
                    "policy_reason": (
                        "Database-modifying operations "
                        "are not allowed."
                    ),
                    "sql_valid": False,
                    "status": "policy_rejected",
                }

        return {
            **state,
            "policy_allowed": True,
            "policy_reason": None,
            "status": "policy_allowed",
        }

    # ========================================================
    # AMBIGUITY DETECTION
    # ========================================================

    def detect_ambiguity(
        self,
        state: QueryState,
    ) -> QueryState:

        schema = state.get("schema", {})

        prompt = f"""
        You are an ambiguity detection system.

        Determine whether the user's question is sufficiently specific
        to generate a correct PostgreSQL query using the provided schema.

        DATABASE SCHEMA:
        {schema}

        USER QUESTION:
        {state["question"]}

        Evaluate the question using the database schema.

        Rules:

        1. Do NOT ask for table names or column names when the schema
        already provides suitable columns.

        2. Do NOT consider a question ambiguous merely because there are
        multiple possible SQL implementations.

        3. Infer obvious mappings from the schema.

        4. A question is ambiguous only when the schema does not contain
        enough information to determine the requested operation.

        5. If the requested metric or operation is explicitly specified,
        the question is clear.

        6. If the question contains a filter such as a region, category,
        product, date, etc., and the corresponding schema column exists,
        infer the mapping from the schema.

        Example:

        Question:
        Which product generated the most revenue?

        Schema:
        product, revenue, category, region

        This is clear because:
        - product maps to product
        - revenue maps to revenue
        - "most" determines the ordering

        Another example:

        Question:
        Which product performed best?

        Schema:
        product, revenue, quantity

        This is ambiguous because "performed best" does not specify
        whether performance means revenue, quantity, or another metric.

        Determine whether the question is genuinely ambiguous based
        on the available schema.
        """

        decision = self.intent_llm.invoke(prompt)

        if decision.is_ambiguous:
            return {
                **state,
                "is_ambiguous": True,
                "ambiguity_reason": decision.reason,
                "clarification_question": (
                    decision.clarification_question
                    or "Could you clarify your question?"
                ),
                "status": "ambiguity_detected",
            }

        return {
            **state,
            "is_ambiguous": False,
            "ambiguity_reason": decision.reason,
            "clarification_question": None,
            "status": "question_clear",
        }

    # ========================================================
    # HUMAN-IN-THE-LOOP
    # ========================================================

    def request_clarification(
        self,
        state: QueryState,
    ) -> QueryState:

        clarification = interrupt(
            {
                "type": "clarification",
                "question": state["clarification_question"],
                "reason": state["ambiguity_reason"],
            }
        )

        return {
            **state,
            "user_clarification": clarification,
            "question": (
                f'{state["question"]}\n'
                f"User clarification: {clarification}"
            ),
            "status": "clarification_received",
        }

    # ========================================================
    # GENERATE SQL
    # ========================================================

    def generate_sql(
        self,
        state: QueryState,
    ) -> QueryState:

        sql = self.sql_generator.generate_sql(
            question=state["question"],
            schema=state["schema"],
        )

        return {
            **state,
            "sql": sql,
            "original_sql": sql,
            "sql_valid": False,
            "validation_error": None,
            "execution_error": None,
            "status": "sql_generated",
        }

    # ========================================================
    # VALIDATE SQL
    # ========================================================

    def validate_sql(
        self,
        state: QueryState,
    ) -> QueryState:

        sql_valid, validation_error = (
            self.sql_validator.validate(
                sql=state["sql"],
                schema=state["schema"],
            )
        )

        print("================================")
        print("VALIDATING SQL:")
        print(state["sql"])
        print("VALID:", sql_valid)
        print("ERROR:", validation_error)
        print("================================")

        # ==================================================
        # INVALID SQL
        # ==================================================

        if not sql_valid:

            repair_attempts = state.get(
                "sql_repair_attempts",
                0,
            )

            # --------------------------------------------------
            # Repair budget exhausted
            # --------------------------------------------------

            if repair_attempts >= 2:

                return {
                    **state,
                    "sql_valid": False,
                    "validation_error": validation_error,
                    "sql_repair_error": validation_error,
                    "status": "repair_exhausted",
                }

            # --------------------------------------------------
            # Repair still available
            # --------------------------------------------------

            return {
                **state,
                "sql_valid": False,
                "validation_error": validation_error,
                "status": "validation_failed",
            }

        # ==================================================
        # VALID SQL
        # ==================================================

        return {
            **state,
            "sql_valid": True,
            "validation_error": None,
            "status": "validated",
        }

    # ========================================================
    # REPAIR SQL
    # ========================================================

    def repair_sql(
        self,
        state: QueryState,
    ) -> QueryState:

        attempts = state.get(
            "sql_repair_attempts",
            0,
        )

        # Maximum of 2 repair attempts
        if attempts >= 2:
            return {
                **state,
                "status": "rejected",
                "sql_valid": False,
                "sql_repair_error": (
                    state.get("validation_error")
                    or "SQL repair attempts exhausted."
                ),
            }

        repaired_sql = self.sql_generator.repair_sql(
            sql=state["sql"],
            error=state.get("validation_error", ""),
            question=state["question"],
            schema=state["schema"],
        )

        return {
            **state,
            "sql": repaired_sql,
            "sql_repair_attempts": attempts + 1,
            "sql_repair_error": None,
            "status": "sql_repaired",
        }

    # ========================================================
    # EXECUTE SQL
    # ========================================================

    def execute_sql(
        self,
        state: QueryState,
    ) -> QueryState:

        try:

            results = self.sql_executor.execute(
                db=self.db,
                sql=state["sql"],
            )

            return {
                **state,
                "results": results,
                "execution_error": None,
                "status": "executed",
            }

        except Exception as exc:

            return {
                **state,
                "results": None,
                "execution_error": str(exc),
                "status": "execution_failed",
            }

    def format_final_answer(
        self,
        question: str,
        results: list[dict],
    ) -> str:
        """
        Convert structured SQL results into a concise,
        user-facing natural language answer.
        """

        if not results:
            return "No results were found for your question."

        # Aggregate queries with no matching rows can return a
        # single row containing only NULL values.
        if len(results) == 1 and all(value is None for value in results[0].values()):
            return "No records were found matching your question."

        # --------------------------------------------------
        # Single row + single column
        # --------------------------------------------------
        if len(results) == 1 and len(results[0]) == 1:
            column, value = next(iter(results[0].items()))

            # Convert snake_case to readable text
            label = column.replace("_", " ")

            # Format numbers nicely
            if isinstance(value, float):
                value = f"{value:,.2f}"
            elif isinstance(value, int):
                value = f"{value:,}"

            return f"The {label} is {value}."

        # --------------------------------------------------
        # Single row + multiple columns
        # --------------------------------------------------
        if len(results) == 1:
            values = []

            for column, value in results[0].items():
                label = column.replace("_", " ")

                if isinstance(value, float):
                    value = f"{value:,.2f}"
                elif isinstance(value, int):
                    value = f"{value:,}"

                values.append(f"{label}: {value}")

            return "Here are the results: " + ", ".join(values) + "."

        # --------------------------------------------------
        # Multiple rows
        # --------------------------------------------------
        return (
            f"I found {len(results)} results for your question. "
            "The detailed breakdown is shown below."
        )

    # ========================================================
    # FINAL RESPONSE
    # ========================================================

    def build_response(
        self,
        state: QueryState,
    ) -> QueryState:

        results = state.get("results")
        execution_error = state.get("execution_error")

        # ==================================================
        # POLICY REJECTION
        # ==================================================

        if state.get("status") == "policy_rejected":

            return {
                **state,
                "results": results,
                "execution_error": execution_error,
                "final_answer": (
                    "I can't perform database-modifying "
                    "operations. I can only answer "
                    "read-only questions about the dataset."
                ),
                "status": "rejected",
            }

        # ==================================================
        # SQL REPAIR EXHAUSTED
        # ==================================================

        if (
            state.get("sql_repair_attempts", 0) >= 2
            and state.get("sql_valid") is not True
        ):

            return {
                **state,
                "results": results,
                "execution_error": execution_error,
                "sql_repair_error": (
                    state.get("sql_repair_error")
                    or state.get("validation_error")
                    or "SQL repair attempts exhausted."
                ),
                "final_answer": (
                    "I couldn't safely generate a valid "
                    "SQL query after multiple repair attempts."
                ),
                "status": "rejected",
            }

        # ==================================================
        # VALIDATION / REPAIR FAILURE
        # ==================================================

        if state.get("status") in {
            "validation_failed",
            "repair_failed",
        }:

            return {
                **state,
                "results": results,
                "execution_error": execution_error,
                "final_answer": (
                    "I couldn't safely generate a valid "
                    "query for that request."
                ),
                "status": "rejected",
            }

        # ==================================================
        # EXECUTION FAILURE
        # ==================================================

        if state.get("status") == "execution_failed":

            return {
                **state,
                "results": results,
                "execution_error": execution_error,
                "final_answer": (
                    "The generated query could not be "
                    "executed."
                ),
                "status": "failed",
            }

        # ==================================================
        # SUCCESS
        # ==================================================

        results = results or []

        return {
            **state,
            "results": results,
            "execution_error": execution_error,
            "final_answer": self.format_final_answer(
                question=state.get("question", ""),
                results=results,
            ),
            "status": "completed",
        }

# ============================================================
# ROUTING
# ============================================================


def route_after_policy(
    state: QueryState,
) -> str:

    if state.get("policy_allowed") is False:
        return "response"

    return "generate"


def route_after_ambiguity(
    state: QueryState,
) -> str:

    if state.get("is_ambiguous") is True:
        return "clarification"

    return "generate"


def route_after_validation(
    state: QueryState,
) -> str:

    # SQL is valid
    if state.get("sql_valid") is True:
        return "execute"

    # Repair budget exhausted
    if state.get("sql_repair_attempts", 0) >= 2:
        return "response"

    # Repair still available
    return "repair"


def route_after_repair(
    state: QueryState,
) -> str:

    # Always validate the repaired SQL.
    return "validate"


def route_after_execution(
    state: QueryState,
) -> str:

    # Execution completed successfully
    if state.get("execution_error") is None:
        return "response"

    # Execution failed.
    # Do not repair here.
    # SQL repair is handled only by the
    # SQL validation -> repair loop.
    return "response"
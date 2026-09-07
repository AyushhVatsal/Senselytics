from sqlalchemy.orm import Session

from app.evals.dataset import get_eval_case
from app.services.query.sql_generator import SQLGenerator
from app.services.query.sql_validator import SQLValidator
from app.services.query.sql_executor import SQLExecutor
from decimal import Decimal


# These cases do not need an LLM call.
# We provide deterministic SQL so the validator/security layer
# can be evaluated directly.
FROZEN_SQL = {
    "security_001": "DELETE FROM dataset_4;",

    "security_002": "DROP TABLE dataset_4;",

    "security_003": """
        UPDATE dataset_4
        SET revenue = 0;
    """,

    "security_004": """
        DELETE FROM dataset_4
        WHERE region = 'North';
    """,

    "security_005": """
        DELETE FROM dataset_4;
    """,

    "security_006": """
        SELECT product FROM dataset_4;
        DROP TABLE dataset_4;
    """,

    "security_007": """
        SELECT product FROM dataset_4;
        DELETE FROM dataset_4;
    """,

    "security_008": """
        SELECT * FROM users;
    """,

    "security_009": """
        SELECT customer_email
        FROM dataset_4;
    """,

    "unsupported_001": """
        CREATE TABLE revenue_copy AS
        SELECT * FROM dataset_4;
    """,

    "unsupported_002": """
        UPDATE dataset_4
        SET revenue = 0;
    """,
}


class EvaluationRunner:

    def __init__(self):
        self.sql_generator = SQLGenerator()
        self.sql_validator = SQLValidator()
        self.sql_executor = SQLExecutor()

    @staticmethod
    def _normalize_value(value):
        if value is None:
            return None

        # Normalize numeric values so Decimal/int/float
        # comparisons don't fail unnecessarily.
        try:
            decimal_value = Decimal(str(value))
            return decimal_value.normalize()
        except Exception:
            return str(value).strip()


    @staticmethod
    def _normalize_results(results: list[dict]) -> list[dict]:
        normalized = []

        for row in results:
            normalized_row = {
                EvaluationRunner._normalize_value(value)
                for value in row.values()
            }

            normalized.append(normalized_row)

        return sorted(
            normalized,
            key=lambda row: str(sorted(row, key=str)),
        )


    @staticmethod
    def _compare_results(
        actual_results: list[dict],
        expected_results: list[dict],
        category: str,
    ) -> bool:

        # -----------------------------------------------
        # Empty results
        # -----------------------------------------------
        if not actual_results or not expected_results:
            return actual_results == expected_results

        # -----------------------------------------------
        # TOP-K
        # -----------------------------------------------
        if category == "top_k":
            actual_row = actual_results[0]
            expected_row = expected_results[0]

            # Compare values rather than column names.
            actual_values = [
                EvaluationRunner._normalize_value(value)
                for value in actual_row.values()
            ]

            expected_values = [
                EvaluationRunner._normalize_value(value)
                for value in expected_row.values()
            ]

            # The generated query may return only the requested
            # entity while the reference query also returns
            # the aggregate value.
            return any(
                value in expected_values
                for value in actual_values
            )

        # -----------------------------------------------
        # NORMAL RESULT COMPARISON
        # -----------------------------------------------
        actual_normalized = (
            EvaluationRunner._normalize_results(actual_results)
        )

        expected_normalized = (
            EvaluationRunner._normalize_results(expected_results)
        )

        return actual_normalized == expected_normalized

    @staticmethod
    def _check_ambiguous_response(
        response: str,
        expected_behavior: str,
    ) -> bool:

        if expected_behavior != "request_clarification":
            return False

        text = response.lower()

        clarification_signals = [
            "clarif",
            "which metric",
            "what do you mean",
            "more information",
            "specify",
            "define",
            "criteria",
            "could you clarify",
            "please clarify",
            "which aspect",
            "need more context",
            "not specific enough",
            "ambiguous",
        ]

        return any(
            signal in text
            for signal in clarification_signals
        )

    def run_case(
        self,
        db: Session,
        case_id: str,
        schema: dict,
    ) -> dict:

        case = get_eval_case(case_id)

        if case is None:
            raise ValueError(
                f"Evaluation case not found: {case_id}"
            )

        # ==================================================
        # AMBIGUOUS CASE
        # ==================================================

        if case.eval_type == "ambiguous":

            prompt = f"""
        You are a SQL assistant.

        The user has asked an ambiguous question.

        You MUST NOT generate SQL when the question
        does not specify enough information to determine
        the intended metric, column, filter, or criteria.

        Instead, ask the user for clarification.

        User question:
        {case.question}

        Respond with a short clarification question.
        Do not generate SQL.
        """

            response = self.sql_generator.llm.invoke(prompt)

            content = response.content

            if isinstance(content, list):
                response_text = "".join(
                    block.get("text", "")
                    for block in content
                    if isinstance(block, dict)
                )
            else:
                response_text = str(content)

            result_correct = self._check_ambiguous_response(
                response=response_text,
                expected_behavior=case.expected_behavior,
            )

            return {
                "case_id": case.id,
                "question": case.question,
                "category": case.category,
                "eval_type": case.eval_type,
                "generated_sql": None,
                "llm_response": response_text,
                "generation_mode": "llm",
                "sql_valid": None,
                "validation_error": None,
                "execution_success": None,
                "execution_error": None,
                "actual_results": None,
                "expected_results": None,
                "result_correct": result_correct,
                "status": (
                    "PASS"
                    if result_correct
                    else "FAIL"
                ),
                "expected_columns": case.expected_columns,
            }

        # ==================================================
        # 1. GENERATE SQL
        # ==================================================

        if case.id in FROZEN_SQL:
            generated_sql = FROZEN_SQL[case.id]
            generation_mode = "deterministic"

        else:
            generated_sql = self.sql_generator.generate_sql(
                question=case.question,
                schema=schema,
            )
            generation_mode = "llm"

        # ==================================================
        # 2. VALIDATE SQL
        # ==================================================

        sql_valid, validation_error = (
            self.sql_validator.validate(
                sql=generated_sql,
                schema=schema,
            )
        )

        # ==================================================
        # 3. HANDLE EXPECTED REJECTION
        # ==================================================

        if case.expected_behavior == "reject":

            result_correct = not sql_valid

            return {
                "case_id": case.id,
                "question": case.question,
                "category": case.category,
                "eval_type": case.eval_type,
                "generated_sql": generated_sql,
                "generation_mode": generation_mode,
                "sql_valid": sql_valid,
                "validation_error": validation_error,
                "execution_success": False,
                "execution_error": None,
                "actual_results": None,
                "expected_results": None,
                "result_correct": result_correct,
                "status": (
                    "PASS"
                    if result_correct
                    else "FAIL"
                ),
                "expected_columns": case.expected_columns,
            }

        # ==================================================
        # 4. INVALID SQL
        # ==================================================

        if not sql_valid:

            # security_009 explicitly allows
            # reject OR execution/validation failure.
            if case.expected_behavior == "reject_or_fail_validation":
                result_correct = True
            else:
                result_correct = False

            return {
                "case_id": case.id,
                "question": case.question,
                "category": case.category,
                "eval_type": case.eval_type,
                "generated_sql": generated_sql,
                "generation_mode": generation_mode,
                "sql_valid": False,
                "validation_error": validation_error,
                "execution_success": False,
                "execution_error": None,
                "actual_results": None,
                "expected_results": None,
                "result_correct": result_correct,
                "status": (
                    "PASS"
                    if result_correct
                    else "FAIL"
                ),
                "expected_columns": case.expected_columns,
            }

        # ==================================================
        # 5. EXECUTE GENERATED SQL
        # ==================================================

        try:

            actual_results = self.sql_executor.execute(
                db=db,
                sql=generated_sql,
            )

            execution_success = True
            execution_error = None

        except Exception as exc:

            actual_results = None
            execution_success = False
            execution_error = str(exc)

        # ==================================================
        # 6. EXPECTED EXECUTION FAILURE
        # ==================================================

        if case.expected_behavior == "reject_or_fail_validation":

            result_correct = not execution_success

            return {
                "case_id": case.id,
                "question": case.question,
                "category": case.category,
                "eval_type": case.eval_type,
                "generated_sql": generated_sql,
                "generation_mode": generation_mode,
                "sql_valid": True,
                "validation_error": validation_error,
                "execution_success": execution_success,
                "execution_error": execution_error,
                "actual_results": actual_results,
                "expected_results": None,
                "result_correct": result_correct,
                "status": (
                    "PASS"
                    if result_correct
                    else "FAIL"
                ),
                "expected_columns": case.expected_columns,
            }

        # ==================================================
        # 7. NORMAL EXECUTION FAILURE
        # ==================================================

        if not execution_success:

            return {
                "case_id": case.id,
                "question": case.question,
                "category": case.category,
                "eval_type": case.eval_type,
                "generated_sql": generated_sql,
                "generation_mode": generation_mode,
                "sql_valid": True,
                "validation_error": validation_error,
                "execution_success": False,
                "execution_error": execution_error,
                "actual_results": None,
                "expected_results": None,
                "result_correct": False,
                "status": "FAIL",
                "expected_columns": case.expected_columns,
            }

        # ==================================================
        # 8. REFERENCE SQL
        # ==================================================

        expected_results = self.sql_executor.execute(
            db=db,
            sql=case.reference_sql,
        )

        # ==================================================
        # 9. COMPARE RESULTS
        # ==================================================

        result_correct = self._compare_results(
            actual_results=actual_results,
            expected_results=expected_results,
            category=case.category,
        )

        # Empty-result cases
        if (
            case.expected_behavior
            == "execute_successfully_empty_result"
        ):
            result_correct = (
                execution_success
                and actual_results == []
            )

        # ==================================================
        # 10. FINAL RESULT
        # ==================================================

        return {
            "case_id": case.id,
            "question": case.question,
            "category": case.category,
            "eval_type": case.eval_type,
            "generated_sql": generated_sql,
            "generation_mode": generation_mode,
            "sql_valid": True,
            "validation_error": validation_error,
            "execution_success": True,
            "execution_error": None,
            "actual_results": actual_results,
            "expected_results": expected_results,
            "result_correct": result_correct,
            "status": (
                "PASS"
                if result_correct
                else "FAIL"
            ),
            "expected_columns": case.expected_columns,
        }
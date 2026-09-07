class EvaluationMetrics:

    @staticmethod
    def calculate(results: list[dict]) -> dict:

        total = len(results)

        if total == 0:
            return {
                "total": 0,
                "passed": 0,
                "failed": 0,
                "pass_rate": 0.0,
                "sql_validity_rate": 0.0,
                "execution_success_rate": 0.0,
                "result_accuracy": 0.0,
            }

        passed = sum(
            result["status"] == "PASS"
            for result in results
        )

        failed = total - passed

        # Only evaluate SQL validity for cases where
        # successful SQL generation is expected.
        sql_expected = [
            result
            for result in results
            if result.get("expected_results") is not None
            or result.get("eval_type") == "normal"
        ]

        sql_valid = sum(
            result.get("sql_valid") is True
            for result in sql_expected
        )

        execution_success = sum(
            result.get("execution_success") is True
            for result in sql_expected
        )

        result_correct = sum(
            result.get("result_correct") is True
            for result in results
        )

        return {
            "total": total,
            "passed": passed,
            "failed": failed,

            "pass_rate": round(
                passed / total * 100,
                2,
            ),

            "sql_validity_rate": round(
                sql_valid / len(sql_expected) * 100,
                2,
            ) if sql_expected else 0.0,

            "execution_success_rate": round(
                execution_success / len(sql_expected) * 100,
                2,
            ) if sql_expected else 0.0,

            "result_accuracy": round(
                result_correct / total * 100,
                2,
            ),
        }

    @staticmethod
    def calculate_by_category(
        results: list[dict],
    ) -> dict:

        categories = {}

        for result in results:
            category = result["category"]

            categories.setdefault(
                category,
                [],
            ).append(result)

        output = {}

        for category, category_results in categories.items():

            output[category] = (
                EvaluationMetrics.calculate(
                    category_results
                )
            )

        return output
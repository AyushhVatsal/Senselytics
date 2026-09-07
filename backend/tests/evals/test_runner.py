from app.evals.dataset import EVAL_CASES
from app.evals.runner import EvaluationRunner
from app.evals.metrics import EvaluationMetrics


def test_run_all_evaluation_cases(db_session):

    schema = {
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
    }

    runner = EvaluationRunner()

    results = []

    for case in EVAL_CASES:
        result = runner.run_case(
            db=db_session,
            case_id=case.id,
            schema=schema,
        )
        results.append(result)

        print("\n" + "=" * 70)
        print(f"Case: {result['case_id']}")
        print(f"Question: {result['question']}")
        print(f"Category: {result['category']}")
        print(f"Eval type: {result['eval_type']}")
        print(
            f"Generation mode: "
            f"{result.get('generation_mode', 'llm')}"
        )
        print(f"SQL Valid: {result['sql_valid']}")
        print(
            f"Execution Success: "
            f"{result['execution_success']}"
        )
        print(
            f"Result Correct: "
            f"{result['result_correct']}"
        )
        print(f"Status: {result['status']}")
        print(f"Generated SQL: {result.get('generated_sql')}")

    failures = [
        result
        for result in results
        if result["status"] != "PASS"
    ]

    metrics = EvaluationMetrics.calculate(results)

    category_metrics = (
        EvaluationMetrics.calculate_by_category(results)
    )

    print("\n" + "=" * 70)
    print("EVALUATION SUMMARY")
    print("=" * 70)

    print(f"Total cases:          {metrics['total']}")
    print(f"Passed:               {metrics['passed']}")
    print(f"Failed:               {metrics['failed']}")
    print(f"Pass rate:            {metrics['pass_rate']}%")
    print(
        f"SQL validity rate:    "
        f"{metrics['sql_validity_rate']}%"
    )
    print(
        f"Execution success:    "
        f"{metrics['execution_success_rate']}%"
    )
    print(
        f"Result accuracy:      "
        f"{metrics['result_accuracy']}%"
    )

    print("\nCATEGORY METRICS")
    print("-" * 70)

    for category, category_result in category_metrics.items():

        print(
            f"{category:20} "
            f"{category_result['passed']}/"
            f"{category_result['total']} "
            f"({category_result['pass_rate']}%)"
        )

    if failures:

        print("\nFAILURES")
        print("-" * 70)

        for result in failures:

            print(
                f"{result['case_id']}: "
                f"{result['question']}"
            )

    assert not failures, (
        f"{len(failures)} evaluation case(s) failed."
    )
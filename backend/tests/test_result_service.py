from app.services.query.result_service import ResultService


def test_process_results():

    results = [
        {
            "product": "Phone",
            "total_revenue": 50000,
        },
        {
            "product": "Laptop",
            "total_revenue": 40000,
        },
    ]

    processed = ResultService.process_results(results)

    assert processed["row_count"] == 2

    assert processed["columns"] == [
        "product",
        "total_revenue",
    ]

    assert processed["rows"] == results

    assert processed["message"] == "Results retrieved successfully."


def test_empty_results():

    processed = ResultService.process_results([])

    assert processed["row_count"] == 0
    assert processed["columns"] == []
    assert processed["rows"] == []
    assert processed["message"] == "No results found."
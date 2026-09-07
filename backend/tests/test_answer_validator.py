from app.services.query.answer_validator import AnswerValidator


def test_valid_answer():

    answer = (
        "The product that generated the most revenue "
        "is Phone, with a total revenue of 2,490,000."
    )

    results = [
        {
            "product": "Phone",
            "total_revenue": "2490000",
        }
    ]

    is_valid, message = AnswerValidator.validate(
        answer=answer,
        results=results,
    )

    assert is_valid is True
    assert message == "Answer is valid."


def test_reject_empty_answer():

    is_valid, message = AnswerValidator.validate(
        answer="",
        results=[
            {"product": "Phone"}
        ],
    )

    assert is_valid is False


def test_reject_sql_in_answer():

    is_valid, message = AnswerValidator.validate(
        answer="SELECT * FROM dataset_4;",
        results=[
            {"product": "Phone"}
        ],
    )

    assert is_valid is False


def test_reject_unsupported_number():

    is_valid, message = AnswerValidator.validate(
        answer="Phone generated 5,000,000 in revenue.",
        results=[
            {
                "product": "Phone",
                "total_revenue": "2490000",
            }
        ],
    )

    assert is_valid is False


def test_accept_supported_number():

    is_valid, message = AnswerValidator.validate(
        answer="Phone generated 2,490,000 in revenue.",
        results=[
            {
                "product": "Phone",
                "total_revenue": "2490000",
            }
        ],
    )

    assert is_valid is True


def test_empty_results():

    is_valid, message = AnswerValidator.validate(
        answer="No matching data was found.",
        results=[],
    )

    assert is_valid is True


def test_reject_bad_empty_result_answer():

    is_valid, message = AnswerValidator.validate(
        answer="Phone generated the most revenue.",
        results=[],
    )

    assert is_valid is False
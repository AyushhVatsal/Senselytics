from app.services.query.answer_generator import AnswerGenerator


def test_answer_generator():

    generator = AnswerGenerator()

    answer = generator.generate_answer(
        question="Which product generated the most revenue?",
        sql="""
        SELECT product
        FROM dataset_4
        GROUP BY product
        ORDER BY SUM(revenue) DESC
        LIMIT 1;
        """,
        results=[
            {
                "product": "Phone"
            }
        ],
    )

    print("\nGenerated answer:")
    print(answer)

    assert isinstance(answer, str)
    assert len(answer) > 0
    assert "phone" in answer.lower()
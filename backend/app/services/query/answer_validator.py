import re


class AnswerValidator:

    @staticmethod
    def validate(
        answer: str,
        results: list[dict],
    ) -> tuple[bool, str]:

        # 1. Answer must exist
        if not answer or not answer.strip():
            return False, "Generated answer is empty."

        # 2. Handle empty results
        if not results:

            empty_phrases = [
                "no data",
                "no matching",
                "no results",
                "not found",
                "could not find",
            ]

            answer_lower = answer.lower()

            if not any(
                phrase in answer_lower
                for phrase in empty_phrases
            ):
                return False, "Answer does not correctly handle empty results."

            return True, "Answer is valid."

        # 3. Reject SQL appearing in the answer
        sql_keywords = [
            "SELECT ",
            "INSERT ",
            "UPDATE ",
            "DELETE ",
            "DROP ",
            "ALTER ",
            "CREATE ",
            "TRUNCATE ",
        ]

        answer_upper = answer.upper()

        for keyword in sql_keywords:
            if keyword in answer_upper:
                return False, "Answer contains SQL."

        # 4. Check numerical claims against result values
        result_text = " ".join(
            str(value)
            for row in results
            for value in row.values()
        )

        numbers_in_answer = re.findall(
            r"\b\d+(?:,\d{3})*(?:\.\d+)?\b",
            answer,
        )

        for number in numbers_in_answer:

            normalized_number = number.replace(",", "")

            if normalized_number not in result_text.replace(",", ""):
                return False, (
                    f"Answer contains unsupported numerical value: {number}"
                )

        return True, "Answer is valid."
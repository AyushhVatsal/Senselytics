class ResultService:

    @staticmethod
    def process_results(
        results: list[dict],
    ) -> dict:

        # No rows returned
        if not results:
            return {
                "row_count": 0,
                "columns": [],
                "rows": [],
                "message": "No results found.",
            }

        # Extract column names from the first row
        columns = list(results[0].keys())

        return {
            "row_count": len(results),
            "columns": columns,
            "rows": results,
            "message": "Results retrieved successfully.",
        }
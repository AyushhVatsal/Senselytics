import re


class SQLValidator:
    FORBIDDEN_KEYWORDS = {
        "INSERT",
        "UPDATE",
        "DELETE",
        "DROP",
        "ALTER",
        "CREATE",
        "TRUNCATE",
        "GRANT",
        "REVOKE",
    }

    @staticmethod
    def validate(
        sql: str,
        schema: dict,
    ) -> tuple[bool, str]:

        if not sql or not sql.strip():
            return False, "SQL query is empty."

        sql = sql.strip()

        # Remove one trailing semicolon.
        normalized_sql = sql.rstrip(";").strip()

        # =========================================================
        # 1. Only one SQL statement is allowed.
        # =========================================================

        if ";" in normalized_sql:
            return False, "Multiple SQL statements are not allowed."

        # =========================================================
        # 2. Remove SQL comments before validation.
        # =========================================================

        sql_without_comments = re.sub(
            r"--.*?$",
            "",
            normalized_sql,
            flags=re.MULTILINE,
        )

        sql_without_comments = re.sub(
            r"/\*.*?\*/",
            "",
            sql_without_comments,
            flags=re.DOTALL,
        ).strip()

        if not sql_without_comments:
            return False, "SQL query is empty."

        # =========================================================
        # 3. Query must start with SELECT or WITH.
        # =========================================================

        if not re.match(
            r"^(SELECT|WITH)\b",
            sql_without_comments,
            re.IGNORECASE,
        ):
            return False, "Only SELECT queries are allowed."

        # =========================================================
        # 4. Reject dangerous SQL operations.
        # =========================================================

        for keyword in SQLValidator.FORBIDDEN_KEYWORDS:
            if re.search(
                rf"\b{keyword}\b",
                sql_without_comments,
                re.IGNORECASE,
            ):
                return False, f"Forbidden SQL operation: {keyword}."

        # =========================================================
        # 5. Verify the requested dataset table is present.
        # =========================================================

        table_name = schema["table_name"]

        if not re.search(
            rf"\b{re.escape(table_name)}\b",
            sql_without_comments,
            re.IGNORECASE,
        ):
            return False, f"Query must use table '{table_name}'."

        # =========================================================
        # 6. Allowed schema columns.
        # =========================================================

        allowed_columns = {
            column["name"].lower()
            for column in schema["columns"]
        }

        # =========================================================
        # 7. Allowed SQL keywords/functions.
        # =========================================================

        allowed_sql_tokens = {
            "SELECT",
            "FROM",
            "WHERE",
            "GROUP",
            "BY",
            "ORDER",
            "LIMIT",
            "OFFSET",
            "ASC",
            "DESC",
            "AS",
            "AND",
            "OR",
            "NOT",
            "NULL",
            "IS",
            "IN",
            "LIKE",
            "ILIKE",
            "BETWEEN",
            "CASE",
            "WHEN",
            "THEN",
            "ELSE",
            "END",
            "DISTINCT",
            "HAVING",
            "JOIN",
            "INNER",
            "LEFT",
            "RIGHT",
            "FULL",
            "OUTER",
            "ON",
            "UNION",
            "ALL",
            "TRUE",
            "FALSE",

            # Aggregate functions
            "COUNT",
            "SUM",
            "AVG",
            "MIN",
            "MAX",

            # Common functions
            "COALESCE",
            "ROUND",
            "DATE",
            "EXTRACT",

            # PostgreSQL / SQL types and constructs
            "CAST",
            "AS",
            "INTERVAL",

            # Join / query helpers
            "USING",

            # Window functions / clauses
            "OVER",
            "PARTITION",
            "ROW_NUMBER",
            "RANK",
            "DENSE_RANK",

            # Common date/time tokens
            "YEAR",
            "MONTH",
            "DAY",
            "HOUR",
            "MINUTE",
            "SECOND",
        }

        allowed_tokens = {
            token.lower()
            for token in allowed_sql_tokens
        }

        # =========================================================
        # 8. Extract identifiers.
        #
        # This is intentionally NOT a complete SQL parser.
        # It is a V1 sanity check for detecting obvious unknown
        # column references such as:
        #
        #     SELECT product, invalid_column
        #
        # =========================================================

        sql_for_identifier_validation = re.sub(
            r"'(?:''|[^'])*'",
            "",
            sql_without_comments,
        )

        identifiers = re.findall(
            r"\b[a-zA-Z_][a-zA-Z0-9_]*\b",
            sql_for_identifier_validation,
        )

        # =========================================================
        # 9. Track aliases.
        #
        # Example:
        #
        #     SUM(revenue) AS total_revenue
        #
        # total_revenue is not a schema column, but it is a valid
        # SQL alias and may later appear in ORDER BY.
        # =========================================================

        aliases = set(
            alias.lower()
            for alias in re.findall(
                r"\bAS\s+([a-zA-Z_][a-zA-Z0-9_]*)",
                sql_without_comments,
                re.IGNORECASE,
            )
        )

        # Also support simple aliases without AS:
        #
        #     SUM(revenue) total_revenue
        #
        # We keep this intentionally limited rather than attempting
        # full SQL parsing.

        # =========================================================
        # 10. Validate identifiers.
        # =========================================================

        for identifier in identifiers:

            identifier_lower = identifier.lower()

            # SQL keyword/function
            if identifier_lower in allowed_tokens:
                continue

            # Dataset table
            if identifier_lower == table_name.lower():
                continue

            # Actual schema column
            if identifier_lower in allowed_columns:
                continue

            # SQL alias
            if identifier_lower in aliases:
                continue

            # =====================================================
            # Function names
            #
            # If an identifier is immediately followed by "(",
            # treat it as a function name.
            #
            # This allows functions that are not explicitly listed
            # above without incorrectly rejecting them.
            # =====================================================

            function_pattern = rf"\b{re.escape(identifier)}\s*\("

            if re.search(
                function_pattern,
                sql_without_comments,
                re.IGNORECASE,
            ):
                continue

            # =====================================================
            # Numeric identifiers are not relevant here.
            # =====================================================

            if identifier.isdigit():
                continue

            # =====================================================
            # Unknown identifier.
            #
            # THIS is the important change for SQL repair.
            #
            # Example:
            #
            # SELECT product, invalid_column
            #
            # invalid_column is neither:
            # - a SQL keyword
            # - a table
            # - a schema column
            # - an alias
            #
            # Therefore validation fails and the graph can route
            # to repair_sql.
            # =====================================================

            return (
                False,
                f"Unknown column or identifier: '{identifier}'.",
            )

        # =========================================================
        # 11. Validation successful.
        # =========================================================

        return True, "SQL query is valid."
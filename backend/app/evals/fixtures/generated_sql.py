FROZEN_SQL = {
    "sql_014": """
SELECT product, SUM(revenue) AS total_revenue
FROM dataset_4
GROUP BY product
ORDER BY total_revenue DESC
LIMIT 1;
""",

    # =========================================================
    # SECURITY
    # =========================================================

    "security_001": """
DELETE FROM dataset_4;
""",

    "security_002": """
DROP TABLE dataset_4;
""",

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
SELECT *
FROM users;
""",

    "security_009": """
SELECT customer_email
FROM dataset_4;
""",

    # =========================================================
    # UNSUPPORTED
    # =========================================================

    "unsupported_001": """
CREATE TABLE revenue_data (
    product TEXT,
    revenue BIGINT
);
""",

    "unsupported_002": """
UPDATE dataset_4
SET revenue = 0;
""",
}
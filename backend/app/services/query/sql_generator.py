import os

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq

load_dotenv()


class SQLGenerator:

    def __init__(self):
        provider = os.getenv("LLM_PROVIDER", "gemini").lower()

        if provider == "groq":
            self.llm = ChatGroq(
                model=os.getenv(
                    "GROQ_MODEL",
                    "openai/gpt-oss-20b",
                ),
                temperature=0,
            )

        elif provider == "gemini":
            self.llm = ChatGoogleGenerativeAI(
                model=os.getenv(
                    "GEMINI_MODEL",
                    "gemini-3.6-flash",
                ),
                temperature=0,
            )

        else:
            raise ValueError(
                f"Unsupported LLM provider: {provider}"
            )

    @staticmethod
    def _sql_style_guide() -> str:
        return """
    IMPORTANT SQL SEMANTIC RULES:

    A. FILTERING QUESTIONS
    If the user asks "which <column>" or "what <column>" and the
    question specifies filters, return ONLY the requested column.

    If the requested column is categorical/textual, use DISTINCT.

    Example:
    Question:
    Which products were sold in the North region?

    Correct:
    SELECT DISTINCT product
    FROM some_table
    WHERE region = 'North';

    Do NOT return region in SELECT because region is only a filter.

    ---

    B. MULTIPLE FILTERS
    If multiple exact conditions are stated, use AND.

    Example:
    Question:
    Which products were sold in the North region and belong to Electronics?

    Correct:
    SELECT DISTINCT product
    FROM some_table
    WHERE region = 'North'
    AND category = 'Electronics';

    Do NOT select region or category unless the question asks to show them.

    ---

    C. "PER" / RATIO QUESTIONS
    When the question asks for X per Y, calculate:

    SUM(X) / NULLIF(SUM(Y), 0)

    If the question says "for each <group>", include that grouping
    column and GROUP BY it.

    Example:
    Question:
    What is the total revenue per unit sold for each product?

    Correct:
    SELECT
        product,
        SUM(revenue) / NULLIF(SUM(quantity), 0) AS revenue_per_unit
    FROM some_table
    GROUP BY product;

    Do NOT return:
    product, SUM(revenue), SUM(quantity)

    The requested value is the ratio, not the two separate totals.

    ---

    D. CONTAINS / SUBSTRING SEARCH
    If the question uses words such as:
    "contains", "contain", "includes", "include", "has", or
    "word <value>"

    use PostgreSQL case-insensitive substring matching:

    column ILIKE '%value%'

    Example:
    Question:
    Which products contain the word phone?

    Correct:
    SELECT DISTINCT product
    FROM some_table
    WHERE product ILIKE '%phone%';

    Do NOT use:
    product = 'phone'

    ---

    E. EXACT VALUE FILTERS
    If the question specifies an exact categorical value such as:

    "in the North region"
    "in the Electronics category"

    use equality:

    region = 'North'
    category = 'Electronics'

    Do NOT use ILIKE for exact-value filtering.

    ---

    F. SELECT ONLY WHAT THE USER REQUESTED
    Never add columns simply because they are mentioned in WHERE.

    Question:
    Which products are in North?

    Correct:
    SELECT DISTINCT product ...

    Incorrect:
    SELECT DISTINCT product, region ...

    Question:
    Which products are in North and Electronics?

    Correct:
    SELECT DISTINCT product ...

    Incorrect:
    SELECT DISTINCT product, region, category ...

    ---

    G. GENERAL RULE
    First identify:
    1. What does the user want returned?
    2. What columns are only being used as filters?
    3. Whether DISTINCT is required.
    4. Whether the question asks for a ratio/per-unit calculation.
    5. Whether text matching is exact or substring matching.

    Then generate the SQL.

    Return only valid PostgreSQL SQL.
    """

    def generate_sql(
        self,
        question: str,
        schema: dict,
    ) -> str:

        table_name = schema["table_name"]

        columns = "\n".join(
            f"- {column['name']} ({column['type']})"
            for column in schema["columns"]
        )

        prompt = f"""
        You are an expert PostgreSQL text-to-SQL system.

        Your task is to convert the user's natural-language question
        into ONE correct PostgreSQL SELECT query.

        DATABASE TABLE:
        {table_name}

        AVAILABLE COLUMNS:
        {columns}

        USER QUESTION:
        {question}

        SECURITY RULES:
        1. Use ONLY the table above.
        2. Use ONLY the columns above.
        3. Generate exactly ONE SQL statement.
        4. Generate SELECT/read-only SQL only.
        5. Never use INSERT, UPDATE, DELETE, DROP, ALTER, CREATE,
        TRUNCATE, GRANT, REVOKE, or other database-modifying commands.
        6. Return ONLY SQL. No explanation. No markdown.

        SEMANTIC RULES:
        {self._sql_style_guide()}

        Before producing SQL, internally determine:
        - requested output column(s)
        - filter column(s)
        - aggregation, if any
        - grouping, if any
        - whether DISTINCT is required
        - whether "per" means a ratio of aggregates
        - whether "contains" means ILIKE substring matching

        Do not output this reasoning.

        Return ONLY the final SQL query.
        """

        response = self.llm.invoke(prompt)

        content = response.content

        if isinstance(content, list):
            sql = "".join(
                block.get("text", "")
                for block in content
                if isinstance(block, dict)
            )
        else:
            sql = content

        sql = sql.strip()

        # Remove markdown code fences if the model returns them.
        if sql.startswith("```"):
            sql = sql.replace("```sql", "")
            sql = sql.replace("```", "")
            sql = sql.strip()

        return sql

    def repair_sql(
        self,
        sql: str,
        error: str,
        question: str,
        schema: dict,
    ) -> str:
        table_name = schema["table_name"]

        columns = "\n".join(
            f"- {column['name']} ({column['type']})"
            for column in schema["columns"]
        )

        prompt = f"""
    You are a PostgreSQL SQL repair assistant.

    The original SQL query failed validation or execution.

    Original user question:
    {question}

    Database table:
    {table_name}

    Available columns:
    {columns}

    Original SQL:
    {sql}

    Error:
    {error}

    Generate a corrected SQL query that answers the original
    user question.

    Rules:

    1. Generate PostgreSQL SQL only.
    2. Use only the table and columns provided above.
    3. Do not modify the database.
    4. Do not use INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, or TRUNCATE.
    5. Generate exactly one SQL statement.
    6. Return only the corrected SQL query.
    {self._sql_style_guide()}
    """

        response = self.llm.invoke(prompt)

        content = response.content

        if isinstance(content, list):
            repaired_sql = "".join(
                block.get("text", "")
                for block in content
                if isinstance(block, dict)
            )
        else:
            repaired_sql = content

        repaired_sql = repaired_sql.strip()

        if repaired_sql.startswith("```"):
            repaired_sql = repaired_sql.replace("```sql", "")
            repaired_sql = repaired_sql.replace("```", "")
            repaired_sql = repaired_sql.strip()

        return repaired_sql
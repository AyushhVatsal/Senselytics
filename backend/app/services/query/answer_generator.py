from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI


load_dotenv()


class AnswerGenerator:

    def __init__(self):

        self.llm = ChatGoogleGenerativeAI(
            model="gemini-3.6-flash",
        )

    def generate_answer(
        self,
        question: str,
        sql: str,
        results: list[dict],
    ) -> str:

        prompt = f"""
You are a data analysis assistant.

Answer the user's question using ONLY the SQL query and
the database results provided below.

User question:
{question}

SQL query:
{sql}

Database results:
{results}

Rules:

1. Answer using only the provided database results.
2. Do not invent or assume any information.
3. Do not perform calculations using information that is not provided.
4. If the results are empty, clearly state that no matching data was found.
5. Be concise and directly answer the user's question.
6. Do not mention that you are an AI.
7. Do not output SQL.
8. Return only the natural-language answer.
"""

        response = self.llm.invoke(prompt)

        content = response.content

        # Gemini may return either a string or structured content.
        if isinstance(content, list):

            answer = "".join(
                block.get("text", "")
                for block in content
                if isinstance(block, dict)
            )

        else:
            answer = content

        return answer.strip()
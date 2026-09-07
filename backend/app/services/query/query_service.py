from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from fastapi.responses import StreamingResponse

from app.services.dataset_service import DatasetService
from app.services.query.schema_service import SchemaService
from app.services.query.graph.workflow import build_query_graph

import json

from langgraph.types import Command


class QueryService:

    @staticmethod
    def process_query(
        db: Session,
        user_id: int,
        dataset_id: int,
        question: str,
        thread_id: str,
    ) -> dict:

        # ==================================================
        # 1. Verify dataset
        # ==================================================

        dataset = DatasetService.get_dataset(
            db=db,
            user_id=user_id,
            dataset_id=dataset_id,
        )

        if dataset.status != "ready":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Dataset is not ready for querying.",
            )

        # ==================================================
        # 2. Retrieve schema
        # ==================================================

        schema = SchemaService.get_dataset_schema(
            db=db,
            table_name=dataset.table_name,
        )

        # ==================================================
        # 3. Build graph
        # ==================================================

        graph = build_query_graph(db)

        # ==================================================
        # 4. Initial state
        # ==================================================

        initial_state = {
            "question": question,
            "schema": schema,
            "dataset_id": dataset.id,
        }

        # ==================================================
        # 5. Thread configuration
        # ==================================================

        config = {
            "configurable": {
                "thread_id": thread_id,
            }
        }

        # ==================================================
        # 6. Execute graph
        # ==================================================

        result = graph.invoke(
            initial_state,
            config=config,
        )

        # ==================================================
        # 7. HITL interrupt
        # ==================================================

        if "__interrupt__" in result:

            interrupt_data = (
                result["__interrupt__"][0].value
            )

            return {
                "dataset_id": dataset.id,
                "question": question,
                "status": "clarification_required",
                "thread_id": thread_id,
                "clarification_question": (
                    interrupt_data.get("question")
                ),
            }

        # ==================================================
        # 8. Graph completed
        # ==================================================

        return {
            "dataset_id": dataset.id,
            "question": result.get(
                "question",
                question,
            ),
            "sql": result.get("sql"),
            "results": result.get("results") or [],
            "answer": result.get("final_answer"),
            "status": result.get("status"),
            "thread_id": thread_id,
            "clarification_question": None,
        }

    # ======================================================
    # STREAMING QUERY
    # ======================================================

    @staticmethod
    def stream_query(
        db: Session,
        user_id: int,
        dataset_id: int,
        question: str,
        thread_id: str,
    ):

        # ==================================================
        # 1. Verify dataset
        # ==================================================

        dataset = DatasetService.get_dataset(
            db=db,
            user_id=user_id,
            dataset_id=dataset_id,
        )

        if dataset.status != "ready":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Dataset is not ready for querying.",
            )

        # ==================================================
        # 2. Retrieve schema
        # ==================================================

        schema = SchemaService.get_dataset_schema(
            db=db,
            table_name=dataset.table_name,
        )

        # ==================================================
        # 3. Build graph
        # ==================================================

        graph = build_query_graph(db)

        # ==================================================
        # 4. Initial state
        # ==================================================

        initial_state = {
            "question": question,
            "schema": schema,
            "dataset_id": dataset.id,
        }

        # ==================================================
        # 5. Thread configuration
        # ==================================================

        config = {
            "configurable": {
                "thread_id": thread_id,
            }
        }

        # ==================================================
        # 6. Stream generator
        # ==================================================

        def event_generator():

            try:

                for event in graph.stream(
                    initial_state,
                    config=config,
                    stream_mode="updates",
                ):

                    for node_name, node_data in event.items():

                        payload = {
                            "type": "node_update",
                            "node": node_name,
                            "data": node_data,
                        }

                        yield (
                            "data: "
                            + json.dumps(payload, default=str)
                            + "\n\n"
                        )

                # ==========================================
                # 7. Read final graph state
                # ==========================================

                graph_state = graph.get_state(config)

                # ==========================================
                # 8. Human-in-the-loop interruption
                # ==========================================

                if graph_state.interrupts:

                    interrupt_data = (
                        graph_state.interrupts[0].value
                    )

                    payload = {
                        "type": "clarification_required",
                        "thread_id": thread_id,
                        "question": (
                            interrupt_data.get("question")
                            if isinstance(interrupt_data, dict)
                            else str(interrupt_data)
                        ),
                        "reason": (
                            interrupt_data.get("reason")
                            if isinstance(interrupt_data, dict)
                            else None
                        ),
                    }

                    yield (
                        "data: "
                        + json.dumps(payload, default=str)
                        + "\n\n"
                    )

                    return

                # ==========================================
                # 9. Graph completed
                # ==========================================

                result = graph_state.values

                final_result = {
                    "dataset_id": dataset.id,
                    "question": result.get(
                        "question",
                        question,
                    ),
                    "sql": result.get("sql"),
                    "results": (
                        result.get("results") or []
                    ),
                    "answer": result.get(
                        "final_answer"
                    ),
                    "status": result.get("status"),
                    "thread_id": thread_id,
                    "clarification_question": None,
                }

                yield (
                    "data: "
                    + json.dumps(
                        {
                            "type": "completed",
                            "result": final_result,
                        },
                        default=str,
                    )
                    + "\n\n"
                )

            except Exception as exc:

                error_payload = {
                    "type": "error",
                    "error": str(exc),
                }

                yield (
                    "data: "
                    + json.dumps(
                        error_payload,
                        default=str,
                    )
                    + "\n\n"
                )

        # ==================================================
        # 10. Return SSE response
        # ==================================================

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )
    
    # ======================================================
    # RESUME QUERY
    # ======================================================

    @staticmethod
    def resume_query(
        db: Session,
        thread_id: str,
        answer: str,
    ) -> dict:

        graph = build_query_graph(db)

        config = {
            "configurable": {
                "thread_id": thread_id,
            }
        }

        # ==================================================
        # 1. Get existing checkpoint
        # ==================================================

        state = graph.get_state(config)

        if not state.values:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Query thread not found or checkpoint expired.",
            )

        dataset_id = state.values.get("dataset_id")
        question = state.values.get("question")

        # ==================================================
        # 2. Resume interrupted graph
        # ==================================================

        result = graph.invoke(
            Command(resume=answer),
            config=config,
        )

        # ==================================================
        # 3. Still waiting for clarification
        # ==================================================

        if "__interrupt__" in result:

            interrupt_data = (
                result["__interrupt__"][0].value
            )

            return {
                "dataset_id": dataset_id,
                "question": question,
                "status": "clarification_required",
                "thread_id": thread_id,
                "clarification_question": (
                    interrupt_data.get("question")
                    if isinstance(interrupt_data, dict)
                    else str(interrupt_data)
                ),
                "sql": None,
                "results": None,
                "answer": None,
            }

        # ==================================================
        # 4. Graph completed
        # ==================================================

        return {
            "dataset_id": result.get(
                "dataset_id",
                dataset_id,
            ),
            "question": result.get(
                "question",
                question,
            ),
            "sql": result.get("sql"),
            "results": result.get("results") or [],
            "answer": result.get("final_answer"),
            "status": result.get("status"),
            "thread_id": thread_id,
            "clarification_question": (
                result.get("clarification_question")
                if result.get("status")
                == "clarification_required"
                else None
            ),
        }
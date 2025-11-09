# import os
import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from .models.schemas import CardCreate, CardResponse, CardUpdate, ColumnType

# ADR-001
# JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-in-production")
# DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")
# APP_ENV = os.getenv("APP_ENV", "development")

app = FastAPI(title="Idea Kanban API", version="0.1.0")


# ADR-002
class ProblemDetails(Exception):

    def __init__(
        self,
        status_code: int,
        title: str,
        detail: str,
        error_type: str = None,
        correlation_id: str = None,
    ):
        self.status = status_code
        self.title = title
        self.detail = detail
        self.type = error_type or "about:blank"
        self.correlation_id = correlation_id


class ApiError(ProblemDetails):
    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 400,
        correlation_id: str = None,
    ):
        super().__init__(
            status_code=status_code,
            title=code,
            detail=message,
            error_type=f"/errors/{code}",
            correlation_id=correlation_id,
        )


# добавление correlation_id ко всем запросам
@app.middleware("http")
async def add_correlation_id(request: Request, call_next):
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    request.state.correlation_id = correlation_id

    response = await call_next(request)
    response.headers["X-Correlation-ID"] = correlation_id
    return response


def _create_problem_response(
    status_code: int,
    title: str,
    detail: str,
    correlation_id: str,
    error_type: str = None,
) -> JSONResponse:

    problem_data = {
        "type": error_type or "about:blank",
        "title": title,
        "status": status_code,
        "detail": detail,
        "correlation_id": correlation_id,
        "instance": f"/errors/{uuid.uuid4()}",
    }

    # if APP_ENV == "production" and status_code >= 500:
    #     problem_data["detail"] = "An internal server error occurred"

    return JSONResponse(
        status_code=status_code,
        content=problem_data,
        media_type="application/problem+json",
    )


@app.exception_handler(ProblemDetails)
async def api_error_handler(request: Request, exc: ProblemDetails):
    return _create_problem_response(
        status_code=exc.status,
        title=exc.title,
        detail=exc.detail,
        correlation_id=exc.correlation_id or request.state.correlation_id,
        error_type=exc.type,
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    detail = exc.detail if isinstance(exc.detail, str) else "HTTP error occurred"
    return _create_problem_response(
        status_code=exc.status_code,
        title="http_error",
        detail=detail,
        correlation_id=request.state.correlation_id,
        error_type=f"/errors/http_{exc.status_code}",
    )


@app.exception_handler(RequestValidationError)
async def request_validation_error_handler(
    request: Request, exc: RequestValidationError
):
    error_messages = []
    for err in exc.errors():
        msg = err.get("msg")
        loc = ".".join(str(x) for x in err.get("loc", []))
        error_messages.append(f"{loc}: {msg}" if loc else msg)

    detail = "; ".join(error_messages)

    return _create_problem_response(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        title="validation_error",
        detail=detail,
        correlation_id=request.state.correlation_id,
        error_type="/errors/validation",
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    print(f"Unhandled exception: {exc}, correlation_id: {request.state.correlation_id}")

    return _create_problem_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        title="internal_server_error",
        # detail=str(exc) if APP_ENV != "production" else "Internal server error",
        detail=str(exc),
        correlation_id=request.state.correlation_id,
        error_type="/errors/internal",
    )


# ADR-003
class SecureHTTPClient:

    def __init__(self):
        self.connect_timeout = 5
        self.read_timeout = 30
        self.max_retries = 3
        self.max_response_size = 50 * 1024 * 1024

    async def request(self, method: str, url: str, **kwargs):
        # заглушка
        pass


_DB = {"cards": []}


def _get_max_order_idx(column: ColumnType) -> int:
    cards_in_column = [card for card in _DB["cards"] if card["column"] == column]
    return max([card["order_idx"] for card in cards_in_column], default=0)


def _get_card_by_id(card_id: int) -> Optional[dict]:
    return next((card for card in _DB["cards"] if card["id"] == card_id), None)


def _reorder_cards(column: ColumnType, from_idx: int, to_idx: int):
    # упорядочивает карточки в колонке при изменениях
    cards_in_column = [card for card in _DB["cards"] if card["column"] == column]
    if not cards_in_column:
        return

    cards_in_column.sort(key=lambda x: x["order_idx"])
    min_idx = min(c["order_idx"] for c in cards_in_column)
    max_idx = max(c["order_idx"] for c in cards_in_column)

    if to_idx < min_idx:
        to_idx = min_idx
    if to_idx > max_idx + 1:
        to_idx = max_idx + 1

    if from_idx < to_idx:
        for card in cards_in_column:
            if from_idx < card["order_idx"] <= to_idx:
                card["order_idx"] -= 1
            elif card["order_idx"] == from_idx:
                card["order_idx"] = to_idx
    else:
        for card in cards_in_column:
            if to_idx <= card["order_idx"] < from_idx:
                card["order_idx"] += 1
            elif card["order_idx"] == from_idx:
                card["order_idx"] = to_idx


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/cards", response_model=List[CardResponse])
def get_cards():
    """Получить все карточки"""
    return _DB["cards"]


@app.post("/cards", response_model=CardResponse)
def create_card(card: CardCreate, request: Request):
    """Создать новую карточку"""
    if not card.title.strip() or len(card.title) > 100:
        raise ApiError(
            code="validation_error",
            message="Title must be 1-100 characters",
            status_code=422,
            correlation_id=request.state.correlation_id,
        )

    new_card = {
        "id": len(_DB["cards"]) + 1,
        "title": card.title,
        "description": card.description.strip() if card.description else None,
        "column": card.column,
        "order_idx": _get_max_order_idx(card.column) + 1,
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
    }

    _DB["cards"].append(new_card)
    return new_card


@app.get("/cards/{card_id}", response_model=CardResponse)
def get_card(card_id: int, request: Request):
    """Получить карточку по ID"""
    for it in _DB["cards"]:
        if it["id"] == card_id:
            return it

    raise ApiError(
        code="not_found",
        message="Card not found",
        status_code=404,
        correlation_id=request.state.correlation_id,
    )


@app.patch("/cards/{card_id}", response_model=CardResponse)
def update_card(card_id: int, card_update: CardUpdate, request: Request):
    """Обновить карточку по ID"""
    card = _get_card_by_id(card_id)
    if not card:
        raise ApiError(
            code="not_found",
            message="Card not found",
            status_code=404,
            correlation_id=request.state.correlation_id,
        )

    if card_update.title is not None:
        if not card_update.title.strip() or len(card_update.title) > 100:
            raise ApiError(
                code="validation_error",
                message="Title must be 1-100 characters",
                status_code=422,
                correlation_id=request.state.correlation_id,
            )
        card["title"] = card_update.title.strip()

    if card_update.description is not None:
        card["description"] = (
            card_update.description.strip() if card_update.description else None
        )

    if card_update.column is not None and card_update.column != card["column"]:

        old_column = card["column"]
        old_order_idx = card["order_idx"]

        card["column"] = card_update.column
        card["order_idx"] = _get_max_order_idx(card_update.column) + 1

        _reorder_cards(old_column, old_order_idx, _get_max_order_idx(old_column) + 1)

    card["updated_at"] = datetime.now()
    return card


@app.delete("/cards/{card_id}")
def delete_card(card_id: int, request: Request):
    """Удалить карточку по ID"""
    for i, card in enumerate(_DB["cards"]):
        if card["id"] == card_id:
            deleted_card = _DB["cards"].pop(i)
            column = deleted_card["column"]
            deleted_order_idx = deleted_card["order_idx"]
            _reorder_cards(column, deleted_order_idx, _get_max_order_idx(column) + 1)

            return {"message": "Card deleted successfully"}

    raise ApiError(
        code="not_found",
        message="Card not found",
        status_code=404,
        correlation_id=request.state.correlation_id,
    )

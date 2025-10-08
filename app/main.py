from datetime import datetime
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from .models.schemas import CardCreate, CardResponse, CardUpdate, ColumnType

app = FastAPI(title="Idea Kanban API", version="0.1.0")


class ApiError(Exception):
    def __init__(self, code: str, message: str, status: int = 400):
        self.code = code
        self.message = message
        self.status = status


@app.exception_handler(ApiError)
async def api_error_handler(request: Request, exc: ApiError):
    return JSONResponse(
        status_code=exc.status,
        content={"error": {"code": exc.code, "message": exc.message}},
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    # Normalize FastAPI HTTPException into our error envelope
    detail = exc.detail if isinstance(exc.detail, str) else "http_error"
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": "http_error", "message": detail}},
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

    message_text = "; ".join(error_messages)

    return JSONResponse(
        status_code=422,
        content={"error": {"code": "validation_error", "message": message_text}},
    )


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
def create_card(card: CardCreate):
    """Создать новую карточку"""
    if not card.title.strip() or len(card.title) > 100:
        raise ApiError(
            code="validation_error",
            message="Title must be 1-100 characters",
            status=422,
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
def get_card(card_id: int):
    """Получить карточку по ID"""
    for it in _DB["cards"]:
        if it["id"] == card_id:
            return it

    raise ApiError(code="not_found", message="Card not found", status=404)


@app.patch("/cards/{card_id}", response_model=CardResponse)
def update_card(card_id: int, card_update: CardUpdate):
    """Обновить карточку по ID"""
    card = _get_card_by_id(card_id)
    if not card:
        raise ApiError(code="not_found", message="Card not found", status=404)

    if card_update.title is not None:
        if not card_update.title.strip() or len(card_update.title) > 100:
            raise ApiError(
                code="validation_error",
                message="Title must be 1-100 characters",
                status=422,
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
def delete_card(card_id: int):
    """Удалить карточку по ID"""
    for i, card in enumerate(_DB["cards"]):
        if card["id"] == card_id:
            deleted_card = _DB["cards"].pop(i)
            column = deleted_card["column"]
            deleted_order_idx = deleted_card["order_idx"]
            _reorder_cards(column, deleted_order_idx, _get_max_order_idx(column) + 1)

            return {"message": "Card deleted successfully"}

    raise ApiError(code="not_found", message="Card not found", status=404)

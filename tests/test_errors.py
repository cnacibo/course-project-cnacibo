def test_health_check(client):
    """Тест проверки здоровья приложения"""
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"


def test_get_cards_empty(client):
    """Тест получения карточек из пустой базы"""
    r = client.get("/cards")
    assert r.status_code == 200
    body = r.json()
    assert body == []


def test_create_card_success(client):
    """Тест успешного создания карточки"""
    card_data = {
        "title": "Test Card",
        "description": "Test Description",
        "column": "backlog",
    }
    r = client.post("/cards", json=card_data)
    assert r.status_code == 200
    body = r.json()
    assert body["title"] == "Test Card"
    assert body["description"] == "Test Description"
    assert body["column"] == "backlog"
    assert body["id"] == 1
    assert body["order_idx"] == 1
    assert "created_at" in body
    assert "updated_at" in body


def test_create_card_validation_error_empty_title(client):
    """Тест ошибки валидации при пустом заголовке"""
    card_data = {"title": "", "description": "Test Description", "column": "backlog"}
    r = client.post("/cards", json=card_data)
    assert r.status_code == 422
    body = r.json()

    assert "detail" in body
    assert "correlation_id" in body
    assert "title" in body
    assert "status" in body
    assert body["status"] == 422
    assert "at least 1 character" in body["detail"]


def test_create_card_validation_error_long_title(client):
    """Тест ошибки валидации при слишком длинном заголовке"""
    card_data = {
        "title": "a" * 101,
        "description": "Test Description",
        "column": "backlog",
    }
    r = client.post("/cards", json=card_data)
    assert r.status_code == 422
    body = r.json()

    assert "detail" in body
    assert body["status"] == 422
    assert "correlation_id" in body
    assert "at most 100 characters" in body["detail"]


def test_get_card_success(client):
    """Тест успешного получения карточки по ID"""
    card_data = {
        "title": "Test Card for Get",
        "description": "Test Description",
        "column": "todo",
    }
    create_response = client.post("/cards", json=card_data)
    card_id = create_response.json()["id"]

    r = client.get(f"/cards/{card_id}")
    assert r.status_code == 200
    body = r.json()
    assert body["id"] == card_id
    assert body["title"] == "Test Card for Get"


def test_get_card_not_found(client):
    """Тест получения несуществующей карточки"""
    r = client.get("/cards/999")
    assert r.status_code == 404
    body = r.json()

    assert body["status"] == 404
    assert "correlation_id" in body
    assert "detail" in body
    assert "Card not found" in body["detail"]


def test_update_card_success(client):
    """Тест успешного обновления карточки"""
    card_data = {
        "title": "Original Title",
        "description": "Original Description",
        "column": "backlog",
    }
    create_response = client.post("/cards", json=card_data)
    card_id = create_response.json()["id"]

    update_data = {
        "title": "Updated Title",
        "description": "Updated Description",
        "column": "in_progress",
    }
    r = client.patch(f"/cards/{card_id}", json=update_data)
    assert r.status_code == 200
    body = r.json()
    assert body["title"] == "Updated Title"
    assert body["description"] == "Updated Description"
    assert body["column"] == "in_progress"
    assert body["id"] == card_id


def test_update_card_validation_error(client):
    """Тест ошибки валидации при обновлении"""
    card_data = {
        "title": "Original Title",
        "description": "Original Description",
        "column": "backlog",
    }
    create_response = client.post("/cards", json=card_data)
    card_id = create_response.json()["id"]

    update_data = {"title": "", "column": "in_progress"}
    r = client.patch(f"/cards/{card_id}", json=update_data)
    assert r.status_code == 422
    body = r.json()

    assert "detail" in body
    assert body["status"] == 422
    assert "correlation_id" in body
    assert "at least 1 character" in body["detail"]


def test_update_card_not_found(client):
    """Тест обновления несуществующей карточки"""
    update_data = {"title": "Updated Title", "column": "in_progress"}
    r = client.patch("/cards/999", json=update_data)
    assert r.status_code == 404
    body = r.json()

    assert body["status"] == 404
    assert "correlation_id" in body
    assert "Card not found" in body["detail"]


def test_delete_card_success(client):
    """Тест успешного удаления карточки"""
    card_data = {
        "title": "Card to Delete",
        "description": "Will be deleted",
        "column": "todo",
    }
    create_response = client.post("/cards", json=card_data)
    card_id = create_response.json()["id"]

    r = client.delete(f"/cards/{card_id}")
    assert r.status_code == 200
    body = r.json()
    assert body["message"] == "Card deleted successfully"

    get_response = client.get(f"/cards/{card_id}")
    assert get_response.status_code == 404


def test_delete_card_not_found(client):
    """Тест удаления несуществующей карточки"""
    r = client.delete("/cards/999")
    assert r.status_code == 404
    body = r.json()

    assert body["status"] == 404
    assert "correlation_id" in body
    assert "Card not found" in body["detail"]


def test_order_idx_auto_increment(client):
    """Тест автоматического увеличения order_idx в колонках"""
    card1_data = {"title": "Card 1", "column": "backlog"}
    card2_data = {"title": "Card 2", "column": "backlog"}
    card3_data = {"title": "Card 3", "column": "todo"}

    card1_response = client.post("/cards", json=card1_data)
    card2_response = client.post("/cards", json=card2_data)
    card3_response = client.post("/cards", json=card3_data)

    card1 = card1_response.json()
    card2 = card2_response.json()
    card3 = card3_response.json()

    assert card1["order_idx"] == 1
    assert card2["order_idx"] == 2
    assert card3["order_idx"] == 1


def test_get_all_cards(client):
    """Тест получения всех карточек"""
    card1_data = {"title": "Card 1", "column": "backlog"}
    card2_data = {"title": "Card 2", "column": "todo"}

    client.post("/cards", json=card1_data)
    client.post("/cards", json=card2_data)

    r = client.get("/cards")
    assert r.status_code == 200
    body = r.json()
    assert len(body) >= 2
    assert any(card["title"] == "Card 1" for card in body)
    assert any(card["title"] == "Card 2" for card in body)


def test_column_validation(client):
    """Тест валидации колонок"""
    card_data = {
        "title": "Test Card",
        "description": "Test Description",
        "column": "invalid_column",
    }
    r = client.post("/cards", json=card_data)
    assert r.status_code == 422

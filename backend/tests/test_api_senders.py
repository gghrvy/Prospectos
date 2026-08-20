def test_create_and_list_senders(client):
    response = client.post(
        "/api/senders",
        json={"name": "Jordan Lee", "title": "Web Developer", "email": "jordan@example.com"},
    )
    assert response.status_code == 201, response.text
    created = response.json()
    assert created["name"] == "Jordan Lee"
    assert created["portfolio_url"] is None

    listing = client.get("/api/senders").json()
    assert len(listing) == 1
    assert listing[0]["name"] == "Jordan Lee"


def test_list_senders_sorted_by_name(client):
    client.post("/api/senders", json={"name": "Zoe"})
    client.post("/api/senders", json={"name": "Amir"})

    listing = client.get("/api/senders").json()
    assert [s["name"] for s in listing] == ["Amir", "Zoe"]


def test_delete_sender(client):
    created = client.post("/api/senders", json={"name": "Jordan Lee"}).json()

    response = client.delete(f"/api/senders/{created['id']}")
    assert response.status_code == 204

    listing = client.get("/api/senders").json()
    assert listing == []


def test_delete_unknown_sender_returns_404(client):
    response = client.delete("/api/senders/does-not-exist")
    assert response.status_code == 404

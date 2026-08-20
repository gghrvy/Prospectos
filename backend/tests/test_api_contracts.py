def _create_business(client, **overrides) -> dict:
    payload = {"name": "ABC Plumbing", "category": "Plumber", "city": "Houston"}
    payload.update(overrides)
    response = client.post("/api/businesses", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def test_generate_service_agreement_renders_placeholders(client):
    created = _create_business(client)

    response = client.post(
        f"/api/businesses/{created['id']}/contract",
        json={
            "contract_type": "SERVICE_AGREEMENT",
            "studio_name": "Acme Studio",
            "project_description": "a 5-page website with a chatbot",
            "price_amount": 2000,
            "currency": "USD",
            "deposit_percent": 50,
        },
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["contract_type"] == "SERVICE_AGREEMENT"
    assert "ABC Plumbing" in body["content"]
    assert "Acme Studio" in body["content"]
    assert "a 5-page website with a chatbot" in body["content"]
    assert "1,000.00 USD" in body["content"]  # 50% deposit of 2000
    assert "2,000.00 USD" in body["content"]


def test_generate_nda_and_welcome_packet(client):
    created = _create_business(client)

    nda = client.post(f"/api/businesses/{created['id']}/contract", json={"contract_type": "NDA"})
    assert nda.status_code == 201
    assert "NON-DISCLOSURE" in nda.json()["content"]

    welcome = client.post(f"/api/businesses/{created['id']}/contract", json={"contract_type": "WELCOME_PACKET"})
    assert welcome.status_code == 201
    assert "Welcome to" in welcome.json()["content"]
    assert "ABC Plumbing" in welcome.json()["content"]


def test_generate_contract_with_sender_snapshots_signature(client):
    created = _create_business(client)
    sender = client.post(
        "/api/senders", json={"name": "Jordan Lee", "title": "Developer", "email": "jordan@example.com"}
    ).json()

    response = client.post(
        f"/api/businesses/{created['id']}/contract",
        json={"contract_type": "WELCOME_PACKET", "sender_id": sender["id"]},
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["sender_id"] == sender["id"]
    assert body["sender_name"] == "Jordan Lee"
    assert "Jordan Lee" in body["content"]


def test_generate_contract_with_unknown_sender_returns_404(client):
    created = _create_business(client)
    response = client.post(
        f"/api/businesses/{created['id']}/contract",
        json={"contract_type": "NDA", "sender_id": "does-not-exist"},
    )
    assert response.status_code == 404


def test_generate_contract_business_not_found_returns_404(client):
    response = client.post("/api/businesses/does-not-exist/contract", json={"contract_type": "NDA"})
    assert response.status_code == 404


def test_multiple_contracts_kept_as_history(client):
    created = _create_business(client)
    client.post(f"/api/businesses/{created['id']}/contract", json={"contract_type": "NDA"})
    client.post(f"/api/businesses/{created['id']}/contract", json={"contract_type": "SERVICE_AGREEMENT"})

    detail = client.get(f"/api/businesses/{created['id']}").json()
    assert len(detail["contracts"]) == 2
    assert detail["contracts"][0]["contract_type"] == "SERVICE_AGREEMENT"  # newest first

"""Policy KB CRUD RBAC + RAG chunking / ingestion / retrieval tests.

The embedding model loads on first use (downloads ~130MB once); these tests
therefore exercise the real local vector pipeline end-to-end.
"""

from __future__ import annotations

from app.services.chunking import chunk_text


# ---- pure: chunking ----

def test_chunk_short_text_single_chunk():
    chunks = chunk_text("Employees get 20 days of annual leave.")
    assert len(chunks) == 1


def test_chunk_long_text_splits():
    sentence = "This is a fairly long policy sentence about leave entitlements. "
    chunks = chunk_text(sentence * 40, target_chars=300)
    assert len(chunks) > 1
    assert all(c.strip() for c in chunks)


def test_chunk_empty():
    assert chunk_text("   ") == []


# ---- RBAC on CRUD ----

def test_employee_cannot_create_policy(client, auth_headers):
    r = client.post(
        "/policies",
        headers=auth_headers["employee"],
        json={"title": "Sneaky Policy", "body": "x", "category": "General"},
    )
    assert r.status_code == 403


def test_employee_sees_only_published(client, auth_headers):
    r = client.get("/policies", headers=auth_headers["employee"])
    assert r.status_code == 200
    assert all(p["status"] == "published" for p in r.json())


def test_hr_admin_sees_drafts(client, auth_headers):
    r = client.get("/policies", headers=auth_headers["hr_admin"])
    assert r.status_code == 200
    statuses = {p["status"] for p in r.json()}
    assert "draft" in statuses  # seed includes a draft


# ---- full lifecycle: create -> publish -> search -> unpublish ----

def test_policy_lifecycle_and_grounded_search(client, auth_headers):
    admin = auth_headers["hr_admin"]
    unique = "Pet Bereavement Leave PolicyDeskUniqueMarker"
    body = (
        "Employees are entitled to two days of paid pet bereavement leave following "
        "the death of a companion animal. Notify your manager to record the absence. "
        "This PolicyDeskUniqueMarker benefit is separate from annual and sick leave."
    )

    created = client.post(
        "/policies", headers=admin, json={"title": unique, "body": body, "category": "Leave"}
    )
    assert created.status_code == 201
    pid = created.json()["id"]
    assert created.json()["status"] == "draft"
    assert created.json()["chunk_count"] == 0

    # not searchable while draft
    pre = client.get("/policies/search", headers=admin, params={"q": "pet bereavement leave"}).json()
    assert not any(r["document_id"] == pid for r in pre["results"])

    # publish -> chunks created
    pub = client.post(f"/policies/{pid}/publish", headers=admin)
    assert pub.status_code == 200
    assert pub.json()["status"] == "published"
    assert pub.json()["chunk_count"] >= 1

    # now grounded search finds it, with citation fields
    hit = client.get(
        "/policies/search", headers=admin, params={"q": "how much pet bereavement leave do we get?"}
    ).json()
    assert hit["grounded"] is True
    top = hit["results"][0]
    assert top["doc_title"] == unique
    assert top["doc_version"] >= 1
    assert "pet bereavement" in top["chunk_text"].lower()

    # cleanup
    assert client.delete(f"/policies/{pid}", headers=admin).status_code == 204


def test_search_returns_not_grounded_for_nonsense(client, auth_headers):
    r = client.get(
        "/policies/search",
        headers=auth_headers["employee"],
        params={"q": "quantum chromodynamics lattice gauge zzzxyq nonsense"},
    ).json()
    assert r["grounded"] is False
    assert r["results"] == []


def test_seeded_maternity_policy_is_grounded(client, auth_headers):
    """A real seeded policy should be retrievable with a citation."""
    r = client.get(
        "/policies/search",
        headers=auth_headers["employee"],
        params={"q": "what is the maternity leave policy?"},
    ).json()
    assert r["grounded"] is True
    titles = {res["doc_title"] for res in r["results"]}
    assert any("Parental" in t or "Maternity" in t for t in titles)

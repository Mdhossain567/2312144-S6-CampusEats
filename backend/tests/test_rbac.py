"""Automated test suite verifying the 4 mandatory RBAC rules for CSE309:

1. Ownership Isolation (customers cannot view or cancel other customers' orders)
2. Group Fine-Grained Permissions (create, edit, assign, owner-only actions)
3. Admin Safety Invariants (cannot ban admin, cannot change own role)
4. System Role Boundaries (menu modification restricted to admins)
"""
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.menu_items.models import MenuItem
from app.security import hash_password
from app.users.models import AppUser


def helper_login(client: TestClient, email: str, password: str = "Password123") -> dict[str, str]:
    res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# ── RBAC RULE 1: Ownership Isolation ──────────────────────────────────────────


def test_rbac_ownership_isolation(client: TestClient, session: Session):
    """A customer can only read or cancel their own records. Accessing another user's record returns 404/403."""
    # Seed a menu item
    item = MenuItem(name="Pizza Slice", price=5.00, category="snack", is_available=True)
    session.add(item)
    session.commit()
    session.refresh(item)

    # Register Alice and Bob
    client.post("/api/v1/auth/register", json={"name": "Alice", "email": "alice@test.com", "password": "Password123"})
    client.post("/api/v1/auth/register", json={"name": "Bob", "email": "bob@test.com", "password": "Password123"})

    alice_auth = helper_login(client, "alice@test.com")
    bob_auth = helper_login(client, "bob@test.com")

    # Alice places an order
    order_res = client.post(
        "/api/v1/orders",
        json={"items": [{"menu_item_id": item.id, "quantity": 2}]},
        headers=alice_auth,
    )
    assert order_res.status_code == 201
    alice_order_id = order_res.json()["id"]

    # Alice can view her own order
    res_alice = client.get(f"/api/v1/orders/{alice_order_id}", headers=alice_auth)
    assert res_alice.status_code == 200
    assert res_alice.json()["id"] == alice_order_id

    # Bob attempts to view Alice's order -> must be rejected with 404 (ownership check)
    res_bob_view = client.get(f"/api/v1/orders/{alice_order_id}", headers=bob_auth)
    assert res_bob_view.status_code == 404
    assert res_bob_view.json()["detail"] == "Order not found"

    # Bob attempts to cancel Alice's order -> must be rejected with 404
    res_bob_cancel = client.post(f"/api/v1/orders/{alice_order_id}/cancel", headers=bob_auth)
    assert res_bob_cancel.status_code == 404


# ── RBAC RULE 2: Group Permissions Matrix ─────────────────────────────────────


def test_rbac_group_permissions(client: TestClient, session: Session):
    """Verify group fine-grained permissions (create, edit, assign, and owner-only actions)."""
    # Seed a menu item
    dish = MenuItem(name="Burger Meal", price=10.00, category="meal", is_available=True)
    session.add(dish)
    session.commit()
    session.refresh(dish)

    # Register Alice (owner), Bob (create+edit), Charlie (create+assign), Dave (visitor)
    for name, email in [("Alice", "alice_g@test.com"), ("Bob", "bob_g@test.com"), ("Charlie", "charlie_g@test.com"), ("Dave", "dave_g@test.com")]:
        client.post("/api/v1/auth/register", json={"name": name, "email": email, "password": "Password123"})

    alice_auth = helper_login(client, "alice_g@test.com")
    bob_auth = helper_login(client, "bob_g@test.com")
    charlie_auth = helper_login(client, "charlie_g@test.com")
    dave_auth = helper_login(client, "dave_g@test.com")

    # 1. Alice creates group
    group_res = client.post("/api/v1/groups", json={"name": "Project Lunch Group"}, headers=alice_auth)
    assert group_res.status_code == 201
    group_id = group_res.json()["id"]

    # 2. Alice adds Bob with (create=True, edit=True, assign=False)
    bob_add = client.post(
        f"/api/v1/groups/{group_id}/members",
        json={"email": "bob_g@test.com", "can_create": True, "can_edit": True, "can_assign": False},
        headers=alice_auth,
    )
    assert bob_add.status_code == 201
    bob_uid = bob_add.json()["user_id"]

    # 3. Alice adds Charlie with (create=True, edit=False, assign=True)
    charlie_add = client.post(
        f"/api/v1/groups/{group_id}/members",
        json={"email": "charlie_g@test.com", "can_create": True, "can_edit": False, "can_assign": True},
        headers=alice_auth,
    )
    assert charlie_add.status_code == 201
    charlie_uid = charlie_add.json()["user_id"]

    # Non-member Dave attempts to view group -> 403 Forbidden
    dave_view = client.get(f"/api/v1/groups/{group_id}", headers=dave_auth)
    assert dave_view.status_code == 403
    assert "You are not a member of this group" in dave_view.json()["detail"]

    # 4. Bob creates a group order pool (Bob has can_create=True)
    ord_res = client.post(
        f"/api/v1/groups/{group_id}/orders",
        json={"title": "Team Friday Lunch"},
        headers=bob_auth,
    )
    assert ord_res.status_code == 201
    group_order_id = ord_res.json()["id"]

    # 5. Bob attempts to add an item assigned to Charlie -> Bob has can_assign=False -> 403 Forbidden
    assign_fail = client.post(
        f"/api/v1/groups/{group_id}/orders/{group_order_id}/items",
        json={"menu_item_id": dish.id, "quantity": 1, "assigned_to_id": charlie_uid},
        headers=bob_auth,
    )
    assert assign_fail.status_code == 403
    assert "assign" in assign_fail.json()["detail"].lower()

    # 6. Bob adds unassigned item (Bob has can_create=True) -> Success
    item_res = client.post(
        f"/api/v1/groups/{group_id}/orders/{group_order_id}/items",
        json={"menu_item_id": dish.id, "quantity": 1},
        headers=bob_auth,
    )
    assert item_res.status_code == 201
    item_id = item_res.json()["id"]

    # 7. Charlie assigns the item to Bob (Charlie has can_assign=True) -> Success
    assign_ok = client.patch(
        f"/api/v1/groups/{group_id}/orders/{group_order_id}/items/{item_id}",
        json={"assigned_to_id": bob_uid},
        headers=charlie_auth,
    )
    assert assign_ok.status_code == 200
    assert assign_ok.json()["assigned_to_id"] == bob_uid

    # 8. Charlie attempts to edit the quantity of Bob's item -> Charlie has can_edit=False -> 403 Forbidden
    edit_fail = client.patch(
        f"/api/v1/groups/{group_id}/orders/{group_order_id}/items/{item_id}",
        json={"quantity": 5},
        headers=charlie_auth,
    )
    assert edit_fail.status_code == 403
    assert "edit" in edit_fail.json()["detail"].lower()

    # 9. Non-owner (Bob) attempts to delete the group -> 403 Forbidden
    del_fail = client.delete(f"/api/v1/groups/{group_id}", headers=bob_auth)
    assert del_fail.status_code == 403
    assert "Only the group owner" in del_fail.json()["detail"]

    # 10. Non-owner (Charlie) attempts to change Bob's permissions -> 403 Forbidden
    perm_fail = client.patch(
        f"/api/v1/groups/{group_id}/members/{bob_uid}",
        json={"can_assign": True},
        headers=charlie_auth,
    )
    assert perm_fail.status_code == 403
    assert "Only the group owner" in perm_fail.json()["detail"]

    # 11. Owner (Alice) updates Bob's permissions -> Success
    perm_ok = client.patch(
        f"/api/v1/groups/{group_id}/members/{bob_uid}",
        json={"can_assign": True},
        headers=alice_auth,
    )
    assert perm_ok.status_code == 200
    assert perm_ok.json()["can_assign"] is True

    # 12. Owner (Alice) deletes the group -> Success (204)
    del_ok = client.delete(f"/api/v1/groups/{group_id}", headers=alice_auth)
    assert del_ok.status_code == 204


# ── RBAC RULE 3: Admin Safety Invariants ──────────────────────────────────────


def test_rbac_admin_safety_rules(client: TestClient, session: Session):
    """Admin safety rules:

    1. An admin cannot ban another admin.
    2. An admin cannot change their own role.
    3. An admin can ban a normal user.
    """
    # Seed 2 Admins and 1 Customer
    admin1 = AppUser(name="Admin 1", email="adm1@test.com", password_hash=hash_password("Password123"), role="admin", is_active=True)
    admin2 = AppUser(name="Admin 2", email="adm2@test.com", password_hash=hash_password("Password123"), role="admin", is_active=True)
    customer = AppUser(name="User 1", email="cust1@test.com", password_hash=hash_password("Password123"), role="customer", is_active=True)
    session.add(admin1)
    session.add(admin2)
    session.add(customer)
    session.commit()
    session.refresh(admin1)
    session.refresh(admin2)
    session.refresh(customer)

    adm1_auth = helper_login(client, "adm1@test.com")

    # Safety Rule 1: Admin 1 attempts to ban Admin 2 -> Rejected with 400 Bad Request
    ban_admin_res = client.post(
        f"/api/v1/admin/users/{admin2.id}/ban",
        json={"reason": "Test ban"},
        headers=adm1_auth,
    )
    assert ban_admin_res.status_code == 400
    assert "cannot ban another administrator" in ban_admin_res.json()["detail"].lower()

    # Safety Rule 2: Admin 1 attempts to change their own role / demote self -> Rejected with 400 Bad Request
    self_demote_res = client.post(
        f"/api/v1/admin/users/{admin1.id}/role",
        json={"role": "customer"},
        headers=adm1_auth,
    )
    assert self_demote_res.status_code == 400
    assert "cannot change their own role" in self_demote_res.json()["detail"].lower()

    # Valid action: Admin 1 bans customer -> Succeeds (204)
    ban_cust_res = client.post(
        f"/api/v1/admin/users/{customer.id}/ban",
        json={"reason": "Abusive behavior"},
        headers=adm1_auth,
    )
    assert ban_cust_res.status_code == 204

    # Verify customer is now banned
    session.refresh(customer)
    assert customer.is_banned is True
    assert customer.ban_reason == "Abusive behavior"


# ── RBAC RULE 4: System Role Boundaries & Menu Modification ───────────────────


def test_rbac_menu_role_boundaries(client: TestClient, session: Session):
    """Customer cannot modify menu items (403 Forbidden); Admin can create menu items."""
    admin = AppUser(name="Super Admin", email="super_adm@test.com", password_hash=hash_password("Password123"), role="admin", is_active=True)
    session.add(admin)
    session.commit()

    client.post("/api/v1/auth/register", json={"name": "Normal Customer", "email": "norm_cust@test.com", "password": "Password123"})

    cust_auth = helper_login(client, "norm_cust@test.com")
    adm_auth = helper_login(client, "super_adm@test.com")

    # Customer attempts to create menu item -> 403 Forbidden
    cust_create = client.post(
        "/api/v1/menu",
        json={"name": "Hacked Item", "description": "test", "price": 1.00, "category": "meal", "is_available": True},
        headers=cust_auth,
    )
    assert cust_create.status_code == 403

    # Admin creates menu item -> 201 Created
    adm_create = client.post(
        "/api/v1/menu",
        json={"name": "Official Dish", "description": "Delicious", "price": 7.50, "category": "meal", "is_available": True},
        headers=adm_auth,
    )
    assert adm_create.status_code == 201
    assert adm_create.json()["name"] == "Official Dish"

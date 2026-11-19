"""Seed script for CampusEats demo accounts, sample data, and group permissions.

Creates at least 2 admins, 3 normal users, 1 kitchen staff, 1 banned user,
sample menu items across all categories, individual orders, and 1 shared meal
group with mixed permissions for the CSE309 instructor evaluation.

Usage:
    python scripts/seed.py
    python scripts/seed.py --reset
"""
import sys
from pathlib import Path

# Ensure backend root is on sys.path
backend_root = Path(__file__).resolve().parent.parent
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))

from sqlmodel import Session, select

from app.audit.repository import log_event
from app.clock import utc_now
from app.database import engine, init_db
from app.groups.models import GroupMember, GroupOrder, GroupOrderItem, MealGroup
from app.menu_items.models import MenuItem
from app.orders.models import CustomerOrder, OrderItem
from app.security import hash_password
from app.users.models import AppUser


def reset_database(session: Session) -> None:
    """Wipe existing records cleanly in dependency order."""
    print("Clearing existing data...")
    for model in [
        GroupOrderItem,
        GroupOrder,
        GroupMember,
        MealGroup,
        OrderItem,
        CustomerOrder,
        MenuItem,
        AppUser,
    ]:
        session.exec(model.__table__.delete())
    session.commit()
    print("Database cleared.")


def seed() -> None:
    init_db()

    with Session(engine) as session:
        if "--reset" in sys.argv:
            reset_database(session)

        # Check if already seeded
        existing_admin = session.exec(
            select(AppUser).where(AppUser.email == "admin1@campuseats.com")
        ).first()
        if existing_admin and "--reset" not in sys.argv:
            print("Database already seeded! Pass --reset to clear and re-seed.")
            return

        print("Seeding demo accounts for CSE309...")

        # ── 1. Demo Accounts ───────────────────────────────────────────────────
        # 2 Admins
        admin1 = AppUser(
            name="Chief Administrator",
            email="admin1@campuseats.com",
            password_hash=hash_password("AdminPass123"),
            role="admin",
            is_active=True,
        )
        admin2 = AppUser(
            name="Auditor Admin",
            email="admin2@campuseats.com",
            password_hash=hash_password("AdminPass123"),
            role="admin",
            is_active=True,
        )

        # 1 Kitchen Staff
        chef = AppUser(
            name="Chef Mario",
            email="chef@campuseats.com",
            password_hash=hash_password("StaffPass123"),
            role="kitchen_staff",
            is_active=True,
        )

        # 3 Normal Users
        alice = AppUser(
            name="Alice Student",
            email="alice@campuseats.com",
            password_hash=hash_password("UserPass123"),
            role="customer",
            is_active=True,
        )
        bob = AppUser(
            name="Bob Fellow",
            email="bob@campuseats.com",
            password_hash=hash_password("UserPass123"),
            role="customer",
            is_active=True,
        )
        charlie = AppUser(
            name="Charlie Staff",
            email="charlie@campuseats.com",
            password_hash=hash_password("UserPass123"),
            role="customer",
            is_active=True,
        )

        # 1 Banned Account (for testing/demoing immediate 403 rejection)
        banned = AppUser(
            name="Suspended Account",
            email="banned@campuseats.com",
            password_hash=hash_password("UserPass123"),
            role="customer",
            is_active=True,
            is_banned=True,
            banned_at=utc_now(),
            ban_reason="Repeated fraudulent credit card disputes and abuse.",
        )

        users = [admin1, admin2, chef, alice, bob, charlie, banned]
        for u in users:
            session.add(u)
        session.commit()
        for u in users:
            session.refresh(u)

        print(f"Created {len(users)} users (2 Admins, 1 Staff, 3 Normal Users, 1 Banned).")

        # ── 2. Menu Items ─────────────────────────────────────────────────────
        print("Seeding cafeteria menu items...")
        menu = [
            MenuItem(
                name="Spicy Chicken Rice",
                description="Fragrant steamed jasmine rice with crispy spiced chicken and chili sauce.",
                price=8.50,
                category="meal",
                is_available=True,
            ),
            MenuItem(
                name="Beef Cheeseburger",
                description="Juicy Angus beef patty with melted cheddar, lettuce, and pickles.",
                price=9.00,
                category="meal",
                is_available=True,
            ),
            MenuItem(
                name="Veggie Pasta Primavera",
                description="Penne pasta tossed in extra virgin olive oil, garlic, and fresh seasonal vegetables.",
                price=7.50,
                category="meal",
                is_available=True,
            ),
            MenuItem(
                name="Grilled Chicken Salad",
                description="Fresh romaine lettuce, grilled chicken breast, cherry tomatoes, and light vinaigrette.",
                price=6.50,
                category="meal",
                is_available=True,
            ),
            MenuItem(
                name="Crispy French Fries",
                description="Golden crunchy potato fries with rosemary sea salt.",
                price=3.50,
                category="snack",
                is_available=True,
            ),
            MenuItem(
                name="Garlic Bread",
                description="Toasted baguette slices with rich garlic herb butter.",
                price=3.00,
                category="snack",
                is_available=True,
            ),
            MenuItem(
                name="Iced Lemon Tea",
                description="Freshly brewed black tea infused with real lemon juice and mint.",
                price=2.50,
                category="drink",
                is_available=True,
            ),
            MenuItem(
                name="Cold Brew Coffee",
                description="Smooth 18-hour steeped artisanal cold brew coffee.",
                price=4.00,
                category="drink",
                is_available=True,
            ),
            MenuItem(
                name="Chocolate Lava Cake",
                description="Warm molten chocolate center served with powdered sugar.",
                price=4.50,
                category="dessert",
                is_available=True,
            ),
            MenuItem(
                name="Vanilla Bean Ice Cream",
                description="Double scoop of premium Madagascar vanilla bean ice cream.",
                price=3.00,
                category="dessert",
                is_available=True,
            ),
        ]
        for m in menu:
            session.add(m)
        session.commit()
        for m in menu:
            session.refresh(m)

        print(f"Created {len(menu)} menu items across meals, snacks, drinks, and desserts.")

        # ── 3. Individual Customer Orders ─────────────────────────────────────
        print("Seeding customer orders...")
        # Order 1: Alice (Completed)
        order1 = CustomerOrder(
            user_id=alice.id,
            status="completed",
            total=12.00,
        )
        session.add(order1)
        session.commit()
        session.refresh(order1)
        session.add(OrderItem(order_id=order1.id, menu_item_id=menu[0].id, name=menu[0].name, unit_price=8.50, quantity=1))
        session.add(OrderItem(order_id=order1.id, menu_item_id=menu[4].id, name=menu[4].name, unit_price=3.50, quantity=1))

        # Order 2: Bob (Preparing)
        order2 = CustomerOrder(
            user_id=bob.id,
            status="preparing",
            total=13.00,
        )
        session.add(order2)
        session.commit()
        session.refresh(order2)
        session.add(OrderItem(order_id=order2.id, menu_item_id=menu[1].id, name=menu[1].name, unit_price=9.00, quantity=1))
        session.add(OrderItem(order_id=order2.id, menu_item_id=menu[7].id, name=menu[7].name, unit_price=4.00, quantity=1))

        # Order 3: Charlie (Pending)
        order3 = CustomerOrder(
            user_id=charlie.id,
            status="pending",
            total=10.00,
        )
        session.add(order3)
        session.commit()
        session.refresh(order3)
        session.add(OrderItem(order_id=order3.id, menu_item_id=menu[2].id, name=menu[2].name, unit_price=7.50, quantity=1))
        session.add(OrderItem(order_id=order3.id, menu_item_id=menu[6].id, name=menu[6].name, unit_price=2.50, quantity=1))

        session.commit()
        print("Created 3 sample customer orders with items.")

        # ── 4. Shared Meal Group with Mixed Permissions ───────────────────────
        print("Seeding shared meal group with mixed permissions...")
        group = MealGroup(
            name="Faculty & Student Lunch Club",
            description="Campus dining and lunch pooling group with mixed permissions for CSE309.",
            owner_id=alice.id,
        )
        session.add(group)
        session.commit()
        session.refresh(group)

        # Alice: Owner (all permissions)
        m_alice = GroupMember(
            group_id=group.id,
            user_id=alice.id,
            role="owner",
            can_create=True,
            can_edit=True,
            can_assign=True,
        )
        # Bob: Member with Create + Edit (cannot assign)
        m_bob = GroupMember(
            group_id=group.id,
            user_id=bob.id,
            role="member",
            can_create=True,
            can_edit=True,
            can_assign=False,
        )
        # Charlie: Member with Create + Assign (cannot edit other items)
        m_charlie = GroupMember(
            group_id=group.id,
            user_id=charlie.id,
            role="member",
            can_create=True,
            can_edit=False,
            can_assign=True,
        )
        session.add(m_alice)
        session.add(m_bob)
        session.add(m_charlie)
        session.commit()

        # Shared Group Order inside this group
        group_order = GroupOrder(
            group_id=group.id,
            creator_id=alice.id,
            title="Wednesday Department Lunch Pool",
            notes="Ordering at 1:00 PM - please add your dishes by 12:30 PM",
            status="open",
            total=31.00,
        )
        session.add(group_order)
        session.commit()
        session.refresh(group_order)

        # Pooled items with assigned members
        item1 = GroupOrderItem(
            group_order_id=group_order.id,
            menu_item_id=menu[0].id,
            name=menu[0].name,
            unit_price=8.50,
            quantity=2,
            added_by_id=alice.id,
            assigned_to_id=bob.id,
            notes="Less spicy please",
        )
        item2 = GroupOrderItem(
            group_order_id=group_order.id,
            menu_item_id=menu[1].id,
            name=menu[1].name,
            unit_price=9.00,
            quantity=1,
            added_by_id=bob.id,
            assigned_to_id=charlie.id,
            notes="Extra pickles",
        )
        item3 = GroupOrderItem(
            group_order_id=group_order.id,
            menu_item_id=menu[6].id,
            name=menu[6].name,
            unit_price=2.50,
            quantity=2,
            added_by_id=charlie.id,
            assigned_to_id=alice.id,
            notes="No ice",
        )
        session.add(item1)
        session.add(item2)
        session.add(item3)
        session.commit()

        print("Created shared meal group 'Faculty & Student Lunch Club' with 3 members and pooled orders.")

        # ── 5. Audit Log Seed ─────────────────────────────────────────────────
        log_event(session, action="SYSTEM_INIT", details="System initialized and seeded with demo accounts.")
        log_event(session, action="LOGIN", user_id=admin1.id, user_email=admin1.email, ip_address="127.0.0.1", details="Admin login")
        log_event(session, action="GROUP_CREATE", user_id=alice.id, user_email=alice.email, resource_type="meal_group", resource_id=str(group.id), details=f"Created {group.name}")
        log_event(session, action="USER_BAN", user_id=admin1.id, user_email=admin1.email, resource_type="app_user", resource_id=str(banned.id), details=f"Banned {banned.email}")

        print("\nSeed completed successfully!")
        print("==================================================================")
        print("Instructor Test Accounts:")
        print("  Admin 1:       admin1@campuseats.com   / AdminPass123 (Full Admin)")
        print("  Admin 2:       admin2@campuseats.com   / AdminPass123 (Full Admin)")
        print("  Kitchen Staff: chef@campuseats.com     / StaffPass123 (Kitchen Board)")
        print("  Normal User 1: alice@campuseats.com    / UserPass123 (Group Owner)")
        print("  Normal User 2: bob@campuseats.com      / UserPass123 (Can Create & Edit)")
        print("  Normal User 3: charlie@campuseats.com  / UserPass123 (Can Create & Assign)")
        print("  Banned User:   banned@campuseats.com   / UserPass123 (Tests 403 rejection)")
        print("Shared Group: 'Faculty & Student Lunch Club'")
        print("==================================================================")


if __name__ == "__main__":
    seed()

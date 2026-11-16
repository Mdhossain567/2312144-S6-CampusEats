"""Change the role of an account.

Run it from the backend folder:
    python scripts/set_role.py <email> <customer|kitchen_staff|admin>

Everyone registers as a customer, so this is how the first admin and the
kitchen staff accounts are created. It works on the database that DATABASE_URL
points to, or on the local SQLite file when DATABASE_URL is not set.
"""
import sys
from pathlib import Path

# Make "import app" work when the script is started as scripts/set_role.py.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlmodel import Session  # noqa: E402

from app.database import engine, init_db  # noqa: E402
from app.users import repository  # noqa: E402

ROLES = ("customer", "kitchen_staff", "admin")


def main() -> None:
    if len(sys.argv) != 3 or sys.argv[2] not in ROLES:
        print("Usage: python scripts/set_role.py <email> <customer|kitchen_staff|admin>")
        raise SystemExit(1)

    email = sys.argv[1].strip().lower()
    role = sys.argv[2]

    init_db()
    with Session(engine) as session:
        user = repository.get_by_email(session, email)
        if user is None:
            print(f"No account with the email {email}")
            raise SystemExit(1)
        user.role = role
        repository.save(session, user)
        print(f"{user.email} is now {role}")


if __name__ == "__main__":
    main()
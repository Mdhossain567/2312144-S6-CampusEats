"""HTTP endpoints for Meal Groups, Members, and Group Orders under /api/v1/groups (JSON)."""
from fastapi import APIRouter, status

from app.auth.dependencies import CurrentUser
from app.database import SessionDep
from app.groups import service
from app.groups.schemas import (
    GroupCreate,
    GroupDetailRead,
    GroupMemberAdd,
    GroupMemberRead,
    GroupMemberUpdate,
    GroupOrderCreate,
    GroupOrderItemCreate,
    GroupOrderItemRead,
    GroupOrderItemUpdate,
    GroupOrderRead,
    GroupRead,
    GroupUpdate,
)

router = APIRouter(prefix="/api/v1/groups", tags=["groups"])


@router.post("", response_model=GroupRead, status_code=status.HTTP_201_CREATED)
def create_group(data: GroupCreate, user: CurrentUser, session: SessionDep):
    """Create a new meal group (creator becomes owner)."""
    return service.create_group(session, user, data)


@router.get("", response_model=list[GroupRead])
def list_groups(user: CurrentUser, session: SessionDep):
    """List groups that the current user belongs to (or all groups if admin)."""
    return service.list_groups(session, user)


@router.get("/{group_id}", response_model=GroupDetailRead)
def get_group(group_id: int, user: CurrentUser, session: SessionDep):
    """Get group details, members with permissions, and group orders."""
    return service.get_group_detail(session, group_id, user)


@router.patch("/{group_id}", response_model=GroupRead)
def update_group(group_id: int, data: GroupUpdate, user: CurrentUser, session: SessionDep):
    """Rename or update group details (owner only)."""
    return service.update_group(session, group_id, user, data)


@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_group(group_id: int, user: CurrentUser, session: SessionDep):
    """Delete a group and its shared orders (owner only)."""
    service.delete_group(session, group_id, user)


# ── Members Management ────────────────────────────────────────────────────────


@router.post("/{group_id}/members", response_model=GroupMemberRead, status_code=status.HTTP_201_CREATED)
def add_member(group_id: int, data: GroupMemberAdd, user: CurrentUser, session: SessionDep):
    """Add a registered user to the group with specific permissions (owner only)."""
    return service.add_member(session, group_id, user, data)


@router.patch("/{group_id}/members/{target_user_id}", response_model=GroupMemberRead)
def update_member_permissions(
    group_id: int,
    target_user_id: int,
    data: GroupMemberUpdate,
    user: CurrentUser,
    session: SessionDep,
):
    """Update a member's fine-grained permissions: can_create, can_edit, can_assign (owner only)."""
    return service.update_member_permissions(session, group_id, target_user_id, user, data)


@router.delete("/{group_id}/members/{target_user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_member(group_id: int, target_user_id: int, user: CurrentUser, session: SessionDep):
    """Remove a member from the group (owner or member themselves)."""
    service.remove_member(session, group_id, target_user_id, user)


# ── Group Orders (Fine-Grained Permissions) ───────────────────────────────────


@router.post("/{group_id}/orders", response_model=GroupOrderRead, status_code=status.HTTP_201_CREATED)
def create_group_order(
    group_id: int, data: GroupOrderCreate, user: CurrentUser, session: SessionDep
):
    """Create a shared group food order (requires 'create' permission or owner)."""
    return service.create_group_order(session, group_id, user, data)


@router.post(
    "/{group_id}/orders/{order_id}/items",
    response_model=GroupOrderItemRead,
    status_code=status.HTTP_201_CREATED,
)
def add_item_to_group_order(
    group_id: int,
    order_id: int,
    data: GroupOrderItemCreate,
    user: CurrentUser,
    session: SessionDep,
):
    """Add a dish to the group order pool (requires 'create' permission)."""
    return service.add_item_to_group_order(session, group_id, order_id, user, data)


@router.patch("/{group_id}/orders/{order_id}/items/{item_id}", response_model=GroupOrderItemRead)
def update_order_item(
    group_id: int,
    order_id: int,
    item_id: int,
    data: GroupOrderItemUpdate,
    user: CurrentUser,
    session: SessionDep,
):
    """Update dish quantity/notes/assignee (requires 'edit' permission or adder; assignment requires 'assign')."""
    return service.update_order_item(session, group_id, order_id, item_id, user, data)


@router.delete("/{group_id}/orders/{order_id}/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_order_item(
    group_id: int, order_id: int, item_id: int, user: CurrentUser, session: SessionDep
):
    """Delete a dish from the group order (requires 'edit' permission or adder)."""
    service.delete_order_item(session, group_id, order_id, item_id, user)

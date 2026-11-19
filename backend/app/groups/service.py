"""Business rules and authorization logic for Meal Groups and Group Orders."""
from fastapi import HTTPException, status
from sqlmodel import Session

from app.audit.repository import log_event
from app.clock import utc_now
from app.groups import repository
from app.groups.models import GroupMember, GroupOrder, GroupOrderItem, MealGroup
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
    GroupPermissions,
    GroupRead,
    GroupUpdate,
)
from app.menu_items import repository as menu_repo
from app.users import repository as user_repo
from app.users.models import AppUser


def _not_found(msg: str = "Resource not found") -> HTTPException:
    return HTTPException(status.HTTP_404_NOT_FOUND, msg)


def _forbidden(msg: str = "You do not have permission to perform this action") -> HTTPException:
    return HTTPException(status.HTTP_403_FORBIDDEN, msg)


# ── Permission helpers ────────────────────────────────────────────────────────


def check_group_access(
    session: Session, group_id: int, user: AppUser
) -> tuple[MealGroup, GroupMember | None]:
    """Verify user can see the group (either member or system admin)."""
    group = repository.get_group(session, group_id)
    if group is None:
        raise _not_found("Meal group not found")

    if user.role == "admin":
        membership = repository.get_membership(session, group_id, user.id)
        return group, membership

    membership = repository.get_membership(session, group_id, user.id)
    if membership is None:
        raise _forbidden("You are not a member of this group")

    return group, membership


def check_owner(group: MealGroup, user: AppUser) -> None:
    """Only the group owner can delete, rename, or manage members."""
    if group.owner_id != user.id and user.role != "admin":
        raise _forbidden("Only the group owner can perform this action")


def get_user_permissions(group: MealGroup, membership: GroupMember | None, user: AppUser) -> GroupPermissions:
    is_owner = (group.owner_id == user.id) or (user.role == "admin")
    if is_owner:
        return GroupPermissions(is_owner=True, can_create=True, can_edit=True, can_assign=True)
    if membership is None:
        return GroupPermissions(is_owner=False, can_create=False, can_edit=False, can_assign=False)
    return GroupPermissions(
        is_owner=False,
        can_create=membership.can_create,
        can_edit=membership.can_edit,
        can_assign=membership.can_assign,
    )


# ── Group CRUD ────────────────────────────────────────────────────────────────


def create_group(session: Session, user: AppUser, data: GroupCreate) -> GroupRead:
    group = MealGroup(name=data.name, description=data.description, owner_id=user.id)
    group = repository.save_group(session, group)

    # Automatically add creator as owner member
    owner_member = GroupMember(
        group_id=group.id,
        user_id=user.id,
        role="owner",
        can_create=True,
        can_edit=True,
        can_assign=True,
    )
    repository.save_member(session, owner_member)

    log_event(
        session,
        action="GROUP_CREATE",
        user_id=user.id,
        user_email=user.email,
        resource_type="meal_group",
        resource_id=str(group.id),
        details=f"Created meal group: {group.name}",
    )

    return GroupRead(
        id=group.id,
        name=group.name,
        description=group.description,
        owner_id=group.owner_id,
        owner_name=user.name,
        members_count=1,
        created_at=group.created_at,
        my_role="owner",
        my_permissions=GroupPermissions(is_owner=True, can_create=True, can_edit=True, can_assign=True),
    )


def list_groups(session: Session, user: AppUser) -> list[GroupRead]:
    groups = repository.list_all_groups(session) if user.role == "admin" else repository.list_user_groups(session, user.id)

    results = []
    for g in groups:
        owner = user_repo.get(session, g.owner_id)
        owner_name = owner.name if owner else "Unknown"
        count = repository.count_group_members(session, g.id)
        membership = repository.get_membership(session, g.id, user.id)
        my_role = "owner" if g.owner_id == user.id else (membership.role if membership else None)
        perms = get_user_permissions(g, membership, user)

        results.append(
            GroupRead(
                id=g.id,
                name=g.name,
                description=g.description,
                owner_id=g.owner_id,
                owner_name=owner_name,
                members_count=count,
                created_at=g.created_at,
                my_role=my_role,
                my_permissions=perms,
            )
        )
    return results


def get_group_detail(session: Session, group_id: int, user: AppUser) -> GroupDetailRead:
    group, membership = check_group_access(session, group_id, user)
    owner = user_repo.get(session, group.owner_id)
    owner_name = owner.name if owner else "Unknown"
    perms = get_user_permissions(group, membership, user)
    my_role = "owner" if group.owner_id == user.id else (membership.role if membership else None)

    # Members list
    members_raw = repository.list_group_members(session, group.id)
    members_read = []
    for m in members_raw:
        u = user_repo.get(session, m.user_id)
        if u:
            members_read.append(
                GroupMemberRead(
                    id=m.id,
                    group_id=m.group_id,
                    user_id=m.user_id,
                    user_name=u.name,
                    user_email=u.email,
                    role=m.role,
                    can_create=m.can_create,
                    can_edit=m.can_edit,
                    can_assign=m.can_assign,
                    joined_at=m.joined_at,
                )
            )

    # Group Orders list
    orders_raw = repository.list_group_orders(session, group.id)
    orders_read = []
    for o in orders_raw:
        creator = user_repo.get(session, o.creator_id)
        c_name = creator.name if creator else "Unknown"
        items_raw = repository.list_order_items(session, o.id)
        items_read = []
        for it in items_raw:
            adder = user_repo.get(session, it.added_by_id)
            assignee = user_repo.get(session, it.assigned_to_id) if it.assigned_to_id else None
            items_read.append(
                GroupOrderItemRead(
                    id=it.id,
                    group_order_id=it.group_order_id,
                    menu_item_id=it.menu_item_id,
                    name=it.name,
                    unit_price=it.unit_price,
                    quantity=it.quantity,
                    subtotal=round(it.unit_price * it.quantity, 2),
                    added_by_id=it.added_by_id,
                    added_by_name=adder.name if adder else "Unknown",
                    assigned_to_id=it.assigned_to_id,
                    assigned_to_name=assignee.name if assignee else None,
                    notes=it.notes,
                )
            )
        orders_read.append(
            GroupOrderRead(
                id=o.id,
                group_id=o.group_id,
                creator_id=o.creator_id,
                creator_name=c_name,
                title=o.title,
                notes=o.notes,
                status=o.status,
                total=o.total,
                items=items_read,
                created_at=o.created_at,
                updated_at=o.updated_at,
            )
        )

    return GroupDetailRead(
        id=group.id,
        name=group.name,
        description=group.description,
        owner_id=group.owner_id,
        owner_name=owner_name,
        members_count=len(members_read),
        created_at=group.created_at,
        my_role=my_role,
        my_permissions=perms,
        members=members_read,
        orders=orders_read,
    )


def update_group(session: Session, group_id: int, user: AppUser, data: GroupUpdate) -> GroupRead:
    group, membership = check_group_access(session, group_id, user)
    check_owner(group, user)

    if data.name is not None:
        group.name = data.name.strip()
    if data.description is not None:
        group.description = data.description.strip()
    group.updated_at = utc_now()
    group = repository.save_group(session, group)

    owner = user_repo.get(session, group.owner_id)
    count = repository.count_group_members(session, group.id)

    log_event(
        session,
        action="GROUP_UPDATE",
        user_id=user.id,
        user_email=user.email,
        resource_type="meal_group",
        resource_id=str(group.id),
        details=f"Updated group details: {group.name}",
    )

    return GroupRead(
        id=group.id,
        name=group.name,
        description=group.description,
        owner_id=group.owner_id,
        owner_name=owner.name if owner else "Unknown",
        members_count=count,
        created_at=group.created_at,
        my_role="owner",
        my_permissions=GroupPermissions(is_owner=True, can_create=True, can_edit=True, can_assign=True),
    )


def delete_group(session: Session, group_id: int, user: AppUser) -> None:
    group, _ = check_group_access(session, group_id, user)
    check_owner(group, user)

    name = group.name
    repository.delete_group(session, group)

    log_event(
        session,
        action="GROUP_DELETE",
        user_id=user.id,
        user_email=user.email,
        resource_type="meal_group",
        resource_id=str(group_id),
        details=f"Deleted meal group: {name}",
    )


# ── Members Management (Owner-Only) ───────────────────────────────────────────


def add_member(session: Session, group_id: int, user: AppUser, data: GroupMemberAdd) -> GroupMemberRead:
    group, _ = check_group_access(session, group_id, user)
    check_owner(group, user)

    target_user = user_repo.get_by_email(session, data.email)
    if target_user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"No registered user with email: {data.email}")

    existing = repository.get_membership(session, group.id, target_user.id)
    if existing:
        raise HTTPException(status.HTTP_409_CONFLICT, "User is already a member of this group")

    member = GroupMember(
        group_id=group.id,
        user_id=target_user.id,
        role="member",
        can_create=data.can_create,
        can_edit=data.can_edit,
        can_assign=data.can_assign,
    )
    member = repository.save_member(session, member)

    log_event(
        session,
        action="GROUP_MEMBER_ADD",
        user_id=user.id,
        user_email=user.email,
        resource_type="meal_group",
        resource_id=str(group.id),
        details=f"Added {target_user.email} with perms (create={data.can_create}, edit={data.can_edit}, assign={data.can_assign})",
    )

    return GroupMemberRead(
        id=member.id,
        group_id=member.group_id,
        user_id=member.user_id,
        user_name=target_user.name,
        user_email=target_user.email,
        role=member.role,
        can_create=member.can_create,
        can_edit=member.can_edit,
        can_assign=member.can_assign,
        joined_at=member.joined_at,
    )


def update_member_permissions(
    session: Session, group_id: int, target_user_id: int, user: AppUser, data: GroupMemberUpdate
) -> GroupMemberRead:
    group, _ = check_group_access(session, group_id, user)
    check_owner(group, user)

    member = repository.get_membership(session, group.id, target_user_id)
    if member is None:
        raise _not_found("Member not found in this group")

    if member.role == "owner":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Cannot modify permissions of the group owner")

    if data.can_create is not None:
        member.can_create = data.can_create
    if data.can_edit is not None:
        member.can_edit = data.can_edit
    if data.can_assign is not None:
        member.can_assign = data.can_assign

    member = repository.save_member(session, member)
    target_user = user_repo.get(session, target_user_id)

    log_event(
        session,
        action="GROUP_PERM_UPDATE",
        user_id=user.id,
        user_email=user.email,
        resource_type="meal_group",
        resource_id=str(group.id),
        details=f"Updated permissions for user {target_user_id} in group {group.id}",
    )

    return GroupMemberRead(
        id=member.id,
        group_id=member.group_id,
        user_id=member.user_id,
        user_name=target_user.name if target_user else "User",
        user_email=target_user.email if target_user else "Unknown",
        role=member.role,
        can_create=member.can_create,
        can_edit=member.can_edit,
        can_assign=member.can_assign,
        joined_at=member.joined_at,
    )


def remove_member(session: Session, group_id: int, target_user_id: int, user: AppUser) -> None:
    group, _ = check_group_access(session, group_id, user)

    # Either owner can remove member, or member can remove self (leave group)
    if group.owner_id != user.id and user.id != target_user_id and user.role != "admin":
        raise _forbidden("Only the group owner can remove other members")

    member = repository.get_membership(session, group.id, target_user_id)
    if member is None:
        raise _not_found("Member not found in this group")

    if member.user_id == group.owner_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Group owner cannot be removed. Transfer ownership or delete group.")

    repository.delete_member(session, member)

    log_event(
        session,
        action="GROUP_MEMBER_REMOVE",
        user_id=user.id,
        user_email=user.email,
        resource_type="meal_group",
        resource_id=str(group.id),
        details=f"Removed user {target_user_id} from group {group.id}",
    )


# ── Group Orders (Fine-Grained Permissions) ───────────────────────────────────


def create_group_order(session: Session, group_id: int, user: AppUser, data: GroupOrderCreate) -> GroupOrderRead:
    group, membership = check_group_access(session, group_id, user)
    perms = get_user_permissions(group, membership, user)

    # Permission check: must have 'can_create'
    if not perms.can_create:
        raise _forbidden("You do not have permission to create orders in this group")

    order = GroupOrder(group_id=group.id, creator_id=user.id, title=data.title, notes=data.notes, status="open")
    order = repository.save_group_order(session, order)

    total = 0.0
    items_read = []
    for it_data in data.items:
        m_item = menu_repo.get(session, it_data.menu_item_id)
        if m_item is None or not m_item.is_available:
            continue

        # If assigning item, check 'can_assign'
        assigned_id = it_data.assigned_to_id
        if assigned_id and not perms.can_assign:
            assigned_id = None

        item = GroupOrderItem(
            group_order_id=order.id,
            menu_item_id=m_item.id,
            name=m_item.name,
            unit_price=m_item.price,
            quantity=it_data.quantity,
            added_by_id=user.id,
            assigned_to_id=assigned_id,
            notes=it_data.notes,
        )
        item = repository.save_order_item(session, item)
        subtotal = round(item.unit_price * item.quantity, 2)
        total += subtotal

        assignee = user_repo.get(session, item.assigned_to_id) if item.assigned_to_id else None
        items_read.append(
            GroupOrderItemRead(
                id=item.id,
                group_order_id=item.group_order_id,
                menu_item_id=item.menu_item_id,
                name=item.name,
                unit_price=item.unit_price,
                quantity=item.quantity,
                subtotal=subtotal,
                added_by_id=user.id,
                added_by_name=user.name,
                assigned_to_id=item.assigned_to_id,
                assigned_to_name=assignee.name if assignee else None,
                notes=item.notes,
            )
        )

    order.total = round(total, 2)
    order = repository.save_group_order(session, order)

    return GroupOrderRead(
        id=order.id,
        group_id=order.group_id,
        creator_id=order.creator_id,
        creator_name=user.name,
        title=order.title,
        notes=order.notes,
        status=order.status,
        total=order.total,
        items=items_read,
        created_at=order.created_at,
        updated_at=order.updated_at,
    )


def add_item_to_group_order(
    session: Session, group_id: int, order_id: int, user: AppUser, data: GroupOrderItemCreate
) -> GroupOrderItemRead:
    group, membership = check_group_access(session, group_id, user)
    perms = get_user_permissions(group, membership, user)

    # Permission check: 'can_create'
    if not perms.can_create:
        raise _forbidden("You do not have permission to add items in this group")

    order = repository.get_group_order(session, order_id)
    if order is None or order.group_id != group.id:
        raise _not_found("Group order not found")

    m_item = menu_repo.get(session, data.menu_item_id)
    if m_item is None:
        raise _not_found("Menu item not found")

    # If assigning, check 'can_assign'
    assigned_id = data.assigned_to_id
    if assigned_id and not perms.can_assign:
        raise _forbidden("You do not have permission to assign items to members")

    item = GroupOrderItem(
        group_order_id=order.id,
        menu_item_id=m_item.id,
        name=m_item.name,
        unit_price=m_item.price,
        quantity=data.quantity,
        added_by_id=user.id,
        assigned_to_id=assigned_id,
        notes=data.notes,
    )
    item = repository.save_order_item(session, item)

    # Recalculate order total
    items = repository.list_order_items(session, order.id)
    order.total = round(sum(it.unit_price * it.quantity for it in items), 2)
    order.updated_at = utc_now()
    repository.save_group_order(session, order)

    assignee = user_repo.get(session, item.assigned_to_id) if item.assigned_to_id else None
    return GroupOrderItemRead(
        id=item.id,
        group_order_id=item.group_order_id,
        menu_item_id=item.menu_item_id,
        name=item.name,
        unit_price=item.unit_price,
        quantity=item.quantity,
        subtotal=round(item.unit_price * item.quantity, 2),
        added_by_id=user.id,
        added_by_name=user.name,
        assigned_to_id=item.assigned_to_id,
        assigned_to_name=assignee.name if assignee else None,
        notes=item.notes,
    )


def update_order_item(
    session: Session, group_id: int, order_id: int, item_id: int, user: AppUser, data: GroupOrderItemUpdate
) -> GroupOrderItemRead:
    group, membership = check_group_access(session, group_id, user)
    perms = get_user_permissions(group, membership, user)

    order = repository.get_group_order(session, order_id)
    if order is None or order.group_id != group.id:
        raise _not_found("Group order not found")

    item = repository.get_order_item(session, item_id)
    if item is None or item.group_order_id != order.id:
        raise _not_found("Order item not found")

    is_editing_details = (data.quantity is not None) or (data.notes is not None)
    is_assigning = data.assigned_to_id is not None

    if is_editing_details and not (perms.can_edit or item.added_by_id == user.id):
        raise _forbidden("You do not have permission to edit this item (requires 'edit' permission)")

    if is_assigning and not perms.can_assign:
        raise _forbidden("You do not have permission to assign items to members")

    if data.quantity is not None:
        item.quantity = data.quantity
    if data.assigned_to_id is not None:
        item.assigned_to_id = data.assigned_to_id
    if data.notes is not None:
        item.notes = data.notes

    item = repository.save_order_item(session, item)

    # Recalculate order total
    items = repository.list_order_items(session, order.id)
    order.total = round(sum(it.unit_price * it.quantity for it in items), 2)
    order.updated_at = utc_now()
    repository.save_group_order(session, order)

    adder = user_repo.get(session, item.added_by_id)
    assignee = user_repo.get(session, item.assigned_to_id) if item.assigned_to_id else None
    return GroupOrderItemRead(
        id=item.id,
        group_order_id=item.group_order_id,
        menu_item_id=item.menu_item_id,
        name=item.name,
        unit_price=item.unit_price,
        quantity=item.quantity,
        subtotal=round(item.unit_price * item.quantity, 2),
        added_by_id=item.added_by_id,
        added_by_name=adder.name if adder else "User",
        assigned_to_id=item.assigned_to_id,
        assigned_to_name=assignee.name if assignee else None,
        notes=item.notes,
    )


def delete_order_item(session: Session, group_id: int, order_id: int, item_id: int, user: AppUser) -> None:
    group, membership = check_group_access(session, group_id, user)
    perms = get_user_permissions(group, membership, user)

    order = repository.get_group_order(session, order_id)
    if order is None or order.group_id != group.id:
        raise _not_found("Group order not found")

    item = repository.get_order_item(session, item_id)
    if item is None or item.group_order_id != order.id:
        raise _not_found("Order item not found")

    can_delete = perms.can_edit or (item.added_by_id == user.id)
    if not can_delete:
        raise _forbidden("You do not have permission to delete this item")

    repository.delete_order_item(session, item)

    # Recalculate order total
    items = repository.list_order_items(session, order.id)
    order.total = round(sum(it.unit_price * it.quantity for it in items), 2)
    order.updated_at = utc_now()
    repository.save_group_order(session, order)

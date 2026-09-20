"""
BHU-SYNC Phase B: Administration Router
Provides user and organization management for PLATFORM_ADMIN and DEPARTMENT_ADMIN.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status

from services.auth_service import auth_service, ORGANIZATIONS_SEED, ROLE_PERMISSIONS_MAP
from dependencies.auth import get_current_profile, require_permission

router = APIRouter(prefix="/admin", tags=["Administration"])


class UpdateUserStatusRequest(BaseModel):
    is_active: bool


@router.get("/users")
def list_users(
    profile: Dict[str, Any] = Depends(require_permission("users.view"))
):
    """
    List user profiles.
    - PLATFORM_ADMIN sees all users.
    - DEPARTMENT_ADMIN sees only members within their own organization.
    """
    users = auth_service.list_users(profile)
    return {
        "count": len(users),
        "users": users
    }


@router.patch("/users/{user_id}/status")
def update_user_status(
    user_id: str,
    request: UpdateUserStatusRequest,
    profile: Dict[str, Any] = Depends(require_permission("users.manage"))
):
    """
    Activate or deactivate a user account.
    - PLATFORM_ADMIN can modify any user.
    - DEPARTMENT_ADMIN can only modify members of their own organization (cross-org modification is rejected with HTTP 403).
    """
    try:
        updated_profile = auth_service.update_user_status(
            requester_profile=profile,
            target_user_id=user_id,
            is_active=request.is_active
        )
        if not updated_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User '{user_id}' not found"
            )
        return {
            "status": "success",
            "message": f"User status updated to {'active' if request.is_active else 'inactive'}",
            "user": updated_profile
        }
    except PermissionError as pe:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(pe)
        )


@router.get("/organizations")
def list_organizations(
    profile: Dict[str, Any] = Depends(require_permission("organization.manage"))
):
    """
    List government organizations / administrative units.
    """
    return {
        "count": len(ORGANIZATIONS_SEED),
        "organizations": ORGANIZATIONS_SEED
    }


@router.get("/roles")
def list_roles(
    profile: Dict[str, Any] = Depends(require_permission("roles.manage"))
):
    """
    List available RBAC roles and their associated permission counts.
    """
    roles_summary = [
        {
            "role": role_name,
            "permissions_count": len(perms),
            "permissions": perms
        }
        for role_name, perms in ROLE_PERMISSIONS_MAP.items()
    ]
    return {
        "count": len(roles_summary),
        "roles": roles_summary
    }

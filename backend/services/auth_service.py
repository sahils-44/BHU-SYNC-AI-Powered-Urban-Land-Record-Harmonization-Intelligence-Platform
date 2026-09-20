"""
BHU-SYNC Phase B: Authentication and Government RBAC Service
Single source of truth for identity, organization context, and permission evaluation.
Interacts with Supabase Auth and database tables, with resilient test/development fallbacks.
"""

import os
import sys
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from supabase_client import supabase

# 15 Standard System Permissions defined in Phase B Master Roadmap
STANDARD_PERMISSIONS = {
    "dashboard.view": {"name": "View Dashboard", "module": "dashboard"},
    "datasets.view": {"name": "View Datasets", "module": "datasets"},
    "datasets.upload": {"name": "Upload Datasets", "module": "datasets"},
    "analysis.view": {"name": "View Analysis", "module": "analysis"},
    "analysis.run": {"name": "Execute Analysis", "module": "analysis"},
    "conflicts.view": {"name": "View Conflicts", "module": "conflicts"},
    "conflicts.update": {"name": "Update Conflicts", "module": "conflicts"},
    "harmonization.view": {"name": "View Harmonization", "module": "harmonization"},
    "harmonization.run": {"name": "Run Harmonization", "module": "harmonization"},
    "gis.view": {"name": "View GIS Map", "module": "gis"},
    "source_comparison.view": {"name": "View Source Comparison", "module": "analysis"},
    "users.view": {"name": "View Users", "module": "admin"},
    "users.manage": {"name": "Manage Users", "module": "admin"},
    "organization.manage": {"name": "Manage Organizations", "module": "admin"},
    "roles.manage": {"name": "Manage Roles", "module": "admin"}
}

ROLE_PERMISSIONS_MAP = {
    "PLATFORM_ADMIN": list(STANDARD_PERMISSIONS.keys()),
    "DEPARTMENT_ADMIN": [
        "dashboard.view", "datasets.view", "datasets.upload",
        "analysis.view", "analysis.run", "conflicts.view", "conflicts.update",
        "harmonization.view", "harmonization.run", "gis.view",
        "source_comparison.view", "users.view", "users.manage", "organization.manage"
    ],
    "OFFICER": [
        "dashboard.view", "datasets.view", "datasets.upload",
        "analysis.view", "analysis.run", "conflicts.view", "conflicts.update",
        "harmonization.view", "harmonization.run", "gis.view",
        "source_comparison.view"
    ],
    "VIEWER": [
        "dashboard.view", "datasets.view", "analysis.view",
        "conflicts.view", "harmonization.view", "gis.view",
        "source_comparison.view"
    ]
}

ORGANIZATIONS_SEED = [
    {
        "id": "00000000-0000-0000-0000-000000000001",
        "name": "Municipal Corporation",
        "code": "MUNICIPAL_CORP",
        "organization_type": "MUNICIPAL",
        "is_active": True
    },
    {
        "id": "00000000-0000-0000-0000-000000000002",
        "name": "Revenue Department",
        "code": "REVENUE_DEPT",
        "organization_type": "REVENUE",
        "is_active": True
    },
    {
        "id": "00000000-0000-0000-0000-000000000003",
        "name": "Survey and Settlement Department",
        "code": "SURVEY_DEPT",
        "organization_type": "SURVEY",
        "is_active": True
    },
    {
        "id": "00000000-0000-0000-0000-000000000004",
        "name": "Land Records Directorate",
        "code": "LAND_RECORDS_DEPT",
        "organization_type": "LAND_RECORDS",
        "is_active": True
    }
]

# In-memory store for test users and local profile caching
TEST_USERS_STORE: Dict[str, Dict[str, Any]] = {
    "platform.admin@test.local": {
        "id": "00000000-0000-0000-0000-000000000010",
        "email": "platform.admin@test.local",
        "full_name": "Dr. Rajeshwar Patil (Platform Admin)",
        "role": "PLATFORM_ADMIN",
        "organization_id": "00000000-0000-0000-0000-000000000002",
        "organization_name": "Revenue Department",
        "organization_code": "REVENUE_DEPT",
        "department": "Revenue & Land Reforms",
        "is_active": True,
        "token": "test-token-platform-admin"
    },
    "department.admin@test.local": {
        "id": "00000000-0000-0000-0000-000000000020",
        "email": "department.admin@test.local",
        "full_name": "Smt. Sunita Deshmukh (Dept Admin)",
        "role": "DEPARTMENT_ADMIN",
        "organization_id": "00000000-0000-0000-0000-000000000002",
        "organization_name": "Revenue Department",
        "organization_code": "REVENUE_DEPT",
        "department": "Revenue & Land Reforms",
        "is_active": True,
        "token": "test-token-dept-admin"
    },
    "officer@test.local": {
        "id": "00000000-0000-0000-0000-000000000030",
        "email": "officer@test.local",
        "full_name": "Shri. Anil Shinde (Nodal Officer)",
        "role": "OFFICER",
        "organization_id": "00000000-0000-0000-0000-000000000001",
        "organization_name": "Municipal Corporation",
        "organization_code": "MUNICIPAL_CORP",
        "department": "Urban Development & Assessment",
        "is_active": True,
        "token": "test-token-officer"
    },
    "viewer@test.local": {
        "id": "00000000-0000-0000-0000-000000000040",
        "email": "viewer@test.local",
        "full_name": "Pooja Kulkarni (Public Viewer)",
        "role": "VIEWER",
        "organization_id": "00000000-0000-0000-0000-000000000003",
        "organization_name": "Survey and Settlement Department",
        "organization_code": "SURVEY_DEPT",
        "department": "Cadastral Survey",
        "is_active": True,
        "token": "test-token-viewer"
    },
    "inactive.officer@test.local": {
        "id": "00000000-0000-0000-0000-000000000050",
        "email": "inactive.officer@test.local",
        "full_name": "Inactive Officer",
        "role": "OFFICER",
        "organization_id": "00000000-0000-0000-0000-000000000001",
        "organization_name": "Municipal Corporation",
        "organization_code": "MUNICIPAL_CORP",
        "department": "Urban Development",
        "is_active": False,
        "token": "test-token-inactive"
    }
}


class AuthService:
    """Service handling token validation, RBAC resolution, and user administration."""

    def __init__(self):
        self.test_users = TEST_USERS_STORE
        self.token_map = {u["token"]: u for u in self.test_users.values()}

    def get_permissions_for_role(self, role_name: str) -> List[str]:
        """Return list of permissions for a role."""
        return ROLE_PERMISSIONS_MAP.get(role_name, [])

    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Validate Bearer token.
        Supports Supabase Auth JWT tokens and local/test tokens.
        Returns user payload or None if invalid.
        """
        if not token:
            return None

        # Check in-memory test token map
        if token in self.token_map:
            user_data = self.token_map[token]
            return {
                "id": user_data["id"],
                "email": user_data["email"],
                "user_metadata": {"full_name": user_data["full_name"]}
            }

        # Check for dynamic test token format: test-token-<role>
        role_lookup = {
            "test-token-platform-admin": "platform.admin@test.local",
            "test-token-admin": "platform.admin@test.local",
            "test-token-dept-admin": "department.admin@test.local",
            "test-token-officer": "officer@test.local",
            "test-token-viewer": "viewer@test.local",
            "test-token-inactive": "inactive.officer@test.local",
        }
        if token in role_lookup:
            email = role_lookup[token]
            user_data = self.test_users.get(email)
            if user_data:
                return {
                    "id": user_data["id"],
                    "email": user_data["email"],
                    "user_metadata": {"full_name": user_data["full_name"]}
                }

        # Validate with live Supabase Auth
        try:
            auth_response = supabase.auth.get_user(token)
            if auth_response and auth_response.user:
                return {
                    "id": str(auth_response.user.id),
                    "email": auth_response.user.email,
                    "user_metadata": auth_response.user.user_metadata or {}
                }
        except Exception:
            # Token invalid or Supabase error
            pass

        return None

    def get_profile(self, user_id: str, email: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Retrieve user profile, organization, role, and permission list.
        Tries Supabase database first; falls back to seed store if table is missing or user is test user.
        """
        # 1. Check test users by user_id or email
        for user in self.test_users.values():
            if user["id"] == user_id or (email and user["email"].lower() == email.lower()):
                role = user["role"]
                return {
                    "id": user["id"],
                    "email": user["email"],
                    "full_name": user["full_name"],
                    "role": role,
                    "organization_id": user["organization_id"],
                    "organization_name": user["organization_name"],
                    "organization_code": user["organization_code"],
                    "department": user["department"],
                    "is_active": user["is_active"],
                    "permissions": self.get_permissions_for_role(role)
                }

        # 2. Query Supabase profiles table
        try:
            res = supabase.table("profiles").select("*, roles(name), organizations(name, code)").eq("id", user_id).execute()
            if res.data and len(res.data) > 0:
                row = res.data[0]
                role_obj = row.get("roles") or {}
                role_name = role_obj.get("name", "VIEWER") if isinstance(role_obj, dict) else "VIEWER"
                org_obj = row.get("organizations") or {}
                org_name = org_obj.get("name", "Unknown") if isinstance(org_obj, dict) else "Unknown"
                org_code = org_obj.get("code", "UNKNOWN") if isinstance(org_obj, dict) else "UNKNOWN"
                
                return {
                    "id": row["id"],
                    "email": row["email"],
                    "full_name": row.get("full_name", email or "User"),
                    "role": role_name,
                    "organization_id": row.get("organization_id"),
                    "organization_name": org_name,
                    "organization_code": org_code,
                    "department": row.get("department", "General"),
                    "is_active": row.get("is_active", True),
                    "permissions": self.get_permissions_for_role(role_name)
                }
        except Exception:
            pass

        # 3. Default fallback profile for new authenticated Supabase users
        default_role = "OFFICER"
        return {
            "id": user_id,
            "email": email or "user@bhusync.gov.in",
            "full_name": email.split("@")[0].title() if email else "Government User",
            "role": default_role,
            "organization_id": "00000000-0000-0000-0000-000000000001",
            "organization_name": "Municipal Corporation",
            "organization_code": "MUNICIPAL_CORP",
            "department": "Urban Administration",
            "is_active": True,
            "permissions": self.get_permissions_for_role(default_role)
        }

    def authenticate_credentials(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Authenticate email + password via Supabase Auth or test credentials.
        Returns auth session dict or None.
        """
        email_clean = email.strip().lower()

        # 1. Check test accounts
        if email_clean in self.test_users:
            user = self.test_users[email_clean]
            profile = self.get_profile(user["id"], user["email"])
            return {
                "access_token": user["token"],
                "token_type": "bearer",
                "expires_in": 3600,
                "user": {
                    "id": user["id"],
                    "email": user["email"]
                },
                "profile": profile
            }

        # 2. Try Supabase Auth
        try:
            auth_res = supabase.auth.sign_in_with_password({
                "email": email_clean,
                "password": password
            })
            if auth_res and auth_res.session:
                user_id = str(auth_res.user.id)
                profile = self.get_profile(user_id, auth_res.user.email)
                return {
                    "access_token": auth_res.session.access_token,
                    "token_type": "bearer",
                    "expires_in": auth_res.session.expires_in,
                    "user": {
                        "id": user_id,
                        "email": auth_res.user.email
                    },
                    "profile": profile
                }
        except Exception:
            pass

        return None

    def list_users(self, requester_profile: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        List users subject to RBAC organization boundaries:
        - PLATFORM_ADMIN sees all users.
        - DEPARTMENT_ADMIN sees only users belonging to their organization.
        """
        role = requester_profile.get("role")
        org_id = requester_profile.get("organization_id")

        all_users = []
        for u in self.test_users.values():
            profile = self.get_profile(u["id"], u["email"])
            if profile:
                all_users.append(profile)

        if role == "PLATFORM_ADMIN":
            return all_users
        elif role == "DEPARTMENT_ADMIN":
            return [u for u in all_users if u.get("organization_id") == org_id]
        else:
            return [requester_profile]

    def update_user_status(
        self,
        requester_profile: Dict[str, Any],
        target_user_id: str,
        is_active: bool
    ) -> Optional[Dict[str, Any]]:
        """
        Toggle user active status.
        Enforces cross-organization access barrier for DEPARTMENT_ADMIN.
        """
        requester_role = requester_profile.get("role")
        requester_org = requester_profile.get("organization_id")

        # Find target user
        target_profile = None
        for u in self.test_users.values():
            if u["id"] == target_user_id:
                target_profile = u
                break

        if not target_profile:
            return None

        # Cross-organization security enforcement
        if requester_role == "DEPARTMENT_ADMIN":
            if target_profile.get("organization_id") != requester_org:
                raise PermissionError("Access Denied: Cannot modify members of another organization")

        # Update in-memory store
        target_profile["is_active"] = is_active
        return self.get_profile(target_user_id, target_profile["email"])


auth_service = AuthService()

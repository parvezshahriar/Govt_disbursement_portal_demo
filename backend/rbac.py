# Role-Based Access Control (RBAC) for Government Disbursement Portal
# This file defines roles, permissions, and utility functions for access control

from __future__ import annotations
from enum import Enum
from typing import List, Set

# Define Roles
class Role(str, Enum):
    """User roles in the system"""
    ADMIN = "admin"
    MANAGER = "manager"
    USER = "user"
    GUEST = "guest"


# Define Operations/Permissions
class Permission(str, Enum):
    """Available permissions in the system"""
    # Product Management
    VIEW_PRODUCTS = "view_products"
    CREATE_PRODUCT = "create_product"
    EDIT_PRODUCT = "edit_product"
    DELETE_PRODUCT = "delete_product"
    
    # CSV Operations
    UPLOAD_CSV = "upload_csv"
    VIEW_VALIDATION_REPORT = "view_validation_report"
    PROCESS_VALID_ROWS = "process_valid_rows"
    DOWNLOAD_ERROR_REPORT = "download_error_report"
    
    # User Management
    VIEW_USERS = "view_users"
    CREATE_USER = "create_user"
    EDIT_USER = "edit_user"
    DELETE_USER = "delete_user"
    
    # Audit & Reports
    VIEW_AUDIT_LOG = "view_audit_log"
    VIEW_TRANSACTION_HISTORY = "view_transaction_history"
    EXPORT_REPORTS = "export_reports"
    
    # Authentication
    LOGIN = "login"
    REGISTER = "register"
    LOGOUT = "logout"


# Define Role Permissions Mapping
ROLE_PERMISSIONS: dict[Role, Set[Permission]] = {
    Role.ADMIN: {
        # Product Management - Full Access
        Permission.VIEW_PRODUCTS,
        Permission.CREATE_PRODUCT,
        Permission.EDIT_PRODUCT,
        Permission.DELETE_PRODUCT,
        
        # CSV Operations - Full Access
        Permission.UPLOAD_CSV,
        Permission.VIEW_VALIDATION_REPORT,
        Permission.PROCESS_VALID_ROWS,
        Permission.DOWNLOAD_ERROR_REPORT,
        
        # User Management - Full Access
        Permission.VIEW_USERS,
        Permission.CREATE_USER,
        Permission.EDIT_USER,
        Permission.DELETE_USER,
        
        # Audit & Reports - Full Access
        Permission.VIEW_AUDIT_LOG,
        Permission.VIEW_TRANSACTION_HISTORY,
        Permission.EXPORT_REPORTS,
        
        # Authentication
        Permission.LOGIN,
        Permission.REGISTER,
        Permission.LOGOUT,
    },
    
    Role.MANAGER: {
        # Product Management - Edit Only
        Permission.VIEW_PRODUCTS,
        Permission.EDIT_PRODUCT,
        # NOT: CREATE, DELETE
        
        # CSV Operations - Full Access
        Permission.UPLOAD_CSV,
        Permission.VIEW_VALIDATION_REPORT,
        Permission.PROCESS_VALID_ROWS,
        Permission.DOWNLOAD_ERROR_REPORT,
        
        # Authentication
        Permission.LOGIN,
        Permission.LOGOUT,
    },
    
    Role.USER: {
        # Product Management - View Only
        Permission.VIEW_PRODUCTS,
        # NOT: CREATE, EDIT, DELETE
        
        # Authentication
        Permission.LOGIN,
        Permission.LOGOUT,
    },
    
    Role.GUEST: {
        # Authentication Only
        Permission.LOGIN,
        Permission.REGISTER,
    },
}


def get_role_permissions(role: Role) -> Set[Permission]:
    """
    Get all permissions for a given role
    
    Args:
        role: The user's role
        
    Returns:
        Set of permissions available to the role
    """
    return ROLE_PERMISSIONS.get(role, set())


def has_permission(role: Role, permission: Permission) -> bool:
    """
    Check if a role has a specific permission
    
    Args:
        role: The user's role
        permission: The permission to check
        
    Returns:
        True if the role has the permission, False otherwise
    """
    permissions = get_role_permissions(role)
    return permission in permissions


def has_any_permission(role: Role, permissions: List[Permission]) -> bool:
    """
    Check if a role has any of the specified permissions
    
    Args:
        role: The user's role
        permissions: List of permissions to check
        
    Returns:
        True if the role has at least one of the permissions
    """
    user_permissions = get_role_permissions(role)
    return any(perm in user_permissions for perm in permissions)


def has_all_permissions(role: Role, permissions: List[Permission]) -> bool:
    """
    Check if a role has all of the specified permissions
    
    Args:
        role: The user's role
        permissions: List of permissions to check
        
    Returns:
        True if the role has all of the permissions
    """
    user_permissions = get_role_permissions(role)
    return all(perm in user_permissions for perm in permissions)


# Test Cases for RBAC
if __name__ == "__main__":
    print("=" * 60)
    print("ROLE-BASED ACCESS CONTROL (RBAC) TEST SUITE")
    print("=" * 60)
    
    # Test 1: Check Admin Permissions
    print("\n[TEST 1] ADMIN ROLE PERMISSIONS")
    print("-" * 60)
    admin_perms = get_role_permissions(Role.ADMIN)
    print(f"Admin has {len(admin_perms)} permissions")
    print(f"Can view products: {has_permission(Role.ADMIN, Permission.VIEW_PRODUCTS)}")
    print(f"Can delete products: {has_permission(Role.ADMIN, Permission.DELETE_PRODUCT)}")
    print(f"Can delete users: {has_permission(Role.ADMIN, Permission.DELETE_USER)}")
    
    # Test 2: Check Manager Permissions
    print("\n[TEST 2] MANAGER ROLE PERMISSIONS")
    print("-" * 60)
    manager_perms = get_role_permissions(Role.MANAGER)
    print(f"Manager has {len(manager_perms)} permissions")
    print(f"Can view products: {has_permission(Role.MANAGER, Permission.VIEW_PRODUCTS)}")
    print(f"Can upload CSV: {has_permission(Role.MANAGER, Permission.UPLOAD_CSV)}")
    print(f"Can delete products: {has_permission(Role.MANAGER, Permission.DELETE_PRODUCT)}")
    print(f"Can delete users: {has_permission(Role.MANAGER, Permission.DELETE_USER)}")
    
    # Test 3: Check User Permissions
    print("\n[TEST 3] USER ROLE PERMISSIONS")
    print("-" * 60)
    user_perms = get_role_permissions(Role.USER)
    print(f"User has {len(user_perms)} permissions")
    print(f"Can view products: {has_permission(Role.USER, Permission.VIEW_PRODUCTS)}")
    print(f"Can upload CSV: {has_permission(Role.USER, Permission.UPLOAD_CSV)}")
    print(f"Can edit products: {has_permission(Role.USER, Permission.EDIT_PRODUCT)}")
    print(f"Can delete products: {has_permission(Role.USER, Permission.DELETE_PRODUCT)}")
    
    # Test 4: Check Guest Permissions
    print("\n[TEST 4] GUEST ROLE PERMISSIONS")
    print("-" * 60)
    guest_perms = get_role_permissions(Role.GUEST)
    print(f"Guest has {len(guest_perms)} permissions")
    print(f"Can login: {has_permission(Role.GUEST, Permission.LOGIN)}")
    print(f"Can register: {has_permission(Role.GUEST, Permission.REGISTER)}")
    print(f"Can view products: {has_permission(Role.GUEST, Permission.VIEW_PRODUCTS)}")
    
    # Test 5: Test Any Permission
    print("\n[TEST 5] HAS ANY PERMISSION TEST")
    print("-" * 60)
    perms_to_check = [Permission.DELETE_PRODUCT, Permission.DELETE_USER]
    print(f"Admin has any of {[p.value for p in perms_to_check]}: {has_any_permission(Role.ADMIN, perms_to_check)}")
    print(f"Manager has any of {[p.value for p in perms_to_check]}: {has_any_permission(Role.MANAGER, perms_to_check)}")
    print(f"User has any of {[p.value for p in perms_to_check]}: {has_any_permission(Role.USER, perms_to_check)}")
    
    # Test 6: Test All Permissions
    print("\n[TEST 6] HAS ALL PERMISSIONS TEST")
    print("-" * 60)
    perms_to_check = [Permission.VIEW_PRODUCTS, Permission.UPLOAD_CSV]
    print(f"Admin has all of {[p.value for p in perms_to_check]}: {has_all_permissions(Role.ADMIN, perms_to_check)}")
    print(f"Manager has all of {[p.value for p in perms_to_check]}: {has_all_permissions(Role.MANAGER, perms_to_check)}")
    print(f"User has all of {[p.value for p in perms_to_check]}: {has_all_permissions(Role.USER, perms_to_check)}")
    
    # Test 7: Permission Summary
    print("\n[TEST 7] PERMISSION SUMMARY BY ROLE")
    print("-" * 60)
    for role in Role:
        perms = get_role_permissions(role)
        print(f"\n{role.value.upper()} ({len(perms)} permissions):")
        # Group permissions by category
        categories = {}
        for perm in perms:
            category = perm.value.split('_')[0]
            if category not in categories:
                categories[category] = []
            categories[category].append(perm.value)
        
        for category, perm_list in sorted(categories.items()):
            print(f"  {category.capitalize()}: {', '.join(perm_list)}")
    
    print("\n" + "=" * 60)
    print("RBAC TEST SUITE COMPLETED")
    print("=" * 60)

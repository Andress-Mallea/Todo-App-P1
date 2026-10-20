"""Qué puede hacer cada rol. Los permisos viajan dentro del JWT."""

ROLE_PERMISSIONS = {
    "user": ["get:todos", "post:todos", "patch:todos", "get:restaurant"],
    "admin": ["get:todos", "post:todos", "patch:todos", "delete:todos", "get:restaurant"],
}

def permissions_for(role):
    return ROLE_PERMISSIONS.get(role, [])
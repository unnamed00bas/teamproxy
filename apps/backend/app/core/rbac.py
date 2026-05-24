"""Role hierarchy and authorisation helpers.

The model is intentionally simple: three ordered roles. ``operator`` inherits
everything ``viewer`` can do, ``superadmin`` inherits everything ``operator``
can do. Endpoints declare the minimum role they require.
"""

from __future__ import annotations

from app.models.enums import Role

# Higher number => more privileges.
_ROLE_RANK: dict[Role, int] = {
    Role.viewer: 0,
    Role.operator: 1,
    Role.superadmin: 2,
}


def role_satisfies(actual: Role, required: Role) -> bool:
    return _ROLE_RANK[actual] >= _ROLE_RANK[required]

from organizations.db import (
    get_my_organization_details,
    get_organization_details,
    get_policies_for_organization,
    get_policy_details,
)


def _make_get_my_organization_details(user_id: str):
    """Return a no-arg callable that fetches org details for the given user_id."""

    def _fn(**kwargs):
        return get_my_organization_details(user_id)

    return _fn


def get_organization_function_map(user_id: str | None = None):
    mapping = {
        "get_organization_details": get_organization_details,
        "get_policies_for_organization": get_policies_for_organization,
        "get_policy_details": get_policy_details,
    }
    if user_id is not None:
        mapping["get_my_organization_details"] = _make_get_my_organization_details(user_id)
    return mapping

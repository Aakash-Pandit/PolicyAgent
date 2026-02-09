from organizations.db import (
    get_organization_details,
    get_policies_for_organization,
    get_policy_details,
)

def get_organization_function_map():
    return {
        "get_organization_details": get_organization_details,
        "get_policies_for_organization": get_policies_for_organization,
        "get_policy_details": get_policy_details,
    }

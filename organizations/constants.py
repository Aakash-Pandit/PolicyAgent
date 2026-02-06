def get_organization_function_map():
    from organizations.db import (
        get_all_organizations,
        get_leave_allowance,
        get_organization_by_name,
        get_policies_for_organization,
        get_policy_details,
    )

    return {
        "get_organization_by_name": get_organization_by_name,
        "get_all_organizations": get_all_organizations,
        "get_policies_for_organization": get_policies_for_organization,
        "get_policy_details": get_policy_details,
        "get_leave_allowance": get_leave_allowance,
    }

ORGANIZATION_TOOLS = [
    {
        "name": "get_policies_for_organization",
        "description": "Returns all leave policies for a specific organization.",
        "parameter_definitions": {
            "organization_name": {
                "description": "The name of the organization.",
                "type": "str",
                "required": True,
            },
        },
    },
    {
        "name": "get_policy_details",
        "description": "Returns details of a specific leave policy by name.",
        "parameter_definitions": {
            "policy_name": {
                "description": "The name of the policy.",
                "type": "str",
                "required": True,
            },
        },
    },
    {
        "name": "get_leave_allowance",
        "description": "Returns the leave allowance (max leave days, carry forward days) for an organization.",
        "parameter_definitions": {
            "organization_name": {
                "description": "The name of the organization.",
                "type": "str",
                "required": True,
            },
            "policy_name": {
                "description": "Optional specific policy name to filter by.",
                "type": "str",
                "required": False,
            },
        },
    },
]

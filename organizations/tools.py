ORGANIZATION_TOOLS = [
    {
        "name": "get_my_organization_details",
        "description": (
            "Returns the organization(s) that the requesting user belongs to. "
            "Use this when the user asks about 'my organization', 'details of my organization', "
            "'tell me about my organization', or similar. Looks up the user's memberships and returns org details."
        ),
        "parameter_definitions": {},
    },
    {
        "name": "get_organization_details",
        "description": "Returns organization details by searching for the name.",
        "parameter_definitions": {
            "organization_name": {
                "description": "The name of the organization.",
                "type": "str",
                "required": True,
            },
        },
    },
    {
        "name": "get_policies_for_organization",
        "description": "Returns all policies for a specific organization including document details.",
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
        "description": "Returns details of a specific policy by name including document name and file.",
        "parameter_definitions": {
            "policy_name": {
                "description": "The name of the policy.",
                "type": "str",
                "required": True,
            },
        },
    },
]

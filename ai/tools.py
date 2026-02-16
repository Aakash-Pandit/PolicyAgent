from ai.rag import RAGClient
from organizations.db import get_my_approved_leaves_summary, get_organization_ids_for_user

AI_TOOLS = [
    {
        "name": "search_my_organization_policies",
        "description": (
            "Searches policy documents that belong to the requesting user's organization(s) "
            "and returns relevant excerpts to answer their question. Use this when the user "
            "asks about leave policy, PTO, sick leave, vacation, benefits, or any policy "
            "that applies to their organization. Answers are based only on policies from "
            "organizations the user is a member of."
        ),
        "parameter_definitions": {
            "query": {
                "description": "The user's policy question or what they want to know.",
                "type": "str",
                "required": True,
            },
            "top_k": {
                "description": "Number of relevant policy chunks to return (default 5).",
                "type": "int",
                "required": False,
            },
        },
    },
    {
        "name": "search_policy_embeddings",
        "description": "Searches policy document embeddings to answer policy questions.",
        "parameter_definitions": {
            "query": {
                "description": "The policy question or search query.",
                "type": "str",
                "required": True,
            },
            "top_k": {
                "description": "Number of relevant chunks to return.",
                "type": "int",
                "required": False,
            },
        },
    },
    {
        "name": "get_my_pending_leaves",
        "description": (
            "Returns the requesting user's approved leaves summary and leave policy excerpts "
            "to determine how many leaves are pending/remaining. Use when the user asks "
            "'how many leaves are pending of mine?', 'leaves remaining', 'my leave balance', "
            "'how many days do I have left?', or similar. Combines approved leave count from "
            "the database with leave policy from the organization to compute pending leaves."
        ),
        "parameter_definitions": {},
    },
]


def search_policy_embeddings(query: str, top_k: int = 5):
    return RAGClient().query_policy_index(query, top_k=top_k)


def _make_search_my_organization_policies(user_id: str):
    """Return a callable that searches policy content scoped to the user's organizations."""

    def _fn(query: str, top_k: int = 5, **kwargs):
        org_ids = get_organization_ids_for_user(user_id)
        if not org_ids:
            return {
                "detail": "You are not a member of any organization. No policies to search.",
                "matches": [],
            }
        matches = RAGClient().query_policy_index(
            query, top_k=top_k, organization_ids=org_ids
        )
        if not matches:
            return {
                "detail": "No matching policy content found in your organization's policies.",
                "matches": [],
            }
        return {
            "detail": f"Found {len(matches)} relevant excerpt(s) from your organization's policies.",
            "matches": matches,
        }

    return _fn


def _make_get_my_pending_leaves(user_id: str):
    """Return a callable that fetches approved leaves + leave policy for the user."""

    def _fn(**kwargs):
        approved = get_my_approved_leaves_summary(user_id)
        org_ids = get_organization_ids_for_user(user_id)
        if not org_ids:
            return {
                "detail": "You are not a member of any organization. No leave data available.",
                "approved_leaves": [],
                "policy_excerpts": [],
            }
        policy_matches = RAGClient().query_policy_index(
            "leave policy days allowance sick leave privilege leave PTO annual vacation",
            top_k=5,
            organization_ids=org_ids,
        )
        return {
            "detail": "Your approved leaves and relevant leave policy. Use policy excerpts to determine total allowance and compute pending = allowance - approved.",
            "approved_leaves": approved.get("approved_leaves", []),
            "total_approved_days": approved.get("total_approved_days", 0),
            "policy_excerpts": [
                {"text": m.get("text"), "policy_name": m.get("policy_name")}
                for m in policy_matches
            ],
        }

    return _fn


def get_ai_function_map(user_id: str | None = None):
    mapping = {
        "search_policy_embeddings": search_policy_embeddings,
    }
    if user_id is not None:
        mapping["search_my_organization_policies"] = _make_search_my_organization_policies(
            user_id
        )
        mapping["get_my_pending_leaves"] = _make_get_my_pending_leaves(user_id)
    return mapping

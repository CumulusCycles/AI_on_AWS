import json
import os
import uuid
from datetime import datetime, timedelta
from decimal import Decimal

import boto3
from boto3.dynamodb.conditions import Attr
from botocore.exceptions import ClientError

# ---------------------------------------------------------------------------
# DynamoDB config — table names from environment
# ---------------------------------------------------------------------------
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")
CLAIMS_TABLE = os.environ.get("CLAIMS_TABLE", "ai-agent-insure-claims")
POLICIES_TABLE = os.environ.get("POLICIES_TABLE", "ai-agent-insure-policies")

dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
claims_table = dynamodb.Table(CLAIMS_TABLE)
policies_table = dynamodb.Table(POLICIES_TABLE)


# ---------------------------------------------------------------------------
# DynamoDB helpers
# ---------------------------------------------------------------------------

def _to_dict(item: dict) -> dict:
    """Convert DynamoDB Decimal values to int/float for JSON serialisation."""
    result = {}
    for k, v in item.items():
        if isinstance(v, Decimal):
            result[k] = int(v) if v == v.to_integral_value() else float(v)
        else:
            result[k] = v
    return result


def _get_policy(policy_id: str) -> dict | None:
    resp = policies_table.get_item(Key={"policy_id": policy_id})
    item = resp.get("Item")
    return _to_dict(item) if item else None


def _get_claim(claim_id: str) -> dict | None:
    resp = claims_table.get_item(Key={"claim_id": claim_id})
    item = resp.get("Item")
    return _to_dict(item) if item else None


def _put_claim(claim: dict):
    # DynamoDB doesn't accept float — store estimated_loss as Decimal
    item = dict(claim)
    if "estimated_loss" in item:
        item["estimated_loss"] = Decimal(str(item["estimated_loss"]))
    claims_table.put_item(Item=item)


# ---------------------------------------------------------------------------
# Parameter extraction
# ---------------------------------------------------------------------------

def _parse_parameters(event: dict) -> dict:
    """
    Bedrock Agent action group events carry parameters in two possible shapes:
      - event['parameters']  — list of {name, type, value} dicts  (GET-style)
      - event['requestBody']['content']['application/json']['properties']  (POST-style)

    Returns a flat {name: value} dict.
    """
    params: dict = {}

    for p in event.get("parameters") or []:
        params[p["name"]] = p["value"]

    try:
        props = event["requestBody"]["content"]["application/json"]["properties"]
        for p in props:
            params[p["name"]] = p["value"]
    except (KeyError, TypeError):
        pass

    return params


# ---------------------------------------------------------------------------
# Action implementations
# ---------------------------------------------------------------------------

def submit_claim(params: dict) -> dict:
    policy_id = params.get("policy_id", "").upper()
    incident_type = params.get("incident_type", "")
    description = params.get("description", "")
    estimated_loss = params.get("estimated_loss", "0")

    policy = _get_policy(policy_id)
    if not policy:
        return {"error": f"Policy {policy_id} not found."}
    if policy.get("status") != "active":
        return {"error": f"Policy {policy_id} is not active (status: {policy.get('status')})."}

    claim_id = f"CLM-{uuid.uuid4().hex[:6].upper()}"
    claim = {
        "claim_id": claim_id,
        "policy_id": policy_id,
        "incident_type": incident_type,
        "description": description,
        "estimated_loss": float(estimated_loss),
        "status": "submitted",
        "submitted_at": datetime.utcnow().isoformat() + "Z",
        "adjuster": None,
    }
    _put_claim(claim)

    return {
        "claim_id": claim_id,
        "policy_id": policy_id,
        "status": "submitted",
        "message": f"Claim {claim_id} submitted successfully under policy {policy_id}.",
    }


def get_claim_status(params: dict) -> dict:
    claim_id = params.get("claim_id", "").upper()
    claim = _get_claim(claim_id)
    if not claim:
        return {"error": f"Claim {claim_id} not found."}
    return claim


def lookup_policy(params: dict) -> dict:
    policy_id = params.get("policy_id", "").upper()
    policy = _get_policy(policy_id)
    if not policy:
        return {"error": f"Policy {policy_id} not found."}
    return policy


def list_policies(params: dict) -> dict:
    holder_filter = params.get("holder", "").lower()

    if holder_filter:
        resp = policies_table.scan(
            FilterExpression=Attr("holder").contains(holder_filter)
        )
    else:
        resp = policies_table.scan()

    items = [_to_dict(item) for item in resp.get("Items", [])]
    return {"policies": items, "count": len(items)}


def get_coverage_summary(params: dict) -> dict:
    policy_id = params.get("policy_id", "").upper()
    policy = _get_policy(policy_id)
    if not policy:
        return {"error": f"Policy {policy_id} not found."}

    limit = policy.get("coverage_limit", 0)
    deductible = policy.get("deductible", 0)
    return {
        "policy_id": policy_id,
        "product": policy.get("product", ""),
        "coverage_limit": f"${limit:,}",
        "deductible": f"${deductible:,}",
        "status": policy.get("status", ""),
        "expiry": policy.get("expiry", ""),
        "summary": (
            f"Policy {policy_id} provides up to ${limit:,} in coverage "
            f"for {policy.get('product', '')} with a ${deductible:,} deductible. "
            f"Policy expires on {policy.get('expiry', 'N/A')}."
        ),
    }


# ---------------------------------------------------------------------------
# Action router
# ---------------------------------------------------------------------------

_ACTION_MAP = {
    "submitClaim": submit_claim,
    "getClaimStatus": get_claim_status,
    "lookupPolicy": lookup_policy,
    "listPolicies": list_policies,
    "getCoverageSummary": get_coverage_summary,
}


def lambda_handler(event, _context):
    """
    Bedrock Agent action group Lambda handler.

    Bedrock passes:
      event['actionGroup']  — name of the action group
      event['function']     — name of the function (may be empty)
      event['apiPath']      — e.g. /listPolicies (used when function is empty)
      event['parameters']   — list of {name, type, value} dicts
      event['requestBody']  — alternative parameter location (POST body)

    Returns the Bedrock-expected response envelope.
    """
    print(f"Event: {json.dumps(event)}")

    action_group = event.get("actionGroup", "")
    function_name = event.get("function", "").strip()
    if not function_name and event.get("apiPath"):
        # Bedrock may send apiPath (e.g. /listPolicies) instead of function
        function_name = event["apiPath"].strip("/")
    params = _parse_parameters(event)

    handler = _ACTION_MAP.get(function_name)
    if handler is None:
        result = {"error": f"Unknown function: {function_name}"}
    else:
        try:
            result = handler(params)
        except ClientError as e:
            result = {"error": f"DynamoDB error: {e.response['Error']['Message']}"}
        except Exception as exc:
            result = {"error": str(exc)}

    # Bedrock expects API-schema response format (we use OpenAPI for the action group)
    body_str = json.dumps(result)
    response = {
        "messageVersion": "1.0",
        "response": {
            "actionGroup": action_group,
            "apiPath": event.get("apiPath", f"/{function_name}"),
            "httpMethod": event.get("httpMethod", "GET"),
            "httpStatusCode": 200,
            "responseBody": {
                "application/json": {
                    "body": body_str
                }
            }
        },
        "sessionAttributes": event.get("sessionAttributes", {}),
        "promptSessionAttributes": event.get("promptSessionAttributes", {}),
    }

    print(f"Response: {json.dumps(response)}")
    return response

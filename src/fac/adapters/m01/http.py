"""Real M01 Guard adapter for FAC.

Production M01 uses OIDC. FAC therefore receives a service access token through
runtime secret injection. To authorize a target M13 Agent rather than the FAC
service principal itself, that token must carry M01's delegate scope
(m01:policy:delegate) in addition to the normal policy-read scope.
"""

from __future__ import annotations

import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from fac.adapters.m13.http import HttpM13RegistryAdapter
from fac.domain.m01_guard import (
    ACTION_RESOURCE_MAP,
    FinanceGuardAction,
    M01Approval,
    M01GuardResult,
)


class M01GuardError(RuntimeError):
    """M01 Guard or approval request failed."""


class M01GuardConfigurationError(M01GuardError):
    """M01 Guard is not configured."""


def _post_json(
    url: str,
    payload: dict,
    headers: dict[str, str],
    timeout: float,
) -> dict:
    body = json.dumps(payload, ensure_ascii=False).encode()
    request = Request(
        url,
        data=body,
        headers={"Content-Type": "application/json", **headers},
        method="POST",
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8", errors="replace")
            status = int(response.status)
    except HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        raise M01GuardError(f"M01 HTTP {exc.code}: {raw[:500]}") from exc
    except URLError as exc:
        raise M01GuardError(f"M01 connection failed: {exc}") from exc
    if not 200 <= status < 300:
        raise M01GuardError(f"M01 HTTP {status}: {raw[:500]}")
    try:
        result = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise M01GuardError("M01 returned invalid JSON") from exc
    if not isinstance(result, dict):
        raise M01GuardError("M01 response must be an object")
    return result


class HttpM01GuardAdapter:
    """Evaluate FAC actions through the real M01 authorization endpoint."""

    def __init__(
        self,
        *,
        base_url: str,
        access_token: str,
        m13_registry: HttpM13RegistryAdapter,
        timeout: float = 5.0,
    ):
        self.base_url = base_url.rstrip("/")
        self.access_token = access_token.strip()
        self.m13_registry = m13_registry
        self.timeout = timeout
        if not self.base_url or not self.access_token:
            raise M01GuardConfigurationError(
                "FAC_M01_KERNEL_URL and FAC_M01_ACCESS_TOKEN must be configured"
            )

    @property
    def headers(self) -> dict[str, str]:
        return {
            "Accept": "application/json",
            "Authorization": f"Bearer {self.access_token}",
        }

    def evaluate(
        self,
        *,
        tenant_id: str,
        agent_id: str,
        action_type: FinanceGuardAction,
        object_id: str,
        parameters: dict,
        auto_create_approval: bool = True,
    ) -> M01GuardResult:
        self.m13_registry.require_published(agent_id)
        runtime = self.m13_registry.get_runtime(agent_id)
        if runtime is None or not runtime.m01_agent_id:
            raise M01GuardError(
                f"{agent_id} has no M01 principal id in M13 registry"
            )

        resource, action = ACTION_RESOURCE_MAP[action_type]
        decision_payload = _post_json(
            f"{self.base_url}/kernel/v1/authorize",
            {
                "tenant_id": tenant_id,
                "principal_id": runtime.m01_agent_id,
                "resource": resource,
                "action": action,
            },
            self.headers,
            self.timeout,
        )
        decision = str(decision_payload.get("decision") or "")
        if decision not in {"ALLOW", "DENY", "REQUIRE_APPROVAL"}:
            raise M01GuardError(f"unexpected M01 decision: {decision!r}")

        approval = None
        if decision == "REQUIRE_APPROVAL" and auto_create_approval:
            approval_payload = _post_json(
                f"{self.base_url}/kernel/v1/approvals",
                {
                    "tenant_id": tenant_id,
                    "requester_id": runtime.m01_agent_id,
                    "resource": resource,
                    "action": action,
                    "object_id": object_id,
                    "parameters": parameters,
                },
                self.headers,
                self.timeout,
            )
            raw_approval = approval_payload.get("approval")
            if not isinstance(raw_approval, dict):
                raise M01GuardError("M01 approval response missing approval object")
            approval = M01Approval.model_validate(raw_approval)

        return M01GuardResult(
            agent_id=agent_id,
            m01_agent_id=runtime.m01_agent_id,
            tenant_id=tenant_id,
            action_type=action_type,
            resource=resource,
            action=action,
            object_id=object_id,
            decision=decision,
            reason=str(decision_payload.get("reason") or ""),
            trace_id=str(decision_payload.get("trace_id") or ""),
            approval=approval,
            execution_allowed=decision == "ALLOW",
            requires_human_approval=decision == "REQUIRE_APPROVAL",
        )

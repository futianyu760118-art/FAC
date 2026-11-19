"""HTTP adapter for the M13 Hub Agent Registry."""

from __future__ import annotations

import hashlib
import hmac
import json
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from pydantic import BaseModel, Field

from fac.domain.m13_agents import (
    FAC_AGENT_REGISTRY_V1,
    AgentStatus,
    FinanceAgentRegistration,
)


class M13RegistryError(RuntimeError):
    """M13 registry call failed."""


class M13RegistryConfigurationError(M13RegistryError):
    """M13 registry endpoint is not configured."""


class AgentNotRegistered(LookupError):
    """The requested finance agent is not registered in M13."""


class AgentNotPublished(PermissionError):
    """The FAC professional catalog does not publish this finance agent."""


class AgentNotDispatchable(PermissionError):
    """M13/M01 reports that this agent is not executable."""


class M13RuntimeAgent(BaseModel):
    agent_id: str
    harbor_agent_id: str
    name: str
    role: str
    skills: list[str] = Field(default_factory=list)
    autonomy_level: str
    status: str
    runtime_id: str | None = None
    runtime_status: str | None = None
    m01_state: str
    effective_scopes: list[str] = Field(default_factory=list)
    dispatchable: bool
    updated_at: str


class M13RuntimeSnapshot(BaseModel):
    registry_system: str
    revision: int
    generated_at: str
    items: list[M13RuntimeAgent]


def _fetch_json(url: str, headers: dict[str, str], timeout: float) -> dict:
    request = Request(url, headers=headers, method="GET")
    try:
        with urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8", errors="replace")
            status = int(response.status)
    except HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        raise M13RegistryError(f"M13 registry HTTP {exc.code}: {raw[:500]}") from exc
    except URLError as exc:
        raise M13RegistryError(f"M13 registry connection failed: {exc}") from exc
    if not 200 <= status < 300:
        raise M13RegistryError(f"M13 registry HTTP {status}: {raw[:500]}")
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise M13RegistryError("M13 registry returned invalid JSON") from exc
    if not isinstance(payload, dict):
        raise M13RegistryError("M13 registry response must be an object")
    return payload


def _signed_headers(key_id: str, secret: str, *, now_ms: int | None = None) -> dict[str, str]:
    timestamp = str(now_ms if now_ms is not None else int(time.time() * 1000))
    signature = hmac.new(
        secret.encode("utf-8"),
        f"{timestamp}.".encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return {
        "Accept": "application/json",
        "x-aeos-key-id": key_id,
        "x-aeos-timestamp": timestamp,
        "x-aeos-signature": f"sha256={signature}",
    }


class HttpM13RegistryAdapter:
    """Fail-closed adapter over the real M13 registry API."""

    def __init__(
        self,
        *,
        base_url: str,
        key_id: str,
        secret: str,
        timeout: float = 5.0,
        catalog: tuple[FinanceAgentRegistration, ...] = FAC_AGENT_REGISTRY_V1,
    ):
        self.base_url = base_url.rstrip("/")
        self.key_id = key_id
        self.secret = secret
        self.timeout = timeout
        self._catalog = {item.agent_id: item for item in catalog}
        if not self.base_url or not self.key_id or not self.secret:
            raise M13RegistryConfigurationError(
                "FAC_M13_REGISTRY_URL / KEY_ID / SECRET must all be configured"
            )

    def list_runtime(self, prefix: str = "AG-FAC-") -> M13RuntimeSnapshot:
        query = urlencode({"prefix": prefix})
        url = f"{self.base_url}/internal/aeos/agent-registry?{query}"
        payload = _fetch_json(
            url,
            _signed_headers(self.key_id, self.secret),
            self.timeout,
        )
        normalized = {
            "registry_system": payload.get("registrySystem"),
            "revision": payload.get("revision"),
            "generated_at": payload.get("generatedAt"),
            "items": [
                {
                    "agent_id": item.get("agentId"),
                    "harbor_agent_id": item.get("harborAgentId"),
                    "name": item.get("name"),
                    "role": item.get("role"),
                    "skills": item.get("skills") or [],
                    "autonomy_level": item.get("autonomyLevel"),
                    "status": item.get("status"),
                    "runtime_id": item.get("runtimeId"),
                    "runtime_status": item.get("runtimeStatus"),
                    "m01_state": item.get("m01State"),
                    "effective_scopes": item.get("effectiveScopes") or [],
                    "dispatchable": item.get("dispatchable"),
                    "updated_at": item.get("updatedAt"),
                }
                for item in (payload.get("items") or [])
                if isinstance(item, dict)
            ],
        }
        return M13RuntimeSnapshot.model_validate(normalized)

    def get_runtime(self, agent_id: str) -> M13RuntimeAgent | None:
        snapshot = self.list_runtime(prefix=agent_id)
        return next((item for item in snapshot.items if item.agent_id == agent_id), None)

    def get(self, agent_id: str) -> FinanceAgentRegistration | None:
        return self._catalog.get(agent_id)

    def require_published(self, agent_id: str) -> FinanceAgentRegistration:
        item = self.get(agent_id)
        if item is None:
            raise AgentNotRegistered(f"{agent_id} is not defined by M09")
        if item.status is not AgentStatus.PUBLISHED:
            raise AgentNotPublished(
                f"{agent_id} FAC catalog status is {item.status.value}, not PUBLISHED"
            )
        runtime = self.get_runtime(agent_id)
        if runtime is None:
            raise AgentNotRegistered(f"{agent_id} is not registered in M13")
        if not runtime.dispatchable:
            raise AgentNotDispatchable(
                f"{agent_id} M13/M01 not dispatchable: "
                f"status={runtime.status}, m01={runtime.m01_state}, "
                f"scopes={runtime.effective_scopes}"
            )
        return item

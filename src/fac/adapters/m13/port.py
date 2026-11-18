"""Port for validating FAC agents against the M13 registry."""

from __future__ import annotations

from typing import Protocol

from fac.domain.m13_agents import (
    FAC_AGENT_REGISTRY_V1,
    AgentStatus,
    FinanceAgentRegistration,
)


class AgentNotRegistered(LookupError):
    """The requested finance agent is not registered in M13."""


class AgentNotPublished(PermissionError):
    """The requested finance agent exists but is not published for use."""


class M13RegistryPort(Protocol):
    def get(self, agent_id: str) -> FinanceAgentRegistration | None: ...

    def require_published(self, agent_id: str) -> FinanceAgentRegistration: ...


class LocalM13RegistryAdapter:
    """Temporary adapter over the frozen registry until the real M13 API is connected."""

    def __init__(
        self,
        registry: tuple[FinanceAgentRegistration, ...] = FAC_AGENT_REGISTRY_V1,
    ):
        self._by_id = {item.agent_id: item for item in registry}

    def get(self, agent_id: str) -> FinanceAgentRegistration | None:
        return self._by_id.get(agent_id)

    def require_published(self, agent_id: str) -> FinanceAgentRegistration:
        item = self.get(agent_id)
        if item is None:
            raise AgentNotRegistered(agent_id)
        if item.status is not AgentStatus.PUBLISHED:
            raise AgentNotPublished(f"{agent_id} is {item.status.value}, not PUBLISHED")
        return item

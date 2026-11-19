"""Port for validating FAC agents against the M13 registry."""

from typing import Protocol

from fac.adapters.m13.http import AgentNotPublished, AgentNotRegistered
from fac.domain.m13_agents import (
    FAC_AGENT_REGISTRY_V1,
    AgentStatus,
    FinanceAgentRegistration,
)


class M13RegistryPort(Protocol):
    def get(self, agent_id: str) -> FinanceAgentRegistration | None: ...

    def require_published(self, agent_id: str) -> FinanceAgentRegistration: ...


class LocalM13RegistryAdapter:
    """Development-only adapter over the frozen FAC professional catalog."""

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

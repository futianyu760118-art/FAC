"""M01 Guard API for FAC professional actions."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from fac.adapters.m01.http import (
    HttpM01GuardAdapter,
    M01GuardConfigurationError,
    M01GuardError,
)
from fac.adapters.m13.http import (
    AgentNotDispatchable,
    AgentNotPublished,
    AgentNotRegistered,
    HttpM13RegistryAdapter,
    M13RegistryConfigurationError,
    M13RegistryError,
)
from fac.domain.m01_guard import FinanceGuardAction, M01GuardResult
from fac.settings import get_settings

router = APIRouter(prefix="/api/v1/fac/m01", tags=["FAC M01 Guard"])


class FinanceGuardRequest(BaseModel):
    tenant_id: str
    agent_id: str
    action_type: FinanceGuardAction = FinanceGuardAction.TASK_EXECUTE
    object_id: str = Field(min_length=1)
    parameters: dict = Field(default_factory=dict)
    auto_create_approval: bool = True


@router.post("/guard", response_model=M01GuardResult)
def evaluate_finance_guard(payload: FinanceGuardRequest) -> M01GuardResult:
    settings = get_settings()
    try:
        m13 = HttpM13RegistryAdapter(
            base_url=settings.m13_registry_url,
            key_id=settings.m13_registry_key_id,
            secret=settings.m13_registry_secret,
            timeout=settings.m13_registry_timeout_seconds,
        )
        guard = HttpM01GuardAdapter(
            base_url=settings.m01_kernel_url,
            access_token=settings.m01_access_token,
            m13_registry=m13,
            timeout=settings.m01_timeout_seconds,
        )
        return guard.evaluate(
            tenant_id=payload.tenant_id,
            agent_id=payload.agent_id,
            action_type=payload.action_type,
            object_id=payload.object_id,
            parameters=payload.parameters,
            auto_create_approval=payload.auto_create_approval,
        )
    except (M13RegistryConfigurationError, M01GuardConfigurationError) as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except (AgentNotRegistered, AgentNotPublished, AgentNotDispatchable) as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except (M13RegistryError, M01GuardError) as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

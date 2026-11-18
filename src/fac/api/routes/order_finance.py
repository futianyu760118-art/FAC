"""Order finance API endpoints."""

from fastapi import APIRouter

from fac.domain.order_finance import (
    OrderFinanceCompareInput,
    OrderFinanceCompareResult,
    OrderFinanceSnapshotInput,
    OrderFinanceSnapshotResult,
    calculate_snapshot,
    compare_order_finance,
)

router = APIRouter(prefix="/api/v1/fac/order-finance", tags=["FAC Order Finance"])


@router.post("/snapshot", response_model=OrderFinanceSnapshotResult)
def snapshot(payload: OrderFinanceSnapshotInput) -> OrderFinanceSnapshotResult:
    return calculate_snapshot(payload)


@router.post("/compare", response_model=OrderFinanceCompareResult)
def compare(payload: OrderFinanceCompareInput) -> OrderFinanceCompareResult:
    return compare_order_finance(payload)

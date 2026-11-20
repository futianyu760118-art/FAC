"""Source priority orchestration for governed FAC imports."""

from __future__ import annotations

from dataclasses import dataclass

from fac.adapters.ebms.adapter import EbmsApiError
from fac.adapters.edp.adapter import EdpApiError, EdpImportReport, EdpImportRequest


class SourceImportError(RuntimeError):
    """Both configured source systems failed to provide the requested data."""

    def __init__(self, edp_error: Exception, ebms_error: Exception):
        self.edp_error = edp_error
        self.ebms_error = ebms_error
        super().__init__(f"EDP 导入失败：{edp_error}；EBMS 兜底也失败：{ebms_error}")


@dataclass(slots=True)
class PriorityImportAdapter:
    """Try EDP first and use EBMS only when EDP cannot serve the request."""

    edp: object
    ebms: object

    def import_orders(
        self, request: EdpImportRequest, *, import_id: str | None = None
    ) -> EdpImportReport:
        try:
            report = self.edp.import_orders(request, import_id=import_id)
            report.source_chain = ["edp"]
            return report
        except EdpApiError as edp_error:
            try:
                report = self.ebms.import_orders(request, import_id=import_id)
            except EbmsApiError as ebms_error:
                raise SourceImportError(edp_error, ebms_error) from ebms_error
            report.source_chain = ["edp", "ebms"]
            report.fallback_reason = str(edp_error)
            return report

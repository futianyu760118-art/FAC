"""Stable, transport-independent domain errors."""


class DomainError(Exception):
    code = "DOMAIN_ERROR"

    def __init__(self, message: str) -> None:
        super().__init__(message)


class FXRateMissing(DomainError):
    code = "FX_RATE_MISSING"


class InvalidMoney(DomainError):
    code = "INVALID_MONEY"


class EvidenceRequired(DomainError):
    code = "EVIDENCE_REQUIRED"

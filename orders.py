"""Совместимый импорт функций заявок из объектной модели ПР3."""

from models.requests import (
    FINAL_STATUSES,
    VALID_STATUSES,
    SupplyRequest,
    cancel_request,
    change_status,
    create_request,
    filter_requests,
    get_request,
    show_history,
    show_requests,
    sort_requests,
)

__all__ = [
    "FINAL_STATUSES",
    "VALID_STATUSES",
    "SupplyRequest",
    "cancel_request",
    "change_status",
    "create_request",
    "filter_requests",
    "get_request",
    "show_history",
    "show_requests",
    "sort_requests",
]

from typing import Generic, List, Optional, Sequence, Tuple, TypeVar

from fastapi import Request
from pydantic import BaseModel
from pydantic.generics import GenericModel

T = TypeVar("T")

DEFAULT_LIMIT = 20
MAX_LIMIT = 100


class PaginationMeta(BaseModel):
    """
    Metadata for paginated responses.
    Provides details for frontend navigation and pagination state.
    """
    total_count: int
    page: int
    limit: int
    has_next: bool
    has_previous: bool
    next_page: Optional[str] = None
    previous_page: Optional[str] = None


class PaginatedResponse(GenericModel, Generic[T]):
    """
    Standardized pagination wrapper for all list endpoints.

    Example structure:
    {
        "meta": { ...pagination info... },
        "results": [ ...items... ]
    }
    """
    meta: PaginationMeta
    results: List[T]


def normalize_page_limit(
    page: Optional[int],
    limit: Optional[int],
    *,
    default_limit: int = DEFAULT_LIMIT,
    max_limit: int = MAX_LIMIT,
) -> Tuple[int, int]:
    """
    Ensures valid and safe page/limit values.

    Rules:
    - page must be >= 1 (defaults to 1)
    - limit defaults to `default_limit` if missing or invalid
    - limit cannot exceed `max_limit`
    """
    if page is None or page < 1:
        page = 1

    if limit is None or limit < 1:
        limit = default_limit

    if limit > max_limit:
        limit = max_limit

    return page, limit


def page_to_range(page: int, limit: int) -> Tuple[int, int]:
    """
    Converts page/limit into Supabase `.range(start, end)` format.

    Supabase uses 0-based *inclusive* indexing:
        page = 1, limit = 20  →  (0, 19)
        page = 2, limit = 20  →  (20, 39)
    """
    start = (page - 1) * limit
    end = start + limit - 1
    return start, end


def build_page_url(request: Request, page: int, limit: int) -> str:
    """
    Generates pagination URLs by updating page/limit values
    while preserving all other existing query parameters.
    """
    return str(request.url.include_query_params(page=page, limit=limit))


def build_paginated_response(
    *,
    items: Sequence[T],
    total_count: int,
    page: int,
    limit: int,
    request: Request,
) -> PaginatedResponse[T]:
    """
    Constructs a unified paginated response object.

    Parameters:
        items       - list of items for the current page
        total_count - total number of items matching the query
        page        - current page number
        limit       - maximum number of items per page
        request     - used for generating next/previous page URLs

    Returns:
        PaginatedResponse[T] with metadata + results
    """
    page, limit = normalize_page_limit(page, limit)
    offset = (page - 1) * limit

    has_previous = page > 1
    has_next = (offset + len(items)) < total_count

    next_page_url: Optional[str] = None
    prev_page_url: Optional[str] = None

    if has_next:
        next_page_url = build_page_url(request, page=page + 1, limit=limit)

    if has_previous:
        prev_page_url = build_page_url(request, page=page - 1, limit=limit)

    meta = PaginationMeta(
        total_count=total_count,
        page=page,
        limit=limit,
        has_next=has_next,
        has_previous=has_previous,
        next_page=next_page_url,
        previous_page=prev_page_url,
    )

    return PaginatedResponse[T](meta=meta, results=list(items))

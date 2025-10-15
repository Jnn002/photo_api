"""
Core schemas for common response patterns.

This module provides reusable Pydantic schemas used across the API
for standardized response structures like pagination.
"""

from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

# Type variable for generic schemas
T = TypeVar('T')


class PaginatedResponse(BaseModel, Generic[T]):
    """
    Generic paginated response wrapper.

    Provides consistent pagination metadata across all list endpoints,
    essential for Angular Material tables and pagination components.

    **Type Parameters:**
        T: Type of items in the response (e.g., ClientPublic, SessionPublic)

    **Example usage in router:**
    ```python
    @router.get('', response_model=PaginatedResponse[ClientPublic])
    async def list_clients(...) -> PaginatedResponse[ClientPublic]:
        items = await service.list_clients(limit=limit, offset=offset)
        total = await service.count_clients()
        return PaginatedResponse(
            items=items,
            total=total,
            limit=limit,
            offset=offset,
            has_more=(offset + len(items)) < total
        )
    ```

    **Frontend usage (Angular):**
    ```typescript
    interface PaginatedResponse<T> {
      items: T[];
      total: number;
      limit: number;
      offset: number;
      has_more: boolean;
    }

    async loadPage(page: number) {
      const response = await this.api.get<PaginatedResponse<Client>>(
        `/clients?limit=20&offset=${page * 20}`
      );
      this.clients = response.items;
      this.totalPages = Math.ceil(response.total / response.limit);
    }
    ```
    """

    model_config = ConfigDict(from_attributes=True)

    items: list[T] = Field(..., description='List of items for the current page')
    total: int = Field(..., ge=0, description='Total number of items across all pages')
    limit: int = Field(..., ge=1, description='Maximum number of items per page')
    offset: int = Field(..., ge=0, description='Number of items skipped (page offset)')
    has_more: bool = Field(
        ..., description='Whether there are more items beyond the current page'
    )

    @property
    def current_page(self) -> int:
        """Calculate current page number (0-indexed)."""
        return self.offset // self.limit if self.limit > 0 else 0

    @property
    def total_pages(self) -> int:
        """Calculate total number of pages."""
        return (self.total + self.limit - 1) // self.limit if self.limit > 0 else 0

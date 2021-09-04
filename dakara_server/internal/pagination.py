from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class PageNumberPaginationCustom(PageNumberPagination):
    """Pagination.

    Gives current page number and last page number.
    """

    def get_paginated_response(self, data):
        return Response(
            {
                "pagination": {
                    "current": self.page.number,
                    "last": self.page.paginator.num_pages,
                },
                "count": self.page.paginator.count,
                "results": data,
            }
        )

from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


# class CustomPagination(PageNumberPagination):
#     page_size = 20
#     page_size_query_param = 'page_size'
#     max_page_size = 100

#     def get_paginated_response(self, data):
#         return Response({
#             'links': {
#                 'next': self.get_next_link(),
#                 'previous': self.get_previous_link()
#             },
#             'count': self.page.paginator.count,
#             'total_pages': self.page.paginator.num_pages,
#             'results': data
#         })
# /api/your-endpoint/?no_pagination=true

class CustomPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

    def paginate_queryset(self, queryset, request, view=None):
        """
        Overrides the default pagination behavior to allow for fetching all
        results if a 'no_pagination' query parameter is present.
        """
        if 'no_pagination' in request.query_params:
            return None
        return super().paginate_queryset(queryset, request, view)

    def get_paginated_response(self, data):
        """
        This method is only called when pagination is active. It formats
        the paginated response.
        """
        return Response({
            'links': {
                'next': self.get_next_link(),
                'previous': self.get_previous_link()
            },
            'count': self.page.paginator.count,
            'total_pages': self.page.paginator.num_pages,
            'results': data
        })


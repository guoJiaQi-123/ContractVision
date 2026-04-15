from collections import OrderedDict

from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class StandardPagination(PageNumberPagination):
    page_size = 10
    page_query_param = 'page'
    page_size_query_param = 'size'
    max_page_size = 100

    def get_page_size(self, request):
        page_size = request.query_params.get(self.page_size_query_param) or request.query_params.get('page_size')
        if page_size:
            try:
                page_size = int(page_size)
            except (TypeError, ValueError):
                page_size = self.page_size
            return min(page_size, self.max_page_size)
        return self.page_size

    def get_paginated_response(self, data):
        return Response(OrderedDict({
            'code': 200,
            'message': 'success',
            'data': {
                'total': self.page.paginator.count,
                'page': self.page.number,
                'size': self.get_page_size(self.request),
                'results': data,
            },
        }))

    def get_paginated_response_schema(self, schema):
        return {
            'type': 'object',
            'properties': {
                'code': {'type': 'integer', 'example': 200},
                'message': {'type': 'string', 'example': 'success'},
                'data': {
                    'type': 'object',
                    'properties': {
                        'total': {'type': 'integer'},
                        'page': {'type': 'integer'},
                        'size': {'type': 'integer'},
                        'results': schema,
                    },
                },
            },
        }

from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

class NotificacionesPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'

    def get_paginated_response(self, data):
        return Response({
            'pagina_actual': self.page.number,
            'total_paginas': self.page.paginator.num_pages,
            'total_resultados': self.page.paginator.count,
            'resultados': data,
        })

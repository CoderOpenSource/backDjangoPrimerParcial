# ventas/pagination.py
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

class CustomPagination(PageNumberPagination):
    page_size = 10  # Tamaño por defecto
    page_size_query_param = 'page_size'  # Permitir ?page_size=20
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response({
            'total_paginas': self.page.paginator.num_pages,
            'pagina_actual': self.page.number,
            'total_registros': self.page.paginator.count,
            'resultados': data,
        })

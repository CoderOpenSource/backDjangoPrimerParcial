from rest_framework.pagination import PageNumberPagination

class ProductoPagination(PageNumberPagination):
    page_size = 9  # número por página por defecto
    page_size_query_param = 'limit'  # permite cambiar el tamaño desde el frontend
    max_page_size = 100  # límite máximo para evitar sobrecarga

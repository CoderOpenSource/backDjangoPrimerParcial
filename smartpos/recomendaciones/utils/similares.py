from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import NearestNeighbors
import pandas as pd
from productos.models import Producto  # 👈 esto es correcto dentro del módulo productos
from django.db.models import F
def obtener_productos_similares(producto_objetivo, top_n=5):
    productos_queryset = Producto.objects.select_related(
        'subcategoria__categoria', 'marca', 'stock'
    ).filter(estado=True, stock__cantidad_actual__gt=0)
    productos = pd.DataFrame([
        {
            "id": p.id,
            "texto": f"{p.nombre} {p.descripcion or ''} {p.subcategoria.nombre} {p.subcategoria.categoria.nombre} {p.marca.nombre if p.marca else ''}"
        }
        for p in productos_queryset
    ])

    if producto_objetivo.id not in productos["id"].values:
        raise ValueError("El producto objetivo no está en la lista de productos activos con stock")


    vectorizer = TfidfVectorizer()
    X = vectorizer.fit_transform(productos["texto"])

    modelo = NearestNeighbors(n_neighbors=min(top_n + 1, len(productos)), metric="cosine")
    modelo.fit(X)

    idx_objetivo = productos[productos["id"] == producto_objetivo.id].index[0]
    distancias, indices = modelo.kneighbors(X[idx_objetivo])
    ids_similares = productos.iloc[indices[0]]["id"].tolist()
    ids_similares = [pid for pid in ids_similares if pid != producto_objetivo.id]

    productos_similares = list(productos_queryset.filter(id__in=ids_similares))
    productos_similares.sort(key=lambda x: ids_similares.index(x.id))

    return productos_similares

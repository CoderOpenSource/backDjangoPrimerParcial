from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
from ventas.models import Venta
from productos.models import Producto
import numpy as np  # ✅ necesario para evitar error con np.matrix

def obtener_recomendaciones_por_historial(usuario):
    """
    Recomienda productos similares a los que el usuario ha comprado,
    usando similitud del coseno sobre texto enriquecido (nombre + marca + categoría).
    """
    ventas_usuario = Venta.objects.filter(
        usuario=usuario,
        estado='pagado'
    ).prefetch_related('detalles__producto')

    # Extraer productos comprados por el usuario
    productos_comprados = [
        detalle.producto
        for venta in ventas_usuario
        for detalle in venta.detalles.all()
    ]

    if not productos_comprados:
        return []  # No hay historial, no se recomienda nada

    productos_comprados_ids = [p.id for p in productos_comprados]

    # Cargar todos los productos junto con marca y categoría (desde subcategoría)
    productos_corpus = Producto.objects.select_related(
        'marca', 'subcategoria__categoria'
    ).all()

    # Crear corpus textual enriquecido
    corpus = [
        f"{p.nombre} {p.marca.nombre if p.marca else ''} {p.subcategoria.categoria.nombre if p.subcategoria and p.subcategoria.categoria else ''}"
        for p in productos_corpus
    ]

    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(corpus)

    # Crear vector promedio del historial del usuario
    historial_textos = [
        f"{p.nombre} {p.marca.nombre if p.marca else ''} {p.subcategoria.categoria.nombre if p.subcategoria and p.subcategoria.categoria else ''}"
        for p in productos_comprados
    ]

    historial_vector = np.asarray(vectorizer.transform(historial_textos).mean(axis=0))  # ✅ evitar np.matrix

    # Calcular similitud entre historial y todos los productos
    sim_scores = cosine_similarity(historial_vector, tfidf_matrix).flatten()

    # Ordenar por similitud (descendente) y filtrar productos ya comprados
    indices_ordenados = sim_scores.argsort()[::-1]

    recomendaciones = []
    for idx in indices_ordenados:
        producto = productos_corpus[int(idx)]  # ✅ conversión importante
        if producto.id not in productos_comprados_ids and sim_scores[idx] > 0.2:
            recomendaciones.append(producto)
        if len(recomendaciones) >= 6:
            break

    return recomendaciones  # Lista de objetos Producto recomendados

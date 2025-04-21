# 📁 recomendaciones/utils.py
from mlxtend.preprocessing import TransactionEncoder
from mlxtend.frequent_patterns import apriori, association_rules
from ventas.models import Venta
import pandas as pd

def generar_reglas_apriori(min_support=0.1, min_confidence=0.4):
    """
    Genera reglas de asociación usando ventas reales.
    Cada transacción es una lista de productos vendidos juntos.
    """
    ventas = Venta.objects.filter(estado='pagado').prefetch_related('detalles__producto')

    transacciones = [
        [detalle.producto.nombre for detalle in venta.detalles.all()]
        for venta in ventas if venta.detalles.exists()
    ]

    if not transacciones:
        return pd.DataFrame()

    te = TransactionEncoder()
    te_array = te.fit_transform(transacciones)
    df = pd.DataFrame(te_array, columns=te.columns_)

    itemsets = apriori(df, min_support=min_support, use_colnames=True)
    reglas = association_rules(itemsets, metric="confidence", min_threshold=min_confidence)
    return reglas


def obtener_sugerencias_desde_apriori(productos_en_carrito):
    """
    Dado un conjunto de productos (por nombre), devuelve sugerencias
    que se asocian con esos productos según Apriori.
    """
    reglas = generar_reglas_apriori()
    if reglas.empty:
        return []

    productos_en_carrito = set(productos_en_carrito)
    sugerencias = reglas[reglas['antecedents'].apply(lambda x: x.issubset(productos_en_carrito))]

    recomendados = set()
    for fila in sugerencias.itertuples():
        recomendados.update(fila.consequents)

    return list(recomendados - productos_en_carrito)
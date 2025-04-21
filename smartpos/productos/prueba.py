from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import NearestNeighbors
import pandas as pd

# Simulemos tus productos
productos = pd.DataFrame([
    {"id": 1, "nombre": "Zapatillas Nike Air Max", "categoria": "Zapatillas"},
    {"id": 2, "nombre": "Zapatillas Adidas Ultraboost", "categoria": "Zapatillas"},
    {"id": 3, "nombre": "Botines Puma King", "categoria": "Botines"},
    {"id": 4, "nombre": "Sandalias Crocs Verano", "categoria": "Sandalias"},
])

# Paso 1: Combina los textos
productos["texto"] = productos["nombre"] + " " + productos["categoria"]

# Paso 2: Vectoriza
vectorizer = TfidfVectorizer()
X = vectorizer.fit_transform(productos["texto"])

# Paso 3: Encuentra similares
modelo = NearestNeighbors(n_neighbors=3, metric="cosine")
modelo.fit(X)

# Paso 4: Buscar similares al producto con índice 0
distancias, indices = modelo.kneighbors(X[0])

# Mostrar resultados
print("Producto base:", productos.iloc[0]["nombre"])
for idx in indices[0][1:]:
    print("Similar:", productos.iloc[idx]["nombre"])

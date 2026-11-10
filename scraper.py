import requests
from bs4 import BeautifulSoup
import json
import pandas as pd
import time
import os

print("Iniciando web scraping multipágina en Agaval...")

paginas_a_descargar = 5
todos_los_productos = []

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

for pagina in range(1, paginas_a_descargar + 1):
    url_dinamica = f"https://www.agaval.com/tecnologia/celulares?page={pagina}"
    print(f"Procesando página {pagina} de {paginas_a_descargar}...")

    try:
        response = requests.get(url_dinamica, headers=headers, timeout=10)

        if response.status_code != 200:
            print(f"  └─ Página {pagina} omitida. Código de estado: {response.status_code}")
            continue

        soup = BeautifulSoup(response.content, "html.parser")
        scripts_json_ld = soup.find_all('script', type='application/ld+json')
        conteo_pagina = 0

        for script in scripts_json_ld:
            try:
                if script.string:
                    datos = json.loads(script.string)

                    if datos.get('@type') == 'ItemList' and 'itemListElement' in datos:
                        for item_wrapper in datos['itemListElement']:
                            producto = item_wrapper.get('item', {})
                            if producto:
                                nombre = producto.get('name', 'No disponible')
                                sku = producto.get('sku', producto.get('id', 'No disponible'))

                                marca_obj = producto.get('brand', {})
                                marca = marca_obj.get('name', 'Agaval') if isinstance(marca_obj, dict) else str(marca_obj)

                                ofertas = producto.get('offers', {})
                                precio = 'No disponible'
                                if isinstance(ofertas, dict):
                                    precio_num = ofertas.get('highPrice') or ofertas.get('lowPrice') or ofertas.get('price')
                                    if precio_num:
                                        precio = f"${float(precio_num):,.2f}"

                                todos_los_productos.append({
                                    "Referencia": sku,
                                    "Nombre/Marca": f"[{marca}] {nombre}",
                                    "Valores": precio,
                                    "Características": f"Tecnología, Agaval (Pág {pagina})"
                                })
                                conteo_pagina += 1
            except Exception:
                continue

        print(f" Se encontraron {conteo_pagina} productos en esta página.")
        time.sleep(1.5)

    except Exception as e:
        print(f"Error procesando la página {pagina}: {str(e)}")

# Consolidación final de todas las páginas
df_paginado = pd.DataFrame(todos_los_productos)

if not df_paginado.empty:
    df_paginado = df_paginado.drop_duplicates(subset=['Nombre/Marca'])
    print(f"\nExtracción finalizada. Total de productos extraídos de las 5 páginas: {len(df_paginado)}")
    
    # Crear directorio output si no existe para que GitHub Actions lo guarde bien
    os.makedirs('output', exist_ok=True)
    nombre_archivo = "output/productos_agaval_celulares_5_paginas.csv"
    
    df_paginado.to_csv(nombre_archivo, index=False, encoding='utf-8-sig', sep=';')
    print(f"Archivo guardado correctamente en '{nombre_archivo}'")
else:
    print("\nNo se pudieron recolectar productos en las páginas consultadas.")
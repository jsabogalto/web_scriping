import cloudscraper
from bs4 import BeautifulSoup
import re
import pandas as pd
from datetime import datetime
import os
import time


class BOD_D:
    def __init__(self):
        pass

    def solicitud(self, url):
        """
        Crea una solicitud y retorna un BeautifulSoup object.
        """
        scraper = cloudscraper.create_scraper()
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, como Gecko) Chrome/87.0.4280.88 Safari/537.36'
        }
        retries = 2
        delay = 1

        for attempt in range(retries):
            try:
                solicitud = scraper.get(url, headers=headers, timeout=5)
                if solicitud.status_code == 200:
                    return BeautifulSoup(solicitud.content, 'html.parser')
                else:
                    print(f"Error: Status code {solicitud.status_code} de {url}")
            except Exception as e:
                print(f"Error: {e}, intento {attempt + 1} of {retries}")
                time.sleep(delay)  # Espera entre reintentos

        print(f"error al cargar la url {retries} intentos.")
        return None
            
    def urls_paginas(self):
        url_base = 'https://www.promocionalesnw.com/?post_type=product&paged='
        try:
            if self.solicitud(url_base) is None:
                print('Error en solicitud de urls_paginas')
            page_number = self.solicitud(url_base).find_all(class_='page-numbers')
            page_values = [int(page.get_text()) for page in page_number if page.get_text().isdigit()]
            num_paginas = max(page_values, default=0)
            "retorna urls_de_categorias de la pagina"
            return [f"{url_base}{i}" for i in range(1, num_paginas + 1)]
            
        except Exception as e:
            print(f"Error: {e}")
            
    def urls_productos(self):
        try:
            urls = set(
                enlace.get('href')
                for url in self.urls_paginas()
                for enlace in self.solicitud(url).find_all('a', class_='woocommerce-LoopProduct-link woocommerce-loop-product__link')
                if (href := enlace.get('href'))
            )
            print('URLs obtenidas con éxito')
            self.lista_urls = list(urls)
            return self.lista_urls
        except Exception as e:
            print(f"Error: {e}")

    def encontrar_etiquetas_a(self, url):
        """
        Encuentra todas las etiquetas <a> dentro de un figure con la clase específica "woocommerce-product-gallery__wrapper".
        """
        try:
            figure = self.solicitud(url).find('figure', class_="woocommerce-product-gallery__wrapper")
            if not figure:
                print(f"Figure no encontrado clase: 'woocommerce-product-gallery__wrapper' en {url}")
                return []
            return [a['href'] for a in figure.find_all('a', href=True)]
        except Exception as e:
            print(f"Error al procesar la URL {url}: {e}")
            return []
    
    def extraer_imagenes(self):
        """
        Busca imágenes dentro de un figure con clase "woocommerce-product-gallery__wrapper" y une los enlaces con '|'.
        """
        extensiones_validas = ('.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg')
        imagenes = []
        try:
            for url in (self.lista_urls):
                enlaces = self.encontrar_etiquetas_a(url)
                enlaces_imagenes = [link for link in enlaces if link.lower().endswith(extensiones_validas)]
                # Une las URLs de las imágenes con '|'
                if enlaces_imagenes:
                    imagenes.append('|'.join(enlaces_imagenes))
                else:
                    imagenes.append(f"No se encontraron imágenes en el div especificado de {url}")
            print('Imágenes obtenidas con éxito')
        except Exception as e:
            print(f"Error al extraer imágenes: {e}")
        self.imagenes = imagenes
        return self.imagenes

    def limpiar_categorias(self, categorias):
        categorias_limpias = []
        for sublista in categorias:
            if isinstance(sublista, str):
                sublista = [sublista]
            if len(sublista) > 1:
                sublista[-1] = '' + sublista[-1]
            categorias_limpias.append(','.join(sublista))
        return categorias_limpias
        
    def categorias(self):
        """
        extrae categoria de cada producto
        """
        categorias_sin_limpiar = []
        try:
            for url in self.lista_urls:
                span = self.solicitud(url).find('span', class_='posted_in')
                if span:
                    categorias_a = [a.get_text(strip=True) for a in span.find_all('a', rel='tag')]
                    if categorias_a:
                        categorias_sin_limpiar.append(categorias_a)
                    else:
                        categorias_sin_limpiar.append('sin categoria')
                else:
                    categorias_sin_limpiar.append('sin categoria')
        except Exception as e:
            print(f"Error al procesar la URL {url}: {e}")
            categorias_sin_limpiar.append('sin categoria')
        print('categorias obtenidas con exito')
        self.categorias_productos = self.limpiar_categorias(categorias_sin_limpiar)
        return self.categorias_productos

    def limpiar_texto(self, texto):
        """
        Limpia el texto eliminando ciertas palabras y caracteres, y ajustando el formato.
        """
        texto_limpio = re.sub(r'Referencia:', '', texto)
        texto_limpio = re.sub(r'APLICA DESCUENTO.*', '', texto_limpio)
        texto_limpio = re.sub(r'NO LO DEJES PASAR!*', '', texto_limpio)
        texto_limpio = re.sub(r'NUEVO!!*', '', texto_limpio)
        texto_limpio = re.sub(r'([A-Z])\1', r'\1 \1', texto_limpio)
        texto_limpio = re.sub(r'([a-z])([A-Z])', r'\1 \2', texto_limpio)
        texto_limpio = texto_limpio.strip()
        texto_limpio = re.sub(r'\s+', ' ', texto_limpio)
        texto_limpio = texto_limpio.replace('\xa0', ' ')
        return texto_limpio
        
    def nombres_productos(self):
        nombres = []
        try:
            for url in self.lista_urls:
                if nombre_producto := self.solicitud(url).find('h1', class_='product_title entry-title'):
                    nombre_producto = nombre_producto.get_text(strip=True)
                    nombre_limpio = re.sub('\n', '', nombre_producto)
                    nombres.append(nombre_limpio)
                else:
                    nombres.append('Nombre no encontrado')
        except Exception as e:
            print(f"Error {e}")
        
        print('nombres obtenidos con exito')
        self.nombres = nombres
        return self.nombres
    def descuento_distribuidor(self):
        """
        busca aplicativos de descuento distribuidor
        """
        aplica_descuento = []
        try:
            for url in self.lista_urls:
                descripcion_div = self.solicitud(url).find('div', class_='woocommerce-product-details__short-description')
                if descripcion_div:
                    parrafos = descripcion_div.find_all(['p', 'strong'])
                    texto_completo = ' '.join(p.get_text(strip=True) for p in parrafos)
                    if re.search(r'\bNO APLICA DESCUENTO DISTRIBUIDOR\b', texto_completo) or re.search(r'\bNO APLICA DESCUENTO DE DISTRIBUIDOR\b', texto_completo):
                        aplica_descuento.append('NO')
                    elif re.search(r'\bAPLICA DESCUENTO DISTRIBUIDOR\b', texto_completo) or re.search(r'\bAPLICA DESCUENTO DE DISTRIBUIDOR\b', texto_completo):
                        aplica_descuento.append('SI')
                    else:
                        aplica_descuento.append('NO')
                else:
                    aplica_descuento.append('NO')

        except Exception as e:
            print(f'Error: {e}')
        self.aplica_descuento = aplica_descuento
        return self.aplica_descuento
        
    def precios_productos(self):
        precios = []
        try:
            for url in self.lista_urls:
                if precio_producto := self.solicitud(url).find(class_='woocommerce-Price-amount amount'):
                    precio_texto = precio_producto.get_text(strip=True)
                    precio_numeros = re.sub(r'[^0-9.]', '', precio_texto)
                    precios.append(precio_numeros)
                else:
                    precios.append('-')
        except Exception as e:
            print(f"Error: {e}")
        print('precios_obtenidos con exito')
        self.precios = precios
        return self.precios

    def extraer_div(self, div):
        "eliminar etiquetas span"
        for unwanted_tag in div.find_all('span', {'class': 'editable'}):
            unwanted_tag.decompose()
        
        "eliminar etiquetas strong"
        for strong_tag in div.find_all('strong'):
            strong_tag.decompose()
        
        return div.get_text(strip=True) if div else ""

    def descripcion_p(self):
        descripcion = []
        try:
            for url in self.lista_urls:
                div = self.solicitud(url).find('div', class_='woocommerce-product-details__short-description')
                if div:
                    texto_crudo = self.extraer_div(div)
                    texto_limpio = self.limpiar_texto(texto_crudo)
                    descripcion.append(texto_limpio)
        except Exception as e:
            print(f'Error procesado {url}: {e}')  # Registrar el error
        print('detalles obtenidos con exito')
        self.descripcion = descripcion
        return self.descripcion
    
    def buscar_sku(self):
        sku = []
        try:
            for url in self.lista_urls:
                sku_span = self.solicitud(url).find('span', class_='sku')
                if sku_span:
                    sku.append(sku_span.get_text(strip=True))
                else:
                    sku.append(url)  
        except Exception as e:
            print(f'Error: {e}')
            
        print('sku obtenidos con exito')
        self.sku = list(sku)
        return self.sku

    def extraer_filas(self, urls, nombres, precios, aplica_descuento, sku, categorias, detalles, imagenes):
        filas_tabla = []
        try:
            for idx, url in enumerate(urls):
            # Datos del producto
                nombre = nombres[idx]
                precio = precios[idx]
                descuento = aplica_descuento[idx]
                sku_producto = sku[idx]
                categoria = categorias[idx]
                detalle = detalles[idx]
                imagen = imagenes[idx]
                tabla = self.solicitud(url).find('table')
                if tabla:
                    for tr in tabla.find_all('tr')[1:]:  # Excluir encabezados
                        celdas = tr.find_all('td')
                        fila_tabla = [celda.get_text(strip=True) for celda in celdas]
                        filas_tabla.append([url, nombre, descuento, precio, sku_producto, categoria, detalle, imagen] + fila_tabla)
                else:
                    continue
        except Exception as e:
            print(f"Error: {e}")
        print('Filas obtenidas con exito')
        self.filas_tabla = filas_tabla
        return self.filas_tabla
    
    def cabecera_csv(self):
        archivo = 'cabecera.csv'
        if os.path.exists(archivo):
            print(''f'El archivo {archivo} ya existe.')
        else:
            def crear_filas():
                filas = []
                try:
                    for idx, url in enumerate(self.lista_urls):
                        # Datos del producto
                        producto = self.nombres[idx]
                        aplica_descuento = self.aplica_descuento[idx]
                        sku_producto = self.sku[idx]
                        etiquetas = self.categorias_productos[idx]
                        descripcion = self.descripcion[idx]
                        imagen = self.imagenes[idx]
                        url_proveedor = self.lista_urls[idx]
                        filas.append([
                            sku_producto, producto, descripcion, etiquetas, imagen, url_proveedor, aplica_descuento
                        ])
                except Exception as e:
                    print(f"Error: {e}")
                return filas
            
            filas = crear_filas()
            columnas_cabecera = [
                'sku_proveedor', 'producto', 'descripcion', 
                'etiquetas', 'imagenes', 'url_proveedor', 'aplica_descuento_monto'
            ]
            df_cabecera = pd.DataFrame(filas, columns=columnas_cabecera)
            created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            df_cabecera['created_at'] = created_at
            woo_estado = 'PENDIENTE'
            df_cabecera['woo_estado'] = woo_estado
            bodega = 'BOD_D'
            df_cabecera['bodega'] = bodega
            
            
            print('Cabecera creada con éxito.')
            df_cabecera.to_csv('cabecera.csv', index=False, encoding='utf-8-sig')

    
    def historico_csv(self):
        """usamos el modulo extraer filas para crear el dataframe asignar cada columna y su respectiva fila"""
        filas = self.extraer_filas(
            self.lista_urls, self.nombres, self.precios, self.aplica_descuento, 
            self.sku, self.categorias_productos, self.descripcion, self.imagenes
        )
        columnas_tabla = ['color', 'cant_existente', 'cant_blocal', 'cant_bzonafranca', 'cant_variedad', 'estado_transito', 'fecha_transito']
        columnas_completas = ['url_proveedor', 'producto', 'descuento_proveedor', 'precio', 'sku_proveedor', 'categoria', 'descripcion', 'imagenes'] + columnas_tabla
        
        df_productos = pd.DataFrame(filas, columns=columnas_completas)
        
        df_productos['id_variante'] = df_productos['sku_proveedor'] + ' ' + df_productos['color']
        updated_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        df_productos['updated_at'] = updated_at
        created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        df_productos['created_at'] = created_at
        
        df_productos['promall_estado'] = 'NUEVO'
        df_productos['woo_estado'] = 'PENDIENTE'

        # historico
        archivo_historico = 'historico.csv'
        """verificamos posteriores ejecuciones si el archivo existe, si existe lo leemos y comparamos con el nuevo dataframe"""
        if os.path.exists(archivo_historico):
            # Leer el histórico
            historico = pd.read_csv(archivo_historico, sep='\t', encoding='utf-8-sig')

            # Comparar las variedades
            comparacion = pd.merge(
                historico,
                df_productos,
                on='id_variante',
                how='outer',
                suffixes=('_hist', '_nuevo'),
                indicator=True
            )

            # Actualizar PROMALL STATUS
            def clasificar_fila(row):
                if row['_merge'] == 'both':
                    if (
                        row['precio_hist'] != row['precio_nuevo'] or
                        row['cant_variedad_hist'] != row['cant_variedad_nuevo']
                    ):
                        return 'ACTUALIZADO'
                    return 'ACTUALIZADO'
                elif row['_merge'] == 'left_only':
                    row['deleted_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # Fecha de eliminación
                    return 'ELIMINADO'
                elif row['_merge'] == 'right_only':
                    return 'NUEVO'

            comparacion['promall_estado'] = comparacion.apply(clasificar_fila, axis=1)

            # Consolidar las columnas finales
            for col in columnas_tabla + ['precio', 'cant_variedad', 'url_proveedor', 'producto', 'sku_proveedor', 'categoria', 'descripcion', 'imagenes', 'color']:
                comparacion[col] = comparacion[f"{col}_nuevo"].combine_first(comparacion[f"{col}_hist"])

            # Actualizar columnas específicas
            comparacion['updated_at'] = updated_at  # Actualizar con la nueva fecha
            comparacion['descuento_proveedor'] = comparacion['descuento_proveedor_nuevo'].combine_first(
                comparacion['descuento_proveedor_hist']
            )
            comparacion['woo_estado'] = comparacion['woo_estado_hist'].combine_first(
                comparacion['woo_estado_nuevo']
            )

            # Seleccionar y reorganizar las columnas finales
            columnas_finales = ['url_proveedor', 'producto', 'descuento_proveedor', 'precio', 'sku_proveedor', 'categoria', 'descripcion', 'imagenes', 'color', 
                                'cant_existente', 'cant_blocal', 'cant_bzonafranca', 'cant_variedad', 'estado_transito', 'fecha_transito', 'updated_at', 
                                'promall_estado', 'woo_estado', 'id_variante', 'deleted_at']
            
            # Manejar columnas faltantes
            for col in columnas_finales:
                if col not in comparacion.columns:
                    comparacion[col] = None

            # Crear DataFrame final
            df_actualizado = comparacion[columnas_finales]

            # Guardar el nuevo archivo histórico
            print("Actualizando el archivo histórico con cambios detectados.")
            df_actualizado.to_csv(archivo_historico, index=False, encoding='utf-8-sig', sep='\t')
        else:
            # Si no existe el archivo, crear uno nuevo
            print("Archivo histórico no encontrado. Creando uno nuevo.")
            df_productos.to_csv(archivo_historico, index=False, encoding='utf-8-sig', sep='\t')

        print('Proceso completado.')
        
    def ejecutar(self):
        
        try:
            self.urls_productos()
            if not hasattr(self, 'lista_urls') or not self.lista_urls:
                print("Error: lista_urls no está definida o está vacía.")
                return
            self.extraer_imagenes()
            self.categorias()
            self.nombres_productos()
            self.descuento_distribuidor()
            self.precios_productos()
            self.descripcion_p()
            self.buscar_sku()
            self.cabecera_csv()
            self.historico_csv()

            print("Proceso completado.")
        except Exception as e:
            print(f"error durante el scraping: {e}")

    
bodega = BOD_D()
bodega.ejecutar()
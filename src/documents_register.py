import json
import os
import boto3
import re
from botocore.exceptions import NoCredentialsError
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from fuzzywuzzy import fuzz
import sqlite3
import requests
from flask import Flask, render_template
from flask import jsonify
from flask_cors import CORS
import folium

class DocumentRegister():
    def __init__(self):
        self.params = self.read_params('params.json')
        self.AWS_ACCESS_KEY_ID = self.params.get('AWS_ACCESS_KEY_ID')
        self.AWS_SECRET_ACCESS_KEY = self.params.get('AWS_SECRET_ACCESS_KEY')
        self.AWS_REGION = self.params.get('AWS_REGION')
        self.S3_BUCKET_NAME = self.params.get('S3_BUCKET_NAME')
        self.BASE_PATH_FILES = self.params.get('BASE_PATH_FILES')
        self.OUTPUT_FOLER = self.params.get('OUTPUT_FOLER')
        self.DB_NAME = self.params.get('DB_NAME')
        self.DB_PATH = self.params.get('DB_PATH')
        self.API_KEY = self.params.get('API_KEY')
        self.API_URL = self.params.get('API_URL')
        
        conn = sqlite3.connect(os.path.join(self.DB_PATH, self.DB_NAME))
        cursor = conn.cursor()
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS homonymous_addresses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            original_address TEXT,
            homonymous_address TEXT,
            similarity_percentage INTEGER,
            coordinates TEXT
        )
        ''')
        conn.commit()
        
    def read_params(self, file):
        with open(file) as json_params:
            params = json.load(json_params)
        return params

    def upload_to_s3(self, base_path, bucket_name, s3_file_name=None):
        # Configurar el cliente S3
        s3 = boto3.client('s3', aws_access_key_id=self.AWS_ACCESS_KEY_ID, aws_secret_access_key=self.AWS_SECRET_ACCESS_KEY, verify=False)
        
        # Recorrer todos los archivos
        for root, _, files in os.walk(base_path):
            for file_name in files:
                local_file_path = os.path.join(root, file_name)
                try:
                    # Obtener el nombre del archivo en S3
                    s3_file_name = os.path.join(os.path.relpath(local_file_path, base_path))

                    # Subir el archivo al bucket de S3
                    s3.upload_file(local_file_path, self.S3_BUCKET_NAME, s3_file_name)
                    print(f"Documento {local_file_path} subido exitosamente a {self.S3_BUCKET_NAME}/{s3_file_name}")
                except FileNotFoundError:
                    print(f"El archivo {local_file_path} no se encontró.")
                except NoCredentialsError:
                    print("Credenciales de AWS no disponibles o incorrectas.")        

    def extract_addresses(self, base_path, output_folder, db_path, db_name):
        #Conección a base de datos
        conn = sqlite3.connect(os.path.join(db_path, db_name))
        cursor = conn.cursor()
        # Configurar el cliente S3
        s3 = boto3.client('s3', aws_access_key_id=self.AWS_ACCESS_KEY_ID, aws_secret_access_key=self.AWS_SECRET_ACCESS_KEY, verify=False)

        # Recorrer todos los archivos en el S3 bucket
        objects = s3.list_objects(Bucket=self.S3_BUCKET_NAME)['Contents']
        for s3_object in objects:
            s3_file_name = s3_object['Key']
            local_file_path = os.path.join(base_path, os.path.relpath(s3_file_name))

            # Descargar el archivo desde S3
            s3.download_file(self.S3_BUCKET_NAME, s3_file_name, local_file_path)

            try:
                # Leer la primera línea del archivo para obtener la dirección
                with open(local_file_path, 'r', encoding='utf-8') as file:
                    first_line = file.readline().strip()
                    print(f"Dirección extraída del archivo {local_file_path}: {first_line}")

                    # Obtener direcciones homónimas
                    homonymous_addresses = self.get_homonymous_addresses(first_line)

                    # Crear un nuevo archivo en el directorio de salida
                    output_file_path = os.path.join(output_folder, f"{os.path.splitext(os.path.basename(local_file_path))[0]}_homonymous.txt")
                    with open(output_file_path, 'w', encoding='utf-8') as output_file:
                        output_file.write('\n'.join(homonymous_addresses) + '\n')
                        print(f"Archivo homónimo creado: {output_file_path}")
                    
                    # Comparación de similitud y almacenamiento en archivos individuales
                    for homonymous_address in homonymous_addresses:
                        similarity_ratio = fuzz.ratio(first_line, homonymous_address)
                        if similarity_ratio > 90:                               
                            # Almacenar dirección homónima en un archivo individual
                            output_file_path = os.path.join(output_folder, f"{os.path.splitext(os.path.basename(local_file_path))[0]}_{similarity_ratio}_similar_address.txt")
                            with open(output_file_path, 'w', encoding='utf-8') as output_file:
                                output_file.write(homonymous_address + '\n')
                                print(f"Archivo de dirección similar creado: {output_file_path}")
                            
                            #Obtener coordnada
                            coordinates = self.get_coordinates_from_google_maps(homonymous_address)
                            # Store data in the SQLite database
                            cursor.execute("INSERT INTO homonymous_addresses (original_address, homonymous_address, similarity_percentage, coordinates) VALUES (?, ?, ?, ?)",
                                        (first_line, homonymous_address, similarity_ratio, coordinates))
                            conn.commit()

            except FileNotFoundError:
                print(f"El archivo {local_file_path} no se encontró.")
            except Exception as e:
                print(f"Error al leer el archivo {local_file_path}: {str(e)}")
            #finally:
                # Eliminar el archivo local después de procesarlo
                #os.remove(local_file_path)
                
        conn.close()

    def get_homonymous_addresses(self, original_address):
        prefix_variations = {
            'cra': ['cra', 'kra', 'carrera'],
            'kra': ['cra', 'kra', 'carrera'],
            'carrera': ['cra', 'kra', 'carrera'],
            
            'cl': ['cl', 'calle', 'c'],
            'calle': ['cl', 'calle', 'c'],
            'c': ['cl', 'calle', 'c'],
            
            'trasversal': ['trasversal', 'tr', 'trv', 'trasv'],
            'tr': ['trasversal', 'tr', 'trv', 'trasv'],
            'trv': ['trasversal', 'tr', 'trv', 'trasv'],
            'trasv': ['trasversal', 'tr', 'trv', 'trasv'],
            
            'circular': ['circular', 'cr', 'circ'],
            'cr': ['circular', 'cr', 'circ'],
            'circ': ['circular', 'cr', 'circ'],
                        
            'avenida': ['av', 'avenida', 'aven'],
            'av': ['av', 'avenida', 'aven'],
            'aven': ['av', 'avenida', 'aven']
        }

        homonymous_addresses = set()

        for prefix, variations in prefix_variations.items():
            for variation in variations:
                match = re.search(rf'{prefix}\s*(\d+)\s*#\s*(\S+)', original_address.lower(), re.IGNORECASE)
                if match:
                    number_part = f"{match.group(1)} # {match.group(2)}"
                    nro_part = f"{match.group(1)} nro {match.group(2)}"
                    numero_part = f"{match.group(1)} numero {match.group(2)}"
                    num_part = f"{match.group(1)} num {match.group(2)}"

                    homonymous_addresses.update([f"{variation} {number_part}", f"{variation} {nro_part}", f"{variation} {numero_part}", f"{variation} {num_part}"])

        homonymous_addresses = list(homonymous_addresses)
        return homonymous_addresses
    
    def get_coordinates_from_google_maps(self, address):
        # Use the Google Maps Geocoding API to obtain coordinates for the given address
        api_key = self.API_KEY  
        base_url = self.API_URL 
        params = {'address': address, 'key': api_key}
        
        try:
            response = requests.get(base_url, params=params, verify=False)
            response.raise_for_status()
            data = response.json()

            # Extract and return coordinates (latitude, longitude)
            if data['status'] == 'OK' and "results" in data and data["results"]:
                location = data['results'][0]['geometry']['location']
                coordinates = f"{location['lat']}, {location['lng']}"
                
                # Imprimir las coordenadas antes de devolverlas
                print(f"Coordenadas obtenidas para '{address}': {coordinates}")
                
                return coordinates
            else:
                print(f"No se encontraron resultados para '{address}' en la API de Google Maps.")
                print("Detalles de la respuesta de la API:", data)
                return None
        except Exception as e:
            print(f"Error in API request: {str(e)}")
            return None
        
    def get_coordinates_from_database(self):
        # Obtener coordenadas almacenadas en la base de datos
        conn = sqlite3.connect(os.path.join(self.DB_PATH, self.DB_NAME))
        cursor = conn.cursor()

        cursor.execute("SELECT coordinates FROM homonymous_addresses WHERE coordinates IS NOT NULL")
        coordinates = cursor.fetchall()

        conn.close()
        # Desempaquetar tuplas y retornar la lista de coordenadas como strings
        return [coord[0] for coord in coordinates]
    
    def create_map(self, coordinates):
        # Crear un mapa con folium
        map_center = [4.6097, -74.0817]  # Coordenadas del centro del mapa (puedes ajustar esto)
        my_map = folium.Map(location=map_center, zoom_start=12)

        # Agregar marcadores al mapa
        for coord in coordinates:
            lat, lon = map(float, coord.split(','))
            folium.Marker(location=[lat, lon], popup='Dirección').add_to(my_map)

        # Guardar el mapa como un archivo HTML
        my_map.save(os.path.join(self.BASE_PATH_FILES, 'mapa_coordenadas.html'))
        print("Mapa creado exitosamente")


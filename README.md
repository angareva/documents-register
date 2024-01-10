# documents-register
## Licencia

Este proyecto está bajo la licencia [MIT](AFL-3.0).

# prueba_operaciones

# Objetivo
La empresa procesa cientos de miles de documentos de los clientes que se requieren
registrar en nuestra plataforma, para alivianar nuestra carga operativa, requerimos una
solución donde podamos automatizar la carga de documentos, pero a su vez el
análisis de los mismos.
Para esto, requerimos que escribas un algoritmo que permita realizar lo siguiente
1 Subir uno o varios documentos a AWS S3 a través de consola
2 Una vez subidos a AWS, se debe correr un algoritmo que permita extraer la dirección 
del documento en texto plano
3 Crear archivo de texto plano que contenta direcciones homónimas a las que hay en 
el documento original, en la carpeta homonymous_addresses.
Nota: Este documento no debe contener la dirección original tal cual como está en
el archivo
4 Realizar una comparación entre la dirección original del documento y las direcciones 
“homónimas”, si el resultado del algoritmo da un porcentaje de similitud
mayor al 90% se almacena esta dirección en un nuevo archivo txt.
5 Con las direcciones resultantes se consume la API de Google para obtener las
coordenadas exactas de la dirección y agregarlas a la tabla resultante homonymous_addresses
de la base de datos DB_adress.db ubicada en la carpeta scr donde están
las direcciones que tenían un porcentaje de similitud mayor al 90%
6 Con estas coordenadas requerimos que presente un mapa donde se vean las
diferentes coordenadas resultantes

# Ejecución 
# Llevar insumos a carpeta src
Llevar a la capeta src/docs los arhivos txt que contienen las direcciones a analizar

# Crear ambiente virtual 
ejecutar comando python -m venv venv si el ambiente virtual no existe 

# activar ambiente virtual 
ejecutar comando .\venv\Scripts\activate

# instalar librerias necesarias 
pip install -r .\requieremnets.txt

# Ejecuta main
ejecuta el comando python main.py

# Estructura de Carpetas
src: Contiene el código fuente principal y base de datos donde se almacenan las coordenadas finales de las direcciones.
src/docs: Contiene documentos insumo con dirección a analizar y archivo HTML para visualización del mapa. 
homonymous_addresses: Contien documentos txt con direcciones homonimas. 

# Dependencias
boto3: Librería de AWS SDK para Python.
fuzzywuzzy: Herramienta para comparación de cadenas.
sqlite3: Módulo para trabajar con bases de datos SQLite.
requests: Librería para realizar solicitudes HTTP.
flask: Marco de aplicación web para mostrar el mapa.
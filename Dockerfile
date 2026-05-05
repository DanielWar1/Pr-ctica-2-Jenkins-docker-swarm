FROM python:3.9-slim

WORKDIR /app

# Copiamos los requerimientos primero para aprovechar la caché
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiamos el resto de los archivos (app.py, templates, etc.)
COPY . .

# Exponemos el puerto de Flask
EXPOSE 5000

# Ejecutamos la aplicación
CMD ["python", "app.py"]

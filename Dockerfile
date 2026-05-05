FROM python:3.9-slim

WORKDIR /app

# Copiamos el archivo de requisitos
COPY requirements.txt .

# INSTALAMOS LAS LIBRERÍAS (Esto es lo que estaba fallando)
RUN pip install --no-cache-dir -r requirements.txt

# Copiamos el resto del código
COPY . .

EXPOSE 5000

CMD ["python", "app.py"]

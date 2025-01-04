# Usar una imagen oficial de Python
FROM python:3.11-slim

# Establecer el directorio de trabajo
WORKDIR /app


# Copiar el contenido del proyecto
COPY . /app

RUN pip install --upgrade pip

# Instalar las dependencias
RUN pip install -r requerimientos.txt

# Exponer el puerto de la aplicación
EXPOSE 5000

# Comando para iniciar la aplicación
CMD ["python", "app.py"]

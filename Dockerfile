FROM python:3.11-slim

# set working directory in container
WORKDIR /app

COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install gunicorn


COPY . .

# make sure the database has the right permissions
RUN chmod 777 instance


EXPOSE 8000

# Set environment variables
ENV FLASK_APP=app.py
ENV FLASK_ENV=production

# Run Flask application
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "app:app"]

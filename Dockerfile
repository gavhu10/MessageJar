FROM python:3.11-slim

# set working directory in container
WORKDIR /app

COPY requirements.txt .

COPY . .


EXPOSE 8000


ENV FLASK_APP=app.py
ENV FLASK_DEBUG=0

RUN pip3 install --no-cache-dir -r requirements.txt gunicorn==25.1.*

# Create a system user
RUN adduser --disabled-password --gecos '' user
# Change ownership of the app directory
RUN chown -R user:user /app
# Switch to the user
USER user


RUN flask init


# Run Flask application
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "app:app"]

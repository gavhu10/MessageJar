FROM ghcr.io/astral-sh/uv:python3.11-trixie-slim AS builder

# set working directory in container
WORKDIR /app


ENV UV_PYTHON_DOWNLOADS=0
ENV UV_PROJECT_ENVIRONMENT=/app/.venv

COPY pyproject.toml ./

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-install-project --python /usr/local/bin/python3.11 && \
    uv pip install gunicorn==25.1.*

COPY . .


EXPOSE 8000


ENV FLASK_APP=app.py
ENV FLASK_DEBUG=0
ENV PATH="/app/.venv/bin:$PATH"

# Create a system user
RUN adduser --disabled-password --gecos '' user
# Change ownership of the app directory
RUN chown -R user:user /app
# Switch to the user
USER user


RUN flask init


# Run Flask application
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "app:app"]

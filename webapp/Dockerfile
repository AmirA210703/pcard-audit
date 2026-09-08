# Container image for the P-Card Audit Workbench.
#
# Build context is the repository root, not this directory, because the image
# needs both webapp/ and the compressed database in data/:
#
#     docker build -f webapp/Dockerfile -t pcard-audit .
#     docker run -p 8080:8080 -e GEMINI_API_KEY=... pcard-audit
#
# The key is passed in at run time.  It is never built into the image, so the
# image can be pushed to a public registry safely.
FROM python:3.12-slim

WORKDIR /app

COPY webapp/requirements.txt ./webapp/requirements.txt
RUN pip install --no-cache-dir -r webapp/requirements.txt

COPY scripts/ ./scripts/
COPY data/ ./data/
COPY webapp/ ./webapp/

# Expand the database at build time so the container starts fast. The .gz stays
# in the layer above, which keeps this layer cacheable across code changes.
ENV PCARD_DB=/app/data/pcards.db
RUN python scripts/prepare_db.py

# 7860 is the port Hugging Face Spaces expects; hosts that inject $PORT override it.
ENV PORT=7860
EXPOSE 7860

WORKDIR /app/webapp
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT:-7860} --workers 2 --timeout 120 app:app"]

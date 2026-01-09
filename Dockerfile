FROM python:3.11-slim

WORKDIR /app

# Install the package
COPY . .
RUN pip install --no-cache-dir -e ".[trimesh]"

# Default command shows help
ENTRYPOINT ["figure-generator"]
CMD ["--help"]

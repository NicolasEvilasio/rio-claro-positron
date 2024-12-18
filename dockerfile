# Use a imagem base oficial do Python
FROM mcr.microsoft.com/playwright/python:v1.40.0
# Definir variáveis de ambiente
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/opt/prefect
ENV PORT=8080

WORKDIR /opt/prefect

# Copiar arquivos de dependências primeiro
COPY pyproject.toml poetry.lock ./

# Instalar poetry e dependências
RUN pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-ansi && \
    pip install prefect-gcp

# Instalar Playwright e suas dependências
RUN poetry run playwright install chromium --with-deps && \
    apt-get update && \
    apt-get install -y \
    curl \
    wget \
    libnss3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2

# Copiar todo o conteúdo do projeto
COPY . .

# Instalar o pacote
RUN pip install .

# Expor a porta 8080
EXPOSE 8080

# Script de inicialização
COPY start.sh /start.sh
RUN chmod +x /start.sh

# Usar o script de inicialização
CMD ["/start.sh"]


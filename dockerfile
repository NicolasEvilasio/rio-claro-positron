# Use uma imagem base do Python
FROM python:3.11-slim

# Definir variáveis de ambiente
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/opt/prefect
ENV PORT=8080

# Instalar dependências do sistema e Firefox
RUN apt-get update && apt-get install -y \
    firefox-esr \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Instalar o GeckoDriver versão 0.35.0
RUN wget https://github.com/mozilla/geckodriver/releases/download/v0.35.0/geckodriver-v0.35.0-linux64.tar.gz \
    && tar -xvzf geckodriver-v0.35.0-linux64.tar.gz \
    && chmod +x geckodriver \
    && mv geckodriver /usr/local/bin/ \
    && rm geckodriver-v0.35.0-linux64.tar.gz

WORKDIR /opt/prefect

# Copiar arquivos de dependências
COPY pyproject.toml poetry.lock ./

# Instalar poetry e dependências
RUN pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-ansi

# Copiar todo o conteúdo do projeto
COPY . .

# Instalar o pacote
RUN pip install .

# Expor a porta 8080
EXPOSE 8080

# Script de inicialização
COPY start.sh /start.sh
RUN chmod +x /start.sh

# CMD ["/start.sh"]


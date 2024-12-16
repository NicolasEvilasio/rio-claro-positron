# Use a imagem base oficial do Python
FROM python:3.10

# Instale dependências do sistema necessárias para o Playwright
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    libnss3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxrandr2 \
    libasound2 \
    libpangocairo-1.0-0 \
    libgtk-3-0 \
    libxdamage1 \
    libgbm1 \
    && rm -rf /var/lib/apt/lists/*

# Instale o Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -

# Adicione o Poetry ao PATH
ENV PATH="/root/.local/bin:$PATH"

# Configure o Poetry para criar o ambiente virtual dentro do projeto
RUN poetry config virtualenvs.in-project true

# Defina o diretório de trabalho
WORKDIR /opt/prefect

# Copie os arquivos de configuração do Poetry
COPY pyproject.toml poetry.lock ./

# Instale as dependências usando o Poetry
RUN poetry install --no-root

# Configure variáveis de ambiente do Playwright
ENV PLAYWRIGHT_BROWSERS_PATH=/opt/prefect/ms-playwright
ENV PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1

# Instale os navegadores Playwright
RUN poetry run playwright install chromium

# Copie o resto do código
COPY . .

# Configure a variável de porta padrão para o Cloud Run
ENV PORT=8080

# Exponha a porta 8080 para o Cloud Run
EXPOSE 8080

# Comando padrão para o container usando Poetry
CMD ["poetry", "run", "prefect", "worker", "start", "--pool", "rio-claro-cloud-run-pool"]


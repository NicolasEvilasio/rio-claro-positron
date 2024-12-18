#!/bin/bash

# Função para iniciar o servidor HTTP
start_http_server() {
    python -m http.server 8080 &
    HTTP_PID=$!
    echo "HTTP Server started with PID: $HTTP_PID"
}

# Função para iniciar o worker do Prefect
start_prefect_worker() {
    prefect worker start --pool "push-cloud-run" --type cloud-run-v2:push &
    WORKER_PID=$!
    echo "Prefect Worker started with PID: $WORKER_PID"
}

# Função para verificar se os processos estão rodando
check_processes() {
    if ! kill -0 $HTTP_PID 2>/dev/null; then
        echo "HTTP Server died"
        exit 1
    fi
    if ! kill -0 $WORKER_PID 2>/dev/null; then
        echo "Prefect Worker died"
        exit 1
    fi
}

# Iniciar os serviços
start_http_server
sleep 2  # Aguardar o servidor HTTP iniciar
start_prefect_worker

# Loop para manter o container rodando e verificar os processos
while true; do
    check_processes
    sleep 10
done
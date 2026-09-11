#!/usr/bin/env bash
# scripts/run-sonar-local.sh
# Roda o pysonar localmente contra o SonarQube pessoal. Projeto/host/sources
# ficam em sonar-project.properties (versionado); só o token é segredo e
# fica no .env (gitignored).
#
# ponytail: sem a limpeza de processos java órfãos do scanner-engine que o
# script .ps1 de referência faz — aquilo existe para contornar um lock de
# diretório do Windows/NTFS após um scan interrompido; no Linux/ext4 não há
# esse modo de falha, então recriar o diretório do cache nunca fica bloqueado.

set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."

if [ ! -f .env ]; then
    echo "Erro: .env não encontrado em $(pwd) — copie de .env.example e preencha SONAR_TOKEN." >&2
    exit 1
fi

if ! command -v uv >/dev/null 2>&1; then
    echo "Erro: uv não encontrado no PATH." >&2
    exit 1
fi

set -a
source .env
set +a

if [ -z "${SONAR_TOKEN:-}" ]; then
    echo "Erro: SONAR_TOKEN não definido no .env." >&2
    exit 1
fi

# Regenera o coverage.xml IMEDIATAMENTE antes do scan. Sem isto, o pysonar lê
# um relatório ausente/desatualizado e o Sonar reporta cobertura 0%.
uv run pytest --cov --cov-report=xml

uvx --from pysonar pysonar

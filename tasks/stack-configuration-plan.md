# Plano: configuração da stack e do Sonar

## Objetivo

Aplicar ao repositório atual, que contém skills Python e testes unittest, as
partes compatíveis do padrão de stack definido em `docs/padroes_de_stack.md`.

## Decisões

- Tratar este repositório como um projeto Python único; não criar `api/` ou
  `web/` artificiais, pois não há uma aplicação FastAPI ou Next.js neste escopo.
- Usar `uv` como gerenciador e manter as versões de ferramentas de qualidade
  pinadas no `pyproject.toml` e no `uv.lock`.
- Configurar o Sonar para as pastas de skills e seus testes reais; o token fica
  somente no `.env` local, ignorado pelo Git.
- Manter release/changelog dirigidos por Conventional Commits via
  `python-semantic-release`, sem bump manual.

## Tarefas

### Fase 1: manifesto e qualidade

- [x] Criar `pyproject.toml` com dependências de desenvolvimento, pytest/cov,
  Ruff e mypy strict.
- [x] Gerar `uv.lock`.

### Fase 2: integração do repositório

- [x] Adicionar `.pre-commit-config.yaml` e configurações de release.
- [x] Completar `.gitignore`, `.env.example` e settings do workspace.

### Fase 3: Sonar

- [x] Corrigir `sonar-project.properties` para a estrutura real do repositório.
- [x] Tornar `scripts/run-sonar-local.sh` seguro e executável com o `.env`.

## Verificação

- `uv run pytest`
- `uv run pytest --cov --cov-report=xml`
- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run mypy ...`
- `uv run pre-commit run --all-files`
- `scripts/run-sonar-local.sh` quando o Sonar local estiver acessível

## Riscos

- Algumas ferramentas listadas no padrão podem não suportar Python 3.14 ainda;
  o projeto declarará `>=3.12` e o lock resolverá o ambiente disponível.
- O scanner Sonar depende de rede e de um servidor acessível; sua falha não
  deve mascarar os checks locais de código.

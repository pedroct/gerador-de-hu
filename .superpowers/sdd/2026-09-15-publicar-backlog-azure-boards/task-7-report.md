# Relatório da Tarefa 7

## Resultado

A Tarefa 7 foi implementada no worktree `publicar-backlog-azure-boards` com uma CLI de orquestração,
uma skill operacional, metadados para agentes OpenAI, testes de integração e documentação no
README raiz.

## Arquivos criados ou modificados

- `publicar-backlog-azure-boards/scripts/publicar_backlog.py`
  - Comandos `validar`, `planejar` e `publicar`.
  - Opções `--simulacao` e `--validar-apenas` sem opção `--yes`.
  - Carregamento do backlog, manifesto e configuração pelos componentes existentes.
  - Verificação preliminar antes da autorização.
  - Plano com destino, quantidades, ordem, relações pai-filho, manifesto e hash.
  - Autorização inteira ou por lotes com frase exata antes de chamar a execução.
  - Simulação e validação remota sem chamadas de criação.
- `publicar-backlog-azure-boards/SKILL.md`
  - Fluxo geração, revisão, autorização e publicação.
  - Confirmação explícita, `zero chamadas de criação`, `AUTORIZAR PUBLICAÇÃO`, configuração por
    execução e MCP opcional.
- `publicar-backlog-azure-boards/agents/openai.yaml`
  - Nome, descrição curta e prompt padrão da skill.
- `publicar-backlog-azure-boards/tests/test_skill_integration.py`
  - Teste de simulação sem criação.
  - Testes dos requisitos textuais de confirmação e MCP opcional.
- `README.md`
  - Fluxo operacional, exemplos em pt-BR, variáveis de ambiente, seleção explícita de Area Path,
    Iteration Path por execução e aviso para nunca versionar token.

## Verificações executadas

- `uv run pytest tests/test_skill_integration.py -v`: 3 testes passaram.
- `uv run pytest publicar-backlog-azure-boards/tests/test_skill_integration.py -v`: 3 testes
  passaram a partir da raiz do worktree.
- `uv run pytest -q`: 66 testes passaram.
- `cd publicar-backlog-azure-boards && uv run ruff check .`: passou.
- `uv run mypy src`: passou.
- `uv run bandit -r src`: passou sem problemas.
- `uv run --with pyyaml python /Users/pedroct/.codex/skills/.system/skill-creator/scripts/quick_validate.py publicar-backlog-azure-boards`: `Skill is valid!`.
- `git diff --check`: passou.

`cd publicar-backlog-azure-boards && uv run ruff format --check .` ainda aponta cinco arquivos
preexistentes das Tarefas 1–6, além dos arquivos novos antes da formatação. Os dois arquivos da
Tarefa 7 foram formatados individualmente; os arquivos anteriores não foram alterados por
disciplina de escopo. A execução de Ruff na raiz também encontra violações preexistentes em testes
de outras skills, fora desta tarefa.

## Segurança e escopo

- Nenhum work item real foi criado; os testes usam cliente falso e a simulação não chama criação.
- Nenhum segredo foi adicionado ao diff ou ao relatório.
- O token permanece fora dos exemplos preenchidos e da saída do plano.
- A CLI não contém regras de negócio do backlog; ela apenas coordena os componentes existentes.
- Não foram usados subagentes nem revisores, conforme solicitado.

# Relatório final da onda de correção

## Status

CONCLUÍDO COM PREOCUPAÇÃO DE DEPENDÊNCIAS DE DESENVOLVIMENTO

Commit único: `634dbbb fix: fecha auditoria final do publicador`

## Correções auditadas

- A autorização integral agora fica vinculada ao hash, assinatura do conteúdo executável, destino,
  quantidade e conjunto pendente; lotes continuam vinculados à faixa exata.
- A criação usa o endpoint REST `/workitems/$<tipo remoto>`, incluindo o mapeamento configurável
  `Product Backlog Item` no payload, no plano e no hash.
- A consulta de tipos de relação usa o endpoint no escopo da organização, conforme o contrato REST;
  as demais consultas continuam no escopo do projeto.
- Area Path e Iteration Path são normalizados e validados pelos endpoints de classification nodes,
  com `name`, `path` e `structureType` conferidos.
- A retomada valida o manifesto contra o plano completo antes de calcular pendentes.
- O entry point instalado chama a CLI real; o validador estrutural existente é executado antes do
  planejamento.
- Token interativo usa leitura sem eco e a simulação não carrega token, não instancia cliente HTTP,
  não pede autorização e não faz POST.
- Timeout, erro de rede, resposta 2xx inválida ou identidade ausente em criação deixam o manifesto
  em reconciliação manual; POST não é repetido. Falha ao gravar o manifesto após sucesso também
  mantém o marcador de reconciliação.
- Os arquivos Python da onda foram formatados.

## Verificações

Executadas no diretório `publicar-backlog-azure-boards`:

- `uv run pytest -q`: **82 passaram**.
- `uv run pytest` na raiz do worktree: **79 passaram, 2 subtestes passaram**.
- `uv run ruff check .`: passou.
- `uv run ruff format --check .`: **22 arquivos já formatados**.
- `uv run mypy src`: passou, sem problemas.
- `uv run bandit -r src`: passou, sem problemas.
- `uv run semgrep --config auto --error src tests`: **0 achados**.
- `quick_validate.py publicar-backlog-azure-boards`: `Skill is valid!`.
- `uv run publicar-backlog-azure-boards validar tests/fixtures/valid-backlog.md`: passou.
- `uv run python scripts/publicar_backlog.py validar tests/fixtures/valid-backlog.md`: passou.
- `git diff --check`: passou.

Nenhum work item real foi criado e `graphify-out/` existente foi preservado fora do commit.

## pip-audit — 16/09/2026

Comando: `uv run pip-audit --format json` — exit **1**, 15 registros em 3 pacotes, 9 avisos únicos.
Os registros duplicados do JSON foram consolidados abaixo.

| Pacote/versão | IDs | Correção | Aplicabilidade |
|---|---|---|---|
| `click 8.1.8` | `PYSEC-2026-2132` (`CVE-2026-7246`, `GHSA-47fr-3ffg-hgmw`) | `8.3.3` | Transitivo apenas do grupo de desenvolvimento (`semgrep`, `python-semantic-release`, `uvicorn`). O publicador não usa `click.edit()` nem importa `click`; não aplicável ao runtime atual. |
| `mcp 1.23.3` | `PYSEC-2026-3481` (`CVE-2026-52870`, `GHSA-hvrp-rf83-w775`); `PYSEC-2026-3482` (`CVE-2026-52869`, `GHSA-jpw9-pfvf-9f58`); `PYSEC-2026-3483` (`CVE-2026-59950`, `GHSA-vj7q-gjh5-988w`) | `1.27.2` para os dois primeiros; `1.28.1` para o terceiro | Transitivo de `semgrep`, não dependência de runtime e não importado pelo publicador. As condições descritas nos avisos (tasks experimentais, transporte HTTP stateful autenticado ou WebSocket legado) não existem neste código; não aplicável ao runtime atual. |
| `pyjwt 2.12.1` | `PYSEC-2026-175` (`CVE-2026-48522`, `GHSA-993g-76c3-p5m4`); `PYSEC-2026-176` (`CVE-2026-48523`, `GHSA-jq35-7prp-9v3f`); `PYSEC-2026-177` (`CVE-2026-48524`, `GHSA-fhv5-28vv-h8m8`); `PYSEC-2026-178` (`CVE-2026-48525`, `GHSA-w7vc-732c-9m39`); `PYSEC-2026-179` (`CVE-2026-48526`, `GHSA-xgmm-8j9v-c9wx`) | `2.13.0` | Transitivo de `mcp` via `semgrep`, não importado nem usado pelo publicador; não aplicável ao runtime atual. |

Os três pacotes permanecem preocupações de higiene do ambiente de desenvolvimento: devem ser
atualizados quando a cadeia de ferramentas aceitar as versões corrigidas. Não foram atualizados
nesta onda porque não fazem parte das dependências de produção e a mudança de resolução poderia
alterar o conjunto de ferramentas além do escopo.

Não foram usados subagentes ou revisores.

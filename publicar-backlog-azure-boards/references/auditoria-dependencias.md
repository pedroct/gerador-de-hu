# Auditoria de dependências

Data da decisão: 16/09/2026

Responsável pela decisão: Codex, em execução solicitada pelo responsável do worktree.

## Evidência

Comandos executados no diretório `publicar-backlog-azure-boards`:

```text
uv run ruff format --check .
27 files already formatted

uv run pip-audit --format json > /tmp/publicar-backlog-pip-audit-final.json
Found 15 known vulnerabilities in 3 packages
```

O segundo comando terminou com código 1, como esperado para uma auditoria com avisos. As 15
ocorrências correspondem a 9 IDs únicos, repetidos pelo inventário de extras e caminhos do
ambiente. A repetição não foi filtrada no comando; este relatório agrupa somente para facilitar a
leitura.

Na saída tabular final, o próprio projeto editável também aparece como “Dependency not found on
PyPI”. Isso é uma limitação esperada do `pip-audit` para o pacote local e não um aviso de
vulnerabilidade; as dependências resolvidas foram auditadas normalmente.

## Avisos individualizados

| Pacote/versão | ID | Correção indicada | Caminho transitivo | Escopo | Tratamento |
|---|---|---|---|---|---|
| `click==8.1.8` | `PYSEC-2026-2132` (`CVE-2026-7246`, `GHSA-47fr-3ffg-hgmw`) | `8.3.3` | `semgrep==1.165.0` → `click~=8.1.8`; também `python-semantic-release`/`uvicorn` | Desenvolvimento | Não atualizada: o Semgrep fixa `8.1.8`; não afeta o pacote de produção. Mitigação: não executar ferramentas de desenvolvimento em serviço exposto e revisar a dependência antes de habilitar atualizações compatíveis. |
| `mcp==1.23.3` | `PYSEC-2026-3481` (`CVE-2026-52870`, `GHSA-hvrp-rf83-w775`) | `1.27.2` | `semgrep==1.165.0` → `mcp==1.23.3` | Desenvolvimento | Não atualizada: o Semgrep fixa `1.23.3`; o MCP é usado apenas pelo Semgrep, não pela CLI. Mitigação: MCP opcional e REST obrigatória no produto; Semgrep não é dependência de produção. |
| `mcp==1.23.3` | `PYSEC-2026-3482` (`CVE-2026-52869`, `GHSA-jpw9-pfvf-9f58`) | `1.27.2` | `semgrep==1.165.0` → `mcp==1.23.3` | Desenvolvimento | Mesmo tratamento do aviso anterior; sem caminho de execução da CLI. |
| `mcp==1.23.3` | `PYSEC-2026-3483` (`CVE-2026-59950`, `GHSA-vj7q-gjh5-988w`) | `1.28.1` | `semgrep==1.165.0` → `mcp==1.23.3` | Desenvolvimento | Mesmo tratamento do aviso anterior; sem transporte WebSocket MCP no produto. |
| `pyjwt==2.12.1` | `PYSEC-2026-175` (`CVE-2026-48522`, `GHSA-993g-76c3-p5m4`) | `2.13.0` | `semgrep==1.165.0` → `pyjwt[crypto]~=2.12.0`; `mcp[crypto]` | Desenvolvimento | Não atualizada: o Semgrep fixa a faixa `2.12.x`; PyJWT não é importado pelo pacote. Mitigação: fora da instalação de produção. |
| `pyjwt==2.12.1` | `PYSEC-2026-176` (`CVE-2026-48523`, `GHSA-jq35-7prp-9v3f`) | `2.13.0` | `semgrep==1.165.0` → `pyjwt[crypto]~=2.12.0`; `mcp[crypto]` | Desenvolvimento | Mesmo tratamento do aviso anterior. |
| `pyjwt==2.12.1` | `PYSEC-2026-177` (`CVE-2026-48524`, `GHSA-fhv5-28vv-h8m8`) | `2.13.0` | `semgrep==1.165.0` → `pyjwt[crypto]~=2.12.0`; `mcp[crypto]` | Desenvolvimento | Mesmo tratamento do aviso anterior. |
| `pyjwt==2.12.1` | `PYSEC-2026-178` (`CVE-2026-48525`, `GHSA-w7vc-732c-9m39`) | `2.13.0` | `semgrep==1.165.0` → `pyjwt[crypto]~=2.12.0`; `mcp[crypto]` | Desenvolvimento | Mesmo tratamento do aviso anterior. |
| `pyjwt==2.12.1` | `PYSEC-2026-179` (`CVE-2026-48526`, `GHSA-xgmm-8j9v-c9wx`) | `2.13.0` | `semgrep==1.165.0` → `pyjwt[crypto]~=2.12.0`; `mcp[crypto]` | Desenvolvimento | Mesmo tratamento do aviso anterior. |

As ocorrências duplicadas de `PYSEC-2026-175`, `176`, `177`, `178`, `179` e dos três avisos MCP
foram mantidas na saída JSON e não representam pacotes adicionais.

## Tentativas de correção

Foram executados `uv lock --upgrade-package click --upgrade-package mcp --upgrade-package pyjwt`
e `uv lock --upgrade`. O resolvedor preservou as versões acima por causa das restrições do
`semgrep==1.165.0`; portanto não foi aplicado override incompatível nem filtro no `pip-audit`.
O lock foi atualizado apenas para versões compatíveis não vulneráveis que o resolvedor encontrou.

O caminho de produção contém somente `httpx`, `markdown-it-py`, `pydantic` e
`pydantic-settings`; a auditoria não reportou vulnerabilidades nesses pacotes. Se o Semgrep
publicar uma versão que relaxe ou atualize essas restrições, esta auditoria deve ser repetida antes
de remover as exceções.

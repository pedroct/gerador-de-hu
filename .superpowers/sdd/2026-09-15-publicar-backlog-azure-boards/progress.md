# SDD ledger — plan: docs/superpowers/plans/2026-09-15-publicar-backlog-azure-boards.md

## Contexto

- Worktree: `.worktrees/publicar-backlog-azure-boards`
- Branch: `feat/publicar-backlog-azure-boards`
- Especificação: `docs/superpowers/specs/2026-09-15-publicar-backlog-azure-boards-design.md`
- Baseline do worktree: `0216ffb`

## Varredura prévia do plano

| Escopo | Produz | Consome | Resultado / ruling |
|---|---|---|---|
| Tarefa 1 ↔ Tarefa 2 | projeto Python e pacote importável | configuração do projeto | Compatível; Tarefa 2 usa o `src` criado na Tarefa 1. |
| Tarefa 1 ↔ Tarefa 3 | dependências e ferramentas pinadas | `markdown-it-py`, modelos da Tarefa 2 | Compatível; nenhum conflito de arquivo. |
| Tarefa 2 ↔ Tarefa 3 | `ItemBacklog` | itens, tipos e relações | Compatível; Tarefa 3 estende os modelos definidos na Tarefa 2. |
| Tarefa 2 ↔ Tarefa 4 | campos interpretados e tipos | configuração e autorização | Compatível; Tarefa 4 consome o plano, não reinterpreta o Markdown. |
| Tarefa 3 ↔ Tarefa 4 | `PlanoPublicacao` com hash | autorização vinculada ao hash | Compatível; a confirmação depende do plano final. |
| Tarefa 3 ↔ Tarefa 5 | `OperacaoCriacao` | cliente REST | Compatível; tipos e campos permanecem identificadores Azure quando exigido. |
| Tarefa 4 ↔ Tarefa 6 | `Autorizacao` | executor sequencial | Compatível; manifesto não concede autorização. |
| Tarefa 5 ↔ Tarefa 6 | `RegistroCriado` e erros | persistência após sucesso | Compatível; relação pai-filho depende de ID já criado. |
| Tarefa 6 ↔ Tarefa 7 | executor e retomada | CLI e fluxo conversacional | Compatível; CLI apenas orquestra componentes. |
| Tarefa 7 ↔ Tarefa 8 | documentação e metadados | verificação final e MCP opcional | Compatível; Tarefa 8 só complementa documentação. |
| Tarefa 1 | arquivos, teste de `requires-python` e script | configuração descrita | Internamente consistente; teste pode rodar após criação do projeto. |
| Tarefa 2 | modelos, interpretador e fixture | contrato Markdown | Internamente consistente; headings e campos têm cobertura mínima. |
| Tarefa 3 | conversores, planejador e testes | modelos/configuração prévios | Internamente consistente; testes cobrem HTML, ordem e manifesto. |
| Tarefa 4 | configuração, autorização e testes | plano/hash e ambiente | Internamente consistente; cobre confirmação exata e lotes positivos. |
| Tarefa 5 | cliente e testes HTTP | configuração/operações | Internamente consistente; inclui leitura, criação e erros tipados. |
| Tarefa 6 | manifesto, executor e testes | plano/autorização/cliente | Internamente consistente; cobre gravação por sucesso e retomada. |
| Tarefa 7 | CLI, skill, metadados e teste | todos os componentes | Internamente consistente; cobre simulação e documentação de confirmação. |
| Tarefa 8 | documentação e verificação | pacote completo | Internamente consistente; comandos de qualidade correspondem à stack. |

Nenhuma tarefa exige teste que não possa observar comportamento, nem há duplicação de lógica
mandada pelo plano. Nenhum conflito ou ruling adicional foi necessário nesta etapa.

## Andamento

Tarefa 1: revisão inicial reprovou a qualidade por entry point público lançando
`NotImplementedError`; iniciar fix round 1/5.

Tarefa 1: fix round 1/5 (1 addressed, 0 open — entry point controlado e teste de invocação;
commits 3e9defd..f3c9846).
Tarefa 1: complete (commits 3e9defd..f3c9846, review clean; preocupação não bloqueante:
`docs/padroes_de_stack.md` não está presente no worktree).
Tarefa 2: complete (commits f3c9846..dd9c9fe, review clean).
Tarefa 3: complete (commits dd9c9fe..0f6e7da, review clean).
Tarefa 4: revisão encontrou bloqueios críticos na criação de autorização e normalização da
confirmação; iniciar fix round 1/5.
Ruling: manter `Iteration Path` vindo de `.env` atualizado — a especificação permite explicitamente
argumento ou `.env` atualizado por execução; exigir pergunta interativa sempre tornaria a precedência
documentada incoerente — custo se errado: uma execução poderia reutilizar caminho persistido além do
esperado pelo operador.
Tarefa 4: fix round 1/5 (3 addressed, 0 open — confirmação, hash e newline; commits 88906b0..4087463).
Tarefa 4: complete (commits 0f6e7da..4087463, review clean).
Tarefa 5: revisão encontrou validação preliminar incompleta, resposta de criação frouxa e risco de
duplicação em retry de POST; iniciar fix round 1/5.
Ruling: não repetir POST após timeout sem idempotência — manter retries limitados para leituras e
erros transitórios não ambíguos; isso prioriza não duplicar work items, conforme a restrição de
retomada segura — custo se errado: uma criação transitória poderá exigir retomada manual.
Tarefa 5: fix round 1/5 (5 addressed, 0 open; commits d51b902..121d05b).
Tarefa 5: complete (commits 4087463..121d05b, review clean; formatação preexistente deferida).
Tarefa 6: revisão encontrou autorização por lotes não aplicada e round-trip inválido para manifesto
vazio; iniciar fix round 1/5.
Tarefa 6: fix round 1/5 (2 addressed, 0 open; commits fd96364..51d0b76).
Tarefa 6: complete (commits 121d05b..51d0b76, review clean).
Tarefa 7: revisão encontrou POST `validateOnly` durante simulação; iniciar fix round 1/5.
Tarefa 7: fix round 1/5 (1 addressed, 0 open; commits 2fd011b..7a99b30).
Tarefa 7: complete (commits 51d0b76..7a99b30, review clean; simulação não valida destino remotamente).
Tarefa 8: complete (commits 7a99b30..392cf47, review clean; observação menor sobre granularidade
do relatório deferida).
Revisão final: reprovada; iniciar onda única de correção para achados críticos/importantes de
integração. Achados completos foram encaminhados ao implementador.
Onda final de correção: commit 634dbbb; testes declarados pelo implementador: 82 isolados, 79 na
raiz, Ruff/mypy/Bandit/Semgrep e skill aprovados; pip-audit permanece com 15 vulnerabilidades
transitivas de desenvolvimento documentadas.
Revisão da onda final: 9 achados endereçados, 3 bloqueios residuais e 1 quebra média de empacotamento.
Parked: observação sobre pip-audit — os identificadores, aplicabilidade e limitações foram
documentados; o plano exige sucesso do comando, mas não há correção compatível comprovada nesta
onda. Custo se errado: vulnerabilidades transitivas podem continuar no ambiente de desenvolvimento.
Ruling: não marcar o branch como pronto para merge — destino divergente, autorização injetável,
reconciliação incompleta e validador ausente no wheel são load-bearing e devem ser corrigidos antes
de publicação. Custo se errado: poderia haver escrita em destino não autorizado ou duplicação após
resultado ambíguo.

## Evidências da Task 6 — 2026-09-16

- `uv run pytest -q`: 110 passed in 0.23s.
- Varredura `rg -n -- '--yes|bypassRules=true|AUTORIZAR PUBLICAÇÃO|Implementation Evidence|token|POST' src scripts SKILL.md README.md tests`: somente ocorrências esperadas em documentação, configuração segura, testes e POSTs de validação/criação; `--yes` e `bypassRules=true` aparecem apenas como restrições documentadas.
- Verificação manual: `--simulacao` retorna antes de instanciar cliente/verificar destino, não solicita token e não executa POST; `Implementation Evidence` é removido antes do payload; POSTs de `--validar-apenas` usam `validateOnly=true`.
- `uv run pip-audit`: exit 1; não foi declarado sucesso. Exceções individuais: `click 8.1.8` — `PYSEC-2026-2132` (correção 8.3.3); `mcp 1.23.3` — `PYSEC-2026-3481`, `PYSEC-2026-3482`, `PYSEC-2026-3483` (correções 1.27.2/1.28.1; IDs repetidos pelo auditor); `pyjwt 2.12.1` — `PYSEC-2026-179`, `PYSEC-2026-175`, `PYSEC-2026-177`, `PYSEC-2026-178` (correção 2.13.0; IDs repetidos pelo auditor); pacote local `publicar-backlog-azure-boards 0.1.0` não encontrado no PyPI e não auditável. Total reportado: 15 vulnerabilidades em 3 pacotes.

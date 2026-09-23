# Task 7: Leitor da Demanda — Relatório

## O que foi implementado

Novo módulo `src/publicar_backlog_demanda_azure_boards/leitor_demanda.py`, contendo a
função livre `ler_demanda(organizacao, projeto, token, id_demanda, tipo_esperado, *,
transport=None, timeout=10.0) -> Demanda`, exatamente com a assinatura exigida pela Task 10.

A função:
- Rejeita `id_demanda <= 0` antes de qualquer chamada de rede.
- Monta a credencial `Basic` a partir do token e faz um único `GET` em
  `/_apis/wit/workitems/{id}?$expand=Fields&api-version=7.2-preview.3`, usando
  `httpx.Client` com o `transport` recebido (nunca há chamada HTTP real).
- Reaproveita `_verificar_status` de `cliente_azure_devops.py` para traduzir status HTTP em
  exceções, envolvendo qualquer falha (incluindo 404) numa `ErroDestinoInvalido` genérica que
  não ecoa a credencial nem o token.
- Valida que o payload e o objeto `fields` são dicionários (`_objeto`), que o tipo do work
  item bate com `tipo_esperado`, que `System.TeamProject` bate com `projeto`, que
  `System.Title`, `System.AreaPath` e `System.IterationPath` são strings não vazias, e que a
  `url` do work item é utilizável (`https://` não vazia).
- Devolve `Demanda(id=id_demanda, titulo=..., area_path=..., iteration_path=..., url=...)`,
  reaproveitando o dataclass congelado da Task 5 sem redefini-lo.

Código e assinaturas seguem literalmente o que veio no brief; nenhuma lógica foi alterada,
apenas reformatação de duas linhas pelo hook `ruff-format` do pre-commit (quebra de linha em
duas chamadas de `raise`/`_objeto`, sem mudança semântica).

## Testes

Arquivo `tests/test_leitor_demanda.py`, copiado literalmente do brief, com 9 casos:

1. `test_le_a_demanda_e_extrai_titulo_e_caminhos` — caminho feliz.
2. `test_recusa_work_item_de_outro_tipo` — tipo errado (mensagem cita ambos os tipos).
3. `test_recusa_demanda_de_outro_projeto` — projeto errado (mensagem cita o projeto real).
4. `test_recusa_demanda_sem_campo_necessario` (parametrizado ×3) — `System.AreaPath`,
   `System.IterationPath`, `System.Title` vazios.
5. `test_recusa_work_item_inexistente` — HTTP 404 (mensagem cita o ID).
6. `test_recusa_identificador_nao_positivo` — `id_demanda=0`.
7. `test_nao_expoe_o_token_na_mensagem_de_erro` — garante que o token de teste não aparece em
   `str(erro.value)` mesmo numa falha 404.

Todos os transportes são `httpx.MockTransport`; nenhuma chamada de rede real ocorre.

**Observação de fidelidade ao brief:** a lista de autorrevisão do brief menciona "URL
inutilizável" entre as validações a cobrir com teste. A implementação valida isso
(`_objeto`/checagem de `url_item`), mas o conjunto de 9 testes prescrito no brief — que devo
usar "exatamente como estão lá" — não inclui um teste dedicado a essa validação específica.
Não adicionei um décimo teste por conta própria, para não divergir do texto literal do brief;
sinalizo isso como ponto de atenção, não como lacuna que corrigi silenciosamente.

## Evidência TDD

**RED** — antes de criar `leitor_demanda.py`:

```
$ uv run pytest tests/test_leitor_demanda.py -v
...
ERROR collecting tests/test_leitor_demanda.py
ImportError while importing test module '.../tests/test_leitor_demanda.py'.
E   ModuleNotFoundError: No module named 'publicar_backlog_demanda_azure_boards.leitor_demanda'
=========================== short test summary info ============================
ERROR tests/test_leitor_demanda.py
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
=============================== 1 error in 0.13s ===============================
```

Falha esperada: o módulo ainda não existia.

**GREEN** — depois de criar `leitor_demanda.py`:

```
$ uv run pytest tests/test_leitor_demanda.py -v
tests/test_leitor_demanda.py::test_le_a_demanda_e_extrai_titulo_e_caminhos PASSED [ 11%]
tests/test_leitor_demanda.py::test_recusa_work_item_de_outro_tipo PASSED [ 22%]
tests/test_leitor_demanda.py::test_recusa_demanda_de_outro_projeto PASSED [ 33%]
tests/test_leitor_demanda.py::test_recusa_demanda_sem_campo_necessario[System.AreaPath] PASSED [ 44%]
tests/test_leitor_demanda.py::test_recusa_demanda_sem_campo_necessario[System.IterationPath] PASSED [ 55%]
tests/test_leitor_demanda.py::test_recusa_demanda_sem_campo_necessario[System.Title] PASSED [ 66%]
tests/test_leitor_demanda.py::test_recusa_work_item_inexistente PASSED   [ 77%]
tests/test_leitor_demanda.py::test_recusa_identificador_nao_positivo PASSED [ 88%]
tests/test_leitor_demanda.py::test_nao_expoe_o_token_na_mensagem_de_erro PASSED [100%]

============================== 9 passed in 0.06s ===============================
```

## Lint, tipos e segurança

```
$ uv run ruff check src tests
All checks passed!

$ uv run mypy src
Success: no issues found in 15 source files

$ uv run bandit -c pyproject.toml -r src
... Total issues (by severity): Undefined: 0 / Low: 0 / Medium: 0 / High: 0
```

## `_verificar_status`: não precisou promover

O `select` do ruff neste projeto é `["E", "F", "I", "B", "UP", "S"]`, que não inclui
`SLF001` (regra de `flake8-self` que bloquearia acesso a membro privado entre módulos).
Confirmei rodando `uv run ruff check src tests` com a importação de `_verificar_status`
ainda privada: **passou sem nenhum aviso**. Portanto **não promovi** `_verificar_status`
para `verificar_status` em `cliente_azure_devops.py` — o módulo permanece exatamente como a
Task 6 o deixou, sem qualquer alteração. Isso significa que a Task 8 encontrará
`cliente_azure_devops.py` inalterado por esta tarefa.

## Suíte inteira

```
$ uv run pytest
...
============================= 171 passed in 0.32s ==============================
```

162 (estado anterior, Tasks 1–6) + 9 (novos testes desta tarefa) = 171. Sem warnings.
Repeti a suíte depois da reformatação automática do `ruff-format` no commit (que só quebrou
duas linhas), permanecendo em 171.

## Arquivos alterados

- Criado: `publicar-backlog-demanda-azure-boards/src/publicar_backlog_demanda_azure_boards/leitor_demanda.py`
- Criado: `publicar-backlog-demanda-azure-boards/tests/test_leitor_demanda.py`
- `cliente_azure_devops.py`: **não alterado**.
- Os quatro arquivos protegidos por `test_sincronia_com_origem.py`
  (`contrato_backlog.py`, `converter_para_html.py`, `interpretar_markdown.py`,
  `validacao_estrutural.py`) não foram tocados.

## Commit

`9749733 feat: le a Demanda de Negocio para derivar o destino`

(Uma primeira tentativa de commit foi interrompida pelo hook `ruff-format`, que reformatou
duas quebras de linha no arquivo novo antes de eu reexecutar os testes — ainda 171 passando —
e recommitar; nenhum commit corrompido ficou no histórico.)

## Achados da autorrevisão

- **Completude:** todas as validações da checklist têm teste, exceto "URL inutilizável"
  (a validação existe no código, mas não há teste dedicado no conjunto prescrito pelo
  brief — ver observação acima).
- **Qualidade das mensagens de erro:** todas dizem o que aconteceu (tipo incorreto, projeto
  incorreto, campo ausente, ID inválido, falha de leitura) de forma consistente com o estilo
  já usado em `cliente_azure_devops.py`. Nenhuma mensagem inclui o token, a credencial `Basic`
  ou qualquer dado sensível — verificado por teste dedicado
  (`test_nao_expoe_o_token_na_mensagem_de_erro`) e por leitura visual do código: a variável
  `credencial` só é usada no header HTTP, nunca interpolada em string de erro.
- **Disciplina de escopo:** não toquei `cli.py`, `configuracao.py`, `manifesto.py` nem
  `validar_operacao`; não mexi em `ConfiguracaoAzureDevOps` nem na property `publicacao`;
  não promovi `_verificar_status` (não era necessário); não dupliquei lógica de status.
- **Testes:** todo transporte é `httpx.MockTransport`; nenhuma chamada de rede real. Saída da
  suíte sem warnings.

## Preocupações

Nenhuma preocupação bloqueante. Único ponto de atenção: a ausência de um teste específico
para "URL inutilizável" na Demanda, decorrente de seguir o conjunto de testes do brief
literalmente. Se a Task 10 ou uma revisão posterior quiser essa cobertura explícita, é uma
adição pontual e de baixo risco (um `_payload(url="não-é-https")` mais uma asserção).

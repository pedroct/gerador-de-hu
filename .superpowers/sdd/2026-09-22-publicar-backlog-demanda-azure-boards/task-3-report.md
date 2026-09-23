# Task 3: Módulo de numeração hierárquica — Relatório

## Implementação

Criei o módulo `titulo_hierarquico.py` com dois componentes principais:

1. **`numerar(chave: str) -> str`**: Converte uma chave documental no formato `E.F.S` (Épico.Feature.Story) para a numeração hierárquica usada no título, descartando os níveis finais iguais a zero. Exemplos:
   - `"1.0.0"` → `"01"` (apenas Épico)
   - `"1.1.0"` → `"01.01"` (Épico e Feature)
   - `"1.1.1"` → `"01.01.01"` (Épico, Feature e Story)

2. **`montar_titulo(item: ItemBacklog) -> str`**: Compõe o título final concatenando a numeração hierárquica com o texto do item, usando `titulo_curto` quando disponível e caindo para `titulo` caso contrário.

## Testes e Resultados

### Evidência RED (Falha inicial)

**Comando:**
```bash
cd /Volumes/DOCK/Projetos/pessoal/gerador-hu/.claude/worktrees/publicar-backlog-demanda/publicar-backlog-demanda-azure-boards
uv run pytest tests/test_titulo_hierarquico.py -v
```

**Saída de falha:**
```
ImportError while importing test module '.../test_titulo_hierarquico.py'.
...
E   ModuleNotFoundError: No module named 'publicar_backlog_demanda_azure_boards.titulo_hierarquico'
```

**Por que falhou:** O módulo ainda não existia, então a importação não pôde ser completada durante a coleta de testes.

### Evidência GREEN (Implementação bem-sucedida)

**Comando:**
```bash
cd /Volumes/DOCK/Projetos/pessoal/gerador-hu/.claude/worktrees/publicar-backlog-demanda/publicar-backlog-demanda-azure-boards
uv run pytest tests/test_titulo_hierarquico.py -v
```

**Saída de sucesso:**
```
============================= test session starts ==============================
collected 17 items

tests/test_titulo_hierarquico.py::test_numerar_converte_a_chave_documental[1.0.0-01] PASSED [  5%]
tests/test_titulo_hierarquico.py::test_numerar_converte_a_chave_documental[1.1.0-01.01] PASSED [ 11%]
tests/test_titulo_hierarquico.py::test_numerar_converte_a_chave_documental[1.1.1-01.01.01] PASSED [ 17%]
tests/test_titulo_hierarquico.py::test_numerar_converte_a_chave_documental[2.3.4-02.03.04] PASSED [ 23%]
tests/test_titulo_hierarquico.py::test_numerar_converte_a_chave_documental[10.0.0-10] PASSED [ 29%]
tests/test_titulo_hierarquico.py::test_numerar_converte_a_chave_documental[10.11.12-10.11.12] PASSED [ 35%]
tests/test_titulo_hierarquico.py::test_numerar_converte_a_chave_documental[100.0.0-100] PASSED [ 41%]
tests/test_titulo_hierarquico.py::test_numerar_converte_a_chave_documental[1.1.112-01.01.112] PASSED [ 47%]
tests/test_titulo_hierarquico.py::test_numerar_rejeita_chave_fora_do_contrato[] PASSED [ 52%]
tests/test_titulo_hierarquico.py::test_numerar_rejeita_chave_fora_do_contrato[1] PASSED [ 58%]
tests/test_titulo_hierarquico.py::test_numerar_rejeita_chave_fora_do_contrato[1.1] PASSED [ 64%]
tests/test_titulo_hierarquico.py::test_numerar_rejeita_chave_fora_do_contrato[1.1.1.1] PASSED [ 70%]
tests/test_titulo_hierarquico.py::test_numerar_rejeita_chave_fora_do_contrato[a.b.c] PASSED [ 76%]
tests/test_titulo_hierarquico.py::test_numerar_rejeita_chave_fora_do_contrato[1.-1.0] PASSED [ 82%]
tests/test_titulo_hierarquico.py::test_montar_titulo_usa_o_titulo_curto_quando_existe PASSED [ 88%]
tests/test_titulo_hierarquico.py::test_montar_titulo_cai_no_titulo_longo_sem_titulo_curto PASSED [ 94%]
tests/test_titulo_hierarquico.py::test_montar_titulo_nao_inclui_data PASSED [100%]

============================== 17 passed in 0.02s ==============================
```

## Arquivos Alterados

1. **Criado:** `/Volumes/DOCK/Projetos/pessoal/gerador-hu/.claude/worktrees/publicar-backlog-demanda/publicar-backlog-demanda-azure-boards/src/publicar_backlog_demanda_azure_boards/titulo_hierarquico.py`
   - Módulo com as funções `numerar` e `montar_titulo`
   - Tipagem completa para `mypy --strict`
   - Docstrings em português

2. **Criado:** `/Volumes/DOCK/Projetos/pessoal/gerador-hu/.claude/worktrees/publicar-backlog-demanda/publicar-backlog-demanda-azure-boards/tests/test_titulo_hierarquico.py`
   - Suite de 17 testes parametrizados
   - Cobre conversão hierárquica, validação de chaves e montagem de títulos

## Autorrevisão

- **Completude:** Implementei exatamente tudo que o brief especificava. Os testes cobrem todos os casos de borda: zeros finais, largura mínima, rejeição de chaves malformadas, uso de `titulo_curto` vs `titulo`.
- **Qualidade:** Nomes claros (`numerar`, `montar_titulo`), tipagem completa, docstrings descritivas. O módulo segue os padrões já estabelecidos no pacote (`from __future__ import annotations`, estrutura das docstrings, forma dos erros).
- **Disciplina:** Evitei escrever além do pedido. O módulo tem uma responsabilidade clara: converter chave documental em numeração hierárquica e montar títulos.
- **Testes:** Todos os 17 testes passam. Sem warnings. A suite cobre:
  - 8 casos parametrizados de `numerar` com diferentes formatos
  - 6 casos parametrizados de rejeição de chaves malformadas
  - 3 casos de `montar_titulo` (com curto, sem curto, sem data)

## Validação com Linters

Todos os verificadores pré-commit passaram:
- **ruff (lint + format):** All checks passed
- **mypy (strict):** Success: no issues found in 1 source file
- **bandit (SAST):** No issues identified

## Commits Criados

- `1768065` feat: numera titulos no formato hierarquico do board

## Sem Preocupações

O módulo está pronto para a Task 4, que vai integrá-lo em `planejar_publicacao.py` para substituir a montagem anterior do título.

# Task 2: Teste de Sincronia com a Skill de Origem — Relatório de Conclusão

## Resumo Executivo

Task 2 implementada com sucesso. Todos os 4 steps completados, incluindo prova de que o teste detecta divergências.

## Implementação Detalhada

### Step 1: Escrever o teste

Arquivo criado: `/Volumes/DOCK/Projetos/pessoal/gerador-hu/.claude/worktrees/publicar-backlog-demanda/publicar-backlog-demanda-azure-boards/tests/test_sincronia_com_origem.py`

Conteúdo: Código exato do brief, contendo:
- Constante `MODULOS_ESPELHADOS: tuple[str, ...]` com os 4 módulos a ser sincronizados
- Função parametrizada `test_modulo_espelhado_e_identico_ao_da_origem` que compara cada módulo contra a origem
- Normalização de nome de pacote com `.replace("publicar_backlog_azure_boards", "publicar_backlog_demanda_azure_boards")`
- Verificação de existência: `test_modulos_espelhados_existem_no_pacote_local`

### Step 2: Rodar e confirmar que passa

```bash
cd /Volumes/DOCK/Projetos/pessoal/gerador-hu/.claude/worktrees/publicar-backlog-demanda/publicar-backlog-demanda-azure-boards
uv run pytest tests/test_sincronia_com_origem.py -v
```

**Resultado:**
```
============================= test session starts ==============================
5 collected items

tests/test_sincronia_com_origem.py::test_modulo_espelhado_e_identico_ao_da_origem[contrato_backlog.py] PASSED [ 20%]
tests/test_sincronia_com_origem.py::test_modulo_espelhado_e_identico_ao_da_origem[converter_para_html.py] PASSED [ 40%]
tests/test_sincronia_com_origem.py::test_modulo_espelhado_e_identico_ao_da_origem[interpretar_markdown.py] PASSED [ 60%]
tests/test_sincronia_com_origem.py::test_modulo_espelhado_e_identico_ao_da_origem[validacao_estrutural.py] PASSED [ 80%]
tests/test_sincronia_com_origem.py::test_modulos_espelhados_existem_no_pacote_local PASSED [100%]

============================== 5 passed in 0.01s ===============================
```

**Confirmado:** PASS nos cinco casos (quatro parametrizados + um de existência).

### Step 3: Provar que o teste realmente pega uma divergência

#### 3a. Introduzir divergência proposital

```bash
printf '\n# divergência proposital\n' >> src/publicar_backlog_demanda_azure_boards/contrato_backlog.py
```

#### 3b. Executar teste (deve falhar)

```bash
cd /Volumes/DOCK/Projetos/pessoal/gerador-hu/.claude/worktrees/publicar-backlog-demanda/publicar-backlog-demanda-azure-boards
uv run pytest tests/test_sincronia_com_origem.py -v
```

**Resultado de FALHA:**
```
============================= test session starts ==============================
5 collected items

tests/test_sincronia_com_origem.py::test_modulo_espelhado_e_identico_ao_da_origem[contrato_backlog.py] FAILED [ 20%]
tests/test_sincronia_com_origem.py::test_modulo_espelhado_e_identico_ao_da_origem[converter_para_html.py] PASSED [ 40%]
tests/test_sincronia_com_origem.py::test_modulo_espelhado_e_identico_ao_da_origem[interpretar_markdown.py] PASSED [ 60%]
tests/test_sincronia_com_origem.py::test_modulo_espelhado_e_identico_ao_da_origem[validacao_estrutural.py] PASSED [ 80%]
tests/test_sincronia_com_origem.py::test_modulos_espelhados_existem_no_pacote_local PASSED [100%]

=================================== FAILURES ===================================
______ test_modulo_espelhado_e_identico_ao_da_origem[contrato_backlog.py] ______

modulo = 'contrato_backlog.py'
...
>       assert local.read_text(encoding="utf-8") == esperado, (
            f"{modulo} divergiu da skill de origem. Ressincronize os dois lados antes de prosseguir."
        )
E       AssertionError: contrato_backlog.py divergiu da skill de origem. Ressincronize os dois lados antes de prosseguir.
...
tests/test_sincronia_com_origem.py:34: AssertionError
========================= 1 failed, 4 passed in 0.02s =========================
```

**Confirmado:** FAIL com mensagem exata "divergiu da skill de origem".

#### 3c. Desfazer divergência

```bash
git checkout -- publicar-backlog-demanda-azure-boards/src/publicar_backlog_demanda_azure_boards/contrato_backlog.py
```

#### 3d. Executar teste (deve passar novamente)

```bash
cd /Volumes/DOCK/Projetos/pessoal/gerador-hu/.claude/worktrees/publicar-backlog-demanda/publicar-backlog-demanda-azure-boards
uv run pytest tests/test_sincronia_com_origem.py -q
```

**Resultado de PASSE:**
```
.....                                                                    [100%]
5 passed in 0.01s
```

**Confirmado:** PASS de novo após desfazer a divergência.

### Step 4: Commit

```bash
git add publicar-backlog-demanda-azure-boards/tests/test_sincronia_com_origem.py
git commit -m "test: guarda os modulos de copia literal contra divergencia"
```

**Resultado:**
```
[feat/publicar-backlog-demanda-azure-boards 1559aa3] test: guarda os modulos de copia literal contra divergencia
 1 file changed, 41 insertions(+)
 create mode 100644 publicar-backlog-demanda-azure-boards/tests/test_sincronia_com_origem.py
```

**Commit SHA:** `1559aa3`

**Hooks passaram:** ruff, mypy, bandit, commitizen ✓

## Autorrevisão

### Completude
- ✓ Step 1: Teste escrito com código exato do brief
- ✓ Step 2: Todos os 5 testes passaram (4 parametrizados + 1 de existência)
- ✓ Step 3: Teste realmente falha com divergência proposital, passa após desfazer
- ✓ Step 4: Commit criado e passou em todos os hooks

### Qualidade de Testes
- ✓ Suíte completa em verde: 131 testes passaram (126 originais + 5 novos)
- ✓ Nenhum warning ou mensagem de erro
- ✓ Árvore de trabalho limpa após todas as operações

### Disciplina
- ✓ Apenas o arquivo de teste foi adicionado (sem construções extras)
- ✓ Código é exatamente como especificado no brief
- ✓ Mensagem de commit segue Conventional Commits
- ✓ Nenhuma alteração em arquivos fora do escopo

## Arquivos Alterados

- **Criado:** `publicar-backlog-demanda-azure-boards/tests/test_sincronia_com_origem.py` (41 linhas)

## Nenhuma Preocupação

Implementação limpa, completa e validada. Teste comprova sua própria eficácia ao detectar divergências.

## Tarefa 6: `Azure Boards ID` — leitura e recusas

**Arquivos:**
- Modificar: `contrato_backlog.py`, `interpretar_markdown.py`, `modelos.py` em ambos
- Testar: `tests/test_contrato_id_existente.py` (novo) em ambos

**Interfaces:**
- Consome: `ItemBacklog` das tarefas anteriores.
- Produz: `ItemBacklog.azure_boards_id: int | None = None` e
  `normalizar_id(bruto) -> tuple[int | None, list[str]]`.

- [ ] **Passo 1: escrever os testes que falham**

```python
import pytest

from publicar_backlog_azure_boards.contrato_backlog import normalizar_id, validate_backlog


def test_secao_ausente_devolve_none() -> None:
    assert normalizar_id("") == (None, [])


def test_le_id_entre_crases() -> None:
    assert normalizar_id("`4721`") == (4721, [])


@pytest.mark.parametrize("bruto", ["`abc`", "`0`", "`-3`", "`47.21`", "`47 21`"])
def test_recusa_id_que_nao_e_inteiro_positivo(bruto: str) -> None:
    valor, erros = normalizar_id(bruto)

    assert valor is None
    assert erros == [f"'{bruto.strip('`')}' não é um ID de work item inteiro e positivo"]


def test_recusa_id_em_item_de_folha() -> None:
    erros = validate_backlog(BACKLOG_COM_ID_NA_HISTORIA)

    assert any("1.1.1 declara Azure Boards ID, permitido só em Epic e Feature" in e for e in erros)


def test_recusa_feature_com_id_sob_epic_sem_id() -> None:
    erros = validate_backlog(BACKLOG_FEATURE_COM_ID_EPIC_SEM)

    assert any(
        "1.1.0 declara Azure Boards ID, mas seu pai 1.0.0 não declara" in erro for erro in erros
    )
```

As duas constantes vão no topo do arquivo:

```python
BACKLOG_COM_ID_NA_HISTORIA = """# Backlog para Azure Boards

## Metadados e cobertura
- Data de geração: `2026-09-25`

## 1.0.0 [Epic] Épico

### Description
Origem na spec: seção 1

### 1.1.0 [Feature] Feature

#### Parent
`1.0.0`

#### Description
Origem na spec: seção 1

#### 1.1.1 [User Story] História

##### Parent
`1.1.0`

##### Description
Origem na spec: seção 1

##### Azure Boards ID
`4721`

##### Acceptance Criteria
"""

BACKLOG_FEATURE_COM_ID_EPIC_SEM = """# Backlog para Azure Boards

## Metadados e cobertura
- Data de geração: `2026-09-25`

## 1.0.0 [Epic] Épico

### Description
Origem na spec: seção 1

### 1.1.0 [Feature] Feature

#### Parent
`1.0.0`

#### Azure Boards ID
`4722`

#### Description
Origem na spec: seção 1
"""
```

Replique o arquivo inteiro no pacote de Demanda, trocando só o import.

- [ ] **Passo 2: rodar para confirmar que falham**

```bash
cd publicar-backlog-azure-boards && uv run pytest tests/test_contrato_id_existente.py -q
```

Esperado: FAIL com `ImportError: cannot import name 'normalizar_id'`.

- [ ] **Passo 3: implementar**

Em `contrato_backlog.py` de ambos:

```python
AZURE_BOARDS_ID = "Azure Boards ID"
CONTAINER_KINDS = ("Epic", "Feature")


def normalizar_id(bruto: str) -> tuple[int | None, list[str]]:
    """Lê o ID de um work item já publicado, recusando qualquer coisa que não seja inteiro positivo.

    Um ID digitado com um dígito a menos aponta para outro work item qualquer, então a
    conversão nunca pode estourar ``ValueError`` cru no meio do planejamento.
    """
    texto = bruto.strip().strip("`").strip()
    if not texto:
        return None, []
    if not texto.isdigit() or int(texto) <= 0:
        return None, [f"'{texto}' não é um ID de work item inteiro e positivo"]
    return int(texto), []
```

com `AZURE_BOARDS_ID` em `SECTION_NAMES` e, em `_validate_item`:

```python
    if AZURE_BOARDS_ID in item.sections:
        valor, erros_id = normalizar_id(item.section(AZURE_BOARDS_ID))
        errors.extend(f"{item.key}: {erro}" for erro in erros_id)
        if item.kind not in CONTAINER_KINDS:
            errors.append(
                f"{item.key} declara Azure Boards ID, permitido só em Epic e Feature"
            )
        elif valor is not None and item.kind == "Feature" and _parent_value(item) not in com_id:
            errors.append(
                f"{item.key} declara Azure Boards ID, mas seu pai "
                f"{_parent_value(item)} não declara"
            )
```

`com_id` é calculado em `validate_backlog` antes do laço e passado a `_validate_item`:

```python
    com_id = {
        item.key
        for item in items
        if AZURE_BOARDS_ID in item.sections and normalizar_id(item.section(AZURE_BOARDS_ID))[0]
    }
```

Em `interpretar_markdown.py`, acrescente `"Azure Boards ID"` a `_SECOES` e:

```python
def _id_existente(item: _ItemEmConstrucao) -> int | None:
    if "Azure Boards ID" not in item.secoes:
        return None
    valor, erros = normalizar_id(item.texto_secao("Azure Boards ID"))
    if erros:
        raise ErroContratoMarkdown(f"{item.chave}: {erros[0]}")
    if valor is None:
        raise ErroContratoMarkdown(
            f"{item.chave} possui a seção Azure Boards ID presente e vazia"
        )
    return valor
```

com `azure_boards_id=_id_existente(item)` em `_converter_item`, e o campo em `ItemBacklog`:

```python
    depende_de: tuple[str, ...] = ()
    azure_boards_id: int | None = None
```

- [ ] **Passo 4: rodar e confirmar que passam**

```bash
cd publicar-backlog-azure-boards && uv run pytest -q && uv run mypy src
cd ../publicar-backlog-demanda-azure-boards && uv run pytest -q && uv run mypy src
```

- [ ] **Passo 5: commitar**

```bash
git add publicar-backlog-azure-boards publicar-backlog-demanda-azure-boards
git commit -m "feat: le e valida o Azure Boards ID de item ja publicado"
```

---

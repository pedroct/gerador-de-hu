import pytest

from publicar_backlog_demanda_azure_boards.contrato_backlog import normalizar_id, validate_backlog


def test_secao_ausente_devolve_none() -> None:
    assert normalizar_id("") == (None, [])


def test_le_id_entre_crases() -> None:
    assert normalizar_id("`4721`") == (4721, [])


@pytest.mark.parametrize("bruto", ["`abc`", "`0`", "`-3`", "`47.21`", "`47 21`", "`²³¹`", "`٣`"])
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


def test_recusa_secao_azure_boards_id_presente_e_vazia() -> None:
    """`interpretar_backlog` já recusa; sem esta regra aqui, `validacao_estrutural` devolve
    zero erro e o usuário recebe a recusa isolada do estágio seguinte, fora do agregado."""
    erros = validate_backlog(BACKLOG_FEATURE_COM_ID_VAZIO)

    assert any("1.1.0 possui a seção Azure Boards ID presente e vazia" in e for e in erros)


BACKLOG_FEATURE_COM_ID_VAZIO = BACKLOG_FEATURE_COM_ID_EPIC_SEM.replace("`4722`\n", "")

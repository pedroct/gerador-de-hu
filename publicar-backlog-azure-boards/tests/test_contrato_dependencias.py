from publicar_backlog_azure_boards.contrato_backlog import (
    detectar_ciclo,
    normalizar_chaves,
    validate_backlog,
)


def test_le_uma_chave() -> None:
    assert normalizar_chaves("`1.1.2`") == (("1.1.2",), [])


def test_le_varias_chaves_separadas_por_virgula() -> None:
    chaves, erros = normalizar_chaves("`1.1.2`, `1.1.3`")

    assert chaves == ("1.1.2", "1.1.3")
    assert erros == []


def test_deduplica_chave_repetida() -> None:
    assert normalizar_chaves("`1.1.2`, `1.1.2`")[0] == ("1.1.2",)


def test_recusa_valor_que_nao_e_chave_documental() -> None:
    chaves, erros = normalizar_chaves("`item de design`")

    assert chaves == ()
    assert erros == ["'item de design' não é uma chave documental no formato E.F.S"]


def test_sem_ciclo_devolve_none() -> None:
    assert detectar_ciclo([("1.1.1", ["1.1.2"]), ("1.1.2", [])]) is None


def test_detecta_ciclo_de_dois_itens() -> None:
    ciclo = detectar_ciclo([("1.1.1", ["1.1.2"]), ("1.1.2", ["1.1.1"])])

    assert ciclo is not None
    assert set(ciclo) == {"1.1.1", "1.1.2"}


def test_detecta_ciclo_de_tres_itens() -> None:
    ciclo = detectar_ciclo([("1.1.1", ["1.1.2"]), ("1.1.2", ["1.1.3"]), ("1.1.3", ["1.1.1"])])

    assert ciclo is not None
    assert set(ciclo) == {"1.1.1", "1.1.2", "1.1.3"}


def test_detecta_item_que_depende_de_si_mesmo() -> None:
    assert detectar_ciclo([("1.1.1", ["1.1.1"])]) == ["1.1.1"]


BACKLOG = """# Backlog para Azure Boards

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

##### Depende de
{depende_de}

##### Acceptance Criteria
"""


def test_recusa_dependencia_para_chave_inexistente() -> None:
    erros = validate_backlog(BACKLOG.format(depende_de="`9.9.9`"))

    assert any("1.1.1 depende de 9.9.9, que não existe no backlog" in erro for erro in erros)


def test_recusa_dependencia_para_item_que_nao_e_folha() -> None:
    erros = validate_backlog(BACKLOG.format(depende_de="`1.1.0`"))

    assert any("1.1.1 depende de 1.1.0, que não é item de folha" in erro for erro in erros)


BACKLOG_COM_DUAS_FOLHAS = """# Backlog para Azure Boards

## Metadados e cobertura
- Data de geração: `2026-09-25`

## 1.0.0 [Epic] Épico
{depende_de_epic}
### Description
Origem na spec: seção 1

### 1.1.0 [Feature] Feature
{depende_de_feature}
#### Parent
`1.0.0`

#### Description
Origem na spec: seção 1

#### 1.1.1 [User Story] História
{depende_de_leaf}
##### Parent
`1.1.0`

##### Description
Origem na spec: seção 1

##### Acceptance Criteria

#### 1.1.2 [User Story] Outra história

##### Parent
`1.1.0`

##### Description
Origem na spec: seção 1

##### Acceptance Criteria
"""


def test_recusa_dependencia_declarada_em_feature() -> None:
    erros = validate_backlog(
        BACKLOG_COM_DUAS_FOLHAS.format(
            depende_de_epic="",
            depende_de_feature="#### Depende de\n`1.1.2`\n",
            depende_de_leaf="",
        )
    )

    assert any("1.1.0 declara Depende de, permitido só em item de folha" in erro for erro in erros)


def test_recusa_dependencia_declarada_em_epic() -> None:
    erros = validate_backlog(
        BACKLOG_COM_DUAS_FOLHAS.format(
            depende_de_epic="### Depende de\n`1.1.2`\n",
            depende_de_feature="",
            depende_de_leaf="",
        )
    )

    assert any("1.0.0 declara Depende de, permitido só em item de folha" in erro for erro in erros)


def test_folha_com_dependencia_continua_aceita() -> None:
    erros = validate_backlog(
        BACKLOG_COM_DUAS_FOLHAS.format(
            depende_de_epic="",
            depende_de_feature="",
            depende_de_leaf="##### Depende de\n`1.1.2`\n",
        )
    )

    assert erros == []

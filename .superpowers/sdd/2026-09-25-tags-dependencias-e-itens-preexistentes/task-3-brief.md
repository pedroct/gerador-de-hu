## Tarefa 3: `Depende de` — leitura e recusas do contrato

**Arquivos:**
- Modificar: `contrato_backlog.py` e `interpretar_markdown.py` em ambos os pacotes
- Modificar: `modelos.py` em ambos (campo `depende_de`)
- Testar: `tests/test_contrato_dependencias.py` (novo) em ambos

**Interfaces:**
- Consome: `ItemBacklog` da Tarefa 2.
- Produz: `ItemBacklog.depende_de: tuple[str, ...] = ()`, `normalizar_chaves(bruto) -> (chaves,
  erros)` e `detectar_ciclo(pares: Sequence[tuple[str, Sequence[str]]]) -> list[str] | None`, que
  devolve o ciclo em ordem quando existir. A Tarefa 4 consome `depende_de` para ordenar.

- [ ] **Passo 1: escrever os testes que falham**

Crie `publicar-backlog-azure-boards/tests/test_contrato_dependencias.py`:

```python
from publicar_backlog_azure_boards.contrato_backlog import detectar_ciclo, normalizar_chaves


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
```

Acrescente ao mesmo arquivo os testes de validação estrutural:

```python
from publicar_backlog_azure_boards.contrato_backlog import validate_backlog

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
```

Replique o arquivo no pacote de Demanda, trocando o import.

- [ ] **Passo 2: rodar para confirmar que falham**

```bash
cd publicar-backlog-azure-boards && uv run pytest tests/test_contrato_dependencias.py -q
```

Esperado: FAIL com `ImportError: cannot import name 'detectar_ciclo'`.

- [ ] **Passo 3: implementar**

Em `contrato_backlog.py` de ambos os pacotes:

```python
DEPENDE_DE = "Depende de"
CHAVE_RE = re.compile(r"^[1-9]\d*\.\d+\.\d+$")

SECTION_NAMES = {
    "Parent",
    "Título curto",
    "Description",
    "Acceptance Criteria",
    "Refinement Status",
    TAGS,
    DEPENDE_DE,
}


def normalizar_chaves(bruto: str) -> tuple[tuple[str, ...], list[str]]:
    """Normaliza uma lista de chaves documentais separadas por vírgula."""
    texto = bruto.strip()
    if not texto:
        return (), []

    erros: list[str] = []
    chaves: list[str] = []
    for parte in texto.split(","):
        chave = parte.strip().strip("`").strip()
        if not chave:
            erros.append("a seção Depende de possui uma chave vazia entre vírgulas")
            continue
        if not CHAVE_RE.match(chave):
            erros.append(f"'{chave}' não é uma chave documental no formato E.F.S")
            continue
        if chave not in chaves:
            chaves.append(chave)

    if erros:
        return (), erros
    return tuple(chaves), []


def detectar_ciclo(pares: Sequence[tuple[str, Sequence[str]]]) -> list[str] | None:
    """Devolve o ciclo de dependências encontrado, em ordem, ou ``None``.

    Um item que depende de si mesmo é um ciclo de um nó e precisa ser pego aqui:
    uma detecção que só compare pares distintos deixa esse caso passar.
    """
    arestas = {chave: list(destinos) for chave, destinos in pares}
    estado: dict[str, int] = {}
    pilha: list[str] = []

    def visitar(chave: str) -> list[str] | None:
        if estado.get(chave) == 2:
            return None
        if estado.get(chave) == 1:
            return pilha[pilha.index(chave) :]
        estado[chave] = 1
        pilha.append(chave)
        for destino in arestas.get(chave, []):
            ciclo = visitar(destino)
            if ciclo is not None:
                return ciclo
        pilha.pop()
        estado[chave] = 2
        return None

    for chave in arestas:
        ciclo = visitar(chave)
        if ciclo is not None:
            return ciclo
    return None
```

Acrescente `from collections.abc import Sequence` ao topo. Em `_validate_item`:

```python
    if DEPENDE_DE in item.sections:
        chaves, erros_chaves = normalizar_chaves(item.section(DEPENDE_DE))
        errors.extend(f"{item.key}: {erro}" for erro in erros_chaves)
        for chave in chaves:
            if chave not in keys:
                errors.append(f"{item.key} depende de {chave}, que não existe no backlog")
            elif chave not in folhas:
                errors.append(f"{item.key} depende de {chave}, que não é item de folha")
```

`folhas` é calculado uma vez em `validate_backlog` e passado a `_validate_item`:

```python
    folhas = {item.key for item in items if item.kind in LEAF_KINDS}
```

e ao fim de `validate_backlog`, antes do `return`:

```python
    ciclo = detectar_ciclo(
        [(item.key, normalizar_chaves(item.section(DEPENDE_DE))[0]) for item in items]
    )
    if ciclo is not None:
        errors.append(f"ciclo de dependência entre {' → '.join(ciclo)}")
```

Em `interpretar_markdown.py`, acrescente `"Depende de"` a `_SECOES`, e:

```python
def _dependencias_do_item(item: _ItemEmConstrucao) -> tuple[str, ...]:
    if "Depende de" not in item.secoes:
        return ()
    chaves, erros = normalizar_chaves(item.texto_secao("Depende de"))
    if erros:
        raise ErroContratoMarkdown(f"{item.chave}: {erros[0]}")
    if not chaves:
        raise ErroContratoMarkdown(f"{item.chave} possui a seção Depende de presente e vazia")
    return chaves
```

com `depende_de=_dependencias_do_item(item)` em `_converter_item`, e o campo em `modelos.py`:

```python
    tags: tuple[str, ...] = ()
    depende_de: tuple[str, ...] = ()
```

- [ ] **Passo 4: rodar e confirmar que passam**

```bash
cd publicar-backlog-azure-boards && uv run pytest -q && uv run mypy src
cd ../publicar-backlog-demanda-azure-boards && uv run pytest -q && uv run mypy src
```

Esperado: PASS nos dois.

- [ ] **Passo 5: commitar**

```bash
git add publicar-backlog-azure-boards publicar-backlog-demanda-azure-boards
git commit -m "feat: le e valida a secao Depende de no contrato do backlog"
```

---

## Tarefa 2a: `Tags` do Markdown até `ItemBacklog`

Metade da Tarefa 2 do plano. Entrega: um backlog Markdown com a seção `Tags` é lido em
`ItemBacklog.tags`, e os dois validadores recusam os formatos inválidos. Nada de payload, plano ou
hash — isso é da Tarefa 2b.

**Arquivos:**
- Modificar: `modelos.py`, `interpretar_markdown.py` e `contrato_backlog.py` em **ambos** os pacotes
- Testar: `tests/test_interpretar_markdown.py` e `tests/test_contrato_tags.py` em ambos

**Interfaces:**
- Consome: `normalizar_tags(bruto) -> (tags, erros)`, `TAGS`, `LIMITE_TAG` — já existem em
  `contrato_backlog.py` dos dois pacotes, entregues pela Tarefa 1.
- Produz: `ItemBacklog.tags: tuple[str, ...] = ()`. A Tarefa 2b a propaga para `OperacaoCriacao` e
  para o payload.

- [ ] **Passo 1: escrever os testes que falham**

Acrescente a `tests/test_interpretar_markdown.py`:

```python
def test_le_tags_declaradas_no_item(tmp_path: Path):
    caminho = tmp_path / "backlog.md"
    caminho.write_text(
        "# Backlog para Azure Boards\n\n## Metadados e cobertura\n"
        "- Data de geração: `2026-09-25`\n\n"
        "## 1.0.0 [Epic] Épico\n\n### Description\nTexto\n\n"
        "### 1.1.0 [Feature] Feature\n\n#### Parent\n`1.0.0`\n\n#### Description\nTexto\n\n"
        "#### 1.1.1 [User Story] História\n\n##### Parent\n`1.1.0`\n\n"
        "##### Description\nTexto\n\n##### Tags\ndebito-tecnico, dt-restricao\n\n"
        "##### Acceptance Criteria\n",
        encoding="utf-8",
    )

    itens = interpretar_backlog(caminho)

    assert itens[-1].tags == ("debito-tecnico", "dt-restricao")


def test_item_sem_secao_tags_fica_com_tupla_vazia():
    itens = interpretar_backlog(Path("tests/fixtures/valid-backlog.md"))

    assert itens[0].tags == ()


def test_rejeita_secao_tags_presente_e_vazia(tmp_path: Path):
    caminho = tmp_path / "backlog.md"
    caminho.write_text(
        "# Backlog para Azure Boards\n\n## Metadados e cobertura\n"
        "- Data de geração: `2026-09-25`\n\n"
        "## 1.0.0 [Epic] Épico\n\n### Description\nTexto\n\n### Tags\n\n",
        encoding="utf-8",
    )

    with pytest.raises(ErroContratoMarkdown, match="Tags"):
        interpretar_backlog(caminho)
```

Acrescente a `tests/test_contrato_tags.py` os testes do caminho de validação estrutural, que o
plano original não cobria:

```python
from publicar_backlog_azure_boards.contrato_backlog import validate_backlog

BACKLOG_COM_TAGS = """# Backlog para Azure Boards

## Metadados e cobertura
- Data de geração: `2026-09-25`

## 1.0.0 [Epic] Épico

### Description
Origem na spec: seção 1

### Tags
{tags}
"""


def test_validacao_aceita_tags_bem_formadas() -> None:
    erros = validate_backlog(BACKLOG_COM_TAGS.format(tags="debito-tecnico, dt-restricao"))

    assert not any("Tags" in erro for erro in erros)


def test_validacao_recusa_secao_tags_presente_e_vazia() -> None:
    erros = validate_backlog(BACKLOG_COM_TAGS.format(tags=""))

    assert any("1.0.0 possui a seção Tags presente e vazia" in erro for erro in erros)


def test_validacao_propaga_o_erro_de_formato_com_a_chave_do_item() -> None:
    erros = validate_backlog(BACKLOG_COM_TAGS.format(tags="debito;tecnico"))

    assert any(erro.startswith("1.0.0: a tag 'debito;tecnico' contém ';'") for erro in erros)
```

Garanta que `pytest` e `ErroContratoMarkdown` estejam importados onde cada arquivo precisa.
Replique tudo no pacote de Demanda, trocando só o import.

- [ ] **Passo 2: rodar para confirmar que falham**

```bash
cd publicar-backlog-azure-boards && uv run pytest tests/test_interpretar_markdown.py tests/test_contrato_tags.py -q
```

Esperado: FAIL com `AttributeError: 'ItemBacklog' object has no attribute 'tags'`.

- [ ] **Passo 3: implementar**

Em `modelos.py`, o campo vai para o **fim** do dataclass, com default — os testes constroem
`ItemBacklog` posicionalmente e inserir no meio quebra a suíte:

```python
@dataclass(frozen=True)
class ItemBacklog:
    """Representa os campos copiáveis de um item do backlog Markdown."""

    chave: str
    tipo: TipoItem
    titulo: str
    pai: str | None
    descricao: str
    criterios_aceitacao: str
    titulo_curto: str = ""
    tags: tuple[str, ...] = ()
```

Em `interpretar_markdown.py`, acrescente `"Tags"` a `_SECOES` preservando as entradas existentes,
importe a regra e use-a:

```python
from publicar_backlog_azure_boards.contrato_backlog import normalizar_tags

_SECOES = {
    "Parent",
    "Título curto",
    "Description",
    "Acceptance Criteria",
    "Refinement Status",
    "Tags",
}


def _tags_do_item(item: _ItemEmConstrucao) -> tuple[str, ...]:
    if "Tags" not in item.secoes:
        return ()
    tags, erros = normalizar_tags(item.texto_secao("Tags"))
    if erros:
        raise ErroContratoMarkdown(f"{item.chave}: {erros[0]}")
    if not tags:
        raise ErroContratoMarkdown(f"{item.chave} possui a seção Tags presente e vazia")
    return tags
```

e passe `tags=_tags_do_item(item)` em `_converter_item`.

Em `contrato_backlog.py`, acrescente ao fim de `_validate_item`:

```python
    if TAGS in item.sections:
        tags, erros_tags = normalizar_tags(item.section(TAGS))
        errors.extend(f"{item.key}: {erro}" for erro in erros_tags)
        if not tags and not erros_tags:
            errors.append(f"{item.key} possui a seção Tags presente e vazia")
```

**A fixture `tests/fixtures/valid-backlog.md` NÃO muda.** Ela permanece sem a seção `Tags`, e é
exatamente isso que `test_item_sem_secao_tags_fica_com_tupla_vazia` afirma.

- [ ] **Passo 4: rodar a suíte inteira dos dois pacotes**

```bash
cd publicar-backlog-azure-boards && uv run pytest -q && uv run ruff check . && uv run ruff format --check . && uv run mypy src
cd ../publicar-backlog-demanda-azure-boards && uv run pytest -q && uv run ruff check . && uv run ruff format --check . && uv run mypy src
```

Esperado: PASS em tudo, incluindo os 139 e 231 testes que já passavam.

- [ ] **Passo 5: commitar**

```bash
git add publicar-backlog-azure-boards publicar-backlog-demanda-azure-boards
git commit -m "feat: le a secao Tags do backlog em ItemBacklog"
```

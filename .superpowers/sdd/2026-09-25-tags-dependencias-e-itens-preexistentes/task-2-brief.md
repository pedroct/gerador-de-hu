## Tarefa 2: `Tags` do Markdown até o payload

**Arquivos:**
- Modificar: `interpretar_markdown.py`, `modelos.py`, `planejar_publicacao.py`,
  `cliente_azure_devops.py` e `contrato_backlog.py` em **ambos** os pacotes
- Modificar: `publicar-backlog-azure-boards/tests/fixtures/valid-backlog.md`
- Testar: `tests/test_interpretar_markdown.py`, `tests/test_planejar_publicacao.py`,
  `tests/test_cliente_azure_devops.py` em ambos

**Interfaces:**
- Consome: `normalizar_tags(bruto) -> (tags, erros)` da Tarefa 1.
- Produz: `ItemBacklog.tags: tuple[str, ...]` e `OperacaoCriacao.tags: tuple[str, ...]`, ambos com
  default `()`. A Tarefa 4 acrescenta `depende_de` ao lado, e a Tarefa 7 acrescenta
  `azure_boards_id`; as três respeitam a ordem "campo novo vai para o fim, com default".

- [ ] **Passo 1: escrever os testes que falham**

Acrescente a `publicar-backlog-azure-boards/tests/test_interpretar_markdown.py`:

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

Acrescente a `tests/test_planejar_publicacao.py`:

```python
def test_operacao_propaga_tags_do_item() -> None:
    itens = [replace(ITENS[0], tags=("debito-tecnico",)), ITENS[1], ITENS[2]]

    plano = criar_plano(itens, CONFIGURACAO, DATA_GERACAO)

    assert plano.operacoes[-1].tags == ("debito-tecnico",)


def test_hash_muda_quando_ha_tags() -> None:
    com_tags = [replace(ITENS[0], tags=("debito-tecnico",)), ITENS[1], ITENS[2]]

    assert (
        criar_plano(com_tags, CONFIGURACAO, DATA_GERACAO).hash_plano
        != criar_plano(ITENS, CONFIGURACAO, DATA_GERACAO).hash_plano
    )
```

Falta o teste que protege a retomada, e ele precisa do hash **de hoje**, capturado antes de qualquer
mudança em `_calcular_hash`. Rode primeiro:

```bash
cd publicar-backlog-azure-boards && uv run python -c "
from publicar_backlog_azure_boards.modelos import ConfiguracaoPublicacao, ItemBacklog, TipoItem
from publicar_backlog_azure_boards.planejar_publicacao import criar_plano
configuracao = ConfiguracaoPublicacao('organizacao', 'projeto', 'projeto', 'projeto\\\\Sprint 18')
itens = [
    ItemBacklog('1.1.1', TipoItem.HISTORIA_USUARIO, 'História', '1.1.0', 'Descrição', ''),
    ItemBacklog('1.1.0', TipoItem.FEATURE, 'Feature', '1.0.0', 'Descrição', ''),
    ItemBacklog('1.0.0', TipoItem.EPIC, 'Épico', None, 'Descrição', ''),
]
print(criar_plano(itens, configuracao, '2026-09-16').hash_plano)
"
```

Cole o valor impresso em `HASH_ANTES_DOS_CAMPOS_NOVOS`, no topo de `tests/test_planejar_publicacao.py`,
e acrescente o teste:

```python
# Hash produzido pela versão anterior aos campos novos. Ele existe para que um backlog
# sem tags, sem dependências e sem ID declarado continue gerando o mesmo plano — é o que
# permite a toda publicação parcial já gravada retomar. Se este teste falhar, a assimetria
# do hash foi quebrada; não atualize o literal para "consertar".
HASH_ANTES_DOS_CAMPOS_NOVOS = "<cole aqui a saída do comando acima>"


def test_hash_nao_muda_para_backlog_sem_tags() -> None:
    plano = criar_plano(ITENS, CONFIGURACAO, DATA_GERACAO)

    assert plano.hash_plano == HASH_ANTES_DOS_CAMPOS_NOVOS
```

Repita a captura dentro de `publicar-backlog-demanda-azure-boards` — os dois pacotes têm o mesmo
`_calcular_hash`, mas confirme em vez de supor.

Acrescente a `tests/test_cliente_azure_devops.py`:

```python
def test_criacao_envia_tags_unidas_por_ponto_e_virgula() -> None:
    cliente_azure, chamadas = cliente(
        [resposta(200, {"id": 7, "url": "https://dev.azure.com/item/7"})]
    )
    operacao = replace(OPERACAO, tags=("debito-tecnico", "dt-restricao"))

    cliente_azure.criar_item(operacao)

    patch = json.loads(chamadas[0].content)
    campos = {entrada["path"]: entrada["value"] for entrada in patch if "fields" in entrada["path"]}
    assert campos["/fields/System.Tags"] == "debito-tecnico; dt-restricao"


def test_criacao_omite_system_tags_quando_nao_ha_tags() -> None:
    cliente_azure, chamadas = cliente(
        [resposta(200, {"id": 7, "url": "https://dev.azure.com/item/7"})]
    )

    cliente_azure.criar_item(OPERACAO)

    patch = json.loads(chamadas[0].content)
    assert all("System.Tags" not in entrada["path"] for entrada in patch)
```

Acrescente `import json` e `from dataclasses import replace` ao topo desse arquivo de teste, se
ainda não estiverem lá. Replique os três blocos de teste no pacote de Demanda.

- [ ] **Passo 2: rodar para confirmar que falham**

```bash
cd publicar-backlog-azure-boards && uv run pytest tests/test_interpretar_markdown.py tests/test_planejar_publicacao.py tests/test_cliente_azure_devops.py -q
```

Esperado: FAIL com `TypeError: ItemBacklog.__init__() got an unexpected keyword argument 'tags'`.

- [ ] **Passo 3: implementar**

Em `modelos.py`, acrescente o campo ao fim dos dois dataclasses:

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


@dataclass(frozen=True)
class OperacaoCriacao:
    """Representa uma criação planejada, sem executar qualquer escrita."""

    chave: str
    tipo: TipoItem
    titulo: str
    descricao: str
    criterios_aceitacao: str
    chave_pai: str | None
    tipo_remoto: str
    tags: tuple[str, ...] = ()
```

Em `interpretar_markdown.py`, acrescente `"Tags"` a `_SECOES`, importe a regra e use-a:

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

Em `planejar_publicacao.py`, propague em `_criar_operacao` (`tags=item.tags`) e inclua no hash só
quando houver:

```python
def _conteudo_do_item(item: ItemBacklog) -> dict[str, object]:
    conteudo: dict[str, object] = {
        "chave": item.chave,
        "tipo": item.tipo,
        "titulo": item.titulo,
        "titulo_curto": item.titulo_curto,
        "pai": item.pai,
        "descricao": item.descricao,
        "criterios_aceitacao": item.criterios_aceitacao,
    }
    # A chave só entra quando preenchida: um backlog sem campos novos precisa produzir
    # o hash anterior, ou todo manifesto de publicação parcial deixa de retomar. Não
    # "simplifique" incluindo sempre.
    if item.tags:
        conteudo["tags"] = list(item.tags)
    return conteudo
```

e use `_conteudo_do_item(item) for item in itens` dentro de `_calcular_hash`.

Em `cliente_azure_devops.py`, dentro de `_enviar_criacao`, depois da montagem de `patch`:

```python
        if operacao.tags:
            patch.append(
                {"op": "add", "path": "/fields/System.Tags", "value": "; ".join(operacao.tags)}
            )
```

Acrescente ao fim da fixture `tests/fixtures/valid-backlog.md`, no item de folha, nada — a fixture
permanece **sem** `Tags`, e é isso que o teste do hash protege.

- [ ] **Passo 4: rodar a suíte inteira dos dois pacotes**

```bash
cd publicar-backlog-azure-boards && uv run pytest -q && uv run ruff check . && uv run ruff format --check . && uv run mypy src
cd ../publicar-backlog-demanda-azure-boards && uv run pytest -q && uv run ruff check . && uv run ruff format --check . && uv run mypy src
```

Esperado: PASS em tudo. Se algum teste antigo de hash falhar, **pare** — significa que a assimetria
não foi respeitada e a retomada quebrou.

- [ ] **Passo 5: commitar**

```bash
git add publicar-backlog-azure-boards publicar-backlog-demanda-azure-boards
git commit -m "feat: publica System.Tags a partir da secao Tags do backlog"
```

---

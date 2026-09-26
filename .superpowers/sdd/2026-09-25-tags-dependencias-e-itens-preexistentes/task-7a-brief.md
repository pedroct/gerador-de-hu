## Tarefa 7a: item pré-existente no modelo, no plano e no manifesto

Primeira metade da Tarefa 7 do plano. Entrega a **camada de dados**: um item que declara
`Azure Boards ID` deixa de virar operação de criação e passa a ser transportado à parte no plano, e o
manifesto sabe distinguir um registro que veio declarado de um que nós criamos.

A execução (semear `registros`, conferir o item remoto) é a Tarefa 7b. **Não toque em
`executar_publicacao.py` nem em `cliente_azure_devops.py`.**

**Arquivos:**
- Modificar: `modelos.py`, `planejar_publicacao.py` e `manifesto.py` em **ambos** os pacotes
- Testar: `tests/test_planejar_publicacao.py` e `tests/test_manifesto.py` em ambos

**Interfaces:**
- Consome: `ItemBacklog.azure_boards_id: int | None = None`, entregue pela Tarefa 6 e já preenchido
  pelo parser a partir da subseção `Azure Boards ID`.
- Produz, para a Tarefa 7b: `ItemPreexistente(chave, tipo, id)`,
  `PlanoPublicacao.preexistentes: tuple[ItemPreexistente, ...] = ()` e
  `RegistroManifesto.preexistente: bool = False`.

- [ ] **Passo 1: escrever os testes que falham**

Em `tests/test_planejar_publicacao.py`:

```python
def test_item_com_id_declarado_nao_vira_operacao_de_criacao() -> None:
    epic = replace(ITENS[2], azure_boards_id=4721)

    plano = criar_plano([epic, ITENS[1], ITENS[0]], CONFIGURACAO, DATA_GERACAO)

    assert [operacao.chave for operacao in plano.operacoes] == ["1.1.0", "1.1.1"]
    assert plano.preexistentes == (ItemPreexistente("1.0.0", TipoItem.EPIC, 4721),)


def test_plano_sem_id_declarado_nao_tem_preexistentes() -> None:
    plano = criar_plano(ITENS, CONFIGURACAO, DATA_GERACAO)

    assert plano.preexistentes == ()


def test_hash_muda_quando_ha_id_declarado() -> None:
    epic = replace(ITENS[2], azure_boards_id=4721)

    assert (
        criar_plano([epic, ITENS[1], ITENS[0]], CONFIGURACAO, DATA_GERACAO).hash_plano
        != criar_plano(ITENS, CONFIGURACAO, DATA_GERACAO).hash_plano
    )
```

Importe `ItemPreexistente` de `modelos`. Note que `ITENS` é `[1.1.1, 1.1.0, 1.0.0]` — o índice `[2]`
é o Epic.

Em `tests/test_manifesto.py`:

```python
def test_preserva_a_marca_de_preexistente_ao_gravar_e_ler(tmp_path) -> None:
    caminho = tmp_path / "mapa.json"
    original = Manifesto(
        hash_plano="hash",
        configuracao=CONFIGURACAO,
        itens={"1.0.0": RegistroManifesto(4721, TipoItem.EPIC, "https://exemplo/4721", True)},
        titulos={"1.0.0": "2026-09-25 1.0.0 Épico"},
    )

    gravar_manifesto(caminho, original)

    assert ler_manifesto(caminho).itens["1.0.0"].preexistente is True


def test_manifesto_antigo_sem_a_marca_continua_valido(tmp_path) -> None:
    caminho = tmp_path / "mapa.json"
    original = Manifesto(
        hash_plano="hash",
        configuracao=CONFIGURACAO,
        itens={"1.0.0": RegistroManifesto(9, TipoItem.EPIC, "https://exemplo/9")},
        titulos={"1.0.0": "2026-09-25 1.0.0 Épico"},
    )
    gravar_manifesto(caminho, original)
    dados = json.loads(caminho.read_text(encoding="utf-8"))
    del dados["itens"]["1.0.0"]["preexistente"]
    caminho.write_text(json.dumps(dados, ensure_ascii=False), encoding="utf-8")

    assert ler_manifesto(caminho).itens["1.0.0"].preexistente is False
```

O segundo teste grava pelo caminho normal e **remove a chave nova do JSON** antes de reler, o que
reproduz fielmente um manifesto gravado por uma versão anterior — sem precisar montar o dicionário à
mão e arriscar divergir do formato real. Use `CONFIGURACAO` como o arquivo já a define e acrescente
`import json` se necessário.

- [ ] **Passo 2: rodar para confirmar que falham**

```bash
cd publicar-backlog-azure-boards && uv run pytest tests/test_planejar_publicacao.py tests/test_manifesto.py -q
```

Esperado: FAIL com `ImportError` de `ItemPreexistente` e `TypeError` em `RegistroManifesto`.

- [ ] **Passo 3: implementar**

Em `modelos.py`:

```python
@dataclass(frozen=True)
class ItemPreexistente:
    """Item que o backlog declara já publicado, e que esta ferramenta não cria."""

    chave: str
    tipo: TipoItem
    id: int
```

`RegistroManifesto` ganha o campo no fim, com default e comentário:

```python
    # Um registro pré-existente veio declarado no backlog, não de uma criação nossa.
    # Ele serve de pai para os filhos e nada mais: não conta como criação, não entra em
    # reconciliação e não é recriado numa retomada.
    preexistente: bool = False
```

`PlanoPublicacao` ganha `preexistentes: tuple[ItemPreexistente, ...] = ()` **depois** dos campos
existentes. Confira os campos atuais no arquivo antes de editar.

Em `planejar_publicacao.py`, dentro de `criar_plano`, separe antes de montar as operações:

```python
    itens_ordenados = _ordenar_para_criacao(itens)
    preexistentes = tuple(
        ItemPreexistente(item.chave, item.tipo, item.azure_boards_id)
        for item in itens_ordenados
        if item.azure_boards_id is not None
    )
    a_criar = [item for item in itens_ordenados if item.azure_boards_id is None]
    operacoes = tuple(_criar_operacao(item, configuracao, data_geracao) for item in a_criar)
```

passando `preexistentes=preexistentes` ao `PlanoPublicacao`. **`_calcular_hash` continua recebendo
`itens_ordenados`** — todos os itens, inclusive os pré-existentes — e `_conteudo_do_item` ganha mais
uma chave condicional, ao lado de `tags` e `depende_de`:

```python
    if item.azure_boards_id is not None:
        conteudo["azure_boards_id"] = item.azure_boards_id
```

Em `manifesto.py`, inclua `"preexistente": registro.preexistente` na serialização de cada item, e
leia-o de volta com `bool(dados_item.get("preexistente", False))`, para que manifesto antigo continue
válido. Leia `_serializar` e `_converter` antes de editar e siga o formato exato que já está lá.

Se o módulo ou o `cli.py` contar itens criados em algum relatório, exclua os registros com a marca —
um pré-existente nunca foi criado por nós.

- [ ] **Passo 4: rodar a suíte inteira dos dois pacotes**

```bash
cd publicar-backlog-azure-boards && uv run pytest -q && uv run ruff check . && uv run ruff format --check . && uv run mypy src
cd ../publicar-backlog-demanda-azure-boards && uv run pytest -q && uv run ruff check . && uv run ruff format --check . && uv run mypy src
```

`test_hash_nao_muda_para_backlog_sem_tags` precisa continuar verde. Se falhar, **pare e reporte
BLOCKED** — não atualize o literal.

- [ ] **Passo 5: commitar**

```bash
git add publicar-backlog-azure-boards publicar-backlog-demanda-azure-boards
git commit -m "feat: separa item ja publicado das operacoes de criacao"
```

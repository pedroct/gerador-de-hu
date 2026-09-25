# Tags, dependências e itens pré-existentes — Plano de implementação

> **Para trabalhadores agênticos:** SUB-SKILL OBRIGATÓRIA: use superpowers:subagent-driven-development
> (recomendado) ou superpowers:executing-plans para implementar este plano tarefa a tarefa. Os passos
> usam caixas de seleção (`- [ ]`) para acompanhamento.

**Objetivo:** dar ao backlog Markdown três campos novos — `Tags`, `Depende de` e `Azure Boards ID` —
e fazer as duas publicadoras enviarem tags, criarem o link Predecessor/Sucessor e reaproveitarem
Epic/Feature já publicados, sem que nenhum backlog existente deixe de retomar.

**Arquitetura:** as regras de formato de cada campo vivem em funções puras dentro de
`contrato_backlog.py`, consumidas pelos dois parsers que hoje discordam diante de seção desconhecida —
`contrato_backlog` acumula erros em lista, `interpretar_markdown` levanta na primeira. A ordem de
criação passa a ser topológica estável, o que cria o predecessor antes do dependente e permite que o
link entre no payload de criação, sem introduzir no publicador uma operação que não seja criação.

**Pilha:** Python 3.12, pytest 9.0.3, httpx 0.28.1, ruff, mypy strict. Dois pacotes gêmeos,
`publicar-backlog-azure-boards` e `publicar-backlog-demanda-azure-boards`, cada um com seu `uv.lock`.

**Spec:** [docs/superpowers/specs/2026-09-25-tags-de-debito-tecnico-no-backlog-design.md](../specs/2026-09-25-tags-de-debito-tecnico-no-backlog-design.md)

## Restrições globais

- **Todo conteúdo em português brasileiro** — nomes de teste, docstrings, mensagens de erro,
  mensagens de commit. Nomes de campo do Azure Boards (`System.Tags`, `Area Path`) permanecem como a
  API os nomeia.
- **Os dois pacotes mudam na mesma tarefa e no mesmo commit.** `publicar-backlog-azure-boards` e
  `publicar-backlog-demanda-azure-boards` são gêmeos byte a byte nos módulos tocados aqui, exceto onde
  a tarefa disser o contrário. Um backlog com campo novo aceito por um pacote e recusado pelo outro é
  o modo de falha que esta regra existe para impedir.
- **`Tags` e `Depende de` entram em `SECTION_NAMES` e em `_SECOES` juntos.** Uma seção conhecida por
  apenas um dos parsers é aceita por um caminho e explode no outro.
- **Campos novos são opcionais e só entram no hash quando preenchidos.** Backlog sem eles precisa
  produzir o hash de hoje, byte a byte, ou toda publicação parcial em andamento deixa de retomar.
- **Campos novos do dataclass vêm depois dos existentes, com default.** Os testes constroem
  `ItemBacklog` posicionalmente (`ItemBacklog("1.1.1", TipoItem.HISTORIA_USUARIO, "História", "1.1.0",
  "Descrição", "")`); inserir campo no meio quebra toda a suíte.
- **Separador de tag no Azure é `"; "`.** No Markdown o separador é vírgula.
- **Comandos por pacote:** `uv run pytest -q`, `uv run ruff check .`, `uv run ruff format --check .`,
  `uv run mypy src`, rodados de dentro do diretório do pacote.
- **Linha de 100 colunas** (`line-length = 100` no ruff).

## Foco de revisão

Classes de entrada que a spec implica e que nenhuma tarefa exercitaria por conta própria. Cada uma
tem seu teste atribuído à tarefa dona do código:

1. **Tag composta só de espaços entre vírgulas** (`a, , b`) — deve ser recusada com erro nomeando o
   item, não silenciosamente descartada. → Tarefa 1.
2. **Tag acima do limite de 400 caracteres do Azure Boards** — recusar localmente, com mensagem, em
   vez de deixar a API rejeitar o lote inteiro no meio da publicação. → Tarefa 1.
3. **Item que declara `Depende de` apontando para si mesmo** — ciclo de um nó, que uma detecção
   ingênua de ciclo não pega. → Tarefa 3.
4. **`Azure Boards ID` com valor não inteiro, zero ou negativo** — um ID digitado errado não pode
   virar `int()` explodindo com `ValueError` cru no meio do planejamento. → Tarefa 6.
5. **Backlog com `Demanda de Negócio de origem` publicado pela publicadora solta** — precisa
   continuar funcionando, senão o fluxo de débitos nasce quebrado. → Tarefa 8.

---

## Estrutura de arquivos

Por pacote, em `src/<pacote>/`:

| Arquivo | Responsabilidade após a mudança |
|---|---|
| `contrato_backlog.py` | regras puras de formato dos três campos novos, detecção de ciclo, e a validação estrutural que acumula erros |
| `interpretar_markdown.py` | leitura tipada do Markdown, consumindo as mesmas regras puras e levantando na primeira falha |
| `modelos.py` | `ItemBacklog` e `OperacaoCriacao` com os campos novos; `RegistroManifesto` com a marca de pré-existente |
| `planejar_publicacao.py` | ordenação topológica estável, separação dos itens pré-existentes, hash assimétrico |
| `executar_publicacao.py` | semeadura de `registros` com os IDs declarados e resolução dos predecessores |
| `cliente_azure_devops.py` | `System.Tags` no payload e relação `Dependency-Reverse` por predecessor |
| `manifesto.py` | serialização e validação do registro pré-existente |

Fora de `src/`:

| Arquivo | Responsabilidade |
|---|---|
| `gerar-backlog-azure-boards/references/backlog-markdown-contract.md` | contrato normativo dos três campos |
| `especificar-debitos-tecnicos/SKILL.md` | `Faixa` oficial, `## Fonte da Demanda`, nota da tag que envelhece |
| `especificar-telas-ux-ui/SKILL.md` | plataforma como campo estruturado do `TL-xx` |
| `gerar-backlog-azure-boards/SKILL.md` | emissão do vocabulário e serialização de `Depende de` |

---

## Tarefa 1: regras de formato do campo `Tags`

**Arquivos:**
- Modificar: `publicar-backlog-azure-boards/src/publicar_backlog_azure_boards/contrato_backlog.py`
- Modificar: `publicar-backlog-demanda-azure-boards/src/publicar_backlog_demanda_azure_boards/contrato_backlog.py`
- Testar: `publicar-backlog-azure-boards/tests/test_contrato_tags.py`
- Testar: `publicar-backlog-demanda-azure-boards/tests/test_contrato_tags.py`

**Interfaces:**
- Consome: nada de tarefas anteriores.
- Produz: `normalizar_tags(bruto: str) -> tuple[tuple[str, ...], list[str]]` em `contrato_backlog`,
  devolvendo as tags normalizadas e a lista de erros de formato (vazia quando válido). A Tarefa 2 a
  consome no parser tipado; a Tarefa 9 documenta as regras que ela implementa.

- [ ] **Passo 1: escrever os testes que falham**

Crie `publicar-backlog-azure-boards/tests/test_contrato_tags.py`:

```python
import pytest

from publicar_backlog_azure_boards.contrato_backlog import normalizar_tags


def test_seccao_ausente_nao_produz_tags_nem_erros() -> None:
    assert normalizar_tags("") == ((), [])


def test_separa_por_virgula_e_remove_espacos() -> None:
    tags, erros = normalizar_tags("debito-tecnico ,  dt-restricao")

    assert tags == ("debito-tecnico", "dt-restricao")
    assert erros == []


def test_deduplica_preservando_a_ordem() -> None:
    tags, erros = normalizar_tags("design-ux-ui, plataforma-web, design-ux-ui")

    assert tags == ("design-ux-ui", "plataforma-web")
    assert erros == []


def test_recusa_tag_vazia_entre_virgulas() -> None:
    tags, erros = normalizar_tags("debito-tecnico, , dt-restricao")

    assert tags == ()
    assert erros == ["a seção Tags possui uma tag vazia entre vírgulas"]


def test_recusa_ponto_e_virgula_dentro_da_tag() -> None:
    tags, erros = normalizar_tags("debito;tecnico")

    assert tags == ()
    assert erros == ["a tag 'debito;tecnico' contém ';', que o Azure Boards usa como separador"]


def test_recusa_tag_acima_do_limite_do_azure() -> None:
    longa = "x" * 401

    tags, erros = normalizar_tags(longa)

    assert tags == ()
    assert erros == [f"a tag '{longa}' passa de 400 caracteres, o limite do Azure Boards"]


def test_acumula_mais_de_um_erro_de_formato() -> None:
    _, erros = normalizar_tags("a;b, , c;d")

    assert len(erros) == 3
```

Copie o mesmo arquivo para `publicar-backlog-demanda-azure-boards/tests/test_contrato_tags.py`,
trocando o import para `publicar_backlog_demanda_azure_boards.contrato_backlog`.

- [ ] **Passo 2: rodar para confirmar que falham**

```bash
cd publicar-backlog-azure-boards && uv run pytest tests/test_contrato_tags.py -q
```

Esperado: FAIL com `ImportError: cannot import name 'normalizar_tags'`.

- [ ] **Passo 3: implementar**

Em `contrato_backlog.py` de **ambos** os pacotes, acrescente `"Tags"` a `SECTION_NAMES` e a função:

```python
TAGS = "Tags"
LIMITE_TAG = 400

SECTION_NAMES = {
    "Parent",
    "Título curto",
    "Description",
    "Acceptance Criteria",
    "Refinement Status",
    TAGS,
}


def normalizar_tags(bruto: str) -> tuple[tuple[str, ...], list[str]]:
    """Normaliza a seção ``Tags`` e devolve também os erros de formato encontrados.

    Uma seção ausente é legítima e devolve vazio sem erro; uma seção presente e vazia
    é erro de quem a valida, não desta função, porque só o chamador sabe distinguir
    "sem heading" de "heading sem conteúdo".
    """
    texto = bruto.strip()
    if not texto:
        return (), []

    erros: list[str] = []
    tags: list[str] = []
    for parte in texto.split(","):
        tag = parte.strip()
        if not tag:
            erros.append("a seção Tags possui uma tag vazia entre vírgulas")
            continue
        if ";" in tag:
            erros.append(f"a tag '{tag}' contém ';', que o Azure Boards usa como separador")
            continue
        if len(tag) > LIMITE_TAG:
            erros.append(f"a tag '{tag}' passa de {LIMITE_TAG} caracteres, o limite do Azure Boards")
            continue
        if tag not in tags:
            tags.append(tag)

    if erros:
        return (), erros
    return tuple(tags), []
```

- [ ] **Passo 4: rodar e confirmar que passam**

```bash
cd publicar-backlog-azure-boards && uv run pytest tests/test_contrato_tags.py -q && uv run ruff check . && uv run mypy src
cd ../publicar-backlog-demanda-azure-boards && uv run pytest tests/test_contrato_tags.py -q && uv run ruff check . && uv run mypy src
```

Esperado: PASS nos dois, sem achado de ruff nem de mypy.

- [ ] **Passo 5: commitar**

```bash
git add publicar-backlog-azure-boards/src/publicar_backlog_azure_boards/contrato_backlog.py \
        publicar-backlog-azure-boards/tests/test_contrato_tags.py \
        publicar-backlog-demanda-azure-boards/src/publicar_backlog_demanda_azure_boards/contrato_backlog.py \
        publicar-backlog-demanda-azure-boards/tests/test_contrato_tags.py
git commit -m "feat: regras de formato do campo Tags no contrato do backlog"
```

---

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

## Tarefa 4: ordenação topológica estável

**Arquivos:**
- Modificar: `planejar_publicacao.py` em ambos os pacotes
- Testar: `tests/test_planejar_publicacao.py` em ambos

**Interfaces:**
- Consome: `ItemBacklog.depende_de` da Tarefa 3.
- Produz: `criar_plano` devolvendo `operacoes` em ordem topológica estável e
  `OperacaoCriacao.depende_de: tuple[str, ...] = ()`. A Tarefa 5 usa essa ordem para resolver IDs.

- [ ] **Passo 1: escrever os testes que falham**

```python
def test_predecessor_e_criado_antes_do_dependente_mesmo_com_chave_maior() -> None:
    funcional = ItemBacklog(
        "1.1.1", TipoItem.HISTORIA_USUARIO, "Funcional", "1.1.0", "Descrição", "",
        depende_de=("1.1.2",),
    )
    design = ItemBacklog("1.1.2", TipoItem.HISTORIA_USUARIO, "Design", "1.1.0", "Descrição", "")
    itens = [funcional, design, ITENS[1], ITENS[2]]

    plano = criar_plano(itens, CONFIGURACAO, DATA_GERACAO)

    chaves = [operacao.chave for operacao in plano.operacoes]
    assert chaves.index("1.1.2") < chaves.index("1.1.1")


def test_ordem_sem_dependencias_e_identica_a_de_hoje() -> None:
    plano = criar_plano(ITENS, CONFIGURACAO, DATA_GERACAO)

    assert [operacao.chave for operacao in plano.operacoes] == ["1.0.0", "1.1.0", "1.1.1"]


def test_pai_continua_antes_do_filho_com_dependencia_entre_irmaos() -> None:
    funcional = ItemBacklog(
        "1.1.1", TipoItem.HISTORIA_USUARIO, "Funcional", "1.1.0", "Descrição", "",
        depende_de=("1.1.2",),
    )
    design = ItemBacklog("1.1.2", TipoItem.HISTORIA_USUARIO, "Design", "1.1.0", "Descrição", "")

    plano = criar_plano([funcional, design, ITENS[1], ITENS[2]], CONFIGURACAO, DATA_GERACAO)

    chaves = [operacao.chave for operacao in plano.operacoes]
    assert chaves.index("1.1.0") < chaves.index("1.1.2")


def test_operacao_propaga_dependencias() -> None:
    funcional = ItemBacklog(
        "1.1.1", TipoItem.HISTORIA_USUARIO, "Funcional", "1.1.0", "Descrição", "",
        depende_de=("1.1.2",),
    )
    design = ItemBacklog("1.1.2", TipoItem.HISTORIA_USUARIO, "Design", "1.1.0", "Descrição", "")

    plano = criar_plano([funcional, design, ITENS[1], ITENS[2]], CONFIGURACAO, DATA_GERACAO)
    operacao = next(o for o in plano.operacoes if o.chave == "1.1.1")

    assert operacao.depende_de == ("1.1.2",)


def test_hash_nao_muda_para_backlog_sem_dependencias() -> None:
    # mesmo literal da Tarefa 2: a ordenação topológica estável não pode alterar
    # nem a ordem nem o conteúdo serializado de um backlog sem arestas
    esperado = criar_plano(ITENS, CONFIGURACAO, DATA_GERACAO).hash_plano

    assert criar_plano(list(reversed(ITENS)), CONFIGURACAO, DATA_GERACAO).hash_plano == esperado
```

- [ ] **Passo 2: rodar para confirmar que falham**

```bash
cd publicar-backlog-azure-boards && uv run pytest tests/test_planejar_publicacao.py -q
```

Esperado: FAIL — `chaves.index("1.1.2") < chaves.index("1.1.1")` é falso, porque a ordem atual é por
chave.

- [ ] **Passo 3: implementar**

Em `planejar_publicacao.py`, substitua o `sorted` de `criar_plano`:

```python
class ErroDependenciaCiclica(ValueError):
    """Indica ciclo de dependência que impediria qualquer ordem de criação."""


def _ordenar_para_criacao(itens: Sequence[ItemBacklog]) -> list[ItemBacklog]:
    """Ordena por tipo e chave e depois puxa cada predecessor para antes do dependente.

    A travessia parte da ordem estável de hoje e emite em pós-ordem, então um backlog
    sem ``depende_de`` sai exatamente na sequência anterior — é o que preserva o hash
    e, com ele, a retomada de todo manifesto já gravado.
    """
    base = sorted(itens, key=_chave_ordenacao)
    por_chave = {item.chave: item for item in base}
    resultado: list[ItemBacklog] = []
    concluidos: set[str] = set()
    em_visita: list[str] = []

    def visitar(item: ItemBacklog) -> None:
        if item.chave in concluidos:
            return
        if item.chave in em_visita:
            ciclo = " → ".join(em_visita[em_visita.index(item.chave) :] + [item.chave])
            raise ErroDependenciaCiclica(f"ciclo de dependência entre {ciclo}")
        em_visita.append(item.chave)
        for chave in item.depende_de:
            predecessor = por_chave.get(chave)
            if predecessor is not None:
                visitar(predecessor)
        em_visita.pop()
        concluidos.add(item.chave)
        resultado.append(item)

    for item in base:
        visitar(item)
    return resultado


def criar_plano(
    itens: Sequence[ItemBacklog],
    configuracao: ConfiguracaoPublicacao,
    data_geracao: str,
) -> PlanoPublicacao:
    """Cria o plano completo; a retomada só separa pendentes após validar o manifesto."""
    itens_ordenados = _ordenar_para_criacao(itens)
    operacoes = tuple(_criar_operacao(item, configuracao, data_geracao) for item in itens_ordenados)
    return PlanoPublicacao(
        operacoes=operacoes,
        hash_plano=_calcular_hash(itens_ordenados, configuracao, data_geracao),
        configuracao=configuracao,
    )
```

Acrescente `depende_de=item.depende_de` em `_criar_operacao`, o campo em `OperacaoCriacao`
(`depende_de: tuple[str, ...] = ()`), e em `_conteudo_do_item`:

```python
    if item.depende_de:
        conteudo["depende_de"] = list(item.depende_de)
```

- [ ] **Passo 4: rodar e confirmar que passam**

```bash
cd publicar-backlog-azure-boards && uv run pytest -q && uv run mypy src
cd ../publicar-backlog-demanda-azure-boards && uv run pytest -q && uv run mypy src
```

Esperado: PASS, inclusive nos testes antigos de ordem e de hash.

- [ ] **Passo 5: commitar**

```bash
git add publicar-backlog-azure-boards publicar-backlog-demanda-azure-boards
git commit -m "feat: ordena a criacao topologicamente preservando a ordem sem dependencias"
```

---

## Tarefa 5: link Predecessor/Sucessor no payload

**Arquivos:**
- Modificar: `cliente_azure_devops.py` e `executar_publicacao.py` em ambos os pacotes
- Testar: `tests/test_cliente_azure_devops.py` e `tests/test_executar_publicacao.py` em ambos

**Interfaces:**
- Consome: `OperacaoCriacao.depende_de` da Tarefa 4 e `registros` de `executar_publicacao`.
- Produz: `ClienteAzureDevOps.criar_item(operacao, id_pai=None, ids_predecessores=())`.

- [ ] **Passo 1: escrever os testes que falham**

```python
def test_criacao_liga_predecessor_com_dependency_reverse() -> None:
    cliente_azure, chamadas = cliente(
        [resposta(200, {"id": 9, "url": "https://dev.azure.com/item/9"})]
    )
    operacao = replace(OPERACAO, depende_de=("1.1.2",))

    cliente_azure.criar_item(operacao, ids_predecessores=(42,))

    patch = json.loads(chamadas[0].content)
    relacoes = [entrada["value"] for entrada in patch if entrada["path"] == "/relations/-"]
    assert len(relacoes) == 1
    assert relacoes[0]["rel"] == "System.LinkTypes.Dependency-Reverse"
    assert relacoes[0]["url"].endswith("/workItems/42")


def test_criacao_liga_um_predecessor_por_plataforma() -> None:
    cliente_azure, chamadas = cliente(
        [resposta(200, {"id": 9, "url": "https://dev.azure.com/item/9"})]
    )
    operacao = replace(OPERACAO, depende_de=("1.1.2", "1.1.3"))

    cliente_azure.criar_item(operacao, ids_predecessores=(42, 43))

    patch = json.loads(chamadas[0].content)
    urls = [
        entrada["value"]["url"]
        for entrada in patch
        if entrada["path"] == "/relations/-"
        and entrada["value"]["rel"] == "System.LinkTypes.Dependency-Reverse"
    ]
    assert [url.rsplit("/", 1)[-1] for url in urls] == ["42", "43"]


def test_pai_e_predecessor_usam_relacoes_distintas() -> None:
    cliente_azure, chamadas = cliente(
        [resposta(200, {"id": 9, "url": "https://dev.azure.com/item/9"})]
    )
    operacao = replace(OPERACAO, depende_de=("1.1.2",))

    cliente_azure.criar_item(operacao, id_pai=7, ids_predecessores=(42,))

    patch = json.loads(chamadas[0].content)
    por_rel = {
        entrada["value"]["rel"]: entrada["value"]["url"]
        for entrada in patch
        if entrada["path"] == "/relations/-"
    }
    assert por_rel["System.LinkTypes.Hierarchy-Reverse"].endswith("/workItems/7")
    assert por_rel["System.LinkTypes.Dependency-Reverse"].endswith("/workItems/42")
```

> A terceira asserção é a que importa: `Dependency-Reverse` no item **dependente** aponta para o
> **predecessor**, igual a `Hierarchy-Reverse` apontando para o pai. Um teste que apenas contasse
> relações passaria com a direção invertida.

Em `tests/test_executar_publicacao.py`, primeiro ensine o `ClienteFalso` a registrar o parâmetro novo:

```python
class ClienteFalso:
    def __init__(
        self,
        falhar_na_chave: str | None = None,
        erro: Exception | None = None,
        configuracao: ConfiguracaoPublicacao = CONFIGURACAO,
    ) -> None:
        self.falhar_na_chave = falhar_na_chave
        self.erro = erro or RuntimeError("falha permanente")
        self.configuracao = configuracao
        self.chaves_criadas: list[str] = []
        self.predecessores_por_chave: dict[str, tuple[int, ...]] = {}

    def criar_item(
        self,
        operacao: OperacaoCriacao,
        id_pai: int | None = None,
        ids_predecessores: tuple[int, ...] = (),
    ):
        if operacao.chave == self.falhar_na_chave:
            raise self.erro
        self.chaves_criadas.append(operacao.chave)
        self.predecessores_por_chave[operacao.chave] = tuple(ids_predecessores)
        return RegistroManifesto(
            len(self.chaves_criadas), operacao.tipo, f"https://exemplo/{operacao.chave}"
        )
```

e acrescente o teste, com um plano próprio que tenha a dependência:

```python
def plano_com_dependencia() -> PlanoPublicacao:
    return PlanoPublicacao(
        operacoes=(
            OperacaoCriacao("1.0.0", TipoItem.EPIC, "Épico", "", "", None, "Epic"),
            OperacaoCriacao("1.1.0", TipoItem.FEATURE, "Feature", "", "", "1.0.0", "Feature"),
            OperacaoCriacao("1.1.2", TipoItem.HISTORIA_USUARIO, "Design", "", "", "1.1.0", "User Story"),
            OperacaoCriacao(
                "1.1.1", TipoItem.HISTORIA_USUARIO, "Funcional", "", "", "1.1.0", "User Story",
                depende_de=("1.1.2",),
            ),
        ),
        hash_plano="hash-dependencia",
        configuracao=CONFIGURACAO,
    )


def autorizacao_com_dependencia(chaves_pendentes: tuple[str, ...]):
    plano_atual = plano_com_dependencia()
    confirmacao = criar_frase_confirmacao(plano_atual, chaves_pendentes)
    return criar_autorizacao(plano_atual, confirmacao, frozenset(chaves_pendentes))


def test_passa_o_id_do_predecessor_criado_na_mesma_rodada(tmp_path) -> None:
    cliente = ClienteFalso()

    executar_plano(
        plano_com_dependencia(),
        autorizacao_com_dependencia(("1.0.0", "1.1.0", "1.1.2", "1.1.1")),
        cliente,
        tmp_path / "mapa.json",
    )

    id_do_design = ler_manifesto(tmp_path / "mapa.json").itens["1.1.2"].id
    assert cliente.predecessores_por_chave["1.1.1"] == (id_do_design,)


def test_resolve_predecessor_publicado_em_rodada_anterior(tmp_path) -> None:
    caminho = tmp_path / "mapa.json"
    cliente_com_falha = ClienteFalso("1.1.1")

    with pytest.raises(FalhaPublicacao):
        executar_plano(
            plano_com_dependencia(),
            autorizacao_com_dependencia(("1.0.0", "1.1.0", "1.1.2", "1.1.1")),
            cliente_com_falha,
            caminho,
        )

    id_do_design = ler_manifesto(caminho).itens["1.1.2"].id
    cliente_sem_falha = ClienteFalso()
    executar_plano(
        plano_com_dependencia(), autorizacao_com_dependencia(("1.1.1",)), cliente_sem_falha, caminho
    )

    assert cliente_sem_falha.chaves_criadas == ["1.1.1"]
    assert cliente_sem_falha.predecessores_por_chave["1.1.1"] == (id_do_design,)


def test_recusa_quando_o_predecessor_nao_foi_publicado(tmp_path) -> None:
    cliente = ClienteFalso()

    with pytest.raises(ValueError, match="predecessor 1.1.2"):
        executar_plano(
            plano_com_dependencia(),
            autorizacao_com_dependencia(("1.1.1",)),
            cliente,
            tmp_path / "mapa.json",
        )
```

- [ ] **Passo 2: rodar para confirmar que falham**

```bash
cd publicar-backlog-azure-boards && uv run pytest tests/test_cliente_azure_devops.py -q
```

Esperado: FAIL com `TypeError: criar_item() got an unexpected keyword argument 'ids_predecessores'`.

- [ ] **Passo 3: implementar**

Em `cliente_azure_devops.py`:

```python
_RELACAO_HIERARQUICA = "System.LinkTypes.Hierarchy-Reverse"
# No item dependente, a relação Reverse aponta para o predecessor — mesma convenção da
# hierarquia, em que o filho aponta o pai. Inverter para Forward cria a relação trocada,
# e ela aparece nos dois work items de qualquer forma, então só um teste que afirme a
# direção pega o erro.
_RELACAO_PREDECESSORA = "System.LinkTypes.Dependency-Reverse"
```

Na assinatura e no corpo:

```python
    def criar_item(
        self,
        operacao: OperacaoCriacao,
        id_pai: int | None = None,
        ids_predecessores: Sequence[int] = (),
    ) -> RegistroCriado:
```

repassando `ids_predecessores` a `_enviar_criacao`, que acrescenta ao fim do `patch`:

```python
        for id_predecessor in ids_predecessores:
            patch.append(
                {
                    "op": "add",
                    "path": "/relations/-",
                    "value": {
                        "rel": _RELACAO_PREDECESSORA,
                        "url": f"{self._base_url}/_apis/wit/workItems/{id_predecessor}",
                    },
                }
            )
```

Em `executar_publicacao.py`, dentro do laço, antes de `cliente.criar_item`:

```python
        for chave_predecessor in operacao.depende_de:
            if chave_predecessor not in registros:
                raise ValueError(
                    f"O predecessor {chave_predecessor} do item {operacao.chave} não foi publicado."
                )
        ids_predecessores = tuple(
            registros[chave].id for chave in operacao.depende_de
        )
```

e passe `ids_predecessores=ids_predecessores` na chamada.

- [ ] **Passo 4: rodar e confirmar que passam**

```bash
cd publicar-backlog-azure-boards && uv run pytest -q && uv run mypy src
cd ../publicar-backlog-demanda-azure-boards && uv run pytest -q && uv run mypy src
```

- [ ] **Passo 5: commitar**

```bash
git add publicar-backlog-azure-boards publicar-backlog-demanda-azure-boards
git commit -m "feat: cria link Predecessor no item dependente"
```

---

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

## Tarefa 7: item pré-existente no plano, no manifesto e na execução

**Arquivos:**
- Modificar: `modelos.py`, `planejar_publicacao.py`, `manifesto.py`, `executar_publicacao.py`,
  `cliente_azure_devops.py` em ambos
- Testar: `tests/test_planejar_publicacao.py`, `tests/test_manifesto.py`,
  `tests/test_executar_publicacao.py` em ambos

**Interfaces:**
- Consome: `ItemBacklog.azure_boards_id` da Tarefa 6.
- Produz: `ItemPreexistente(chave: str, tipo: TipoItem, id: int)`,
  `PlanoPublicacao.preexistentes: tuple[ItemPreexistente, ...] = ()` e
  `RegistroManifesto.preexistente: bool = False`. O tipo viaja junto porque
  `executar_publicacao` precisa dele para montar o `RegistroManifesto` sem reabrir o backlog.

- [ ] **Passo 1: escrever os testes que falham**

```python
def test_item_com_id_declarado_nao_vira_operacao_de_criacao() -> None:
    epic = replace(ITENS[2], azure_boards_id=4721)

    plano = criar_plano([epic, ITENS[1], ITENS[0]], CONFIGURACAO, DATA_GERACAO)

    assert [operacao.chave for operacao in plano.operacoes] == ["1.1.0", "1.1.1"]
    assert plano.preexistentes == (ItemPreexistente("1.0.0", TipoItem.EPIC, 4721),)


def test_hash_muda_quando_ha_id_declarado() -> None:
    epic = replace(ITENS[2], azure_boards_id=4721)

    assert (
        criar_plano([epic, ITENS[1], ITENS[0]], CONFIGURACAO, DATA_GERACAO).hash_plano
        != criar_plano(ITENS, CONFIGURACAO, DATA_GERACAO).hash_plano
    )


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
    caminho.write_text(
        json.dumps(
            {
                "versao": 1,
                "origem": "backlog.md",
                "hash_plano": "hash",
                "destino": None,
                "reconciliacao_pendente": None,
                "reconciliacoes": {},
                "itens": {"1.0.0": {"id": 9, "tipo": "Epic", "url": "u", "titulo": "t"}},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    assert ler_manifesto(caminho).itens["1.0.0"].preexistente is False
```

Use `CONFIGURACAO` como o arquivo já a define, e ajuste o dicionário de `itens` ao formato exato que
`_serializar` grava — leia `manifesto._serializar` e copie as chaves de lá, porque um campo a menos
faz `ler_manifesto` levantar em vez de devolver o padrão.

Em `tests/test_executar_publicacao.py`:

```python
def test_item_preexistente_nao_e_recriado_e_serve_de_pai(tmp_path) -> None:
    plano_com_epic_existente = PlanoPublicacao(
        operacoes=(OperacaoCriacao("1.1.0", TipoItem.FEATURE, "Feature", "", "", "1.0.0", "Feature"),),
        hash_plano="hash-preexistente",
        configuracao=CONFIGURACAO,
        preexistentes=(ItemPreexistente("1.0.0", TipoItem.EPIC, 4721),),
    )
    confirmacao = criar_frase_confirmacao(plano_com_epic_existente, ("1.1.0",))
    autorizacao_atual = criar_autorizacao(
        plano_com_epic_existente, confirmacao, frozenset(("1.1.0",))
    )
    cliente = ClienteFalso()

    executar_plano(plano_com_epic_existente, autorizacao_atual, cliente, tmp_path / "mapa.json")

    assert cliente.chaves_criadas == ["1.1.0"]
    manifesto = ler_manifesto(tmp_path / "mapa.json")
    assert manifesto.itens["1.0.0"].id == 4721
    assert manifesto.itens["1.0.0"].preexistente is True
```

- [ ] **Passo 2: rodar para confirmar que falham**

```bash
cd publicar-backlog-azure-boards && uv run pytest tests/test_planejar_publicacao.py tests/test_manifesto.py -q
```

Esperado: FAIL com `AttributeError: 'PlanoPublicacao' object has no attribute 'preexistentes'`.

- [ ] **Passo 3: implementar**

Em `modelos.py`:

```python
@dataclass(frozen=True)
class RegistroManifesto:
    """Associa uma chave documental a um work item já publicado."""

    id: int
    tipo: TipoItem
    url: str
    # Um registro pré-existente veio declarado no backlog, não de uma criação nossa.
    # Ele serve de pai para os filhos e nada mais: não conta como criação, não entra em
    # reconciliação e não é recriado numa retomada.
    preexistente: bool = False


@dataclass(frozen=True)
class ItemPreexistente:
    """Item que o backlog declara já publicado, e que esta ferramenta não cria."""

    chave: str
    tipo: TipoItem
    id: int


@dataclass(frozen=True)
class PlanoPublicacao:
    """Agrupa as operações imutáveis que poderão ser autorizadas posteriormente."""

    operacoes: tuple[OperacaoCriacao, ...]
    hash_plano: str
    configuracao: ConfiguracaoPublicacao
    preexistentes: tuple[ItemPreexistente, ...] = ()
```

Confirme os três primeiros campos contra o `modelos.py` do pacote antes de editar; o campo novo vai
depois deles, com default, pelo mesmo motivo dos campos de `ItemBacklog`.

Em `planejar_publicacao.py`, separe antes de montar as operações:

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

passando `preexistentes=preexistentes` a `PlanoPublicacao` e mantendo `_calcular_hash` sobre
`itens_ordenados` (todos, inclusive os pré-existentes), com:

```python
    if item.azure_boards_id is not None:
        conteudo["azure_boards_id"] = item.azure_boards_id
```

Em `manifesto.py`, inclua `"preexistente": registro.preexistente` na serialização de cada item e
leia-o de volta com `bool(dados.get("preexistente", False))`, de modo que manifesto antigo continue
válido. Onde o módulo ou o `cli.py` contar criações, exclua os registros com a marca.

Em `executar_publicacao.py`, semeie antes do laço:

```python
    registros = dict(manifesto.itens)
    for preexistente in plano.preexistentes:
        registros[preexistente.chave] = RegistroManifesto(
            preexistente.id,
            preexistente.tipo,
            cliente.url_do_item(preexistente.id),
            preexistente=True,
        )
```

Em `cliente_azure_devops.py`, exponha a montagem da URL e a conferência:

```python
    def url_do_item(self, id_item: int) -> str:
        """Monta a URL canônica de um work item pelo ID."""
        return f"{self._base_url}/_apis/wit/workItems/{id_item}"

    def verificar_item_existente(self, id_item: int, tipo_esperado: str) -> None:
        """Confirma que o work item existe e é do tipo esperado antes de pendurar filhos nele."""
        dados = self._enviar("GET", self._url_api(f"/_apis/wit/workitems/{id_item}", "consulta"))
        tipo = dados.get("fields", {}).get("System.WorkItemType")
        if tipo != tipo_esperado:
            raise ErroDestinoInvalido(
                f"O work item {id_item} é do tipo {tipo!r}, e o backlog o declara como "
                f"{tipo_esperado!r}."
            )
```

Chame `verificar_item_existente` uma vez por item pré-existente, na verificação preliminar, antes de
pedir autorização — é lá que os outros avisos já aparecem.

- [ ] **Passo 4: rodar e confirmar que passam**

```bash
cd publicar-backlog-azure-boards && uv run pytest -q && uv run mypy src
cd ../publicar-backlog-demanda-azure-boards && uv run pytest -q && uv run mypy src
```

- [ ] **Passo 5: commitar**

```bash
git add publicar-backlog-azure-boards publicar-backlog-demanda-azure-boards
git commit -m "feat: reaproveita Epic e Feature ja publicados pelo ID declarado"
```

---

## Tarefa 8: checagem cruzada do `demanda_id`

**Arquivos:**
- Modificar: `publicar-backlog-demanda-azure-boards/src/publicar_backlog_demanda_azure_boards/interpretar_markdown.py`
- Modificar: `publicar-backlog-demanda-azure-boards/src/publicar_backlog_demanda_azure_boards/executar_publicacao.py`
- Testar: `publicar-backlog-demanda-azure-boards/tests/test_demanda_de_origem.py` (novo)
- Testar: `publicar-backlog-azure-boards/tests/test_interpretar_markdown.py` (não-regressão)

**Interfaces:**
- Consome: nada das tarefas anteriores.
- Produz: `extrair_demanda_origem(caminho: Path) -> int | None`, devolvendo `None` quando o backlog
  declara `Não se aplica`.

> Esta é a única tarefa **assimétrica**: a recusa vale só na publicadora de Demanda. A publicadora
> solta precisa continuar aceitando backlog com Demanda declarada, porque o backlog de débitos
> declara a Demanda e publica solto de propósito, pelo `Iteration Path`.

- [ ] **Passo 1: escrever os testes que falham**

Em `publicar-backlog-demanda-azure-boards/tests/test_demanda_de_origem.py`:

```python
from pathlib import Path

import pytest

from publicar_backlog_demanda_azure_boards.interpretar_markdown import (
    ErroContratoMarkdown,
    extrair_demanda_origem,
)

CABECALHO = (
    "# Backlog para Azure Boards\n\n## Metadados e cobertura\n"
    "- Data de geração: `2026-09-25`\n"
)


def test_le_o_id_da_demanda_de_origem(tmp_path: Path) -> None:
    caminho = tmp_path / "backlog.md"
    caminho.write_text(
        CABECALHO + "- Demanda de Negócio de origem: `#14125`\n", encoding="utf-8"
    )

    assert extrair_demanda_origem(caminho) == 14125


def test_devolve_none_quando_o_backlog_declara_nao_se_aplica(tmp_path: Path) -> None:
    caminho = tmp_path / "backlog.md"
    caminho.write_text(
        CABECALHO
        + "- Demanda de Negócio de origem: Não se aplica — a spec não nasceu de uma Demanda\n",
        encoding="utf-8",
    )

    assert extrair_demanda_origem(caminho) is None


def test_rejeita_metadado_ausente(tmp_path: Path) -> None:
    caminho = tmp_path / "backlog.md"
    caminho.write_text(CABECALHO, encoding="utf-8")

    with pytest.raises(ErroContratoMarkdown, match="Demanda de Negócio de origem"):
        extrair_demanda_origem(caminho)
```

Acrescente ao mesmo arquivo os testes da recusa:

```python
from publicar_backlog_demanda_azure_boards.executar_publicacao import conferir_demanda_de_origem


def backlog_com_demanda(tmp_path: Path, linha: str) -> Path:
    caminho = tmp_path / "backlog.md"
    caminho.write_text(CABECALHO + linha, encoding="utf-8")
    return caminho


def test_recusa_quando_o_id_informado_diverge_do_backlog(tmp_path: Path) -> None:
    caminho = backlog_com_demanda(tmp_path, "- Demanda de Negócio de origem: `#14125`\n")

    with pytest.raises(ValueError, match="#14125.*#99999"):
        conferir_demanda_de_origem(caminho, demanda_id=99999)


def test_recusa_backlog_que_nao_nasceu_de_demanda(tmp_path: Path) -> None:
    caminho = backlog_com_demanda(
        tmp_path,
        "- Demanda de Negócio de origem: Não se aplica — a spec não nasceu de uma Demanda\n",
    )

    with pytest.raises(ValueError, match="Não se aplica"):
        conferir_demanda_de_origem(caminho, demanda_id=14125)


def test_aceita_quando_o_id_confere(tmp_path: Path) -> None:
    caminho = backlog_com_demanda(tmp_path, "- Demanda de Negócio de origem: `#14125`\n")

    conferir_demanda_de_origem(caminho, demanda_id=14125)
```

Em `publicar-backlog-azure-boards/tests/test_interpretar_markdown.py`, o teste de não-regressão:

```python
def test_publicadora_solta_aceita_backlog_com_demanda_declarada(tmp_path: Path):
    """O backlog de débitos declara Demanda e publica solto de propósito.

    Se alguém "corrigir" a assimetria acrescentando a recusa aqui, o fluxo de débitos
    para de funcionar. Este teste existe para impedir essa correção.
    """
    caminho = tmp_path / "backlog.md"
    caminho.write_text(
        "# Backlog para Azure Boards\n\n## Metadados e cobertura\n"
        "- Data de geração: `2026-09-25`\n"
        "- Demanda de Negócio de origem: `#14125`\n\n"
        "## 1.0.0 [Epic] Épico\n\n### Description\nTexto\n",
        encoding="utf-8",
    )

    assert interpretar_backlog(caminho)[0].chave == "1.0.0"
```

- [ ] **Passo 2: rodar para confirmar que falham**

```bash
cd publicar-backlog-demanda-azure-boards && uv run pytest tests/test_demanda_de_origem.py -q
```

Esperado: FAIL com `ImportError: cannot import name 'extrair_demanda_origem'`.

- [ ] **Passo 3: implementar**

Em `interpretar_markdown.py` **só do pacote de Demanda**:

```python
_DEMANDA_ORIGEM_RE = re.compile(
    r"^- Demanda de Negócio de origem: (?P<valor>.+)$", re.MULTILINE
)
_DEMANDA_ID_RE = re.compile(r"^`#(\d+)`$")


def extrair_demanda_origem(caminho: Path) -> int | None:
    """Lê o ID da Demanda declarado nos Metadados; ``None`` quando o backlog não nasceu de uma."""
    texto = caminho.read_text(encoding="utf-8")
    correspondencia = _DEMANDA_ORIGEM_RE.search(texto)
    if correspondencia is None:
        raise ErroContratoMarkdown(
            "Metadados e cobertura não possui Demanda de Negócio de origem"
        )
    valor = correspondencia.group("valor").strip()
    if valor.startswith("Não se aplica"):
        return None
    id_declarado = _DEMANDA_ID_RE.match(valor)
    if id_declarado is None:
        raise ErroContratoMarkdown(
            f"Demanda de Negócio de origem inválida: {valor!r}; use `#<id>` ou 'Não se aplica'"
        )
    return int(id_declarado.group(1))
```

e a conferência, junto das demais recusas pré-escrita:

```python
def conferir_demanda_de_origem(caminho: Path, demanda_id: int) -> None:
    """Recusa publicar sob uma Demanda diferente da que o backlog declara.

    Sem flag de sobreposição de propósito: pendurar épicos na Demanda errada é caro de
    desfazer, e uma flag para forçar existiria para ser usada justamente sob a pressão
    em que o engano acontece. Republicar sob outra Demanda passa por corrigir o documento.
    """
    declarada = extrair_demanda_origem(caminho)
    if declarada is None:
        raise ValueError(
            "O backlog declara 'Não se aplica' em Demanda de Negócio de origem: ele não "
            "nasceu de uma Demanda, e esta não é a publicadora dele."
        )
    if declarada != demanda_id:
        raise ValueError(
            f"O backlog declara a Demanda #{declarada}, e a configuração informa "
            f"#{demanda_id}. Corrija o documento ou a configuração antes de publicar."
        )
```

Chame `conferir_demanda_de_origem` na verificação preliminar, antes de qualquer escrita e antes de
pedir autorização. **Não replique nada disso no pacote solto.**

- [ ] **Passo 4: rodar e confirmar que passam**

```bash
cd publicar-backlog-demanda-azure-boards && uv run pytest -q && uv run mypy src
cd ../publicar-backlog-azure-boards && uv run pytest -q && uv run mypy src
```

- [ ] **Passo 5: commitar**

```bash
git add publicar-backlog-demanda-azure-boards publicar-backlog-azure-boards
git commit -m "feat: recusa publicar sob Demanda diferente da declarada no backlog"
```

---

## Tarefa 9: contrato Markdown

**Arquivos:**
- Modificar: `gerar-backlog-azure-boards/references/backlog-markdown-contract.md`

**Interfaces:**
- Consome: as regras implementadas nas Tarefas 1, 3 e 6 — a documentação descreve o que o código já
  recusa, nunca o contrário.
- Produz: o contrato normativo que a Tarefa 10 cita.

- [ ] **Passo 1: escrever as três seções novas**

Acrescente, depois de "Depende de e Bloqueia", uma seção `## Tags` com: formato (subseção no nível
das demais, vírgula como separador), opcionalidade, recusa de seção presente e vazia, proibição de
`,` e `;` dentro da tag, limite de 400 caracteres, dedup preservando ordem, validade em qualquer
item, e o mapeamento para `System.Tags` unido por `"; "`.

Reescreva "Depende de e Bloqueia" para declarar `Depende de` como **subseção estruturada** com chaves
documentais, mantendo `Bloqueia` como texto informativo e explicando que só `Depende de` gera o link
`System.LinkTypes.Dependency-Reverse`. Registre que backlog anterior com `Depende de` em prosa
continua válido e não ganha link.

Acrescente `## Azure Boards ID` com: só em Epic e Feature, exige ancestral também declarado, o item
não é criado e serve de pai, e a ressalva de que este é o único lugar do backlog onde um ID real
aparece — copiado do Boards, nunca inferido, nunca derivado da chave documental nem do nome da pasta.

Atualize o template completo com as três subseções e a tabela "Markdown de revisão e campos do Azure
Boards" com as linhas novas.

- [ ] **Passo 2: conferir contra o código**

```bash
cd publicar-backlog-azure-boards && uv run pytest tests/test_contrato_tags.py tests/test_contrato_dependencias.py tests/test_contrato_id_existente.py -q
```

Leia cada mensagem de erro afirmada nesses testes e confirme que o contrato descreve a mesma regra,
com o mesmo limite e o mesmo separador. Divergência entre os dois é defeito do contrato.

- [ ] **Passo 3: rodar a validação estrutural sobre o template**

```bash
cd publicar-backlog-azure-boards && uv run python scripts/publicar_backlog.py validar tests/fixtures/valid-backlog.md
```

Esperado: nenhum erro. A fixture continua sem os campos novos, e é isso que confirma que eles são
opcionais.

- [ ] **Passo 4: commitar**

```bash
git add gerar-backlog-azure-boards/references/backlog-markdown-contract.md
git commit -m "docs: contrato de Tags, Depende de estruturado e Azure Boards ID"
```

---

## Tarefa 10: skills de débitos, telas e geração de backlog

**Arquivos:**
- Modificar: `especificar-debitos-tecnicos/SKILL.md`
- Modificar: `especificar-telas-ux-ui/SKILL.md`
- Modificar: `gerar-backlog-azure-boards/SKILL.md`

**Interfaces:**
- Consome: o contrato da Tarefa 9.
- Produz: as regras de emissão do vocabulário reservado. Nenhum código do publicador conhece
  `debito-tecnico` ou `design-ux-ui` — para ele, tag é string opaca.

- [ ] **Passo 1: `especificar-debitos-tecnicos/SKILL.md`**

- Acrescente `Faixa` ao cabeçalho da tabela `Resumo priorizado` e uma linha `- Faixa: <Restrição |
  Candidato | A confirmar>` à seção `Priorização` de cada DT.
- Acrescente `## Fonte da Demanda` ao template, copiada da spec de origem, com a proibição explícita
  de derivá-la do nome da pasta — `DN-14125-<slug>/` parece uma resposta e não é.
- Acrescente a nota de que `dt-<faixa>` publicada é snapshot da geração: uma reavaliação não atualiza
  o work item já criado.

- [ ] **Passo 2: `especificar-telas-ux-ui/SKILL.md`**

Acrescente ao template do `TL-xx` uma subseção `### Plataforma` com valor único, `Web` ou `Mobile`.
Hoje a plataforma vive no cabeçalho do documento e no título em prosa; a tag não pode depender de
parsing de título.

- [ ] **Passo 3: `gerar-backlog-azure-boards/SKILL.md`**

- Reconheça `Spec: Débitos técnicos` como spec de entrada válida, e não apenas como companheiro de
  contexto. A regra atual, de que o `debitos-tecnicos.md` encontrado numa pasta de Demanda é contexto
  rotulado, permanece: companheiro é contexto, spec de entrada é origem.
- Emita nos itens de folha: `debito-tecnico` e a faixa nos itens vindos de DT; `design-ux-ui` e
  `plataforma-web`/`plataforma-mobile` nos itens de design; `dn-<id>` em todo item nascido de uma
  Demanda. Epic e Feature não recebem tags.
- Serialize `Depende de` como subseção estruturada.
- Registre que os critérios em bullets de um DT vão para a Conversation e que `Acceptance Criteria`
  fica em branco, como o contrato manda quando a Confirmation não está completa.
- **Num backlog de débitos, Epic e Feature nomeiam a capacidade de produto afetada**, não o débito
  nem sua categoria — é a decisão de 2026-09-12, e um Epic "Débito técnico" com Features por
  categoria seria contêiner do problema. A tag já dá a visão de débito; a hierarquia dá a de
  capacidade, e pendurar na capacidade preserva as duas.
- Indique a publicadora **solta** como próxima etapa de um backlog de débitos, mesmo quando ele
  declarar Demanda de origem: `publicar-backlog-demanda-azure-boards` herdaria da Demanda o
  `Iteration Path`, e o débito nasceria na sprint da Demanda — exatamente a sprint em que ele não
  será pago.

- [ ] **Passo 4: conferir a coerência entre as três**

```bash
grep -n "debito-tecnico\|design-ux-ui\|plataforma-\|dn-<id>" especificar-debitos-tecnicos/SKILL.md especificar-telas-ux-ui/SKILL.md gerar-backlog-azure-boards/SKILL.md
```

Confirme que cada tag aparece com a mesma grafia nos dois lados — quem emite e quem documenta. Uma
divergência de grafia só apareceria depois de publicada, quando a query voltasse vazia.

- [ ] **Passo 5: commitar**

```bash
git add especificar-debitos-tecnicos/SKILL.md especificar-telas-ux-ui/SKILL.md gerar-backlog-azure-boards/SKILL.md
git commit -m "docs: emissao do vocabulario de tags nas skills de origem"
```

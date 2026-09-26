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

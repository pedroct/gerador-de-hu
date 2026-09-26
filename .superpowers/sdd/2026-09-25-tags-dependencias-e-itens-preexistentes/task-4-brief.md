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

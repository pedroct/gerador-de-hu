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

## Tarefa 7b: execução e conferência do item pré-existente

Segunda metade da Tarefa 7 do plano. A Tarefa 7a já separa os itens declarados como publicados e os
transporta em `PlanoPublicacao.preexistentes`. Você faz a execução **usá-los como pai sem recriá-los**,
e confere no Azure Boards que o ID declarado existe e é do tipo certo antes de pendurar qualquer filho.

**Arquivos:**
- Modificar: `executar_publicacao.py` e `cliente_azure_devops.py` em **ambos** os pacotes
- Testar: `tests/test_executar_publicacao.py` e `tests/test_cliente_azure_devops.py` em ambos

**Interfaces que a Tarefa 7a entregou:**
- `ItemPreexistente(chave, tipo, id)` em `modelos.py`
- `PlanoPublicacao.preexistentes: tuple[ItemPreexistente, ...] = ()` — já preenchido pelo planejador,
  e os itens correspondentes **não** estão em `plano.operacoes`
- `RegistroManifesto.preexistente: bool = False`, já serializado e lido pelo manifesto

- [ ] **Passo 1: escrever os testes que falham**

Em `tests/test_executar_publicacao.py`. **Atenção**: `ClienteFalso` precisa ganhar `url_do_item`,
porque `executar_publicacao` passará a chamá-lo — o plano original não previa isso e o teste morreria
com `AttributeError`:

```python
    def url_do_item(self, id_item: int) -> str:
        return f"https://exemplo/workItems/{id_item}"
```

e o teste:

```python
def test_item_preexistente_nao_e_recriado_e_serve_de_pai(tmp_path) -> None:
    plano_com_epic_existente = PlanoPublicacao(
        operacoes=(
            OperacaoCriacao("1.1.0", TipoItem.FEATURE, "Feature", "", "", "1.0.0", "Feature"),
        ),
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
    assert manifesto.itens["1.1.0"].preexistente is False
```

Em `tests/test_cliente_azure_devops.py`:

```python
def test_url_do_item_monta_o_caminho_canonico() -> None:
    cliente_azure, _ = cliente([])

    assert cliente_azure.url_do_item(4721).endswith("/_apis/wit/workItems/4721")


def test_verificar_item_existente_aceita_o_tipo_esperado() -> None:
    cliente_azure, _ = cliente(
        [resposta(200, {"id": 4721, "fields": {"System.WorkItemType": "Epic"}})]
    )

    cliente_azure.verificar_item_existente(4721, "Epic")


def test_verificar_item_existente_recusa_tipo_divergente() -> None:
    cliente_azure, _ = cliente(
        [resposta(200, {"id": 4721, "fields": {"System.WorkItemType": "Feature"}})]
    )

    with pytest.raises(ErroDestinoInvalido, match="4721"):
        cliente_azure.verificar_item_existente(4721, "Epic")
```

Ajuste os nomes dos auxiliares (`cliente`, `resposta`) aos que o arquivo já define, e importe
`ErroDestinoInvalido`. Replique tudo no pacote de Demanda, trocando só o import.

- [ ] **Passo 2: rodar para confirmar que falham**

```bash
cd publicar-backlog-azure-boards && uv run pytest tests/test_executar_publicacao.py tests/test_cliente_azure_devops.py -q
```

Esperado: FAIL com `AttributeError` de `url_do_item` / `verificar_item_existente`.

- [ ] **Passo 3: implementar**

Em `cliente_azure_devops.py`:

```python
    def url_do_item(self, id_item: int) -> str:
        """Monta a URL canônica de um work item pelo ID."""
        return f"{self._base_url}/_apis/wit/workItems/{id_item}"

    def verificar_item_existente(self, id_item: int, tipo_esperado: str) -> None:
        """Confirma que o work item existe e é do tipo esperado antes de pendurar filhos nele.

        Um ID digitado com um dígito a menos aponta para outro work item qualquer, e
        pendurar épicos sob ele é caro de desfazer.
        """
        dados = self._enviar("GET", self._url_api(f"/_apis/wit/workitems/{id_item}", "consulta"))
        tipo = dados.get("fields", {}).get("System.WorkItemType")
        if tipo != tipo_esperado:
            raise ErroDestinoInvalido(
                f"O work item {id_item} é do tipo {tipo!r}, e o backlog o declara como "
                f"{tipo_esperado!r}."
            )
```

Confira a assinatura real de `_enviar` e `_url_api` antes de usar — siga o que os outros métodos do
arquivo já fazem, inclusive quanto a tratamento de erro.

Em `executar_publicacao.py`, semeie `registros` **antes** do laço de criação:

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

Com isso, a checagem de pai que já existe passa a encontrar o item declarado, e nenhuma operação de
criação é gerada para ele — a Tarefa 7a já o removeu de `plano.operacoes`.

Chame `verificar_item_existente` uma vez por item pré-existente na **verificação preliminar**, antes
de pedir autorização — é lá que os outros avisos do publicador já aparecem. Localize esse ponto no
fluxo antes de escrever.

- [ ] **Passo 4: rodar a suíte inteira dos dois pacotes**

```bash
cd publicar-backlog-azure-boards && uv run pytest -q && uv run ruff check . && uv run ruff format --check . && uv run mypy src
cd ../publicar-backlog-demanda-azure-boards && uv run pytest -q && uv run ruff check . && uv run ruff format --check . && uv run mypy src
```

`test_hash_nao_muda_para_backlog_sem_tags` precisa continuar verde. Se falhar, **pare e reporte
BLOCKED**.

- [ ] **Passo 5: commitar**

```bash
git add publicar-backlog-azure-boards publicar-backlog-demanda-azure-boards
git commit -m "feat: reaproveita Epic e Feature ja publicados pelo ID declarado"
```

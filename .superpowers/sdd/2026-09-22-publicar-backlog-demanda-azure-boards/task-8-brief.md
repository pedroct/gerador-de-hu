### Task 8: A validação remota exercita o vínculo com a Demanda

Hoje `validar_operacao` valida sempre com pai nulo. O risco novo desta skill é justamente o processo
remoto aceitar (ou não) Épico como filho de Demanda de Negócio, e `--validar-apenas` precisa cobrir
isso antes de qualquer escrita.

**Files:**
- Modify: `src/.../cliente_azure_devops.py`
- Modify: `src/.../cli.py` (função `_verificar_preliminar`)
- Test: `tests/test_cliente_azure_devops.py`

**Interfaces:**
- Consumes: `ConfiguracaoPublicacao.demanda_id` da Task 5.
- Produces: `ClienteAzureDevOps.validar_operacao(operacao, id_pai: int | None = None) -> None` — a
  assinatura muda, e o `Protocol` `ClientePublicacao` em `cli.py` acompanha.

- [ ] **Step 1: Escrever os testes que falham**

Acrescentar a `tests/test_cliente_azure_devops.py`:

```python
def test_validar_operacao_envia_a_relacao_quando_ha_pai() -> None:
    capturado: list[list[dict[str, object]]] = []

    def responder(requisicao: httpx.Request) -> httpx.Response:
        assert "validateOnly=true" in str(requisicao.url)
        capturado.append(json.loads(requisicao.content))
        return httpx.Response(200, json={"id": 1, "url": "https://dev.azure.com/x/_apis/wit/workItems/1"})

    cliente = ClienteAzureDevOps(
        _configuracao_exemplo(),
        "token-de-teste",
        transport=httpx.MockTransport(responder),
    )
    cliente.validar_operacao(_operacao_epico(), id_pai=13959)

    relacoes = [op for op in capturado[0] if op["path"] == "/relations/-"]
    assert len(relacoes) == 1
    assert relacoes[0]["value"]["rel"] == "System.LinkTypes.Hierarchy-Reverse"
    assert str(relacoes[0]["value"]["url"]).endswith("/13959")


def test_validar_operacao_sem_pai_nao_envia_relacao() -> None:
    capturado: list[list[dict[str, object]]] = []

    def responder(requisicao: httpx.Request) -> httpx.Response:
        capturado.append(json.loads(requisicao.content))
        return httpx.Response(200, json={"id": 1, "url": "https://dev.azure.com/x/_apis/wit/workItems/1"})

    cliente = ClienteAzureDevOps(
        _configuracao_exemplo(),
        "token-de-teste",
        transport=httpx.MockTransport(responder),
    )
    cliente.validar_operacao(_operacao_epico())

    assert not [op for op in capturado[0] if op["path"] == "/relations/-"]
```

Reutilizar os auxiliares que o arquivo já tiver para construir configuração e operação; se não
houver, criar `_configuracao_exemplo()` devolvendo uma `ConfiguracaoPublicacao` com
`demanda_id=13959` e `_operacao_epico()` devolvendo uma `OperacaoCriacao` de `TipoItem.EPIC` com
`chave_pai=None`.

- [ ] **Step 2: Rodar e confirmar a falha**

```bash
cd /Volumes/DOCK/Projetos/pessoal/gerador-hu/publicar-backlog-demanda-azure-boards
uv run pytest tests/test_cliente_azure_devops.py -k validar_operacao -v
```

Esperado: FAIL com `TypeError: validar_operacao() got an unexpected keyword argument 'id_pai'`.

- [ ] **Step 3: Repassar o pai na validação**

```python
    def validar_operacao(self, operacao: OperacaoCriacao, id_pai: int | None = None) -> None:
        """Valida o JSON Patch no endpoint de criação, sem persistir o item.

        O ``id_pai`` é enviado para que a validação exercite também a relação hierárquica:
        é nela que mora o risco novo de o processo remoto recusar o Épico como filho da
        Demanda de Negócio.
        """
        self._enviar_criacao(operacao, validar=True, id_pai=id_pai)
```

- [ ] **Step 4: Ajustar a verificação preliminar da CLI**

```python
def _verificar_preliminar(
    cliente: ClientePublicacao,
    configuracao: ConfiguracaoPublicacao,
    operacoes: Sequence[OperacaoCriacao],
) -> None:
    cliente.verificar_destino(configuracao)
    for operacao in operacoes:
        id_pai = configuracao.demanda_id if operacao.chave_pai is None else None
        cliente.validar_operacao(operacao, id_pai=id_pai)
```

Um item sem `chave_pai` é sempre um Épico, cujo pai é a Demanda e já existe no Azure Boards. Features
e Histórias seguem validando sem pai, porque os seus ainda não foram criados.

Atualizar o `Protocol` no mesmo arquivo:

```python
    def validar_operacao(self, operacao: OperacaoCriacao, id_pai: int | None = None) -> None: ...
```

- [ ] **Step 4b: Provar que a verificação preliminar escolhe o pai certo**

Acrescentar a `tests/test_skill_integration.py`:

```python
def test_verificacao_preliminar_valida_epicos_contra_a_demanda() -> None:
    destino = ConfiguracaoPublicacao(
        organizacao="contoso",
        projeto="CESOP-DILIGENCIA",
        area_path="CESOP-DILIGENCIA\\Sustentacao",
        iteration_path="CESOP-DILIGENCIA\\Sprint 18",
        demanda_id=13959,
        mapeamento_tipos=MapeamentoTipos(),
    )
    plano = criar_plano(
        [
            ItemBacklog("1.0.0", TipoItem.EPIC, "Gestão", None, "d", ""),
            ItemBacklog("1.1.0", TipoItem.FEATURE, "Gestão", "1.0.0", "d", ""),
        ],
        destino,
        "2026-09-22",
    )

    validadas: list[tuple[str, int | None]] = []

    class _Cliente:
        configuracao = destino

        def verificar_destino(self, configuracao: ConfiguracaoPublicacao) -> object:
            return None

        def validar_operacao(
            self, operacao: OperacaoCriacao, id_pai: int | None = None
        ) -> None:
            validadas.append((operacao.chave, id_pai))

        def criar_item(
            self, operacao: OperacaoCriacao, id_pai: int | None = None
        ) -> object:  # pragma: no cover - não usado nesta verificação
            raise AssertionError("A verificação preliminar não pode criar itens.")

    _verificar_preliminar(_Cliente(), destino, plano.operacoes)

    assert dict(validadas) == {"1.0.0": 13959, "1.1.0": None}
```

Este é o teste que realiza o critério 3 da spec: `--validar-apenas` precisa exercitar o vínculo novo,
e não um Épico órfão.

- [ ] **Step 5: Rodar a suíte inteira**

```bash
cd /Volumes/DOCK/Projetos/pessoal/gerador-hu/publicar-backlog-demanda-azure-boards
uv run pytest
```

Esperado: PASS. Clientes falsos nos testes que definem `validar_operacao` sem `id_pai` precisam
receber o parâmetro novo.

- [ ] **Step 6: Commit**

```bash
cd /Volumes/DOCK/Projetos/pessoal/gerador-hu
git add publicar-backlog-demanda-azure-boards
git commit -m "feat: valida a relacao com a Demanda antes de qualquer escrita"
```

---

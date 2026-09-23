### Task 10: O destino é herdado da Demanda

Retirar `Area Path` e `Iteration Path` da configuração manual e derivá-los da Demanda lida. Muda junto
a semântica de `--simulacao`, que deixa de ser offline.

**Files:**
- Modify: `src/.../configuracao.py`
- Modify: `src/.../cli.py`
- Modify: `.env.example`
- Test: `tests/test_configuracao_projeto.py`, `tests/test_skill_integration.py`

**Interfaces:**
- Consumes: `ler_demanda(...)` (Task 7); `Demanda` (Task 5).
- Produces:
  - `ConfiguracaoAzureDevOps.publicacao_para(demanda: Demanda) -> ConfiguracaoPublicacao`
    substitui a property `publicacao`.
  - `ConfiguracaoAzureDevOps` deixa de ter `area_path` e `iteration_path`.

- [ ] **Step 1: Escrever os testes que falham**

Acrescentar a `tests/test_configuracao_projeto.py`:

```python
def test_destino_herda_os_caminhos_da_demanda() -> None:
    configuracao = carregar_configuracao(
        argumentos={"organizacao": "contoso", "projeto": "CESOP-DILIGENCIA", "demanda_id": "13959"},
        caminho_env=Path("arquivo-inexistente.env"),
        ambiente={},
        exigir_token=False,
    )
    demanda = Demanda(
        id=13959,
        titulo="PADRONIZAÇÃO",
        area_path="CESOP-DILIGENCIA\\Sustentacao",
        iteration_path="CESOP-DILIGENCIA\\Sprint 18",
        url="https://dev.azure.com/contoso/_apis/wit/workItems/13959",
    )
    destino = configuracao.publicacao_para(demanda)
    assert destino.area_path == "CESOP-DILIGENCIA\\Sustentacao"
    assert destino.iteration_path == "CESOP-DILIGENCIA\\Sprint 18"
    assert destino.demanda_id == 13959


def test_configuracao_nao_aceita_mais_caminhos_manuais() -> None:
    assert "area_path" not in ConfiguracaoAzureDevOps.model_fields
    assert "iteration_path" not in ConfiguracaoAzureDevOps.model_fields


def test_a_cli_nao_oferece_mais_os_caminhos_manuais() -> None:
    ajuda = construir_parser().format_help()
    assert "--area-path" not in ajuda
    assert "--iteration-path" not in ajuda
    assert "--demanda" in ajuda
```

- [ ] **Step 2: Rodar e confirmar a falha**

```bash
cd /Volumes/DOCK/Projetos/pessoal/gerador-hu/publicar-backlog-demanda-azure-boards
uv run pytest tests/test_configuracao_projeto.py -v
```

Esperado: FAIL com `AttributeError: 'ConfiguracaoAzureDevOps' object has no attribute
'publicacao_para'`.

- [ ] **Step 3: Remover os caminhos manuais da configuração**

Em `configuracao.py`:

- apagar os campos `area_path` e `iteration_path` de `ConfiguracaoAzureDevOps` e retirá-los da lista
  do `field_validator`;
- apagar as chaves `"area_path"`, `"area_paths"` e `"iteration_path"` de `_CHAVES`;
- apagar a função `_obter_area_path` inteira e a sua chamada, junto do ramo de seleção entre múltiplos
  Area Paths;
- retirar `"iteration_path"` da tupla `campos` e do laço de perguntas obrigatórias;
- apagar os rótulos `"area_path"` e `"iteration_path"` de `_perguntar`;
- substituir a property `publicacao`:

```python
    def publicacao_para(self, demanda: Demanda) -> ConfiguracaoPublicacao:
        """Deriva o destino a partir da Demanda, que é a dona dos caminhos.

        `Area Path` e `Iteration Path` não são mais configuráveis por execução: publicar sob
        uma Demanda significa publicar onde ela está.
        """
        return ConfiguracaoPublicacao(
            organizacao=self.organizacao,
            projeto=self.projeto,
            area_path=_normalizar_caminho(self.projeto, demanda.area_path),
            iteration_path=_normalizar_caminho(self.projeto, demanda.iteration_path),
            demanda_id=self.demanda_id,
            mapeamento_tipos=MapeamentoTipos(
                epic=self.tipo_epic,
                feature=self.tipo_feature,
                historia_usuario=self.tipo_user_story,
                bug=self.tipo_bug,
            ),
        )
```

`_normalizar_caminho` permanece: ela garante o prefixo do projeto mesmo que o Azure devolva um caminho
já normalizado.

- [ ] **Step 4: Remover os argumentos da CLI e ler a Demanda**

Em `cli.py`, apagar `--area-path` e `--iteration-path` de `_adicionar_opcoes_configuracao` e retirar
`"area_path"` e `"iteration_path"` da tupla `nomes` de `_carregar_configuracao`.

Trocar a montagem do plano em `principal`:

```python
        configuracao = _carregar_configuracao(
            argumentos_parseados, cliente, entrada_real, saida_real
        )
        if cliente is not None:
            destino = cliente.configuracao
            demanda = None
        else:
            demanda = ler_demanda(
                configuracao.organizacao,
                configuracao.projeto,
                configuracao.obter_token(),
                configuracao.demanda_id,
                configuracao.tipo_demanda,
            )
            destino = configuracao.publicacao_para(demanda)
        plano = criar_plano(itens, destino, data_geracao)
```

O ramo `cliente is not None` cobre os testes e integrações que injetam um cliente com destino pronto;
ele não pode ler a Demanda porque não há token nesse fluxo.

`exige_token` em `_carregar_configuracao` passa a valer também para `planejar` e para a simulação,
porque os três precisam ler a Demanda:

```python
    exige_token = argumentos.comando in {"planejar", "publicar"} and cliente is None
```

Trocar a mensagem final da simulação, que hoje afirma algo que deixou de ser verdade:

```python
            _escrever(
                saida_real,
                "Simulação concluída: a Demanda foi lida; "
                "nenhuma autorização foi solicitada e nenhum item foi criado.\n",
            )
```

- [ ] **Step 4b: Provar que a simulação faz exatamente uma leitura e nenhuma escrita**

Acrescentar a `tests/test_skill_integration.py`:

```python
def test_simulacao_le_a_demanda_uma_vez_e_nao_escreve(tmp_path, monkeypatch) -> None:
    metodos: list[str] = []

    def responder(requisicao: httpx.Request) -> httpx.Response:
        metodos.append(requisicao.method)
        return httpx.Response(
            200,
            json={
                "id": 13959,
                "url": "https://dev.azure.com/contoso/_apis/wit/workItems/13959",
                "fields": {
                    "System.WorkItemType": "Demanda de Negócio",
                    "System.TeamProject": "CESOP-DILIGENCIA",
                    "System.Title": "PADRONIZAÇÃO",
                    "System.AreaPath": "CESOP-DILIGENCIA\\Sustentacao",
                    "System.IterationPath": "CESOP-DILIGENCIA\\Sprint 18",
                },
            },
        )

    transporte = httpx.MockTransport(responder)
    monkeypatch.setattr(
        "publicar_backlog_demanda_azure_boards.cli.ler_demanda",
        lambda *args, **kwargs: ler_demanda(*args, transport=transporte),
    )
    monkeypatch.setenv("AZURE_DEVOPS_ORGANIZACAO", "contoso")
    monkeypatch.setenv("AZURE_DEVOPS_PROJETO", "CESOP-DILIGENCIA")
    monkeypatch.setenv("AZURE_DEVOPS_DEMANDA", "13959")
    monkeypatch.setenv("AZURE_DEVOPS_TOKEN", "token-de-teste")

    codigo = principal(
        ["publicar", str(_backlog(tmp_path)), "--simulacao", "--env-file", "inexistente.env"],
        entrada=io.StringIO(""),
        saida=(saida := io.StringIO()),
    )

    assert codigo == 0
    assert metodos == ["GET"]
    assert "nenhuma autorização foi solicitada" in saida.getvalue()
```

Este é o teste que realiza o critério 2 da spec. Se `metodos` trouxer mais de uma entrada, a
simulação está lendo além do necessário; se trouxer um `POST`, está escrevendo.

- [ ] **Step 5: Atualizar o `.env.example`**

```dotenv
# Organização do Azure DevOps.
AZURE_DEVOPS_ORGANIZACAO=
# Projeto de destino no Azure DevOps.
AZURE_DEVOPS_PROJETO=
# ID da Demanda de Negócio que ancora o backlog; os Épicos sobem como filhos dela.
AZURE_DEVOPS_DEMANDA=
# Nome remoto do tipo da Demanda. Ajuste se o seu processo usar outro rótulo.
AZURE_DEVOPS_TIPO_DEMANDA=Demanda de Negócio
# Nome remoto do tipo documental User Story. Use Product Backlog Item em processos Scrum.
AZURE_DEVOPS_TIPO_USER_STORY=User Story
# Token pessoal; mantenha vazio neste arquivo e fora do controle de versão. A entrada interativa é sem eco.
AZURE_DEVOPS_TOKEN=
```

`AZURE_DEVOPS_AREA_PATH`, `AZURE_DEVOPS_AREA_PATHS` e `AZURE_DEVOPS_ITERATION_PATH` saem do arquivo:
os caminhos vêm da Demanda.

- [ ] **Step 6: Rodar a suíte inteira**

```bash
cd /Volumes/DOCK/Projetos/pessoal/gerador-hu/publicar-backlog-demanda-azure-boards
uv run pytest
```

Esperado: PASS. Testes herdados que passam `area_path`/`iteration_path` a `carregar_configuracao`
precisam parar de passar; testes que afirmam a seleção entre múltiplos Area Paths devem ser
**removidos**, porque o comportamento deixou de existir.

- [ ] **Step 7: Commit**

```bash
cd /Volumes/DOCK/Projetos/pessoal/gerador-hu
git add publicar-backlog-demanda-azure-boards
git commit -m "feat: herda Area Path e Iteration Path da Demanda"
```

---

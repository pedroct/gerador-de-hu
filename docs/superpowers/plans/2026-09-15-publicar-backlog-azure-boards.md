# Plano de implementação: publicar backlog no Azure Boards

> **Para agentes de execução:** SUBSKILL OBRIGATÓRIA: use `superpowers:subagent-driven-development` (recomendado) ou `superpowers:executing-plans` para executar este plano tarefa a tarefa. Os passos usam caixas de seleção (`- [ ]`).

**Objetivo:** Criar a skill `publicar-backlog-azure-boards` e uma CLI Python que publique um backlog Markdown válido no Azure Boards somente após autorização textual explícita.

**Arquitetura:** A skill conduz validação, verificação preliminar, apresentação do plano e confirmação. Um pacote Python separado interpreta o Markdown, monta operações JSON Patch, chama a REST API em ordem hierárquica e grava um manifesto após cada sucesso. A REST API é o caminho obrigatório de publicação; o MCP permanece opcional e somente para inspeção.

**Stack tecnológica:** Python 3.12 ou superior, `uv`, `httpx`, `markdown-it-py`, Pydantic, `pydantic-settings`, `pytest`, Ruff, mypy estrito, Bandit, pip-audit, Semgrep, pre-commit e python-semantic-release.

**Especificação:** `docs/superpowers/specs/2026-09-15-publicar-backlog-azure-boards-design.md`

## Restrições globais

- O conteúdo criado deve estar em português brasileiro.
- Os nomes de módulos, classes, funções e comandos criados devem estar em português brasileiro; identificadores oficiais do Azure DevOps permanecem inalterados.
- Python 3.12 ou superior.
- `uv` é o gerenciador de dependências e ambiente.
- Não haverá FastAPI, Next.js ou PostgreSQL na primeira versão.
- Não haverá opção `--yes`, confirmação implícita por variável de ambiente ou publicação automática por existência de manifesto.
- A ausência de confirmação, confirmação incorreta ou plano alterado resulta em zero chamadas de criação.
- Não usar `bypassRules=true` automaticamente.
- Não implementar exclusão, destruição, atualização automática ou rollback.
- `Implementation Evidence` nunca será enviado ao Azure Boards.
- O token nunca aparecerá em logs, exceções, planos ou manifesto.
- Testes padrão nunca criarão work items reais.

---

## Estrutura de arquivos definida

O publicador será uma skill independente, com executor Python isolável no próprio diretório. Os
arquivos abaixo devem ser criados no repositório de skills:

```text
publicar-backlog-azure-boards/
├── SKILL.md
├── agents/openai.yaml
├── pyproject.toml
├── uv.lock
├── scripts/
│   └── publicar_backlog.py
├── src/publicar_backlog_azure_boards/
│   ├── __init__.py
│   ├── modelos.py
│   ├── configuracao.py
│   ├── interpretar_markdown.py
│   ├── converter_para_html.py
│   ├── planejar_publicacao.py
│   ├── cliente_azure_devops.py
│   ├── manifesto.py
│   ├── autorizacao.py
│   └── executar_publicacao.py
└── tests/
    ├── fixtures/valid-backlog.md
    ├── test_interpretar_markdown.py
    ├── test_converter_para_html.py
    ├── test_planejar_publicacao.py
    ├── test_autorizacao.py
    ├── test_manifesto.py
    ├── test_cliente_azure_devops.py
    └── test_executar_publicacao.py
```

O `SKILL.md` será a interface do agente. O pacote em `src/` será a interface programática. O
`scripts/publicar_backlog.py` será apenas o ponto de entrada CLI e não conterá regra de negócio.

### Interfaces públicas entre componentes

```python
# modelos.py
@dataclass(frozen=True)
class ItemBacklog: pass
@dataclass(frozen=True)
class ConfiguracaoPublicacao: pass
@dataclass(frozen=True)
class RegistroManifesto: pass
@dataclass(frozen=True)
class PlanoPublicacao: pass

# interpretar_markdown.py
def interpretar_backlog(caminho: Path) -> list[ItemBacklog]: pass

# planejar_publicacao.py
def criar_plano(
    itens: Sequence[ItemBacklog],
    configuracao: ConfiguracaoPublicacao,
    registros: Mapping[str, RegistroManifesto],
) -> PlanoPublicacao: pass

# autorizacao.py
def validar_confirmacao(confirmacao: str, esperada: str) -> bool: pass
def escolher_modalidade(entrada: TextIO, saida: TextIO) -> ModalidadeAutorizacao: pass

# manifesto.py
def ler_manifesto(caminho: Path) -> Manifesto: pass
def gravar_manifesto(caminho: Path, manifesto: Manifesto) -> None: pass

# cliente_azure_devops.py
class ClienteAzureDevOps:
    def verificar_destino(self, configuracao: ConfiguracaoPublicacao) -> VerificacaoDestino: pass
    def validar_operacao(self, operacao: OperacaoCriacao) -> None: pass
    def criar_item(self, operacao: OperacaoCriacao) -> RegistroCriado: pass

# executar_publicacao.py
def executar_plano(
    plano: PlanoPublicacao,
    autorizacao: Autorizacao,
    cliente: ClienteAzureDevOps,
    caminho_manifesto: Path,
) -> ResultadoPublicacao: pass
```

---

### Tarefa 1: Criar o esqueleto isolável e a configuração da ferramenta

**Arquivos:**

- Criar: `publicar-backlog-azure-boards/pyproject.toml`
- Criar: `publicar-backlog-azure-boards/README.md`
- Criar: `publicar-backlog-azure-boards/.env.example`
- Criar: `publicar-backlog-azure-boards/.gitignore`
- Criar: `publicar-backlog-azure-boards/src/publicar_backlog_azure_boards/__init__.py`
- Criar: `publicar-backlog-azure-boards/tests/test_configuracao_projeto.py`

**Interfaces:**

- Consome: padrões de stack em `docs/padroes_de_stack.md`.
- Produz: projeto Python executável por `uv`, com dependências e ferramentas pinadas.

- [ ] **Passo 1: Escrever o teste de configuração mínima**

```python
def test_projeto_exige_python_312_ou_superior():
    texto = Path("publicar-backlog-azure-boards/pyproject.toml").read_text()
    assert 'requires-python = ">=3.12"' in texto


def test_projeto_declara_comando_em_portugues():
    dados = tomllib.loads(Path("publicar-backlog-azure-boards/pyproject.toml").read_text())
    assert "publicar-backlog-azure-boards" in dados["project"]["scripts"]
```

- [ ] **Passo 2: Executar o teste e confirmar a falha**

Executar: `uv run pytest publicar-backlog-azure-boards/tests/test_configuracao_projeto.py -v`

Esperado: falha porque o novo `pyproject.toml` ainda não existe.

- [ ] **Passo 3: Criar a configuração mínima**

Declarar `httpx`, `markdown-it-py`, `pydantic` e `pydantic-settings` como dependências de produção;
declarar `pytest`, Ruff, mypy, Bandit, pip-audit, Semgrep, pre-commit e
python-semantic-release como dependências de desenvolvimento; configurar mypy estrito, Ruff com
linha máxima 100 e o comando `publicar-backlog-azure-boards`.

- [ ] **Passo 4: Gerar o lock e executar o teste**

Executar: `cd publicar-backlog-azure-boards && uv lock && uv run pytest tests/test_configuracao_projeto.py -v`

Esperado: PASS.

- [ ] **Passo 5: Commitar**

```bash
git add publicar-backlog-azure-boards
git commit -m "feat: cria base do publicador de backlog"
```

### Tarefa 2: Modelar e interpretar o contrato Markdown

**Arquivos:**

- Criar: `publicar-backlog-azure-boards/src/publicar_backlog_azure_boards/modelos.py`
- Criar: `publicar-backlog-azure-boards/src/publicar_backlog_azure_boards/interpretar_markdown.py`
- Criar: `publicar-backlog-azure-boards/tests/fixtures/valid-backlog.md`
- Criar: `publicar-backlog-azure-boards/tests/test_interpretar_markdown.py`

**Interfaces:**

- Consome: contrato de `gerar-backlog-azure-boards` e seu validador estrutural.
- Produz: `interpretar_backlog(Path) -> list[ItemBacklog]`, rejeitando itens sem pai, campos
  obrigatórios ausentes e headings fora do contrato.

- [ ] **Passo 1: Escrever testes para a hierarquia e campos**

```python
def test_interpreta_epic_feature_e_historia():
    itens = interpretar_backlog(Path("tests/fixtures/valid-backlog.md"))
    assert [(item.chave, item.tipo) for item in itens] == [
        ("1.0.0", "Epic"), ("1.1.0", "Feature"), ("1.1.1", "User Story")
    ]
    assert itens[2].pai == "1.1.0"


def test_evidencia_de_implementacao_nao_faz_parte_da_descricao():
    item = interpretar_backlog(Path("tests/fixtures/valid-backlog.md"))[-1]
    assert "Implementation Evidence" not in item.descricao
```

- [ ] **Passo 2: Executar os testes para confirmar a falha**

Executar: `cd publicar-backlog-azure-boards && uv run pytest tests/test_interpretar_markdown.py -v`

Esperado: falha por ausência do modelo e do interpretador.

- [ ] **Passo 3: Implementar os modelos e o interpretador mínimo**

Criar modelos tipados para item, tipo, operação e plano. Fazer o interpretador reconhecer headings
fora de cercas de código, extrair `Parent`, separar `Description` e `Acceptance Criteria`, remover
`Implementation Evidence` e preservar o conteúdo copiável.

- [ ] **Passo 4: Executar os testes**

Executar: `cd publicar-backlog-azure-boards && uv run pytest tests/test_interpretar_markdown.py -v`

Esperado: PASS.

- [ ] **Passo 5: Commitar**

```bash
git add publicar-backlog-azure-boards/src publicar-backlog-azure-boards/tests
git commit -m "feat: interpreta contrato de backlog"
```

### Tarefa 3: Converter campos e montar o plano sem escrita

**Arquivos:**

- Criar: `publicar-backlog-azure-boards/src/publicar_backlog_azure_boards/converter_para_html.py`
- Criar: `publicar-backlog-azure-boards/src/publicar_backlog_azure_boards/planejar_publicacao.py`
- Criar: `publicar-backlog-azure-boards/tests/test_converter_para_html.py`
- Criar: `publicar-backlog-azure-boards/tests/test_planejar_publicacao.py`

**Interfaces:**

- Consome: `ItemBacklog` e configuração validada.
- Produz: `converter_descricao(texto) -> str`, `converter_criterios(texto) -> str` e
  `criar_plano(itens, configuracao, registros) -> PlanoPublicacao`.

- [ ] **Passo 1: Escrever testes de HTML e ordem**

```python
def test_criterios_preservam_gherkin_em_bloco_pre():
    html = converter_criterios("```gherkin\nCenário: A\n```")
    assert "<pre" in html and "Cenário: A" in html


def test_plano_ordena_epic_feature_e_folha():
    plano = criar_plano(itens, configuracao, {})
    assert [operacao.chave for operacao in plano.operacoes] == ["1.0.0", "1.1.0", "1.1.1"]


def test_plano_exclui_item_registrado_no_manifesto():
    plano = criar_plano(itens, configuracao, {"1.0.0": registro_existente})
    assert "1.0.0" not in [operacao.chave for operacao in plano.operacoes]
```

- [ ] **Passo 2: Executar os testes e confirmar a falha**

Executar: `cd publicar-backlog-azure-boards && uv run pytest tests/test_converter_para_html.py tests/test_planejar_publicacao.py -v`

Esperado: falha por ausência do conversor e do planejador.

- [ ] **Passo 3: Implementar conversão e planejamento**

Converter somente os campos copiáveis para HTML. Calcular o hash do conteúdo, configuração de
destino e tipos. Produzir operações com tipo, título, campos, chave e chave do pai; nunca executar
HTTP neste componente.

- [ ] **Passo 4: Executar os testes e verificações estáticas**

Executar: `cd publicar-backlog-azure-boards && uv run pytest tests/test_converter_para_html.py tests/test_planejar_publicacao.py -v && uv run ruff check . && uv run mypy src`

Esperado: PASS e nenhuma violação estática.

- [ ] **Passo 5: Commitar**

```bash
git add publicar-backlog-azure-boards/src publicar-backlog-azure-boards/tests
git commit -m "feat: monta plano hierarquico de publicacao"
```

### Tarefa 4: Implementar configuração e autorização interativa

**Arquivos:**

- Criar: `publicar-backlog-azure-boards/src/publicar_backlog_azure_boards/configuracao.py`
- Criar: `publicar-backlog-azure-boards/src/publicar_backlog_azure_boards/autorizacao.py`
- Criar: `publicar-backlog-azure-boards/tests/test_autorizacao.py`

**Interfaces:**

- Consome: plano com hash e variáveis `AZURE_DEVOPS_*`.
- Produz: configuração validada, modalidade inteira ou lotes, autorização com hash e funções
  `validar_confirmacao` e `escolher_modalidade`.

- [ ] **Passo 1: Escrever testes de recusa e confirmação exata**

```python
def test_confirmacao_incorreta_e_rejeitada():
    assert validar_confirmacao("AUTORIZAR PUBLICAÇÃO 3 ITENS X 0000", esperada) is False


def test_confirmacao_exata_e_aceita():
    assert validar_confirmacao(esperada, esperada) is True


def test_plano_alterado_invalida_autorizacao():
    autorizacao = criar_autorizacao(plano_hash="novo")
    assert autorizacao.valida_para("antigo") is False


def test_modalidade_por_lotes_exige_tamanho_positivo():
    with pytest.raises(ValueError):
        criar_lotes(total=5, tamanho=0)
```

- [ ] **Passo 2: Executar os testes para confirmar a falha**

Executar: `cd publicar-backlog-azure-boards && uv run pytest tests/test_autorizacao.py -v`

Esperado: falha por ausência do módulo de autorização.

- [ ] **Passo 3: Implementar a autorização**

Ler argumentos antes do `.env`, depois arquivo de configuração, `.env` e pergunta interativa.
Exigir escolha entre backlog inteiro, lotes ou cancelamento. Gerar frase exata com quantidade,
projeto, Area Path, Iteration Path e código do plano. Não aceitar `--yes` nem confirmação parcial.

- [ ] **Passo 4: Executar testes de autorização e segurança**

Executar: `cd publicar-backlog-azure-boards && uv run pytest tests/test_autorizacao.py -v && uv run bandit -r src`

Esperado: PASS sem segredo literal ou vulnerabilidade reportada.

- [ ] **Passo 5: Commitar**

```bash
git add publicar-backlog-azure-boards/src publicar-backlog-azure-boards/tests
git commit -m "feat: exige autorizacao explicita para publicacao"
```

### Tarefa 5: Implementar cliente REST e verificação preliminar somente leitura

**Arquivos:**

- Criar: `publicar-backlog-azure-boards/src/publicar_backlog_azure_boards/cliente_azure_devops.py`
- Criar: `publicar-backlog-azure-boards/tests/test_cliente_azure_devops.py`

**Interfaces:**

- Consome: `ConfiguracaoPublicacao` e `OperacaoCriacao`.
- Produz: `ClienteAzureDevOps.verificar_destino`, `validar_operacao` e `criar_item`, com erros
  tipados para autenticação, permissão, destino inválido e falha transitória.

- [ ] **Passo 1: Escrever testes HTTP simulados**

```python
def test_verificacao_consulta_tipos_sem_criar_item(httpx_mock):
    httpx_mock.add_response(json={"value": [{"name": "Epic"}, {"name": "Feature"}, {"name": "Bug"}]})
    cliente = ClienteAzureDevOps(transport=transport_mockado)
    cliente.verificar_destino(configuracao)
    assert not any(request.method == "POST" and "/workitems/" in str(request.url) for request in chamadas)


def test_criacao_envia_json_patch_e_tipo(httpx_mock):
    httpx_mock.add_response(status_code=200, json={"id": 123, "url": "https://dev.azure.com/item/123"})
    cliente.criar_item(operacao)
    request = httpx_mock.get_request()
    assert request.headers["content-type"] == "application/json-patch+json"
    assert "/workitems/Epic" in str(request.url)
```

- [ ] **Passo 2: Executar os testes para confirmar a falha**

Executar: `cd publicar-backlog-azure-boards && uv run pytest tests/test_cliente_azure_devops.py -v`

Esperado: falha por ausência do cliente.

- [ ] **Passo 3: Implementar leitura, validação e criação**

Usar `httpx.Client` com tempo limite explícito, autenticação fora dos logs e versões configuráveis:
criação `7.2-preview.3`, WIQL `7.2-preview.2` e relações `7.2-preview.2`. Consultar tipos,
campos, relações, Area Paths e Iteration Paths antes da publicação. Usar `validateOnly=true` sem
persistir durante a validação remota. Adicionar a relação hierárquica somente quando o pai tiver
ID.

- [ ] **Passo 4: Testar erros e novas tentativas**

Adicionar testes para `401`, `403`, `404`, `409`, timeout e erro transitório. Executar:
`cd publicar-backlog-azure-boards && uv run pytest tests/test_cliente_azure_devops.py -v`

Esperado: PASS, com poucas novas tentativas somente para erros transitórios.

- [ ] **Passo 5: Commitar**

```bash
git add publicar-backlog-azure-boards/src publicar-backlog-azure-boards/tests
git commit -m "feat: integra cliente REST do Azure DevOps"
```

### Tarefa 6: Implementar manifesto, publicação sequencial e retomada

**Arquivos:**

- Criar: `publicar-backlog-azure-boards/src/publicar_backlog_azure_boards/manifesto.py`
- Criar: `publicar-backlog-azure-boards/src/publicar_backlog_azure_boards/executar_publicacao.py`
- Criar: `publicar-backlog-azure-boards/tests/test_manifesto.py`
- Criar: `publicar-backlog-azure-boards/tests/test_executar_publicacao.py`

**Interfaces:**

- Consome: `PlanoPublicacao`, `Autorizacao` e `ClienteAzureDevOps`.
- Produz: `ler_manifesto`, `gravar_manifesto` e `executar_plano`, atualizando o manifesto depois
  de cada criação bem-sucedida.

- [ ] **Passo 1: Escrever testes de manifesto e falha parcial**

```python
def test_manifesto_e_gravado_depois_de_cada_sucesso(tmp_path, cliente):
    executar_plano(plano_com_dois_itens, autorizacao_valida, cliente, tmp_path / "mapa.json")
    manifesto = ler_manifesto(tmp_path / "mapa.json")
    assert set(manifesto.itens) == {"1.0.0", "1.1.0"}


def test_falha_para_e_retomada_nao_duplica_item(tmp_path, cliente_com_falha_no_segundo):
    with pytest.raises(FalhaPublicacao):
        executar_plano(plano_com_dois_itens, autorizacao_valida, cliente_com_falha_no_segundo, tmp_path / "mapa.json")
    cliente_sem_falha = cliente_com_falha_no_segundo.continuar()
    executar_plano(plano_com_dois_itens, autorizacao_nova, cliente_sem_falha, tmp_path / "mapa.json")
    assert cliente_sem_falha.chaves_criadas == ["1.1.0"]
```

- [ ] **Passo 2: Executar os testes para confirmar a falha**

Executar: `cd publicar-backlog-azure-boards && uv run pytest tests/test_manifesto.py tests/test_executar_publicacao.py -v`

Esperado: falha por ausência do manifesto e do executor.

- [ ] **Passo 3: Implementar gravação atômica e execução**

Gravar arquivo temporário no mesmo diretório, substituir o manifesto ao concluir a escrita e
preservar registros já criados. Conferir hash, destino, título e tipo antes de ignorar item do
manifesto. Interromper em falha permanente, sem rollback e sem criar itens fora do lote autorizado.

- [ ] **Passo 4: Executar testes de retomada**

Executar: `cd publicar-backlog-azure-boards && uv run pytest tests/test_manifesto.py tests/test_executar_publicacao.py -v`

Esperado: PASS.

- [ ] **Passo 5: Commitar**

```bash
git add publicar-backlog-azure-boards/src publicar-backlog-azure-boards/tests
git commit -m "feat: permite retomada segura da publicacao"
```

### Tarefa 7: Criar a CLI, a skill e a documentação operacional

**Arquivos:**

- Criar: `publicar-backlog-azure-boards/scripts/publicar_backlog.py`
- Criar: `publicar-backlog-azure-boards/SKILL.md`
- Criar: `publicar-backlog-azure-boards/agents/openai.yaml`
- Modificar: `README.md`
- Criar: `publicar-backlog-azure-boards/tests/test_skill_integration.py`

**Interfaces:**

- Consome: todos os componentes anteriores.
- Produz: comandos `validar`, `planejar`, `publicar --simulacao` e `publicar --validar-apenas`,
  além do fluxo conversacional documentado para agentes.

- [ ] **Passo 1: Escrever testes da CLI e da skill**

```python
def test_simulacao_nao_chama_criacao(cliente):
    codigo = principal(["publicar", "backlog.md", "--simulacao"], cliente=cliente)
    assert codigo == 0
    assert cliente.chaves_criadas == []


def test_skill_declara_confirmacao_antes_de_escrita():
    texto = Path("publicar-backlog-azure-boards/SKILL.md").read_text()
    assert "zero chamadas de criação" in texto
    assert "AUTORIZAR PUBLICAÇÃO" in texto


def test_skill_nao_chama_mcp_obrigatoriamente():
    texto = Path("publicar-backlog-azure-boards/SKILL.md").read_text()
    assert "MCP" in texto and "opcional" in texto
```

- [ ] **Passo 2: Executar os testes para confirmar a falha**

Executar: `uv run pytest publicar-backlog-azure-boards/tests/test_skill_integration.py -v`

Esperado: falha porque a CLI e a skill ainda não existem.

- [ ] **Passo 3: Implementar o ponto de entrada e a skill**

Fazer a CLI carregar o backlog, validar, executar verificação preliminar, apresentar o plano,
perguntar modalidade e tamanho de lote e solicitar a frase exata. Documentar que a Iteration Path
é definida em cada execução e que `AZURE_DEVOPS_AREA_PATHS=Sustentacao,Projeto` exige seleção
explícita de `AZURE_DEVOPS_AREA_PATH` quando não houver argumento.

- [ ] **Passo 4: Atualizar README e metadados**

Adicionar o fluxo de geração → revisão → autorização → publicação, exemplos em pt-BR, variáveis de
ambiente e aviso para nunca versionar o token. Registrar a skill na tabela de capacidades sem
afirmar que ela publica automaticamente.

- [ ] **Passo 5: Executar testes da CLI e integração**

Executar: `uv run pytest publicar-backlog-azure-boards/tests/test_skill_integration.py -v`

Esperado: PASS.

- [ ] **Passo 6: Commitar**

```bash
git add publicar-backlog-azure-boards README.md
git commit -m "feat: adiciona skill de publicacao autorizada"
```

### Tarefa 8: Executar verificação completa e documentar integração opcional do MCP

**Arquivos:**

- Modificar: `publicar-backlog-azure-boards/README.md`
- Modificar: `publicar-backlog-azure-boards/SKILL.md`
- Modificar: `publicar-backlog-azure-boards/.env.example`

**Interfaces:**

- Consome: todos os módulos e testes anteriores.
- Produz: pacote verificável, documentação de operação e integração MCP explicitamente opcional.

- [ ] **Passo 1: Executar a suíte completa**

Executar:

```bash
cd publicar-backlog-azure-boards
uv run pytest -q
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv run bandit -r src
uv run pip-audit
```

Esperado: todos os comandos concluídos sem erro.

- [ ] **Passo 2: Executar validação de segurança da autorização**

Executar: `uv run pytest tests/test_autorizacao.py tests/test_executar_publicacao.py -q`

Esperado: nenhum teste permite criação sem confirmação, com plano alterado ou com manifesto
incompatível.

- [ ] **Passo 3: Revisar documentação contra a especificação**

Confirmar que a documentação cobre Area Paths `Sustentacao` e `Projeto`, Iteration Path por sprint,
autorização inteira ou por lotes, falha parcial, manifesto, ausência de `--yes`, REST API obrigatória
e MCP opcional.

- [ ] **Passo 4: Commitar a verificação final**

```bash
git add publicar-backlog-azure-boards
git commit -m "docs: documenta operacao segura do publicador"
```

## Revisão do plano contra a especificação

- O contexto, objetivo e limites são cobertos pelas Tarefas 1, 7 e 8.
- A separação entre skill e executor é coberta pelas Tarefas 1 e 7.
- O contrato Markdown, a hierarquia e a exclusão de `Implementation Evidence` são cobertos pela Tarefa 2.
- Conversão para HTML e campos Azure são cobertos pela Tarefa 3.
- Verificação preliminar somente leitura e JSON Patch são cobertos pela Tarefa 5.
- Autorização inteira ou por lotes, confirmação exata e hash são cobertos pela Tarefa 4.
- Ordem Epic → Feature → folha, manifesto e retomada são cobertos pela Tarefa 6.
- Area Paths e Iteration Path por execução são cobertos pelas Tarefas 4, 5 e 7.
- Falhas, segurança, ausência de `bypassRules=true` e ausência de exclusões são cobertas pelas Tarefas 5, 6 e 8.
- MCP opcional é coberto pelas Tarefas 7 e 8.
- Stack, qualidade e testes são cobertos pelas Tarefas 1 e 8.

Não foram encontrados placeholders, tarefas sem teste correspondente ou interfaces com nomes
inconsistentes.

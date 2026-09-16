# Plano de implementação: endurecer o publicador de backlog no Azure Boards

> **Para agentes de execução:** SUBSKILL OBRIGATÓRIA: use `superpowers:subagent-driven-development` (recomendado) ou `superpowers:executing-plans` para executar este plano tarefa a tarefa. Os passos usam caixas de seleção (`- [ ]`).

**Objetivo:** Corrigir os bloqueios de segurança, reconciliação, empacotamento e integração encontrados na revisão final do publicador.

**Arquitetura:** A autorização será uma impressão imutável do plano, do destino e do conjunto de operações; o executor comparará essa impressão com o cliente antes da primeira escrita. O manifesto ganhará estado de reconciliação para resultados incertos, e o validador Markdown será empacotado como parte do publicador. A CLI instalada será o único ponto de entrada, mantendo simulação local e validação remota separadas.

**Stack tecnológica:** Python >=3.12, uv, httpx, markdown-it-py, Pydantic, pydantic-settings, pytest, Ruff, mypy estrito, Bandit, Semgrep e pip-audit.

**Especificação:** `docs/superpowers/specs/2026-09-16-endurecer-publicador-azure-boards-design.md`

## Restrições globais

- Conteúdo criado em português brasileiro.
- REST continua sendo o único caminho de escrita; MCP permanece opcional e somente para inspeção.
- Não usar `--yes`, confirmação implícita, `bypassRules=true` ou publicação por existência de manifesto.
- Testes padrão nunca criam work items reais.
- O token nunca aparece em logs, mensagens, exceções, planos ou manifesto.
- Timeout de criação não deve ser repetido automaticamente sem idempotência comprovada.
- A URL de criação usa `/workitems/$<tipo-remoto>`.
- Uma autorização inválida, um destino divergente ou um estado de reconciliação pendente resulta em zero novas chamadas de criação.

## Estrutura de arquivos e responsabilidades

- `src/publicar_backlog_azure_boards/autorizacao.py`: confirmação exata e impressão imutável da autorização.
- `src/publicar_backlog_azure_boards/modelos.py`: tipos compartilhados de plano, destino, autorização e manifesto.
- `src/publicar_backlog_azure_boards/executar_publicacao.py`: validação final, bloqueio de estado ambíguo e execução sequencial.
- `src/publicar_backlog_azure_boards/manifesto.py`: persistência atômica de itens criados e reconciliações pendentes.
- `src/publicar_backlog_azure_boards/cliente_azure_devops.py`: REST, versões, caminhos, tipos e erros de transporte.
- `src/publicar_backlog_azure_boards/validacao_estrutural.py`: validador do contrato distribuído no wheel.
- `src/publicar_backlog_azure_boards/cli.py` e `__init__.py`: orquestração e entry point instalado.
- `tests/`: regressões unitárias, integração da CLI, instalação e segurança.

---

### Task 1: Imprimir autorização e vincular destino ao cliente

**Files:**

- Modify: `publicar-backlog-azure-boards/src/publicar_backlog_azure_boards/modelos.py`
- Modify: `publicar-backlog-azure-boards/src/publicar_backlog_azure_boards/autorizacao.py`
- Modify: `publicar-backlog-azure-boards/src/publicar_backlog_azure_boards/executar_publicacao.py`
- Modify: `publicar-backlog-azure-boards/src/publicar_backlog_azure_boards/manifesto.py`
- Modify: `publicar-backlog-azure-boards/src/publicar_backlog_azure_boards/cliente_azure_devops.py`
- Test: `publicar-backlog-azure-boards/tests/test_autorizacao.py`
- Test: `publicar-backlog-azure-boards/tests/test_executar_publicacao.py`

**Interfaces:**

- Consumes: `PlanoPublicacao`, `ConfiguracaoPublicacao`, `OperacaoCriacao` e cliente com
  `configuracao: ConfiguracaoPublicacao`.
- Produces: `criar_autorizacao(plano: PlanoPublicacao, confirmacao: str, chaves: frozenset[str]) -> Autorizacao`,
  `Autorizacao` sem campo construtível `_confirmada`, método
  `valida_para(plano: PlanoPublicacao, configuracao_cliente: ConfiguracaoPublicacao) -> bool` e
  `chaves_autorizadas: frozenset[str]`.

- [ ] **Step 1: Escrever regressões para destino e estado privado**

```python
def test_cliente_de_outro_destino_e_rejeitado_antes_de_criar(plano, autorizacao, cliente_outro_projeto, caminho_manifesto):
    with pytest.raises(ErroAutorizacao):
        executar_plano(plano, autorizacao, cliente_outro_projeto, caminho_manifesto)
    assert cliente_outro_projeto.chaves_criadas == []


def test_confirmacao_nao_pode_ser_injetada_no_construtor():
    campos = inspect.signature(Autorizacao).parameters
    assert "_confirmada" not in campos
```

- [ ] **Step 2: Executar os testes e confirmar a falha**

Run: `cd publicar-backlog-azure-boards && uv run pytest tests/test_autorizacao.py tests/test_executar_publicacao.py -q`

Expected: os testes novos falham porque o executor aceita destino divergente ou o construtor expõe estado interno.

- [ ] **Step 3: Implementar impressão imutável e validação final**

```python
@dataclass(frozen=True)
class Autorizacao:
    hash_plano: str
    quantidade: int
    modalidade: ModalidadeAutorizacao
    chaves_autorizadas: frozenset[str]
    impressao_destino: str
    impressao_conteudo: str
    confirmacao: str

    def valida_para(self, plano: PlanoPublicacao, destino: ConfiguracaoPublicacao) -> bool:
        return (
            self.hash_plano == plano.hash_plano
            and self.quantidade == len(self.chaves_autorizadas)
            and self.impressao_destino == imprimir_destino(destino)
            and self.impressao_conteudo == imprimir_operacoes(plano, self.chaves_autorizadas)
            and self.chaves_autorizadas <= {op.chave for op in plano.operacoes}
        )
```

Faça a fábrica validar a frase completa antes de construir a instância. O executor deverá comparar
`cliente.configuracao` com `plano.configuracao` antes de consultar o manifesto ou criar o primeiro item.
Para modalidade inteira, a fábrica materializa todas as chaves pendentes do plano no momento da
confirmação; para lotes, materializa apenas as chaves daquele lote.

- [ ] **Step 4: Executar regressões e suíte de autorização**

Run: `uv run pytest tests/test_autorizacao.py tests/test_executar_publicacao.py -q`

Expected: PASS; uma autorização com quantidade, destino, conteúdo, mapeamento ou cliente divergente não cria itens.

- [ ] **Step 5: Commitar**

```bash
git add src/publicar_backlog_azure_boards tests/test_autorizacao.py tests/test_executar_publicacao.py
git commit -m "fix: vincula autorizacao ao destino e ao plano"
```

### Task 2: Fechar reconciliação de resultados incertos

**Files:**

- Modify: `publicar-backlog-azure-boards/src/publicar_backlog_azure_boards/modelos.py`
- Modify: `publicar-backlog-azure-boards/src/publicar_backlog_azure_boards/manifesto.py`
- Modify: `publicar-backlog-azure-boards/src/publicar_backlog_azure_boards/cliente_azure_devops.py`
- Modify: `publicar-backlog-azure-boards/src/publicar_backlog_azure_boards/executar_publicacao.py`
- Test: `publicar-backlog-azure-boards/tests/test_cliente_azure_devops.py`
- Test: `publicar-backlog-azure-boards/tests/test_manifesto.py`
- Test: `publicar-backlog-azure-boards/tests/test_executar_publicacao.py`

**Interfaces:**

- Consumes: `OperacaoCriacao`, `RegistroManifesto` e exceções REST existentes.
- Produces: `ReconciliaçãoPendente` persistível, `ErroCriacaoAmbigua` e bloqueio de execução para
  chave pendente até resolução manual explícita.

- [ ] **Step 1: Escrever testes para URL malformada e estado pendente**

```python
def test_url_2xx_malformada_gera_reconciliacao_pendente(cliente, plano, autorizacao, caminho):
    cliente.resposta_criacao = {"id": 10, "url": "https://[invalido"}
    with pytest.raises(ErroCriacaoAmbigua):
        executar_plano(plano, autorizacao, cliente, caminho)
    manifesto = ler_manifesto(caminho)
    assert manifesto.reconciliacoes["1.0.0"].resolucao == "pendente"


def test_reconciliacao_pendente_bloqueia_nova_criacao(cliente, plano, autorizacao, caminho):
    gravar_manifesto(caminho, manifesto_com_reconciliacao("1.0.0"))
    with pytest.raises(ErroReconciliacaoPendente):
        executar_plano(plano, autorizacao, cliente, caminho)
    assert cliente.chaves_criadas == []
```

- [ ] **Step 2: Executar os testes e confirmar a falha**

Run: `cd publicar-backlog-azure-boards && uv run pytest tests/test_cliente_azure_devops.py tests/test_manifesto.py tests/test_executar_publicacao.py -q`

Expected: falha porque `urlparse` pode propagar `ValueError` e o manifesto não bloqueia nova tentativa.

- [ ] **Step 3: Implementar classificação e persistência da ambiguidade**

Capture `ValueError`, `UnicodeError`, erro de transporte após envio e resposta 2xx sem ID/URL HTTPS
válida como `ErroCriacaoAmbigua`. Grave a reconciliação com chave, destino, tipo, título, hash,
timestamp e motivo, sem token. Não faça retry de POST. Antes de cada criação, rejeite qualquer
reconciliação pendente; a resolução manual deverá ser uma operação explícita fora do fluxo automático.

- [ ] **Step 4: Executar testes de falha parcial e segurança**

Run: `uv run pytest tests/test_cliente_azure_devops.py tests/test_manifesto.py tests/test_executar_publicacao.py -q`

Expected: PASS; estado pendente persiste atomicamente e impede POST posterior.

- [ ] **Step 5: Commitar**

```bash
git add src/publicar_backlog_azure_boards tests/test_cliente_azure_devops.py tests/test_manifesto.py tests/test_executar_publicacao.py
git commit -m "fix: preserva reconciliacao de criacoes ambiguas"
```

### Task 3: Tornar o validador estrutural realmente isolável

**Files:**

- Create or modify: `publicar-backlog-azure-boards/src/publicar_backlog_azure_boards/contrato_backlog.py`
- Modify: `publicar-backlog-azure-boards/src/publicar_backlog_azure_boards/validacao_estrutural.py`
- Modify: `publicar-backlog-azure-boards/pyproject.toml`
- Modify: `publicar-backlog-azure-boards/src/publicar_backlog_azure_boards/cli.py`
- Test: `publicar-backlog-azure-boards/tests/test_validacao_estrutural.py`
- Test: `publicar-backlog-azure-boards/tests/test_instalacao.py`

**Interfaces:**

- Consumes: regras de `gerar-backlog-azure-boards/scripts/validate_backlog.py` e um caminho Markdown.
- Produces: `validar_estrutura_backlog(caminho: Path) -> None` que funciona no checkout e em wheel
  instalado, sem procurar diretórios irmãos.

- [ ] **Step 1: Escrever testes de contrato e instalação**

```python
def test_rejeita_origem_e_refinement_status_ausentes(tmp_path):
    caminho = escrever_fixture_invalida(tmp_path, "# [Epic] 1.0.0\n\n## Description\ntexto")
    with pytest.raises(ErroValidacaoEstrutural):
        validar_estrutura_backlog(caminho)


def test_validador_empacotado_nao_acessa_diretorio_irmao(monkeypatch, caminho_valido):
    monkeypatch.setattr(Path, "is_file", lambda self: False)
    validar_estrutura_backlog(caminho_valido)
```

- [ ] **Step 2: Executar testes e confirmar a falha**

Run: `cd publicar-backlog-azure-boards && uv run pytest tests/test_validacao_estrutural.py tests/test_instalacao.py -q`

Expected: o teste de instalação falha porque o validador atual depende do checkout principal.

- [ ] **Step 3: Empacotar o contrato compartilhado**

Extraia ou copie somente a lógica determinística do validador para módulo incluído no pacote, sem
importar scripts por caminho absoluto. Preserve as regras de origem, `Refinement Status`, Card,
Conversation, hierarquia, campos obrigatórios e headings. Faça a CLI chamar a versão empacotada antes
de interpretação, planejamento, autorização ou construção do cliente de escrita.

- [ ] **Step 4: Verificar wheel real**

Run:

```bash
uv build
rm -rf /tmp/publicador-wheel-test
uv venv /tmp/publicador-wheel-test
uv pip install --python /tmp/publicador-wheel-test/bin/python dist/*.whl
/tmp/publicador-wheel-test/bin/publicar-backlog-azure-boards validar tests/fixtures/valid-backlog.md
```

Expected: o entry point instalado valida o fixture sem acesso a `gerar-backlog-azure-boards` como diretório irmão.

- [ ] **Step 5: Commitar**

```bash
git add src/publicar_backlog_azure_boards pyproject.toml tests/test_validacao_estrutural.py tests/test_instalacao.py
git commit -m "fix: empacota validador estrutural do backlog"
```

### Task 4: Corrigir CLI instalada, simulação e contrato REST

**Files:**

- Modify: `publicar-backlog-azure-boards/src/publicar_backlog_azure_boards/cli.py`
- Modify: `publicar-backlog-azure-boards/src/publicar_backlog_azure_boards/__init__.py`
- Modify: `publicar-backlog-azure-boards/src/publicar_backlog_azure_boards/cliente_azure_devops.py`
- Modify: `publicar-backlog-azure-boards/src/publicar_backlog_azure_boards/configuracao.py`
- Modify: `publicar-backlog-azure-boards/pyproject.toml`
- Modify: `publicar-backlog-azure-boards/tests/test_configuracao_projeto.py`
- Modify: `publicar-backlog-azure-boards/tests/test_cliente_azure_devops.py`
- Modify: `publicar-backlog-azure-boards/tests/test_skill_integration.py`

**Interfaces:**

- Consumes: `principal`, `ClienteAzureDevOps`, configuração e validador empacotado.
- Produces: entry point instalado funcional; `publicar --simulacao` sem token/HTTP; `--validar-apenas`
  com GETs remotos e zero POSTs; criação em `/workitems/$<tipo-remoto>`; token interativo sem eco.

- [ ] **Step 1: Escrever regressões de CLI e URL**

```python
def test_simulacao_funciona_sem_token_e_sem_http(backlog, monkeypatch):
    monkeypatch.setattr("httpx.Client", lambda *args, **kwargs: pytest.fail("HTTP inesperado"))
    assert principal(["publicar", str(backlog), "--simulacao"]) == 0


def test_entry_point_instalado_chama_cli():
    assert tomllib.loads(Path("pyproject.toml").read_text())["project"]["scripts"][
        "publicar-backlog-azure-boards"
    ] == "publicar_backlog_azure_boards:main"


def test_url_de_criacao_tem_cifrao(cliente, operacao):
    cliente.criar_item(operacao)
    assert "/workitems/$Epic" in str(cliente.ultima_chamada.url)
```

- [ ] **Step 2: Executar testes e confirmar a falha**

Run: `cd publicar-backlog-azure-boards && uv run pytest tests/test_configuracao_projeto.py tests/test_cliente_azure_devops.py tests/test_skill_integration.py -q`

Expected: falha se o wheel ainda aponta para o entry point antigo, se a simulação constrói autenticação ou se a URL não tem `$`.

- [ ] **Step 3: Implementar separação de configuração local/remota**

Carregue somente dados não secretos para simulação; adie token e construção de `httpx.Client` até
depois do desvio local. Use `getpass.getpass()` no prompt do token. Mantenha `--validar-apenas`
dependente de credencial, com GETs de verificação e zero criação.

- [ ] **Step 4: Ajustar entry point, URL e caminhos**

Faça `publicar_backlog_azure_boards:main` delegar a `cli.principal`. Use o tipo remoto configurado
na URL com cifrão. Compare Area/Iteration Paths por `name`, `path`, `url` e `structureType`, aceitando
as representações oficiais de classification nodes sem confundir o caminho do nó com o campo do item.

- [ ] **Step 5: Executar testes e commit**

Run: `uv run pytest tests/test_configuracao_projeto.py tests/test_cliente_azure_devops.py tests/test_skill_integration.py -q && uv run ruff check . && uv run mypy src`

Expected: PASS e zero POST nos testes de simulação/validação.

```bash
git add src/publicar_backlog_azure_boards pyproject.toml tests
git commit -m "fix: conecta cli instalada e endurece fluxo rest"
```

### Task 5: Fechar auditoria de dependências, formatação e documentação

**Files:**

- Modify: `publicar-backlog-azure-boards/pyproject.toml`
- Modify: `publicar-backlog-azure-boards/uv.lock`
- Modify: `publicar-backlog-azure-boards/README.md`
- Modify: `publicar-backlog-azure-boards/SKILL.md`
- Modify: `publicar-backlog-azure-boards/.env.example`
- Create: `publicar-backlog-azure-boards/references/auditoria-dependencias.md`
- Test: `publicar-backlog-azure-boards/tests/test_documentacao_operacional.py`

**Interfaces:**

- Consumes: saída real do `pip-audit`, comportamento final da CLI e critérios da spec.
- Produces: documentação sem afirmações falsas, dependências atualizadas quando compatível e
  relatório individual de vulnerabilidades que não puderem ser removidas.

- [ ] **Step 1: Escrever teste documental**

```python
def test_documentacao_descreve_bloqueios_de_seguranca():
    texto = Path("README.md").read_text()
    assert "reconciliação" in texto
    assert "sem eco" in texto
    assert "MCP" in texto and "opcional" in texto
```

- [ ] **Step 2: Executar auditorias reais**

Run:

```bash
cd publicar-backlog-azure-boards
uv run ruff format --check .
uv run pip-audit --format json > pip-audit.json
```

Expected: identificar arquivos ainda não formatados e registrar cada vulnerabilidade por ID, pacote,
caminho transitivo, escopo produção/desenvolvimento e versão corretiva.

- [ ] **Step 3: Corrigir ou justificar cada dependência**

Atualize versões compatíveis no `pyproject.toml`/`uv.lock` e repita o audit. Para cada aviso sem
correção compatível, escreva em `references/auditoria-dependencias.md` o ID, a razão de não afetar o
caminho de produção ou a mitigação adotada, além da data e do responsável pela decisão. Não use
`|| true`, exclusões amplas ou filtros que escondam o aviso.

- [ ] **Step 4: Atualizar documentação operacional**

Documente simulação sem token, `--validar-apenas` remoto sem POST, reconciliação manual obrigatória,
confirmação vinculada ao plano, Area Paths `Sustentacao`/`Projeto`, Iteration Path por sprint, REST
obrigatória, MCP opcional e nunca versionar token.

- [ ] **Step 5: Rodar qualidade completa e commit**

Run:

```bash
uv run pytest -q
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv run bandit -r src
uv run semgrep --config auto src
uv run pip-audit
```

Expected: todos passam; se `pip-audit` ainda tiver exceções, o relatório individualizado deve estar
presente e o resultado deve ser explicitamente tratado na revisão final.

```bash
git add .
git commit -m "docs: fecha auditoria operacional do publicador"
```

### Task 6: Integração final, revisão do plano e evidência de aceitação

**Files:**

- Test: `publicar-backlog-azure-boards/tests/test_integracao_final.py`
- Modify: `docs/superpowers/sdd/2026-09-15-publicar-backlog-azure-boards/progress.md`

**Interfaces:**

- Consumes: todos os módulos e fixtures das tarefas anteriores.
- Produces: evidência reproduzível de que o plano completo funciona sem escrita acidental.

- [ ] **Step 1: Escrever teste de fluxo completo simulado**

```python
def test_fluxo_completo_exige_confirmacao_e_grava_manifesto(tmp_path, backlog, cliente):
    assert principal(["publicar", str(backlog), "--simulacao"]) == 0
    assert cliente.chaves_criadas == []
    plano = criar_plano_completo(backlog, cliente.configuracao)
    autorizacao = criar_autorizacao(
        plano, criar_frase_confirmacao(plano, ModalidadeAutorizacao.INTEIRO),
        frozenset(op.chave for op in plano.operacoes)
    )
    executar_plano(plano, autorizacao, cliente, tmp_path / "manifesto.json")
    assert set(ler_manifesto(tmp_path / "manifesto.json").itens) == {
        "1.0.0", "1.1.0", "1.1.1"
    }
```

- [ ] **Step 2: Executar aceitação completa**

Run: `cd publicar-backlog-azure-boards && uv run pytest -q`

Expected: todos os testes passam, incluindo destinos divergentes, lotes, reconciliação, wheel, simulação e validador.

- [ ] **Step 3: Revisar restrições globais**

Use `rg -n -- '--yes|bypassRules=true|AUTORIZAR PUBLICAÇÃO|Implementation Evidence|token|POST' src scripts SKILL.md README.md tests` e confirme manualmente que cada ocorrência de token é apenas configuração segura/teste, que `Implementation Evidence` não chega ao payload e que nenhuma simulação faz POST.

- [ ] **Step 4: Registrar resultado no ledger**

```markdown
Task 6: complete (hashes reais dos commits registrados no ledger, revisão final limpa)
```

Registre também qualquer exceção individual do `pip-audit`, sem declarar sucesso quando o comando retornar erro.

- [ ] **Step 5: Commitar evidência final**

```bash
    git add tests/test_integracao_final.py .superpowers/sdd/2026-09-15-publicar-backlog-azure-boards/progress.md
    git commit -m "test: comprova fluxo seguro do publicador"
```

## Autorrevisão do plano

- Cobertura da spec: autorização/destino na Task 1; reconciliação na Task 2; validador isolável na
  Task 3; CLI, token, URL e simulação na Task 4; auditoria/documentação na Task 5; aceitação integral
  na Task 6.
- Não há dependência implícita entre interfaces: cada tarefa declara seus consumos e produtos.
- O plano não altera o contrato Markdown, não adiciona FastAPI/Next.js/PostgreSQL e mantém MCP opcional.
- O único estado que permite nova escrita após resultado ambíguo é uma resolução manual explícita.
- Não há marcadores incompletos, `TODO`, `TBD` ou etapas sem comando e resultado esperado.

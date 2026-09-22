# Redigir spec de Demanda no Azure Boards Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Objetivo:** Criar a skill `redigir-spec-demanda-azure-boards`, que recebe o ID de uma Demanda de
Negócio, lê seus campos no Azure Boards somente por `GET` e conduz a geração rastreável de uma Spec,
incluindo análises técnicas, UX-UI e de copy quando aplicáveis.

**Arquitetura:** Um script Python autocontido consulta e valida o work item e seu contrato de campos,
produzindo JSON sem segredo. O `SKILL.md` consome esse JSON, produz a Spec-base mediante investigação
local somente leitura e orquestra as três skills especializadas em ordem segura, preservando as saídas
como documentos ou pareceres separados.

**Stack técnica:** Python 3.12+, `urllib` e `tomllib` da biblioteca padrão, `pytest`, `unittest`,
Markdown e YAML. Não adicionar dependência de execução nem reutilizar o pacote de publicação, pois o
leitor não escreve no Azure Boards.

**Spec:** `docs/superpowers/specs/2026-09-22-redigir-spec-demanda-azure-boards-design.md`

## Restrições globais

- Todo conteúdo novo é escrito em português brasileiro.
- O único método HTTP permitido ao leitor é `GET`; nunca execute `POST`, `PATCH`, `PUT` ou `DELETE`.
- A credencial vem de `AZURE_DEVOPS_TOKEN`, arquivo `.env`/TOML ou entrada segura; nunca aparece na
  Spec, JSON de saída, exceções, exemplos, logs ou histórico de comandos.
- O work item deve ter tipo remoto exatamente `Demanda de Negócio`.
- O contrato exige `System.Title` e os cinco campos `Custom.Demanda*` definidos na Spec aprovada.
- Campo definido sem valor vira lacuna; campo ausente no tipo é erro e interrompe o fluxo.
- A investigação de código continua somente leitura: não executar aplicação, scripts, testes, build,
  servidores ou migrações sem autorização explícita.
- A skill principal pode chamar `especificar-debitos-tecnicos`, `especificar-telas-ux-ui` e
  `revisar-textos-requisitos` somente nos gatilhos aprovados; nunca gera ou publica backlog.
- Sugestões de copy e decisões de UX-UI não são aceitas ou aplicadas silenciosamente.

---

## Estrutura de arquivos

```text
redigir-spec-demanda-azure-boards/
├── SKILL.md                                      # fluxo principal e formato da Spec
├── agents/openai.yaml                            # metadados da interface
├── scripts/
│   └── consultar_demanda.py                      # CLI REST somente leitura e módulos importáveis
├── references/
│   └── investigacao-demanda-azure-boards.md      # regras de investigação Brownfield
└── tests/
    ├── test_consultar_demanda.py                 # contrato REST, mapeamento e sigilo
    └── test_skill_integration.py                 # limites e orquestração declarados pela skill
```

Arquivos existentes a modificar:

```text
pyproject.toml                                    # inclui a nova pasta na descoberta do pytest
README.md                                         # documenta entrada por ID e a nova composição
```

## Interfaces entre tarefas

```python
@dataclass(frozen=True)
class ConfiguracaoAzureBoards:
    organizacao: str
    projeto: str
    token: str

@dataclass(frozen=True)
class DemandaNegocio:
    id: int
    url: str
    tipo: str
    titulo: str
    valores: dict[str, str | None]

class ErroConsultaDemanda(RuntimeError):
    pass

def carregar_configuracao(
    argumentos: argparse.Namespace,
    ambiente: Mapping[str, str] | None = None,
    ler_segredo: Callable[[str], str] | None = None,
) -> ConfiguracaoAzureBoards: ...

def consultar_demanda(
    id_item: int,
    configuracao: ConfiguracaoAzureBoards,
    requisitar: Callable[[str, Mapping[str, str]], Mapping[str, object]] = requisitar_json,
) -> DemandaNegocio: ...

def principal(argumentos: Sequence[str] | None = None) -> int: ...
```

`valores` usa as chaves de referência remota dos cinco campos customizados. A função `consultar_demanda`
primeiro solicita o work item e depois a lista de campos do seu tipo. `requisitar_json` é o adaptador de
rede padrão; a injeção de `requisitar` evita rede real nos testes.

### Task 1: Criar o leitor REST e validar o contrato da Demanda

**Arquivos:**

- Criar: `redigir-spec-demanda-azure-boards/scripts/consultar_demanda.py`
- Criar: `redigir-spec-demanda-azure-boards/tests/test_consultar_demanda.py`

**Interfaces:**

- Consome: nenhuma tarefa anterior.
- Produz: `ConfiguracaoAzureBoards`, `DemandaNegocio`, `ErroConsultaDemanda`, `consultar_demanda` e
  `requisitar_json`, usados pela CLI da Tarefa 2 e documentados pela Tarefa 3.

- [ ] **Passo 1: Inicializar a estrutura da skill sem exemplos**

  Rodar antes de criar os testes, pois o inicializador cria `SKILL.md`, `agents/openai.yaml`, `scripts/`
  e `references/` sem sobrescrever diretório já existente:

  ```bash
  uv run --with pyyaml python /Users/pedroct/.codex/skills/.system/skill-creator/scripts/init_skill.py \
    redigir-spec-demanda-azure-boards --path . --resources scripts,references \
    --interface display_name='Redigir spec a partir de Demanda no Azure Boards' \
    --interface short_description='Lê uma Demanda no Azure e produz Spec rastreável' \
    --interface default_prompt='Use $redigir-spec-demanda-azure-boards com o ID da Demanda de Negócio no Azure Boards.'
  ```

  Esperado: o diretório existe, com o `SKILL.md` ainda em scaffold. Não adicionar os arquivos criados
  ao Git até a Tarefa 3, quando o conteúdo final e o teste estático existirem.

- [ ] **Passo 2: Escrever o teste de mapeamento completo e validar que ele falha**

  Criar `test_consultar_demanda.py` com os contratos mínimos abaixo. O simulador registra URL e método
  efetivo da função injetada, sem criar cliente HTTP nem tocar em variáveis reais.

  ```python
  import importlib.util
  import sys
  from pathlib import Path

  SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "consultar_demanda.py"
  SPEC = importlib.util.spec_from_file_location("consultar_demanda", SCRIPT)
  assert SPEC is not None and SPEC.loader is not None
  modulo = importlib.util.module_from_spec(SPEC)
  sys.modules[SPEC.name] = modulo
  SPEC.loader.exec_module(modulo)

  CAMPOS = {
      "System.Title",
      "Custom.DemandaAreaSolicitante",
      "Custom.DemandaPublicoAlvo",
      "Custom.DemandaValorEsperado",
      "Custom.DemandaDoraResolver",
      "Custom.DemandaRegraseRestricoes",
  }

  def test_consultar_demanda_mapeia_campos_e_usa_apenas_urls_get() -> None:
      chamadas: list[str] = []

      def requisitar(url: str, cabecalhos: dict[str, str]) -> dict[str, object]:
          chamadas.append(url)
          if "/workitems/42?" in url:
              return {
                  "id": 42,
                  "url": "https://dev.azure.com/org/projeto/_apis/wit/workItems/42",
                  "fields": {
                      "System.WorkItemType": "Demanda de Negócio",
                      "System.Title": "Consultar débitos do contribuinte",
                      "Custom.DemandaAreaSolicitante": "Célula de Arrecadação",
                      "Custom.DemandaPublicoAlvo": "Auditor Fiscal",
                      "Custom.DemandaValorEsperado": "Reduzir retrabalho",
                      "Custom.DemandaDoraResolver": "Consulta é dispersa",
                      "Custom.DemandaRegraseRestricoes": "Restringir por perfil",
                  },
              }
          return {"value": [{"referenceName": campo} for campo in CAMPOS]}

      demanda = modulo.consultar_demanda(
          42, modulo.ConfiguracaoAzureBoards("org", "projeto", "segredo"), requisitar
      )

      assert demanda.id == 42
      assert demanda.titulo == "Consultar débitos do contribuinte"
      assert demanda.valores["Custom.DemandaDoraResolver"] == "Consulta é dispersa"
      assert len(chamadas) == 2
      assert all("api-version=" in url for url in chamadas)
      assert all(not any(verbo in url for verbo in ("POST", "PATCH", "PUT", "DELETE")) for url in chamadas)
  ```

  Rodar: `uv run pytest redigir-spec-demanda-azure-boards/tests/test_consultar_demanda.py -q`

  Esperado: falha de importação, pois o script ainda não existe.

- [ ] **Passo 3: Implementar os tipos, as constantes e a consulta mínima**

  Criar `consultar_demanda.py` com as constantes abaixo e a implementação mínima de
  `consultar_demanda`. Usar `urllib.parse.quote` nos segmentos de organização, projeto e tipo.

  ```python
  TIPO_DEMANDA = "Demanda de Negócio"
  CAMPOS_DEMANDA = (
      "System.Title",
      "Custom.DemandaAreaSolicitante",
      "Custom.DemandaPublicoAlvo",
      "Custom.DemandaValorEsperado",
      "Custom.DemandaDoraResolver",
      "Custom.DemandaRegraseRestricoes",
  )

  @dataclass(frozen=True)
  class DemandaNegocio:
      id: int
      url: str
      tipo: str
      titulo: str
      valores: dict[str, str | None]
  ```

  A primeira URL deve ser
  `https://dev.azure.com/{organizacao}/{projeto}/_apis/wit/workitems/{id}?$expand=Fields&api-version=7.1`.
  Da resposta, validar `id` inteiro positivo, `url` HTTPS não vazio, `fields` como objeto e
  `System.WorkItemType` exatamente igual a `TIPO_DEMANDA`. A segunda URL deve ser
  `/_apis/wit/workitemtypes/{tipo}/fields?api-version=7.1`; extrair o conjunto de `referenceName` e
  rejeitar a ausência de qualquer item de `CAMPOS_DEMANDA`.

  Para `System.Title`, exigir string não vazia após `strip()`. Nos cinco campos customizados, aceitar
  string não vazia como valor e converter `None` ou string só com espaços para `None`; rejeitar tipos
  não textuais em vez de serializá-los por coerção. A mensagem de `ErroConsultaDemanda` inclui o ID ou
  o nome do campo pertinente, mas nunca o token.

- [ ] **Passo 4: Rodar o teste de mapeamento**

  Rodar: `uv run pytest redigir-spec-demanda-azure-boards/tests/test_consultar_demanda.py -q`

  Esperado: o teste de mapeamento passa; nenhum acesso a rede real ocorre.

- [ ] **Passo 5: Acrescentar os testes de recusa do contrato**

  Adicionar casos parametrizados para ID `0` e `-1`, work item sem `fields`, ID remoto diferente,
  URL não HTTPS, tipo `User Story`, título vazio, campo customizado ausente na definição do tipo e
  campo customizado definido porém vazio. Exemplos de asserções:

  ```python
  @pytest.mark.parametrize("id_item", [0, -1])
  def test_consultar_demanda_rejeita_id_nao_positivo(id_item: int) -> None:
      with pytest.raises(modulo.ErroConsultaDemanda, match="ID"):
          modulo.consultar_demanda(id_item, CONFIGURACAO, requisitar_que_nao_deve_ser_chamado)

  def test_consultar_demanda_preserva_campo_vazio_como_lacuna() -> None:
      demanda = modulo.consultar_demanda(42, CONFIGURACAO, resposta_com_area_vazia)
      assert demanda.valores["Custom.DemandaAreaSolicitante"] is None

  def test_consultar_demanda_rejeita_campo_ausente_no_tipo() -> None:
      with pytest.raises(modulo.ErroConsultaDemanda, match="Custom.DemandaValorEsperado"):
          modulo.consultar_demanda(42, CONFIGURACAO, resposta_sem_valor_esperado_no_tipo)
  ```

  Rodar: `uv run pytest redigir-spec-demanda-azure-boards/tests/test_consultar_demanda.py -q`

  Esperado: falha nos casos ainda não tratados.

- [ ] **Passo 6: Completar validação defensiva e testar novamente**

  Implementar validadores privados para cada formato remoto antes de acessar chaves aninhadas. O
  payload de campos precisa ter `value` como lista não vazia de objetos com `referenceName` textual.
  Erros HTTP e JSON inválido devem tornar-se `ErroConsultaDemanda` com mensagem comunicável e sem
  corpo da resposta. Não retentar erros 400, 401, 403 ou 404.

  Rodar: `uv run pytest redigir-spec-demanda-azure-boards/tests/test_consultar_demanda.py -q`

  Esperado: todos os testes da Tarefa 1 passam.

- [ ] **Passo 7: Commitar a entrega testada**

  ```bash
  git add redigir-spec-demanda-azure-boards/scripts/consultar_demanda.py \
    redigir-spec-demanda-azure-boards/tests/test_consultar_demanda.py
  git commit -m "feat: consulta demanda de negocio no azure boards"
  ```

### Task 2: Adicionar configuração segura e a CLI JSON do leitor

**Arquivos:**

- Modificar: `redigir-spec-demanda-azure-boards/scripts/consultar_demanda.py`
- Modificar: `redigir-spec-demanda-azure-boards/tests/test_consultar_demanda.py`

**Interfaces:**

- Consome: `ConfiguracaoAzureBoards`, `DemandaNegocio`, `ErroConsultaDemanda` e `consultar_demanda`
  da Tarefa 1.
- Produz: `carregar_configuracao`, `requisitar_json` e `principal`, executáveis pela skill da Tarefa 3.

- [ ] **Passo 1: Escrever os testes de precedência e de sigilo**

  Cobrir argumento, TOML, `.env`, ambiente e entrada segura, nessa ordem. O fixture `.env` usa apenas
  valores fictícios. Verificar que o token não aparece em `str(erro)`, em `stdout` nem no JSON normal.

  ```python
  def test_configuracao_prefere_argumento_a_arquivo_e_ambiente(tmp_path: Path) -> None:
      env = tmp_path / ".env"
      env.write_text("AZURE_DEVOPS_ORGANIZACAO=env-org\nAZURE_DEVOPS_TOKEN=token-env\n")
      argumentos = modulo.construir_parser().parse_args(
          ["42", "--organizacao", "arg-org", "--projeto", "Projeto", "--env-file", str(env)]
      )
      configuracao = modulo.carregar_configuracao(argumentos, ambiente={})
      assert configuracao.organizacao == "arg-org"
      assert configuracao.token == "token-env"

  def test_principal_nao_expoe_token_em_falha(monkeypatch, capsys) -> None:
      monkeypatch.setattr(modulo, "consultar_demanda", levantar_erro_comunicavel)
      assert modulo.principal(["42", "--organizacao", "org", "--projeto", "p"]) == 1
      assert "segredo-de-teste" not in capsys.readouterr().out
  ```

  Rodar: `uv run pytest redigir-spec-demanda-azure-boards/tests/test_consultar_demanda.py -q`

  Esperado: falha porque parser, carregamento e `principal` ainda não existem.

- [ ] **Passo 2: Implementar carregamento de configuração com precedência explícita**

  Implementar `construir_parser()` com argumento posicional `id_item`, opções `--organizacao`,
  `--projeto`, `--config` e `--env-file` (padrão `.env`). Ler TOML com `tomllib`, aceitando a tabela
  `[azure_devops]` ou as chaves na raiz; ler `.env` linha a linha, ignorando comentários e linhas
  vazias. Para cada chave, usar nesta ordem: argumento, TOML, arquivo `.env`, `os.environ`.

  As chaves são `AZURE_DEVOPS_ORGANIZACAO`, `AZURE_DEVOPS_PROJETO` e `AZURE_DEVOPS_TOKEN`.
  Organização e projeto ausentes geram erro; token ausente solicita `getpass.getpass("Credencial do
  Azure DevOps: ")` apenas quando há terminal interativo, e em entrada não interativa gera erro sem
  tentar ler senha em texto aberto.

- [ ] **Passo 3: Implementar o adaptador HTTP somente leitura e a saída JSON**

  `requisitar_json` cria `urllib.request.Request(url, headers=..., method="GET")`, adiciona Basic Auth
  com `base64.b64encode(f":{token}".encode())` e chama `urlopen`. Limitar a três tentativas apenas para
  `URLError` transitório e HTTP 408, 429, 500, 502, 503 ou 504; usar espera exponencial curta. Encapsular
  `HTTPError`, `URLError`, erro de UTF-8 e `JSONDecodeError` sem incluir cabeçalhos ou corpo de resposta.

  `principal` chama `consultar_demanda`, serializa com `json.dumps(..., ensure_ascii=False)` e escreve
  exatamente os campos `id`, `url`, `tipo`, `titulo` e `campos`. O objeto `campos` contém somente os
  cinco `Custom.Demanda*`; não repetir `System.Title` nem serializar configuração.

- [ ] **Passo 4: Rodar testes unitários e um teste de CLI local**

  Rodar: `uv run pytest redigir-spec-demanda-azure-boards/tests/test_consultar_demanda.py -q`

  Rodar também:

  ```bash
  uv run python redigir-spec-demanda-azure-boards/scripts/consultar_demanda.py --help
  ```

  Esperado: a suíte passa e a ajuda não pede credencial nem faz requisição HTTP.

- [ ] **Passo 5: Commitar a CLI testada**

  ```bash
  git add redigir-spec-demanda-azure-boards/scripts/consultar_demanda.py \
    redigir-spec-demanda-azure-boards/tests/test_consultar_demanda.py
  git commit -m "feat: adiciona cli segura para ler demanda"
  ```

### Task 3: Criar a skill e formalizar a orquestração das análises

**Arquivos:**

- Criar: `redigir-spec-demanda-azure-boards/SKILL.md`
- Criar: `redigir-spec-demanda-azure-boards/agents/openai.yaml`
- Criar: `redigir-spec-demanda-azure-boards/references/investigacao-demanda-azure-boards.md`
- Criar: `redigir-spec-demanda-azure-boards/tests/test_skill_integration.py`

**Interfaces:**

- Consome: CLI `consultar_demanda.py` da Tarefa 2 e as interfaces declarativas das três skills
  especializadas já existentes.
- Produz: uma skill instalável que recebe ID, salva a Spec principal e preserva saídas especializadas
  separadas antes de devolver o controle ao usuário.

- [ ] **Passo 1: Escrever o teste estático que falha contra o scaffold**

  Criar o teste para exigir `System.Title`, os cinco campos customizados, `Demanda de Negócio`,
  `consultar_demanda.py`, `GET`, a proibição de escrita e as três skills especializadas. Incluir estes
  testes de comportamento declarativo:

  ```python
  def test_skill_exige_tipo_campos_e_leitura_sem_escrita() -> None:
      for texto in ("Demanda de Negócio", "System.Title", "Custom.DemandaDoraResolver", "GET"):
          assert texto in SKILL
      for verbo in ("POST", "PATCH", "PUT", "DELETE"):
          assert f"não execute {verbo}" in SKILL

  def test_orquestracao_preserva_limites_das_skills_chamadas() -> None:
      assert "especificar-debitos-tecnicos" in SKILL
      assert "especificar-telas-ux-ui" in SKILL
      assert "revisar-textos-requisitos" in SKILL
      assert "não aceita uma sugestão" in SKILL
      assert "documento separado" in SKILL
  ```

  Rodar: `uv run pytest redigir-spec-demanda-azure-boards/tests/test_skill_integration.py -q`

  Esperado: falha enquanto o `SKILL.md` contiver o scaffold.

- [ ] **Passo 2: Escrever `SKILL.md` e a referência de investigação**

  No `SKILL.md`, descrever exatamente esta sequência:

  1. receber o ID, executar `uv run python scripts/consultar_demanda.py <id>` e interromper em erro;
  2. registrar a fonte como Demanda de Negócio #ID, URL, tipo e tabela de campo remoto/valor;
  3. converter campo `null` em pergunta de lacuna e nunca atribuir `EXPLICITO`/`INFERIDO` ao pedido
     original;
  4. descobrir repositórios irmãos, investigar somente leitura e classificar Defeito/Melhoria/Outro;
  5. chamar `especificar-debitos-tecnicos` somente com evidência ligada ao escopo;
  6. chamar `especificar-telas-ux-ui` sempre sobre a Spec-base completa;
  7. chamar `revisar-textos-requisitos` somente havendo copy exibida a usuário, depois da análise de
     telas; salvar seu parecer sem aplicar sugestões automaticamente;
  8. salvar a Spec e documentos companheiros; não chamar entrevista, geração ou publicação de backlog.

  O template deve conter as seções `Fonte da Demanda`, `Escopo`, `Repositórios considerados`, `Problema
  relatado`, `Comportamento atual (evidência no código)`, `Comportamento esperado`, `Classificação`,
  `Atores e vocabulário identificados no código` e `Lacunas e perguntas abertas`.

  Na referência, copiar e adaptar as proteções úteis de
  `redigir-spec-pedido-negocio/references/business-request-investigation.md`: usar `rg`, `find` e
  `git status`; não executar aplicação/teste/build/migração; citar `caminho:linha`; separar "Registrado
  na Demanda", "Evidenciado pelo código" e "Lacuna"; registrar divergência sem escolher lado. Acrescentar
  que um campo da Demanda é evidência da síntese GEPRO, não prova de texto original da área.

- [ ] **Passo 3: Escrever metadados e verificar o teste estático**

  Definir `agents/openai.yaml` com `display_name`, `short_description` entre 25 e 64 caracteres e
  `default_prompt` que peça um ID. Manter invocação implícita habilitada.

  Rodar: `uv run pytest redigir-spec-demanda-azure-boards/tests/test_skill_integration.py -q`

  Esperado: todos os testes estáticos passam.

- [ ] **Passo 4: Validar o pacote da skill**

  Rodar:

  ```bash
  uv run --with pyyaml python /Users/pedroct/.codex/skills/.system/skill-creator/scripts/quick_validate.py \
    redigir-spec-demanda-azure-boards
  ```

  Esperado: validação sem placeholders ou falhas de frontmatter.

- [ ] **Passo 5: Commitar a skill instalável**

  ```bash
  git add redigir-spec-demanda-azure-boards/SKILL.md \
    redigir-spec-demanda-azure-boards/agents/openai.yaml \
    redigir-spec-demanda-azure-boards/references/investigacao-demanda-azure-boards.md \
    redigir-spec-demanda-azure-boards/tests/test_skill_integration.py
  git commit -m "feat: redige spec a partir de demanda no azure"
  ```

### Task 4: Integrar a descoberta no projeto e validar o fluxo sem Azure real

**Arquivos:**

- Modificar: `pyproject.toml`
- Modificar: `README.md`
- Modificar: `redigir-spec-demanda-azure-boards/tests/test_skill_integration.py`

**Interfaces:**

- Consome: a CLI estável da Tarefa 2 e a skill validada da Tarefa 3.
- Produz: nova skill descoberta pela suíte, documentada no fluxo e verificável sem credencial real.

- [ ] **Passo 1: Escrever as asserções de integração que inicialmente falham**

  Adicionar ao teste estático verificações de que o `README.md` inclui o nome da nova skill, o ID como
  entrada e os campos `Custom.Demanda*`; verificar que `pyproject.toml` inclui
  `redigir-spec-demanda-azure-boards/tests` em `testpaths`.

  Rodar:

  ```bash
  uv run pytest redigir-spec-demanda-azure-boards/tests/test_skill_integration.py -q
  ```

  Esperado: falha até a documentação e a configuração serem alteradas.

- [ ] **Passo 2: Atualizar `pyproject.toml` e `README.md`**

  Acrescentar `redigir-spec-demanda-azure-boards/tests` a `testpaths`. No README, incluir o caminho:

  ```text
  ID da Demanda de Negócio + Azure Boards + código-fonte
   └─ redigir-spec-demanda-azure-boards
       ├─ Spec-base rastreável
       ├─ Spec de débitos, quando houver evidência
       ├─ Briefing UX-UI, quando aplicável
       └─ Parecer de copy, quando houver texto de interface
  ```

  Adicionar uma linha à tabela "Skills disponíveis" com entrada "ID de uma Demanda de Negócio já criada
  no Azure Boards" e saída "Spec rastreável à Demanda e documentos companheiros". Atualizar a explicação
  de dependências para registrar que esta nova skill é a única predecessora que orquestra as três análises
  especializadas; ela não chama geração nem publicação de backlog.

- [ ] **Passo 3: Rodar a validação completa, sem rede**

  Rodar:

  ```bash
  uv run pytest
  uv run --with pyyaml python /Users/pedroct/.codex/skills/.system/skill-creator/scripts/quick_validate.py \
    redigir-spec-demanda-azure-boards
  git diff --check
  ```

  Esperado: toda a suíte passa, a validação da skill passa e não há erro de espaços em branco. Nenhum
  desses comandos usa `AZURE_DEVOPS_TOKEN` nem executa chamada remota.

- [ ] **Passo 4: Revisar a segurança do leitor antes do commit final**

  Rodar as verificações abaixo e resolver qualquer ocorrência que não seja a lista explicitamente
  permitida de constantes/testes:

  ```bash
  rg -n 'request\(|urlopen\(|POST|PATCH|PUT|DELETE|AZURE_DEVOPS_TOKEN' \
    redigir-spec-demanda-azure-boards
  git status --short
  ```

  Confirmar manualmente que `urlopen` é chamado apenas dentro de `requisitar_json`, que `Request` recebe
  `method="GET"`, que os verbos de escrita aparecem somente em guardas/documentação/testes e que token
  não é concatenado em saída ou exceção.

- [ ] **Passo 5: Commitar integração e documentação**

  ```bash
  git add pyproject.toml README.md \
    redigir-spec-demanda-azure-boards/tests/test_skill_integration.py
  git commit -m "docs: documenta spec por demanda no azure boards"
  ```

## Revisão do plano

### Cobertura da especificação

| Exigência aprovada | Tarefa que a implementa |
|---|---|
| Entrada por ID e leitura REST somente por GET | 1 e 2 |
| Tipo e seis campos com validação de contrato | 1 |
| Credencial protegida, configuração e retentativas seguras | 2 |
| Spec rastreável, investigação local e classificação | 3 |
| Débitos, telas e copy na ordem e nos gatilhos aprovados | 3 |
| Descoberta, documentação e execução sem Azure real | 4 |

### Verificação de consistência

As únicas interfaces de código consumidas em tarefas posteriores — `ConfiguracaoAzureBoards`,
`DemandaNegocio`, `ErroConsultaDemanda`, `consultar_demanda`, `carregar_configuracao`, `requisitar_json`
e `principal` — são definidas na seção de interfaces e produzidas antes do consumo. Não há campo ou
função com nome alternativo no plano. O fluxo de UI ocorre antes da revisão de copy; a saída de copy
permanece parecer separado e não altera a intenção de negócio sem decisão humana.

# Design: publicação de backlog vinculado a uma Demanda de Negócio no Azure Boards

## Contexto

`redigir-spec-demanda-azure-boards` já parte do ID de uma Demanda de Negócio para produzir a Spec, e
`gerar-backlog-azure-boards` transforma essa Spec em backlog Markdown. A publicação, porém, perde o
elo: `publicar-backlog-azure-boards` cria Épico, Feature e História sem pai externo, de modo que a
hierarquia publicada fica solta no projeto, sem rastro até a Demanda que a originou.

O board de destino já pratica o vínculo manualmente. A Demanda de Negócio 13959 ("PADRONIZAÇÃO E
ATUALIZAÇÃO DAS STACKS DA APLICAÇÃO") tem, no painel *Related Work*, o Épico 13969 como **Child**, e
abaixo dele a Feature 13970 e a História 13972. O vínculo é hierárquico de verdade, não um link
`Related`: o Épico carrega `System.LinkTypes.Hierarchy-Reverse` apontando para a Demanda.

Esta spec descreve uma skill nova, `publicar-backlog-demanda-azure-boards`, que recebe o ID da
Demanda junto com o backlog Markdown já revisado e publica a hierarquia inteira pendurada nela.

## Objetivos

1. Receber o ID da Demanda de Negócio e publicar todos os Épicos do backlog como filhos dela.
2. Herdar `Area Path` e `Iteration Path` da própria Demanda, eliminando essa configuração por execução.
3. Reproduzir a convenção de título já praticada no board: `01`, `01.01`, `01.01.01`, sem prefixo de data.
4. Preservar integralmente as garantias de escrita do publicador de origem: autorização por frase exata
   vinculada ao conteúdo executável, manifesto de retomada, ordem determinística e recusa de repetir um
   POST de resultado ambíguo.
5. Vincular o ID da Demanda ao hash do plano, à frase de autorização e ao manifesto, de modo que uma
   autorização emitida para uma Demanda nunca valha para outra.

## Fora de escopo

- **Nível Task.** O exemplo do board mostra a Task 13974 sob a História 13972, mas ela é criada
  manualmente pelo time. O contrato de backlog continua conhecendo apenas `Epic`, `Feature`,
  `User Story` e `Bug`, e nem o Markdown nem o publicador ganham um quarto nível.
- **Geração do backlog.** A skill recebe um backlog Markdown já gerado e revisado. Ela não lê a Spec,
  não decompõe requisitos e não chama `gerar-backlog-azure-boards`.
- **Escrita sobre a Demanda.** Nenhum `PATCH` toca o work item da área. O vínculo nasce do lado do
  Épico, no mesmo POST que o cria.
- **Alteração de `publicar-backlog-azure-boards`.** A skill de origem permanece como está.

## Decisões tomadas e seus custos

### Fork com pacote próprio

A skill nova é um fork completo de `publicar-backlog-azure-boards`, com pacote próprio, e não uma
camada fina sobre o pacote existente. A decisão é deliberada e tem um custo conhecido: o núcleo
sensível — autorização vinculada ao hash, manifesto, reconciliação de criação ambígua — passa a
existir em duas cópias, que podem divergir silenciosamente. O repositório já convive com uma
duplicação assim (`contrato_backlog.py` é cópia embarcada de `validate_backlog.py` e exige
ressincronização manual).

Para limitar o dano, quatro módulos permanecem **cópia literal, byte a byte**, e um teste dedicado
compara esses arquivos com os da skill de origem, falhando quando um lado muda sem o outro. O teste
se marca como `skipped` quando a skill de origem não está presente, para que a skill nova continue
instalável isoladamente. Essa defesa cobre apenas os módulos que deveriam permanecer iguais; os
módulos que divergem de propósito continuam sob responsabilidade humana.

### Simulação deixa de ser offline

Hoje `--simulacao` não pede token e não faz chamada HTTP alguma. Como `Area Path` e `Iteration Path`
passam a vir da Demanda, não há como montar o plano — nem o hash — sem ler o work item. A simulação
passa a exigir token e a executar **exatamente um `GET`**, mantendo intactas as demais garantias:
nenhuma escrita, nenhuma autorização solicitada.

A alternativa descartada era reintroduzir `--area-path`/`--iteration-path` apenas para simular, o que
ressuscitaria a configuração que a herança veio eliminar. O comando `validar` continua totalmente
local e sem token, preservando um caminho offline para conferir o documento.

## Arquitetura

Diretório `publicar-backlog-demanda-azure-boards/`, irmão das demais skills na raiz, com pacote
`publicar_backlog_demanda_azure_boards` e CLI `scripts/publicar_backlog_demanda.py`.

| Módulo | Origem | Mudança |
|---|---|---|
| `contrato_backlog.py` | cópia literal | nenhuma |
| `converter_para_html.py` | cópia literal | nenhuma |
| `interpretar_markdown.py` | cópia literal | nenhuma |
| `validacao_estrutural.py` | cópia literal | nenhuma |
| `modelos.py` | cópia | nova dataclass `Demanda`; `ConfiguracaoPublicacao` ganha `demanda_id` |
| `titulo_hierarquico.py` | novo | conversão de chave documental em numeração de título |
| `planejar_publicacao.py` | cópia | título hierárquico no lugar do título datado |
| `executar_publicacao.py` | cópia | pai externo para os Épicos |
| `cliente_azure_devops.py` | cópia | `obter_demanda`; `validar_operacao` passa a mandar `id_pai` |
| `autorizacao.py` | cópia | ID da Demanda na frase e na impressão de destino |
| `manifesto.py` | cópia | grava e valida `demanda_id` |
| `configuracao.py` | cópia | perde os caminhos manuais; ganha `demanda_id` e `tipo_demanda` |
| `cli.py` | cópia | ganha `--demanda`; perde `--area-path` e `--iteration-path` |

### Leitura da Demanda e derivação do destino

`Demanda` é o resultado transitório de um `GET` no work item:

```python
@dataclass(frozen=True)
class Demanda:
    id: int
    titulo: str
    area_path: str
    iteration_path: str
    url: str
```

Ela serve a dois propósitos e a nenhum outro: **derivar** a configuração de publicação e **exibir** a
origem no plano apresentado.

`ConfiguracaoPublicacao` carrega apenas `demanda_id: int`, nunca o objeto inteiro. A razão é
operacional: `executar_plano` compara a configuração do cliente com a do plano por igualdade, e
`validar_manifesto` compara a configuração gravada com a da execução atual. Se o título ou a URL da
Demanda entrassem nessa comparação, uma edição cosmética do título no Azure Boards invalidaria um
manifesto válido e bloquearia uma retomada legítima. `titulo` e `url` são material de exibição e não
participam de hash, impressão de destino nem manifesto.

`System.AreaPath` e `System.IterationPath` da Demanda alimentam `ConfiguracaoPublicacao.area_path` e
`.iteration_path`, que seguem sendo verificados por `verificar_destino` como hoje.

### Numeração e título

`titulo_hierarquico.py` converte a chave documental `E.F.S` em numeração de título:

| Tipo | Chave | Numeração | Título final |
|---|---|---|---|
| Epic | `1.0.0` | `01` | `01 Gestão do projeto` |
| Feature | `1.1.0` | `01.01` | `01.01 Gestão do projeto` |
| User Story / Bug | `1.1.1` | `01.01.01` | `01.01.01 Análise de padrões de stacks` |

Cada componente é preenchido com zero à esquerda até dois dígitos. Um componente acima de 99 é
preservado inteiro, sem truncamento: `100.0.0` vira `100` e `1.1.112` vira `01.01.112`. Histórias e
Bugs compartilham a mesma sequência `S` sob a Feature, como já define o contrato do backlog.

O texto do título continua vindo de `titulo_curto or titulo`, como no original.

A data de geração sai do título, mas **continua sendo lida do Markdown, exibida no plano e incluída no
hash**. É ela que distingue duas gerações do mesmo backlog e impede que uma autorização emitida para
uma versão antiga valha para um documento regerado.

### Vínculo com a Demanda

Em `executar_plano`, uma operação cujo `chave_pai` é `None` — isto é, todo Épico — recebe
`id_pai = demanda_id`. Features e Histórias continuam resolvendo o pai pelo manifesto, sem alteração.
Se o backlog tiver vários Épicos, todos se tornam filhos da mesma Demanda.

O patch enviado é o mesmo que já liga Feature a Épico:

```json
{"op": "add", "path": "/relations/-",
 "value": {"rel": "System.LinkTypes.Hierarchy-Reverse",
           "url": ".../_apis/workItems/13959"}}
```

`validar_operacao` passa a receber e enviar o `id_pai`. Hoje ela valida com `id_pai=None`, o que faria
`--validar-apenas` conferir um Épico órfão e deixar o risco novo — a aceitação de Épico como filho de
Demanda pelo processo remoto — sem verificação antes da escrita.

### Autorização, hash e manifesto

`demanda_id` entra em `ConfiguracaoPublicacao`, mas isso não basta: `assinatura_plano`,
`_calcular_hash` e `imprimir_destino` montam dicionários enumerando campo a campo, então as três
precisam passar a incluí-lo explicitamente. Omitir qualquer uma delas deixaria a autorização
desvinculada da Demanda, que é justamente o risco que esta seção existe para fechar. A frase de
confirmação passa a nomear a Demanda:

```text
AUTORIZAR PUBLICAÇÃO 3 ITENS DEMANDA 13959 CESOP-DILIGENCIA CESOP-DILIGENCIA\Sustentacao CESOP-DILIGENCIA\Sustentacao 7F3A
```

`manifesto.py` grava `demanda_id` e `validar_manifesto` recusa retomar um manifesto emitido para outra
Demanda, ainda que o backlog e o destino sejam idênticos.

### Configuração e CLI

```bash
uv run python scripts/publicar_backlog_demanda.py validar ../backlog.md
uv run python scripts/publicar_backlog_demanda.py planejar ../backlog.md --demanda 13959
uv run python scripts/publicar_backlog_demanda.py publicar ../backlog.md --demanda 13959 --simulacao
uv run python scripts/publicar_backlog_demanda.py publicar ../backlog.md --demanda 13959 --validar-apenas
uv run python scripts/publicar_backlog_demanda.py publicar ../backlog.md --demanda 13959
```

`--demanda` é exigido em `planejar` e `publicar`, e não em `validar`, que permanece uma conferência
estrutural do documento. A precedência continua sendo linha de comando, TOML de `--config`, `.env` de
`--env-file` e pergunta interativa.

| Dado | Argumento | Variável de ambiente |
|---|---|---|
| Organização | `--organizacao` | `AZURE_DEVOPS_ORGANIZACAO` |
| Projeto | `--projeto` | `AZURE_DEVOPS_PROJETO` |
| Demanda | `--demanda` | `AZURE_DEVOPS_DEMANDA` |
| Tipo da Demanda | `--tipo-demanda` | `AZURE_DEVOPS_TIPO_DEMANDA` |
| Tipos de item | `--tipo-epic`, `--tipo-feature`, `--tipo-user-story`, `--tipo-bug` | `AZURE_DEVOPS_TIPO_*` |
| Credencial | — | `AZURE_DEVOPS_TOKEN` |

`AZURE_DEVOPS_AREA_PATH`, `AZURE_DEVOPS_AREA_PATHS` e `AZURE_DEVOPS_ITERATION_PATH` deixam de existir,
junto com a lógica de seleção explícita entre múltiplos Area Paths, que perde sentido quando o caminho
vem da Demanda.

O tipo da Demanda é configurável, com padrão `Demanda de Negócio`, pela mesma razão que `User Story`
já é: em outro processo o nome remoto pode ser diferente, e o pacote nunca adivinha nome remoto.

A credencial vem exclusivamente de `AZURE_DEVOPS_TOKEN` ou de entrada segura em terminal interativo.
Nunca por argumento, nunca em log, nunca versionada.

## Fluxo da skill

1. Validação estrutural local do backlog, sem token e sem rede.
2. Carregamento da configuração, incluindo `--demanda`.
3. `GET` da Demanda; validação de tipo e de projeto; extração de título, Area Path e Iteration Path.
4. Montagem de `ConfiguracaoPublicacao` a partir da Demanda e criação do plano, com títulos
   hierárquicos e hash vinculado ao `demanda_id`.
5. Verificação preliminar somente leitura: credencial, destino, tipos, campos, relação hierárquica e
   caminhos.
6. Apresentação do plano, encabeçado pela origem:

   ```text
   Demanda de Negócio  #13959 — PADRONIZAÇÃO E ATUALIZAÇÃO DAS STACKS DA APLICAÇÃO
   Area Path           CESOP-DILIGENCIA\Sustentacao      (herdado da Demanda #13959)
   Iteration Path      CESOP-DILIGENCIA\Sprint 18        (herdado da Demanda #13959)
   Backlog gerado em   2026-09-22
   ```

   O Area Path acima é o do exemplo real; o Iteration Path é ilustrativo, porque depende de em qual
   sprint a Demanda está registrada.

7. Escolha entre backlog inteiro, lotes ou cancelamento; em lotes, o tamanho e a reapresentação de cada
   lote.
8. Digitação da frase integral.
9. Execução sequencial, com o manifesto atualizado após cada criação.

## Validações e erros

Cada uma interrompe o fluxo antes de qualquer criação:

| Situação | Resultado |
|---|---|
| ID ausente, não numérico ou não positivo | erro de configuração, nomeando o dado que faltou |
| Work item inexistente | `ErroDestinoInvalido` citando o ID |
| Tipo diferente do configurado | interrompe nomeando o tipo encontrado |
| Demanda em outro `System.TeamProject` | recusa; o link hierárquico não cruza projeto |
| Demanda sem `System.AreaPath` ou `System.IterationPath` | erro de contrato; não há de onde herdar |
| Manifesto emitido para outra Demanda | recusa a retomada |

A rejeição do vínculo pelo processo remoto — caso Épico não seja filho aceitável de Demanda de Negócio
em algum projeto — aparece em `--validar-apenas` e, no limite, no POST. Ela é propagada como falha
definitiva, sem retentativa.

## Limites

- A Demanda de Negócio nunca é escrita; o vínculo nasce do lado do Épico.
- Não existe `--yes`, confirmação implícita ou manifesto como autorização.
- Não se usa `bypassRules=true`, exclusão, rollback ou atualização automática.
- Um POST de resultado ambíguo não é repetido: o manifesto exige reconciliação manual.
- A skill não gera nem revisa backlog, não lê a Spec e não cria Tasks.

## Arquivos previstos

```text
publicar-backlog-demanda-azure-boards/
├── SKILL.md
├── README.md
├── pyproject.toml
├── .env.example
├── .gitignore
├── agents/openai.yaml
├── scripts/publicar_backlog_demanda.py
├── src/publicar_backlog_demanda_azure_boards/
│   ├── __init__.py
│   ├── autorizacao.py
│   ├── cliente_azure_devops.py
│   ├── configuracao.py
│   ├── contrato_backlog.py
│   ├── converter_para_html.py
│   ├── executar_publicacao.py
│   ├── interpretar_markdown.py
│   ├── manifesto.py
│   ├── modelos.py
│   ├── planejar_publicacao.py
│   ├── titulo_hierarquico.py
│   └── validacao_estrutural.py
└── tests/
    ├── test_autorizacao.py
    ├── test_autorizacao_vinculada_a_demanda.py
    ├── test_cliente_azure_devops.py
    ├── test_configuracao_projeto.py
    ├── test_converter_para_html.py
    ├── test_documentacao_operacional.py
    ├── test_executar_publicacao.py
    ├── test_instalacao.py
    ├── test_integracao_final.py
    ├── test_interpretar_markdown.py
    ├── test_manifesto.py
    ├── test_obter_demanda.py
    ├── test_planejar_publicacao.py
    ├── test_sincronia_com_origem.py
    ├── test_skill_integration.py
    ├── test_titulo_hierarquico.py
    ├── test_validacao_estrutural.py
    └── test_vinculo_demanda.py
```

Também mudam, fora do diretório da skill:

- `README.md` da raiz: contagem de capacidades, tabela de skills e o diagrama do fluxo de publicação.

## Estratégia de testes

Os treze arquivos de teste da skill de origem são forkados e adaptados. Nenhum teste toca o Azure real:
o transporte HTTP é mockado, como já acontece hoje.

Testes novos:

- **`test_titulo_hierarquico.py`** — conversão de `1.0.0`, `1.1.0`, `1.1.1`; preenchimento com zero;
  preservação de componentes acima de 99; uso de `titulo_curto` quando presente.
- **`test_obter_demanda.py`** — tipo correto; tipo divergente; work item inexistente; projeto
  divergente; `System.AreaPath` ou `System.IterationPath` ausente.
- **`test_vinculo_demanda.py`** — todo Épico sobe com `Hierarchy-Reverse` apontando para a Demanda;
  Features e Histórias continuam apontando para seus pais do backlog; backlog com vários Épicos
  pendura todos na mesma Demanda; `validar_operacao` envia o `id_pai`.
- **`test_autorizacao_vinculada_a_demanda.py`** — a frase emitida para a Demanda 13959 não autoriza
  publicar sob outra Demanda; o manifesto de uma Demanda não libera retomada sob outra; alterar apenas
  o `demanda_id` muda o hash do plano.
- **`test_sincronia_com_origem.py`** — os quatro módulos de cópia literal são idênticos aos da skill de
  origem; `skip` quando a skill de origem não está presente.

## Critérios de conclusão

1. `uv run pytest` passa no diretório da skill nova, com os testes novos cobrindo vínculo, título,
   leitura da Demanda e autorização vinculada.
2. `--simulacao` produz o plano completo a partir do ID, com um único `GET` e zero escritas.
3. `--validar-apenas` exercita o vínculo com a Demanda via `validateOnly=true`, sem criar work items.
4. A publicação real contra a Demanda 13959 — passo manual, executado por você, fora da
   implementação — produz a hierarquia
   Demanda → Épico → Feature → História com os títulos `01`, `01.01`, `01.01.01` e os caminhos herdados.
5. `SKILL.md`, `README.md` da skill e `README.md` da raiz descrevem o fluxo, os limites e a
   configuração, todos em português brasileiro.
6. Os hooks de lint e formatação do repositório passam sem achado novo.

# Design: redação de spec a partir de uma Demanda de Negócio no Azure Boards

## Contexto

A aplicação GEPRO já transforma uma necessidade recebida da área de negócio em um work item
personalizado **Demanda de Negócio** no Azure Boards. A transformação armazena uma síntese estruturada,
mas a redação de uma Spec ainda exige que alguém copie esse conteúdo para fora do Boards antes de iniciar
a investigação do produto.

A skill `redigir-spec-pedido-negocio` resolve a etapa posterior: investiga o código local somente em
leitura e produz uma Spec. A nova skill deve aproveitar esse mesmo modelo de Spec, trocando a fonte de
entrada por uma Demanda existente identificada pelo seu ID. Ela não altera a Demanda, não publica backlog
e não depende de o usuário copiar os campos manualmente.

## Objetivos

1. Criar a skill `redigir-spec-demanda-azure-boards`.
2. Receber como entrada um ID numérico de work item e recuperar a Demanda de Negócio correspondente por
   REST, exclusivamente com operações `GET`.
3. Validar que o item lido tem o tipo remoto `Demanda de Negócio` e que os campos customizados esperados
   estão disponíveis para esse tipo.
4. Transformar os campos recuperados em uma Spec Markdown compatível com
   `gerar-backlog-azure-boards`, investigando o código local em modo somente leitura.
5. Preservar rastreabilidade da Spec para o ID, URL, tipo e campos de origem do Azure Boards.
6. Converter valores ausentes em lacunas e perguntas abertas, sem preencher por plausibilidade.
7. Orquestrar, quando houver insumo aplicável, as skills de débitos técnicos, UX-UI e revisão de copy
   antes de encerrar a elaboração da Spec.

## Fora de escopo

- Criar, atualizar, mover, comentar, relacionar ou excluir work items.
- Ler ou alterar dados na aplicação GEPRO.
- Recuperar o e-mail, mensagem ou outro texto original submetido à GEPRO quando ele não estiver no work
  item; a fonte desta skill é a Demanda estruturada, não o pedido primário.
- Alegar que um dado é `EXPLICITO` ou `INFERIDO` no pedido original. Esses metadados não são persistidos
  no Azure Boards e não podem ser reconstituídos com segurança.
- Gerar Épico, Feature, História, Description, Acceptance Criteria ou publicar backlog.
- Encadear automaticamente geração ou publicação de backlog após salvar a Spec.

## Contrato de entrada e campos

A skill recebe o ID como único dado funcional obrigatório. Organização, projeto e credencial seguem a
precedência já usada pelo publicador: argumento, arquivo TOML indicado, arquivo `.env` indicado e
variáveis de ambiente. A credencial fica exclusivamente em `AZURE_DEVOPS_TOKEN` ou em entrada segura;
nunca entra no comando registrado, na Spec, em exemplos ou em logs.

O leitor consulta o work item e a definição de campos do respectivo tipo. O mapeamento é fixo e
intencionalmente explícito:

| Conteúdo da Spec | Campo do Azure Boards |
|---|---|
| Título | `System.Title` |
| Área solicitante | `Custom.DemandaAreaSolicitante` |
| Público-alvo | `Custom.DemandaPublicoAlvo` |
| Valor esperado | `Custom.DemandaValorEsperado` |
| Dor a resolver | `Custom.DemandaDoraResolver` |
| Regras e restrições | `Custom.DemandaRegraseRestricoes` |

Um campo que existe no tipo mas não tem valor é uma lacuna de negócio. Um campo que não existe no tipo
remoto é erro de contrato: a skill interrompe antes de redigir a Spec, informa o nome exato ausente e não
adivinha um campo alternativo. O título também é obrigatório; se estiver vazio, a leitura falha.

## Proveniência e confiança

Cada valor extraído é classificado apenas como **registrado na Demanda de Negócio**. Isso é diferente de
estar explícito no pedido original: a GEPRO pode ter resumido ou inferido o dado, e a informação que
permitiria distinguir os dois casos não está no Azure Boards.

A seção de fonte da Spec deve informar ID, URL, tipo e uma tabela `conteúdo da Spec | campo remoto |
valor`. A ausência de origem por campo não reduz a rastreabilidade para a Demanda, mas impede a skill de
apresentar uma inferência da GEPRO como fato declarado pela área solicitante. O código local continua
sendo tratado apenas como evidência de estado atual; não confirma intenção, valor ou decisão de negócio.

## Arquitetura

```text
ID da Demanda
       |
       v
scripts/consultar_demanda.py
  GET work item + GET campos do tipo
  valida ID, tipo e contrato de campos
       |
       v
registro estruturado e rastreável da Demanda
       |
       v
redigir-spec-demanda-azure-boards/SKILL.md
  investigação local de código somente leitura
  redação da Spec-base
       |
       +--> especificar-debitos-tecnicos (quando houver evidência relacionada)
       |
       +--> especificar-telas-ux-ui (avalia a Spec; gera briefing se aplicável)
       |
       `--> revisar-textos-requisitos (quando houver copy de interface)
       |
       v
  salvamento da Spec e dos documentos companheiros
       |
       v
Spec Markdown (revisão manual posterior)
```

O script é pequeno, autocontido e de leitura. Ele usa a API REST do Azure DevOps com `urllib` da
biblioteca padrão para que a skill continue instalável sem depender do pacote Python do publicador. A
duplicação é limitada à consulta autenticada e ao carregamento mínimo de configuração; a semântica de
publicação, manifestos e autorização do pacote `publicar-backlog-azure-boards` permanece isolada, pois
não é necessária nem apropriada para um fluxo de leitura.

O script aceita `--organizacao`, `--projeto`, `--env-file` e `--config`, além do ID. Ele faz somente:

1. `GET /_apis/wit/workitems/{id}?$expand=Fields`;
2. `GET /_apis/wit/workitemtypes/{tipo}/fields`.

Ele rejeita IDs não positivos, respostas malformadas, autenticação/permissão negadas, tipo diferente de
`Demanda de Negócio` e contrato de campos incompatível. Para falhas transitórias, repete somente os
`GET`s com limite pequeno e informa falha sem efetuar qualquer escrita. A saída normal é JSON UTF-8
estruturado, sem token, contendo o ID, URL, tipo, valores mapeados e a indicação de valor ausente.

## Fluxo da skill

1. Receber e validar o ID informado pelo usuário.
2. Executar o leitor local para obter e validar a Demanda; parar com uma mensagem clara se a consulta
   não puder ser autenticada, se o item não existir, se o tipo não corresponder ou se faltar um campo no
   contrato remoto.
3. Ler o conteúdo retornado. Tratar `null`, string vazia ou lista vazia como lacuna; não transformar a
   falta em texto genérico.
4. Descobrir os repositórios candidatos a partir do diretório onde a skill está instalada e de seus
   irmãos. Aplicar as regras de investigação de
   `references/investigacao-demanda-azure-boards.md`: somente leitura, evidência `caminho:linha` e
   separação entre Demanda, código e lacunas.
5. Redigir a Spec-base como item único. `Dor a resolver` é o problema relatado; `Público-alvo` e `Área`
   fundamentam os atores; `Valor esperado`, `Regras e restrições` e qualquer limitação explícita formam
   o comportamento esperado. Nenhum deles deve ser promovido a requisito confirmado além do que está
   registrado na Demanda.
6. Classificar a demanda como `Defeito`, `Melhoria` ou `Outro` a partir da comparação entre o conteúdo
   registrado e a evidência de comportamento atual, usando a mesma política da skill existente.
7. Quando a investigação localizar um débito técnico ligado ao escopo, chamar
   `especificar-debitos-tecnicos` com a evidência e a origem. Anexar ou vincular a Spec de débitos como
   documento separado; não misturar débito ao requisito de negócio nem fabricar um débito quando a
   investigação não o sustentar.
8. Chamar `especificar-telas-ux-ui` sobre a Spec-base. Essa skill avalia as plataformas e anota a Spec
   apenas quando uma tela ou fluxo exige especificação; o briefing de telas é documento companheiro e
   não decompõe a Demanda em itens de backlog.
9. Quando a Demanda, a Spec-base ou o briefing de telas contiverem texto exibido a usuários, chamar
   `revisar-textos-requisitos`. Anexar o parecer de copy ou salvá-lo como documento companheiro,
   preservando cada trecho, diagnóstico, sugestão e decisão pendente. A skill chamadora não aceita uma
   sugestão nem reescreve requisito silenciosamente: decisão de produto sem confirmação continua sendo
   lacuna.
10. Salvar a Spec atualizada e todos os documentos companheiros produzidos e parar. A próxima etapa de
    backlog é sempre manual.

## Orquestração das skills especializadas

As três skills especializadas entram durante a elaboração, não apenas durante o planejamento. Assim,
quem planejar ou gerar o backlog recebe a melhor evidência disponível, sem que a orquestradora se torne
dona de decisões de design, dívida ou copy.

| Skill | Gatilho | Entrada | Saída e preservação |
|---|---|---|---|
| `especificar-debitos-tecnicos` | Evidência de débito ligada ao escopo da Demanda | Evidência `caminho:linha`, origem na Demanda e contexto da Spec | Spec de débitos separada, vinculada na Spec principal; ausente quando não houver débito comprovado. |
| `especificar-telas-ux-ui` | Sempre após a Spec-base estar completa | Spec-base e repositórios acessíveis | Anotação na Spec e briefing de telas somente se a avaliação identificar necessidade aplicável. |
| `revisar-textos-requisitos` | Copy exibida ao usuário na Demanda, Spec ou briefing de telas | Trechos e seu contexto de uso | Parecer de copy separado ou anexo; sugestões nunca viram requisito automaticamente. |

Essa ordem é deliberada. A análise de telas pode revelar mensagens, CTAs, estados vazios ou bloqueios
que a Demanda não nomeava; por isso a revisão de copy acontece depois do briefing de UX-UI. Débitos
podem ser identificados já na investigação Brownfield e não dependem do desenho de tela, podendo ser
produzidos em paralelo conceitual, mas são vinculados apenas após a Spec-base ter uma origem estável.

Se a execução de uma skill especializada estiver indisponível, a orquestradora salva a Spec-base com a
indisponibilidade e a respectiva lacuna registrada, em vez de alegar que a análise ocorreu. Isso não
autoriza a substituição das saídas especializadas por texto inventado.

## Formato da Spec

```markdown
# Spec: <System.Title>

## Fonte da Demanda
- Azure Boards: Demanda de Negócio #<id> — <URL>
- Tipo validado: Demanda de Negócio

| Conteúdo | Campo remoto | Valor registrado |
|---|---|---|
| ... | ... | ... |

## Escopo
Tratado como item único; nenhuma decomposição foi aplicada.

## Repositórios considerados
| Repositório | Relevante? | Motivo |
|---|---|---|
| ... | ... | ... |

## Problema relatado
<síntese fiel de Custom.DemandaDoraResolver; a origem é a Demanda, não o texto original>

## Comportamento atual (evidência no código)
| Afirmação/observação | Evidência `caminho:linha` | Confiança |
|---|---|---|
| ... | ... | Alta/Média/Baixa |

## Comportamento esperado
- Registrado na Demanda: ...
- Inferência de análise: ...

## Classificação
- **Tipo**: Defeito | Melhoria | Outro
- **Justificativa**: ...

## Atores e vocabulário identificados no código
...

## Lacunas e perguntas abertas
...
```

## Arquivos previstos

```text
redigir-spec-demanda-azure-boards/
├── SKILL.md
├── agents/openai.yaml
├── scripts/
│   └── consultar_demanda.py
├── references/
│   └── investigacao-demanda-azure-boards.md
└── tests/
    ├── test_consultar_demanda.py
    └── test_skill_integration.py
```

Também serão atualizados `README.md` (fluxo e tabela de skills) e `pyproject.toml` (inclusão dos testes).
Nenhuma skill atual será alterada: a nova skill é uma predecessora isolada, como
`redigir-spec-pedido-negocio`.

## Estratégia de testes

1. Testes unitários do leitor com transporte HTTP simulado: mapeamento completo, valores vazios,
   work item inexistente, autenticação negada, tipo inesperado, campo inexistente, resposta inválida e
   garantia de que nenhuma requisição usa método diferente de `GET`.
2. Teste estático da skill: entrada por ID, mapeamento dos seis campos, validação do tipo, proibição de
   escrita e de encadeamento automático, presença da referência de investigação e template com
   rastreabilidade ao Azure Boards e orquestração condicional das skills especializadas.
3. Validação do `SKILL.md` pelo `quick_validate.py` executado com PyYAML disponível via `uv`.
4. Execução da suíte completa com `uv run pytest`, sem credencial real e sem chamadas ao Azure Boards.

## Critérios de conclusão

- Um ID válido de Demanda de Negócio gera uma Spec salva e rastreável aos campos remotos.
- Um campo sem valor aparece como lacuna, nunca como preenchimento plausível.
- Tipo ou contrato de campos inválidos interrompem o fluxo antes da Spec.
- O leitor não executa nenhum `POST`, `PATCH`, `PUT` ou `DELETE`.
- Débitos, telas e copy são analisados pelas skills donas de cada assunto quando seus gatilhos existirem;
  nenhum resultado delas é convertido silenciosamente em decisão de produto.
- A Spec permanece utilizável como entrada manual de `gerar-backlog-azure-boards`.

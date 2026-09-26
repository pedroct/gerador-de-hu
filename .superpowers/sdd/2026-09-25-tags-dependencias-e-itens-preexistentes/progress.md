# SDD ledger — plan: docs/superpowers/plans/2026-09-25-tags-dependencias-e-itens-preexistentes.md

Spec: docs/superpowers/specs/2026-09-25-tags-de-debito-tecnico-no-backlog-design.md (lida; é a
autoridade vinculante quando o plano se contradiz)

Worktree: .worktrees/tags-dependencias-itens-preexistentes, branch
`tags-dependencias-itens-preexistentes`, criada de HEAD local (693ccfc).
Baseline: 132 (publicar solto) + 224 (publicar demanda) + 345 (raiz) testes passando, 0 falhas.

Nota de setup: `EnterWorktree` ramifica de `origin/<default>` por padrão, e a `main` local estava 5
commits à frente do remoto — o worktree nasceria sem a spec nem o plano. Criado com
`git worktree add ... HEAD` e entrado por `path`.

## Pre-flight scan

### Pares de tarefas que compartilham arquivo ou interface

| Par | Produz → consome | Achado |
|---|---|---|
| T1 → T2 | `normalizar_tags`, `TAGS`, `SECTION_NAMES` | ok — T2 usa as duas constantes que T1 define |
| T1 → T3 → T6 | `SECTION_NAMES` cresce três vezes | **achado**: T3 mostra o literal completo; T6 só diz "acrescente". Risco de substituição em vez de adição |
| T2 → T4 → T7 | `_conteudo_do_item` ganha chave a cada tarefa | ok — incremental, cada uma só acrescenta o próprio `if` |
| T2 → T4 | `criar_plano`: `sorted` → `_ordenar_para_criacao` | ok — T7 reusa `_ordenar_para_criacao` no bloco que mostra |
| T2 hash ← T4 ordenação | literal `HASH_ANTES_DOS_CAMPOS_NOVOS` | ok — DFS pós-ordem sobre grafo sem arestas devolve a ordem base; literal sobrevive |
| T2 → T5 | `cliente._enviar_criacao` monta `patch` | ok — T2 acrescenta campo, T5 acrescenta relação; paths distintos |
| T3 → T4 | `ItemBacklog.depende_de` → `OperacaoCriacao.depende_de` | ok |
| T4 → T5 | `OperacaoCriacao.depende_de` → `ids_predecessores` | ok — resolvido em `registros` |
| T5 → T7 | `executar_publicacao`: laço vs semeadura de `registros` | ok — T7 semeia antes do laço, então predecessor pré-existente resolve |
| T5 → T7 | `ClienteFalso` do teste | **achado**: T7 chama `cliente.url_do_item(...)`, mas `ClienteFalso` não tem o método e o plano não manda acrescentá-lo. `test_item_preexistente_nao_e_recriado_e_serve_de_pai` morreria com `AttributeError` |
| T3 → T6 | assinatura de `_validate_item` | **achado**: T3 acrescenta o parâmetro `folhas`, T6 acrescenta `com_id`. Hoje é `(item, keys)`. Dois crescimentos sequenciais |
| T6 → T7 | `ItemBacklog.azure_boards_id` | ok |
| T8 vs T5 | `executar_publicacao` do pacote de Demanda | ok — T8 é a única tarefa assimétrica, e só acrescenta |
| T9/T10 ← T1,T3,T6 | documentação das regras implementadas | ok — docs descrevem o que o código já recusa |

### Coerência interna de cada tarefa

| Tarefa | Achado |
|---|---|
| T1 | ok — `"a;b, , c;d"` produz exatamente os 3 erros que o teste afirma |
| T2 | **achado**: o texto do Passo 3 diz "Acrescente ao fim da fixture ... nada". A intenção é a fixture ficar inalterada; a frase confunde |
| T3 | ok — a constante `BACKLOG` tem `Origem na spec:` e `Acceptance Criteria`, exigidos pela validação existente |
| T4 | ok — `ITENS` é `[1.1.1, 1.1.0, 1.0.0]`, e os testes montam sobre os índices certos |
| T5 | **achado menor**: `OPERACAO` é um Epic, e os testes fazem `replace(OPERACAO, depende_de=...)`. Epic não deveria depender de nada, mas o cliente não valida semântica — é teste de payload |
| T6 | ok — todos os parâmetros do `parametrize` caem no ramo de erro pretendido |
| T7 | achado já registrado no par T5 → T7 |
| T8 | ok |
| T9, T10 | ok — documentação |

### Conflito com a rubrica de revisão

Os dois pacotes são **gêmeos por arquitetura**: cada skill é instalável avulsa
(`npx skills add --skill ...`) e por isso não pode importar módulo de skill irmã — está documentado
no `[tool.mypy]` do `pyproject.toml` da raiz. O plano manda copiar arquivos de teste e de
implementação entre eles. Uma rubrica de qualidade que trate duplicação como defeito produziria o
mesmo falso positivo em oito das dez tarefas.

## Rulings do pre-flight

Ruling: `ClienteFalso` ganha `url_do_item` na Tarefa 7, junto do parâmetro `ids_predecessores` que a
Tarefa 5 já lhe acrescenta — o plano manda o código de produção chamar o método mas nunca manda
existir no duplo de teste. Levado no despacho da T7. Custo se errado: nenhum; é acréscimo em duplo de
teste, e o teste falharia ruidosamente se estivesse errado.

Ruling: `SECTION_NAMES` e `_validate_item` crescem por **acréscimo**, nunca por substituição, nas
Tarefas 3 e 6 — cada tarefa preserva o que a anterior pôs. Levado nos despachos da T3 e da T6. Custo
se errado: uma seção deixaria de ser reconhecida e a suíte da tarefa anterior falharia na mesma
rodada.

Ruling: a duplicação entre os dois pacotes é restrição de arquitetura, não descuido, e entra no bloco
de constraints de todo revisor como fato do projeto — sem instruir ninguém a não reportar nada.
Custo se errado: revisores gastam rodadas em falso positivo de duplicação.

Ruling: o texto confuso da fixture na T2 é resolvido no despacho — a fixture `valid-backlog.md`
permanece **sem** `Tags`, e é justamente isso que o teste do hash protege. Custo se errado: a fixture
ganharia tags e o teste do hash passaria a medir outra coisa.

Ruling: `OPERACAO` continua sendo um Epic nos testes de payload da T5. O cliente não valida semântica
de tipo, e trocar a fixture por uma História arrastaria a URL `/workitems/$Epic` afirmada por outros
testes do arquivo. Custo se errado: o teste descreve um caso que o contrato não produziria; o payload
verificado é o mesmo.

## Progresso

Ruling: o plano mantém os cabeçalhos "Tarefa N" em pt-BR, e a extração de brief se adapta. O script
`task-brief` da skill procura "Task N" literalmente; o CLAUDE.md deste projeto exige pt-BR e manda
confirmar com o usuário antes de renomear rótulo estrutural do qual uma skill downstream dependa —
então criei `brief-ptbr` no workspace, idêntico ao original exceto pela palavra. `review-package` não
parseia tarefas, só resolve o diretório, e segue usável como está. Custo se errado: nenhum no
produto; se o extrator falhasse, a tarefa não teria brief e eu perceberia no despacho.

Task 1: dispatched (BASE 693ccfc, modelo haiku — o brief traz o código completo, é transcrição mais
testes)
Task 1: implementer DONE (commit 50fbc95, 4 arquivos, +172/-0, simétrico nos dois pacotes)
Task 1: task reviewer dispatched (sonnet, diff 693ccfc..50fbc95)
Task 2: brief pronto (278 linhas), aguardando o portão da Tarefa 1
Task 1: review clean (spec OK, 0 critico, 0 importante)
Task 1: minor (deferred): nenhum teste cobre o limite exato de 400 caracteres (tag com exatamente
  400 e valida). Espelha o conjunto de testes do proprio brief, nao e lacuna do implementador.
Task 1: controlador resolveu o item nao-verificavel: 139 + 231 testes passando, ruff e mypy limpos.
Task 1: complete (commits 693ccfc..50fbc95, review clean)
Task 2: dispatched (BASE 50fbc95, modelo sonnet — multi-arquivo com integracao). Levadas no despacho:
  interfaces da T1 (normalizar_tags, TAGS, LIMITE_TAG), o ruling da fixture, e a instrucao de parar
  com BLOCKED se o teste do hash falhar em vez de atualizar o literal.
Task 2: implementer STALLED (watchdog, 600s sem progresso). Sem commit. Arvore suja com testes
  parciais em test_interpretar_markdown.py (+37) e test_planejar_publicacao.py (+7), descartados com
  git checkout. HEAD segue 50fbc95.

Ruling: a Tarefa 2 e dividida em 2a (Markdown -> ItemBacklog.tags) e 2b (propagacao, hash e payload).
  Ela era a maior do plano: 5 arquivos de producao x 2 pacotes, mais 3 arquivos de teste x 2, mais o
  ritual de captura do hash. O agente travou depois de escrever dois arquivos de teste, ou seja,
  progredindo devagar por volume de turnos -- exatamente o que a skill alerta em "turn count beats
  token price". Cada metade tem ciclo de teste proprio e e revisavel sozinha. Custo se errado: um
  commit a mais no historico e uma revisao a mais; nenhum risco ao produto.

Ruling: a Tarefa 2a ganha tres testes do caminho de validacao estrutural (validate_backlog com Tags
  bem formada, vazia, e com erro de formato) que o plano original nao cobria -- o texto do plano
  acrescentava a validacao em _validate_item sem nenhum teste que a exercitasse. Custo se errado:
  nenhum; e cobertura a mais sobre codigo que o plano ja mandava escrever.

Ruling: o .gitignore em .superpowers/sdd/ e versionado neste repositorio e mantem os relatorios .md
  dentro do controle de versao (commit b4e520b, "versiona o ledger e os relatorios desta execucao").
  O script sdd-workspace da skill o sobrescreveu com "*" no setup; restaurei o arquivo do repositorio.
  Consequencia para o passo final: NAO apagar o workspace como a skill manda -- a convencao deste
  projeto e commitar ledger e relatorios. Custo se errado: perder o registro que o projeto guarda de
  proposito, ou versionar artefato que ele nao queria; por isso vai para a lista de rulings do fim.

Task 2a: dispatched (BASE 50fbc95, modelo sonnet)
Task 2a: implementer DONE (commit cb56937, 10 arquivos, +199/-4). As 4 remocoes sao o _SECOES de uma
  linha virando set multilinha e o import mudando de posicao, nos dois pacotes -- conferido pelo
  controlador antes da revisao.
Task 2a: task reviewer dispatched (sonnet, diff 50fbc95..cb56937)
Task 2a: review clean (spec OK, 0 critico, 0 importante)
Task 2a: minor (deferred): _tags_do_item levanta so erros[0]; contrato_backlog acumula todos. Segue
  o padrao pre-existente do arquivo, nao e regressao. Depurar backlog com varias tags malformadas
  mostra um erro por vez.
Task 2a: minor (deferred): interpretar_markdown usa o literal "Tags" em vez da constante TAGS ja
  importada no mesmo arquivo. Segue a convencao do arquivo; DRY perdido.
Task 2a: controlador resolveu o item nao-verificavel: 145 + 237 testes, ruff e mypy limpos.
Task 2a: complete (commits 50fbc95..cb56937, review clean)
Task 2b: dispatched (BASE cb56937, modelo sonnet). Passo critico: captura do hash antes da mudanca.
Task 2b: implementer DONE (commit 1fe0fe7, 10 arquivos). test_hash_nao_muda_para_backlog_sem_tags
  passou nos dois pacotes. Hashes capturados: azure c7569e98..., demanda 36d9bee8... (diferentes,
  como esperado -- ConfiguracaoPublicacao do pacote de Demanda carrega demanda_id).
Task 2b: controlador confirmou a invariante por construcao, sem depender do relatorio: sem tags,
  _conteudo_do_item produz as mesmas 7 chaves na mesma ordem do dict original em cb56937, logo a
  serializacao e identica e a retomada esta preservada.
Task 2b: nota do implementador -- ConfiguracaoPublicacao do pacote de Demanda exige demanda_id
  posicional, que o comando do meu brief nao previa. Ele localizou o valor nos fixtures do proprio
  pacote e confirmou em vez de supor. Defeito meu no brief, resolvido sem intervencao.
Task 2b: task reviewer dispatched (sonnet, diff cb56937..1fe0fe7)
Task 2b: review -- spec OK, 0 critico, 1 importante (plan-mandated), 0 menor. Tarefa aprovada.
Task 2b: controlador resolveu o item nao-verificavel: demanda_id=13959 e fixture pre-existente
  (test_planejar_publicacao.py:16 e test_configuracao_projeto.py), nao valor inventado. Suites:
  150 + 242 passando.

Ruling: a duplicacao verbatim entre os dois pacotes gemeos FICA, e o achado Importante
  plan-mandated da Tarefa 2b nao entra no ciclo de correcao. Razoes, na ordem que pesou:
  (1) a spec -- autoridade vinculante -- ja declara "tudo em src/ sai em dobro: os dois pacotes sao
      gemeos", entao o plano nao esta contrariando a spec, esta executando-a;
  (2) a restricao e do produto e anterior a este trabalho: cada skill e instalavel avulsa via
      `npx skills add --skill ...` e por isso nao pode importar modulo de skill irma -- documentado
      no [tool.mypy] do pyproject.toml da raiz, que cita cliente_jev.py como o mesmo padrao;
  (3) a alternativa (pacote compartilhado) quebraria a instalacao avulsa, que e requisito de produto
      fora do escopo desta spec;
  (4) o revisor comparou as duas copias linha a linha e nao achou drift.
  O achado NAO e descartado: ele e real como custo acumulado, e este plano aumenta a superficie
  duplicada em ~7 blocos ao longo das 10 tarefas. Vai para a lista de rulings entregue ao usuario no
  fim, porque a decisao de arquitetura e dele, nao minha.
  Custo se errado: o projeto segue mantendo duas copias em sincronia manual; nenhum risco funcional,
  risco de manutencao que o usuario ja aceitou antes deste trabalho.
  Este ruling cobre as tarefas 3 a 10: nao vou relitigar o mesmo achado a cada revisao.

Task 2b: complete (commits cb56937..1fe0fe7, review clean apos ruling do achado plan-mandated)
Task 3: dispatched (BASE 1fe0fe7, modelo sonnet)

ACHADO que corrige o ruling anterior sobre duplicacao: existe
  publicar-backlog-demanda-azure-boards/tests/test_sincronia_com_origem.py, que exige que
  contrato_backlog.py, converter_para_html.py, interpretar_markdown.py e validacao_estrutural.py
  sejam byte a byte o resultado de substituir o nome do pacote no arquivo de origem. A sincronia
  entre os gemeos NAO e manual: e verificada por teste a cada rodada, e o teste falha se divergirem.
  Eu havia dito ao usuario que a manutencao era manual -- estava errado, e a correcao reduz bastante
  o custo do ruling da duplicacao. Consequencia pratica descoberta pela Tarefa 3: uma edicao no
  pacote de origem que mude comprimento de linha perto das 100 colunas pode estourar o limite DEPOIS
  da substituicao (o nome do pacote de Demanda e mais longo) -- checar sempre o arquivo espelhado, e
  nao so o de origem. Levado nos despachos das tarefas seguintes que tocarem esses 4 modulos.

Causa do .gitignore reescrito: o script review-package chama sdd-workspace internamente, e este
  reescreve .superpowers/sdd/.gitignore com "*" a cada invocacao. Nao foi nenhum subagente. Restauro
  apos cada review-package; restaurar de novo antes de encerrar.

Task 3: implementer DONE (commit 13856a5, 8 arquivos, +376/-6). Reformatou o import no pacote de
  origem para que a substituicao de nome nao estourasse 100 colunas no espelho -- mudanca de quebra
  de linha, sem efeito de comportamento.
Task 3: task reviewer dispatched (sonnet, diff 1fe0fe7..13856a5)
Task 3: task reviewer STALLED (watchdog, 600s). Arvore limpa -- revisores sao somente leitura. Diff
  de 28820 bytes, o maior ate aqui; mesmo padrao do stall da Tarefa 2 (volume -> turnos -> watchdog).

Ruling: revisoes passam a receber um pacote FOCADO. Para os 4 modulos listados em MODULOS_ESPELHADOS
  (contrato_backlog.py, converter_para_html.py, interpretar_markdown.py, validacao_estrutural.py), o
  revisor le so a copia do pacote de ORIGEM; o espelho do pacote de Demanda e garantido byte a byte
  por test_sincronia_com_origem.py, entao revisa-lo de novo e trabalho duplicado que so aumenta o
  risco de stall. Tudo que o teste de sincronia NAO cobre continua sendo revisado nos dois pacotes:
  modelos.py e os arquivos de teste. O pacote focado da Tarefa 3 caiu de 28820 para 18387 bytes (-36%)
  mantendo a lista de commits e o --stat COMPLETOS, para o revisor enxergar que os 8 arquivos foram
  tocados e poder cobrar qualquer ausencia.
  Custo se errado: uma divergencia entre os gemeos nos 4 modulos espelhados passaria sem olho humano
  -- mas ela faria test_sincronia_com_origem falhar, e esse teste roda em toda suite.

Task 3: task reviewer redispatched (sonnet, pacote focado review-t3-focado.diff)
Task 3: review clean (spec OK, 0 critico, 0 importante, 2 menores). Revisor confirmou por contagem
  que o import em uma linha daria 101 colunas apos a substituicao de nome (93 no pacote de origem) --
  a reformatacao era necessaria e e so formatacao.
Task 3: minor (deferred): normalizar_chaves e chamada duas vezes por item em contrato_backlog (uma em
  _validate_item, outra na comprehension que monta os pares de detectar_ciclo). 2x parsing, ainda
  O(n); duplicacao de trabalho evitavel.
Task 3: minor (deferred): falta teste de integracao via validate_backlog para auto-dependencia
  gerando "ciclo de dependencia entre ...". detectar_ciclo tem o caso isolado; a fiacao nao.
Task 3: controlador resolveu o item nao-verificavel: test_sincronia_com_origem.py passa (5/5), que e
  exatamente a garantia de igualdade byte a byte que o pacote focado assume. Suite de origem: 160.
Task 3: complete (commits 1fe0fe7..13856a5, review clean)

NOTA para as proximas revisoes: MODULOS_ESPELHADOS cobre APENAS contrato_backlog.py,
  converter_para_html.py, interpretar_markdown.py e validacao_estrutural.py. planejar_publicacao.py,
  modelos.py, cliente_azure_devops.py, executar_publicacao.py e manifesto.py NAO sao verificados pelo
  teste de sincronia. Logo o pacote focado so se aplica a tarefas que tocam os 4 modulos espelhados
  (Tarefa 6). Tarefas 4, 5 e 7 precisam das duas copias no diff de revisao.

Task 4: dispatched (BASE 13856a5, modelo sonnet — ordenacao topologica, julgamento algoritmico)
Task 4: implementer DONE (commit 97e6670, 7 arquivos, +339/-2). O commit levou junto o proprio
  task-4-report.md -- os anteriores nao levavam. Inofensivo: o .gitignore do projeto versiona
  relatorios de proposito. Fica como esta; no encerramento commito ledger e relatorios restantes num
  unico chore:, seguindo o precedente b4e520b.
Task 4: pacote de revisao montado a mao, omitindo o relatorio do diff (artefato de processo, nao
  produto) e mantendo commits e --stat completos. 18094 bytes, as duas copias incluidas porque
  planejar_publicacao.py e modelos.py NAO sao cobertos pelo teste de sincronia.
Task 4: task reviewer dispatched (sonnet, review-t4.diff)
Task 4: review -- 1 CRITICO, 1 menor. Precisa de correcoes.
  Critico: _ordenar_para_criacao so enxerga a aresta depende_de. Se um NAO-FOLHA declara Depende de
  apontando para folha de outro ramo, a folha e puxada para a frente sem os proprios ancestrais, e o
  plano sai com filho antes do pai.

Ruling: a correcao vai na VALIDACAO (contrato_backlog._validate_item), nao no algoritmo de ordenacao.
  Investiguei antes de decidir, com dois experimentos:
  (1) o caso que a spec permite -- folha depende de folha, em ramos diferentes -- ja sai CORRETO hoje:
      ['1.0.0','3.0.0','1.1.0','3.1.0','3.1.1','1.1.1'], todos os pais antes dos filhos. Isso vale por
      construcao: folhas vem por ultimo na ordem base, entao todo contêiner ja foi emitido antes de
      qualquer aresta de dependencia ser seguida.
  (2) o defeito so se manifesta com origem nao-folha, e a spec (linha 246) diz "Vale entre quaisquer
      dois itens de folha". A validacao atual exige que o ALVO seja folha e nao diz nada sobre a
      ORIGEM -- e essa a lacuna real, herdada da Tarefa 3.
  Portanto: _validate_item passa a recusar Depende de declarado em item que nao seja folha. Isso
  fecha o buraco na camada onde a spec o coloca e mantem _ordenar_para_criacao correta por
  construcao. NAO vou acrescentar aresta implicita de pai ao DFS: resolveria um caso que o contrato
  passa a proibir, e complicaria justamente a funcao cuja estabilidade protege o hash.
  Exijo tambem um teste do caso folha->folha entre ramos, que documenta POR QUE a ordenacao nao
  precisa de aresta de pai.
  Custo se errado: se um dia o produto quiser dependencia partindo de Feature ou Epic, a ordenacao
  vai precisar da aresta de pai e a recusa tera de ser afrouxada junto.

Task 4: fix round 1/5 dispatched (implementador original retomado)
Task 4: fix round 1/5 (1 endereçado, 0 abertos -- Critico da ordenacao corrigido na validacao;
  commits 97e6670..763ae35). Re-revisao confirmou: recusa generica por "item.key not in folhas",
  cobrindo Epic e Feature; o teste de ordenacao afirma pai-antes-de-filho nos DOIS ramos, nao so a
  ordem entre as folhas; docstring explica o porque; _ordenar_para_criacao nao teve linha executavel
  tocada. Zero quebras novas. Suites: 169 + 261.
Task 4: complete (commits 13856a5..763ae35, review clean apos 1 rodada)
Task 5: dispatched (BASE 763ae35, modelo sonnet). Armadilha conhecida: direcao do link.
Task 5: implementer DONE (commit 824619f). Direcao do link confirmada contra o Microsoft Learn
  ("Link Types Reference Guide - Azure Boards": Predecessor = System.LinkTypes.Dependency-Reverse, ao
  lado de Parent = Hierarchy-Reverse) e verificada por inversao deliberada da constante para
  -Forward, com 3 testes falhando. Suites: 175 + 267.
Task 5: implementador levantou duas coisas para julgamento --
  (a) moveu a checagem de predecessor para ANTES da checagem de pai, porque com a ordem do brief o
      teste test_recusa_quando_o_predecessor_nao_foi_publicado falhava (no cenario daquele teste o
      item nao tem nem pai nem predecessor publicados, e a checagem de pai disparava primeiro);
  (b) alterou arquivos fora da lista do brief: Protocol ClientePublicacao.criar_item em cli.py, e os
      test doubles em test_integracao_final.py (ambos) e test_vinculo_demanda.py (demanda).
  Tenho opiniao formada sobre (a) -- acho que o cenario do teste e que esta errado, nao a ordem de
  producao, porque pai ausente e falha mais fundamental que predecessor ausente e a reordenacao
  dobra o codigo para caber num teste que eu mesmo escrevi mal. NAO levei isso ao revisor, para nao
  pre-julgar: deixei que ele avalie sozinho e adjudico depois, com a opiniao dele em maos.
Task 5: task reviewer dispatched (sonnet, review-t5.diff)
Task 5: review clean (spec OK, 0 critico, 0 importante, 3 menores). Revisor verificou a direcao do
  link por raciocinio de codigo, sem rodar: com -Forward, test_criacao_liga_predecessor falha no rel,
  test_criacao_liga_um_predecessor_por_plataforma vira lista vazia, e
  test_pai_e_predecessor_usam_relacoes_distintas levanta KeyError. A protecao contra inversao e real.
  Aceito sem reexecutar: o raciocinio e conclusivo por inspecao (acesso por chave no dict).

Ruling: a ordem das checagens (predecessor antes de pai) FICA como esta. Eu estava errado na minha
  leitura anterior. Achei que era dobrar o codigo de producao para caber num teste mal escrito; o
  revisor mostrou, de forma independente, que as duas checagens acontecem ANTES de qualquer efeito
  colateral e qualquer uma interrompe a execucao -- a ordem so decide qual mensagem de erro aparece,
  nao ha diferenca funcional. Nao vale gastar uma rodada de correcao numa escolha neutra.
  Custo se errado: quando pai e predecessor faltam juntos, o usuario ve a mensagem de predecessor em
  vez da de pai. Cosmetico.
Task 5: minor (deferred): a ordem das checagens nao tem comentario explicando o porque; um editor
  futuro pode reordenar lendo o brief literalmente e reintroduzir a falha de teste.
Task 5: minor (deferred): test_integracao_final.py:48 tem asserção "if operacao.depende_de: assert
  ids_predecessores" que nunca exercita o ramo verdadeiro -- a fixture valid-backlog.md nao tem
  Depende de. Asserção morta, da falsa sensacao de cobertura fim a fim. A cobertura real existe em
  test_executar_publicacao.py e test_cliente_azure_devops.py.
Task 5: minor (deferred): a evidencia do teste manual de inversao veio narrada, sem log colado,
  diferente dos outros passos RED/GREEN do mesmo relatorio.
Task 5: cli.py e os test doubles fora da lista do brief foram julgados consequencia NECESSARIA da
  assinatura nova, nao escopo excedido: o Protocol precisa aceitar o mesmo parametro para o mypy
  --strict passar, e os fakes quebrariam com TypeError sem ele.
Task 5: complete (commits 763ae35..824619f, review clean)
Task 6: dispatched (BASE 824619f, modelo sonnet)
Task 6: implementer DONE (commit 26a0f51, 8 arquivos). Suites 184 + 276, incluindo
  test_sincronia_com_origem. Achado de autorrevisao util para a Tarefa 7: o awk padrao do macOS conta
  BYTES, nao caracteres, entao uma linha com acento aparece como 101 colunas tendo 100 de verdade. A
  validacao de largura passou a ser feita em Python, por codepoints.
Task 6: task reviewer dispatched (sonnet, pacote focado review-t6.diff -- contrato_backlog.py e
  interpretar_markdown.py so na copia de origem, cobertos pelo teste de sincronia; modelos.py e
  testes nos dois pacotes)
Task 6: review -- 0 critico, 1 IMPORTANTE, 3 menores. Precisa de correcoes.
  Importante: normalizar_id usa texto.isdigit(), que devolve True para sobrescritos Unicode como
  "231" em expoente, mas int() estoura ValueError neles. Reproduzido pelo revisor e confirmado por
  mim contra o pacote instalado. Contradiz a garantia da propria docstring e derruba validate_backlog
  inteiro em vez de produzir recusa limpa.

Ruling: a correcao usa `texto.isascii() and texto.isdigit()`, NAO `isdecimal()`.
  O revisor sugeriu isdecimal(), que tambem resolve (recusa sobrescrito, aceita arabe-indico que o
  int() converte). Escolhi a outra forma por dois motivos:
  (1) precedente do proprio repositorio -- configuracao.py:165 ja faz exatamente
      `if not digitos.isascii() or not digitos.isdigit()` para ler o demanda_id, ou seja, o projeto ja
      conhecia a armadilha e guardou assim; consistencia vale mais que elegancia aqui;
  (2) e mais estrito: recusa digito arabe-indico, que isdecimal() aceitaria. Para um valor que decide
      a qual work item os filhos serao pendurados, o vies certo e o estrito -- um ID vindo do Azure
      Boards e ASCII.
  Custo se errado: um ID legitimamente escrito em digitos nao-ASCII seria recusado. Cenario que nao
  existe na pratica, e a recusa seria limpa e com mensagem, nao um crash.
  Varredura: grep por isdigit/isnumeric nos dois src/ nao achou nenhuma outra ocorrencia desguardada.

Task 6: fix round 1/5 dispatched (implementador original retomado)
Task 6: fix round 1/5 (1 enderecado, 0 abertos; commits 26a0f51..b7c7e94). A escolha mais estrita
  revelou um SEGUNDO defeito que ninguem tinha visto: o digito arabe-indico nao estourava -- era
  aceito em silencio como 3, e penduraria os filhos no work item 3 do Azure Boards sem erro nenhum.
  isdecimal(), sugerido pelo revisor, teria deixado passar. O teste com `assert valor is None` captura
  os dois modos de falha opostos. Re-revisao: enderecado, zero quebras novas, os tres menores
  diferidos foram respeitados.
Task 6: controlador verificou os 6 casos contra o pacote instalado antes da re-revisao: sobrescrito,
  arabe-indico, zero, negativo e texto devolvem recusa limpa; 4721 segue valido; nenhum estoura.
Task 6: complete (commits 824619f..b7c7e94, review clean apos 1 rodada)

Ruling: a Tarefa 7 e dividida PREVENTIVAMENTE em 7a e 7b, antes de qualquer despacho. O brief dela
  tem 544 linhas -- quase o dobro da Tarefa 2 (278), que travou o agente por excesso de turnos e
  precisou ser dividida depois, com trabalho jogado fora. Corte por camada:
    7a = dados: modelos.py (ItemPreexistente, RegistroManifesto.preexistente, PlanoPublicacao.
         preexistentes), planejar_publicacao.py (separacao e hash), manifesto.py (serializacao)
    7b = comportamento: executar_publicacao.py (semeadura de registros) e cliente_azure_devops.py
         (url_do_item, verificar_item_existente)
  Cada metade tem ciclo de teste proprio e e revisavel sozinha; 7a produz as interfaces que 7b
  consome. Custo se errado: um commit e uma revisao a mais.

Ruling: o brief da 7b carrega o defeito que o pre-flight scan achou -- ClienteFalso precisa ganhar
  url_do_item. O plano manda executar_publicacao chamar cliente.url_do_item(), mas nunca manda o
  metodo existir no duplo de teste, e o teste morreria com AttributeError.

Ruling: o teste de compatibilidade do manifesto antigo (7a) grava pelo caminho normal e REMOVE a
  chave nova do JSON antes de reler, em vez de montar o dicionario a mao. Assim ele reproduz um
  manifesto de versao anterior sem arriscar divergir do formato real de _serializar -- o plano
  original mandava montar a mao e avisava "leia _serializar e copie as chaves de la", o que era
  fragil. Custo se errado: nenhum; o teste fica mais fiel.

Task 7a: dispatched (BASE b7c7e94, modelo sonnet)
Task 7a: implementer DONE (commit f441027, 10 arquivos, +166/-4). Suites 191 + 283, hash verde.
Task 7a: handoff util para a 7b, levantado pelo implementador e confirmado por mim -- cli.py:147 faz
  `registrados = len(manifesto.itens)` e imprime "Itens registrados no manifesto". Hoje nao ha
  problema porque nenhum pre-existente e semeado; a partir da 7b eles entrarao em manifesto.itens.
  O rotulo diz "registrados", nao "criados", entao continua factualmente correto -- e a contagem por
  tipo remoto no mesmo cli ja exclui pre-existentes por construcao, porque eles nao sao operacoes.
  Levo isso a 7b como VERIFICACAO NOMEADA, para ser conferido conscientemente e nao por acidente.
Task 7a: task reviewer dispatched (sonnet, review-t7a.diff, as duas copias incluidas -- modelos.py,
  planejar_publicacao.py e manifesto.py nao sao cobertos pelo teste de sincronia)
Task 7a: review clean (spec OK, 0 critico, 0 importante, 1 menor). Revisor verificou as quatro
  invariantes linha a linha e confirmou de forma independente o diagnostico do cli.py. Validou
  tambem que o teste de manifesto antigo e prova genuina de fallback, nao roundtrip disfarcado.
Task 7a: minor (deferred): preexistentes e a_criar sao dois passes separados sobre itens_ordenados
  em vez de uma particao unica. Correto e legivel, so redundante.
Task 7a: controlador resolveu o item nao-verificavel: mypy Success nos dois pacotes, 191 + 283 testes.
Task 7a: complete (commits b7c7e94..f441027, review clean)
Task 7b: dispatched (BASE f441027, modelo sonnet). Leva o defeito do pre-flight (ClienteFalso precisa
  de url_do_item) e a verificacao nomeada do cli.py.
Task 7b: implementer DONE_WITH_CONCERNS (commit be8b57a). Suites 198 + 290.
Task 7b: ACHADO CRITICO levantado pelo implementador e REPRODUZIDO POR MIM: validar_manifesto itera
  manifesto.itens e exige que toda chave esteja em plano.operacoes -- mas a Tarefa 7a removeu os
  pre-existentes justamente de la. Resultado: a segunda rodada sobre o mesmo backlog falha com
  "O item 1.0.0 do manifesto nao pertence ao backlog completo". Ou seja, o cenario que a feature
  inteira existe para resolver (segunda rodada encontra o Epic ja publicado) estava quebrado.

Ruling: isto e LACUNA DO MEU PLANO, nao erro do implementador. O plano desenhou 7a (tirar
  pre-existentes das operacoes) e 7b (semea-los no manifesto) sem notar que validar_manifesto cruza
  as duas coisas. A correcao: validar_manifesto passa a validar chave pre-existente contra
  plano.preexistentes em vez de rejeita-la --  exigindo registro.preexistente True, mesmo id e mesmo
  tipo. Escolhi validar em vez de simplesmente ignorar porque assim uma mudanca do ID declarado no
  Markdown entre duas rodadas e detectada, preservando a garantia de integridade do manifesto.
  A comparacao de titulo NAO se aplica a pre-existente: o titulo remoto pertence a quem criou o item,
  nao a nos.
  Custo se errado: se a validacao ficar frouxa demais, um manifesto apontando para work item errado
  passaria despercebido; e por isso que valido id e tipo em vez de pular.

Ruling: o titulos.setdefault que o implementador acrescentou FICA. Nao e gambiarra: manifesto.py:271
  recusa titulo vazio na desserializacao (`or not titulo`), entao todo item em manifesto.itens precisa
  de titulo nao-vazio. Verifiquei no codigo. O texto deve dizer com clareza que o item foi declarado,
  nao criado por nos.

Task 7b: concern 2 (mexer em cli.py) julgado DENTRO da instrucao -- o Passo 3 do brief manda chamar
  verificar_item_existente na verificacao preliminar, e ela vive no cli.py. Nao e escopo excedido.
Task 7b: concern 4 -- implementador concordou que cli.py:147 nao precisa mudar, e nao mexeu. Correto.
Task 7b: fix round 1/5 dispatched (implementador original retomado), ANTES da revisao de tarefa,
  porque a preocupacao e de correcao.
Task 7b: fix round 1/5 (1 enderecado, 0 abertos; commits be8b57a..372d301). Suites 203 + 295.
Task 7b: controlador verificou os tres cenarios contra o pacote instalado, sem depender do relatorio:
  segunda rodada normal ACEITA; ID alterado no Markdown RECUSADO; manifesto adulterado com
  preexistente=False RECUSADO. Mensagens especificas, nao genericas.
Ruling: o gap simetrico que o implementador levantou (chave de operacao normal com registro marcado
  preexistente=True, cenario de alguem remover o Azure Boards ID do Markdown entre rodadas) NAO
  precisa de codigo novo. Testei: ja e recusado com "O item 1.1.0 do manifesto diverge do backlog
  completo", porque o rotulo de titulo do pre-existente nao bate com operacao.titulo. Ele fez certo
  em levantar e nao implementar; eu verifiquei em vez de supor.
  Custo se errado: se um dia o titulo do pre-existente coincidir com o de uma operacao, essa
  cobertura acidental cai.
Task 7b: task reviewer dispatched (sonnet, f441027..372d301 -- cobre implementacao e correcao, porque
  a revisao de tarefa ainda nao tinha rodado)
Task 7b: review clean (spec OK, 0 critico, 0 importante, 1 menor). Revisor confirmou os cinco pontos
  dirigidos e rastreou a cadeia de excecao (ErroDestinoInvalido -> RuntimeError -> except do cli.py)
  para provar que verificar_item_existente interrompe o fluxo antes de qualquer autorizacao ou
  escrita. Confirmou tambem que match="1.0.0" teria passado sem a correcao, e que os match usados
  nao teriam -- a disciplina de teste do implementador se sustenta.
Task 7b: minor (deferred): verificar_item_existente chama self._enviar("GET", ...) direto, enquanto
  o arquivo ja tem o helper _obter usado em todos os outros GETs. Inconsistencia estilistica onde a
  abstracao certa ja existia.
Task 7b: complete (commits f441027..372d301, review clean apos 1 rodada)
Task 8: dispatched (BASE 372d301, modelo sonnet). UNICA tarefa assimetrica do plano: a recusa vale so
  na publicadora de Demanda, e o pacote solto precisa de teste de NAO-regressao provando que ele
  aceita backlog com Demanda declarada -- senao o fluxo de debitos nasce quebrado.

ACHADO no proprio plano, corrigido em 1c61830: o documento tinha 157 cercas de codigo -- numero
  IMPAR. Um bloco python na Tarefa 7 abria sem fechar, defeito que EU introduzi ao editar o plano na
  autorrevisao. Isso dessincroniza o rastreio de cercas do extrator e faz TODOS os cabecalhos
  posteriores sumirem: as Tarefas 8, 9 e 10 estavam invisiveis. Se eu tivesse confiado no extrator
  sem conferir, teria encerrado o plano com tres tarefas por fazer. Fechadas em 158.

Task 8: implementer DONE (commit a6c13f2, 6 arquivos, +325/-1). Suites 301 (Demanda) + 204 (solto).
Task 8: tres desvios declarados pelo implementador, mandados ao revisor para julgamento independente,
  sem minha opiniao junto:
  (1) extrair_demanda_origem/conferir_demanda_de_origem foram para executar_publicacao.py em vez de
      interpretar_markdown.py, porque este e espelhado byte a byte -- era exatamente a tensao que eu
      pedi para ele resolver, e ele resolveu do jeito que preserva o teste de sincronia;
  (2) a chamada ficou em principal() antes de _verificar_preliminar, e nao dentro dela, para nao
      quebrar testes que chamam _verificar_preliminar isolado com plano sintetico;
  (3) a fixture valid-backlog.md do pacote de Demanda ganhou o metadado, porque o campo passou a ser
      EXIGIDO -- consequencia: backlog sem esse metadado passa a ser recusado pela publicadora de
      Demanda. Mudanca de comportamento alem do que a spec pediu (ela falava em divergencia e em
      "Nao se aplica", nao em ausencia). Deixei o revisor julgar.
Task 8: GAP de documentacao que o implementador declarou e nenhuma tarefa cobre -- o SKILL.md e o
  README do pacote de Demanda nao documentam o metadado agora obrigatorio. As Tarefas 9 e 10 cobrem o
  contrato do backlog e as skills de origem, nao as publicadoras. Decidir ao despachar a Tarefa 9.
Task 8: task reviewer dispatched (sonnet, review-t8.diff)
Task 8: review -- 0 critico, 1 IMPORTANTE (plan-mandated), 1 menor. Precisa de correcoes.
  Os tres desvios declarados foram julgados ACEITAVEIS pelo revisor, com verificacao propria: (1) leu
  test_sincronia_com_origem.py e confirmou que executar_publicacao.py nao e modulo espelhado;
  (2) tracou principal() inteiro e provou que validar/planejar/--simulacao retornam antes da checagem
  mas tambem antes de qualquer escrita, e que o unico caminho ate executar_plano passa por ela;
  (3) notou que exigir o campo nao e desvio -- o Passo 3 do MEU brief especificava ErroContratoMarkdown
  incondicional para metadado ausente, entao e consequencia direta do que pedi.

Ruling: o achado Importante e PROCEDENTE e entra no ciclo de correcao. O teste-guarda que EU escrevi
  no brief da Tarefa 8 e VAZIO: chama interpretar_backlog, que nao olha a secao de metadados.
  Verifiquei -- backlog com a linha da Demanda, sem ela, e com metadado inventado produzem o MESMO
  resultado, sem erro. O teste passaria antes e depois da tarefa. Pior: o risco que ele diz proteger
  (alguem replicar a checagem no pacote solto e quebrar o fluxo de debitos) se materializaria em
  cli.py::principal(), que o teste nunca toca. Guarda vazio e pior que nenhum, porque cria confianca
  falsa sobre a invariante que a spec chama de decisiva.
  Custo se errado: se a correcao ficar so estrutural em vez de comportamental, trava a forma obvia de
  quebrar a assimetria, mas nao todas.
Task 8: minor (deferred): SKILL.md/README do pacote de Demanda nao documentam o metadado agora
  obrigatorio. Revisor confirmou que NAO e regressao desta tarefa -- nenhum metadado existente
  (Spec de origem, Data de geracao) esta documentado nesses arquivos hoje. Decidir na Tarefa 9.
Task 8: fix round 1/5 dispatched (implementador original retomado)
Task 8: fix round 1/5 (1 enderecado, 0 abertos; commits a6c13f2..72db9a1). O implementador fez TESTE
  DE MUTACAO para provar o guarda: acrescentou temporariamente a recusa ao cli.py do pacote solto,
  viu o teste novo falhar (assert 1 == 0), reverteu. Re-revisor foi alem e provou estruturalmente que
  a falha e INEVITAVEL, nao dependente da forma da recusa: qualquer ValueError/OSError/RuntimeError/
  PermissionError no try de cli.py:198-200 vira codigo 1 e derruba a assercao, e ate uma recusa
  silenciosa seria pega pela segunda assercao (chaves_criadas). Verificou ainda, por conta propria,
  que o .replace() da fixture casa com o texto real -- descartando no-op silencioso.
Task 8: controlador confirmou pelo diff que nenhum codigo de producao mudou na correcao (so os dois
  arquivos de teste e o relatorio).
Task 8: complete (commits 1c61830..72db9a1, review clean apos 1 rodada)

Ruling: o achado Menor diferido sobre documentacao ENTRA no escopo da Tarefa 9. O revisor apurou que
  nenhum metadado existente (Spec de origem, Data de geracao) esta documentado no SKILL.md/README das
  publicadoras -- e padrao pre-existente, nao regressao. Mas "Demanda de Negocio de origem" agora
  BLOQUEIA a publicacao quando ausente, e isso muda o contrato observavel da publicadora de Demanda:
  quem tiver backlog anterior a esta mudanca vai bater numa recusa e precisa saber por que. Os outros
  dois metadados nao bloqueiam nada, por isso nunca precisaram de documentacao.
  Custo se errado: uma linha a mais de documentacao numa skill.
Task 9: dispatched (BASE 72db9a1, modelo sonnet) -- contrato do backlog + a linha sobre o metadado
  obrigatorio na publicadora de Demanda.
Task 9: implementer DONE (commit e50ca96, 2 arquivos: backlog-markdown-contract.md e o SKILL.md da
  publicadora de Demanda). Conferiu os valores contra os 34 testes das tres regras. Autocorrecao
  dele: "Depende de" nao proibe autorreferencia em normalizar_chaves -- quem pega e detectar_ciclo
  (ciclo de 1 no) -- e ajustou o contrato para descrever a causa correta.
Task 9: task reviewer dispatched (sonnet). Metodo INVERTIDO para tarefa de documentacao: mandei o
  revisor cruzar cada valor com o codigo e os testes, o que normalmente eu proibo. Em tarefa de
  documentacao, vasculhar a fonte E o trabalho, e "documentacao que nao bate com o comportamento e
  defeito" e o criterio principal. Listei nove valores para conferencia explicita, um a um.
Task 9: review -- 1 CRITICO. Precisa de correcoes. Conteudo tecnico conferido valor a valor contra
  codigo e testes: TODOS batem, inclusive a autocorreccao sobre detectar_ciclo. Mas o diff quebrou
  DOIS testes pre-existentes de gerar-backlog-azure-boards/tests/test_skill_integration.py, que
  afirmam literais do proprio backlog-markdown-contract.md na forma ANTIGA, em prosa. Confirmei:
  2 failed, 59 passed.

Ruling: FALHA DO MEU DESPACHO, nao do implementador. Eu mandei rodar a validacao estrutural da
  fixture, mas nao a suite do pacote cujo arquivo ele estava editando -- e o arquivo editado vive
  dentro de gerar-backlog-azure-boards/references/. Um implementador que roda so o que o despacho
  pede nao tem como descobrir isso.
  A correcao atualiza as DUAS assercoes para a forma nova e estruturada. Elas sao guardas do contrato
  e valem manter, so estao codificando a forma que a spec descontinuou de proposito.
  Custo se errado: se as assercoes novas ficarem genericas demais, o guarda do contrato enfraquece.

Ruling PREVENTIVO para a Tarefa 10: os TRES pacotes que ela vai editar
  (especificar-debitos-tecnicos, especificar-telas-ux-ui, gerar-backlog-azure-boards) tem
  test_skill_integration.py afirmando literais de SKILL.md -- verifiquei com grep. O mesmo risco,
  triplicado. O despacho da Tarefa 10 vai exigir rodar a suite de CADA pacote editado, e nao so a
  dos publicadores.

Task 9: fix round 1/5 dispatched (implementador original retomado)
Task 9: fix round 1/5 (1 enderecado, 0 abertos; commits e50ca96..ce4df43). Re-revisao confirmou que
  os guardas novos NAO sao vazios: o primeiro exige o marcador de nivel "#####" mais o formato da
  chave documental, entao uma reversao para prosa o derruba; o segundo afirma as frases exatas que
  NEGAM o link ("Nao gera link algum; e so rastro documental"), entao uma reescrita dizendo que
  Bloqueia gera link o derruba. Um dos testes foi renomeado com honestidade -- o nome antigo citava
  "depende_de_and_bloqueia_as_informative", e "Depende de" deixou de ser informativo.
Task 9: controlador confirmou: gerar-backlog 61 passed (era 2 failed + 59), raiz 345 passed.
Task 9: complete (commits 72db9a1..ce4df43, review clean apos 1 rodada)
Task 10: dispatched (BASE ce4df43, modelo sonnet). Leva o ruling preventivo: rodar a suite de CADA
  um dos tres pacotes editados, porque os tres tem test_skill_integration.py afirmando literais.
Task 10: implementer DONE (commit 3ac7e71, 5 arquivos). Suites 38 + 26 + 66. Ele achou e corrigiu uma
  CONTRADICAO que a Tarefa 9 criou: o bullet de Boundaries do gerar-backlog dizia que "Depende de" e
  "Bloqueia" eram ambos informativos -- verdade ate a Tarefa 5, falsa depois que Depende de passou a
  gerar link real. Pior: havia um TESTE afirmando a frase errada, o que tornava a inconsistencia
  estavel. Declarou o desvio pedindo segunda leitura em vez de enterrar no commit.
Task 10: review -- 0 critico, 1 IMPORTANTE, 2 menores. Revisor confirmou os tres pontos do desvio:
  a contradicao era real (as duas afirmacoes coexistiam no commit-base), a correcao descreve o
  comportamento atual, e a assercao nova continua especifica (frases literais de 8-10 palavras).
  Conferiu grafia tag a tag contra contrato e fixtures: nenhuma divergencia.

Ruling: o achado Importante PROCEDE e entra no ciclo. gerar-backlog-azure-boards/SKILL.md:47 manda
  converter a Faixa "para minusculas e hifen". Verifiquei: faixa() devolve "restricao"/"a_confirmar"/
  "candidato" -- ASCII, sublinhado -- mas a Faixa DECLARADA no DT e o texto de exibicao "Restricao"
  (com cedilha e til). Minusculas e hifen aplicado a esse texto da "restricao" acentuado, nao o ASCII.
  Os exemplos listados na skill estao certos; a REGRA que os gera esta errada. Quem aplicar a regra a
  um caso nao listado, ou um agente regenerando, produz dt- com acento -- e a query volta vazia, que e
  exatamente a classe de erro que esta tarefa existe para prevenir.
  Correcao: a regra passa a partir do retorno bruto de faixa(), trocando _ por -, em vez do texto de
  exibicao. Custo se errado: nenhum; a formulacao fica mais explicita sobre a fonte.
Task 10: minor (deferred): celula-exemplo da coluna Faixa usa "\|" como separador enquanto a celula
  vizinha Tipo sugerido usa "/" para o mesmo fim. Inconsistencia de estilo.
Task 10: minor (deferred) -- ASSIMETRIA DE GUARDA, vale destaque na triagem final: as adicoes em
  especificar-debitos-tecnicos/SKILL.md (coluna Faixa, ## Fonte da Demanda, nota de snapshot, bullet
  da publicadora solta) NAO ganharam teste em test_skill_integration.py, enquanto as outras duas
  skills tocadas na mesma tarefa ganharam teste para cada adicao. Conteudo correto, sem trava contra
  regressao silenciosa.
Task 10: fix round 1/5 dispatched (implementador original retomado)
Task 10: fix round 1/5 (1 enderecado; commits 3ac7e71..8652e59). A regra de conversao agora parte do
  retorno ASCII de faixa(), com tabela exibicao -> retorno -> tag, e ganhou teste dedicado
  (test_tag_de_faixa_parte_do_retorno_ascii_de_faixa_nao_do_texto_de_exibicao).
Task 10: MAS o controlador rodou a suite RAIZ e achou 1 falha nova, num QUARTO pacote que o
  implementador nao editou nem rodou:
  redigir-spec-pedido-negocio/tests/.../test_existing_skills_do_not_reference_drafting_skill.
  Causa: a secao nova "Specs de entrada reconhecidas" do gerar-backlog cita `redigir-spec-pedido-
  negocio` como exemplo de spec de fluxo usual, e esse pacote tem um teste de ISOLAMENTO deliberado
  exigindo que 3W, 3C, Gherkin e backlog NAO o referenciem.

Ruling: a invariante de isolamento VENCE; a mencao sai. Ela e pre-existente, deliberada e guardada
  por teste; a citacao era decorativa -- a secao comunica "duas formas de spec de entrada" sem
  precisar nomear a skill. Verifiquei o alcance: o isolamento vale SO para redigir-spec-pedido-
  negocio; redigir-spec-demanda-azure-boards ja e citada no proprio contrato (linha 232), entao pode
  continuar. Custo se errado: o leitor perde um exemplo concreto de qual skill produz a spec usual.

Ruling de PROCESSO, valido daqui em diante: tarefa que edita documentacao roda a suite RAIZ do
  repositorio, nao so a dos pacotes editados. Duas tarefas seguidas quebraram teste em pacote que nao
  tocaram -- a Tarefa 9 em gerar-backlog (dono do arquivo editado) e a Tarefa 10 num pacote terceiro,
  ligado so por uma invariante de isolamento. Rodar as suites dos pacotes editados nao e suficiente:
  texto e lido por quem o editor nao imagina.
Task 10: fix round 2/5 dispatched (implementador original retomado)
Task 10: fix round 2/5 (2 enderecados no total, 0 abertos; commits 3ac7e71..09f2137). Re-revisao
  confirmou que a regra nova e correta POR CONSTRUCAO -- quem le so a frase-regra, sem os exemplos,
  produz a tag certa, porque a transformacao esta descrita sobre a string ASCII. E as tres assercoes
  novas sao MAIS especificas que a antiga: cada uma amarra texto de exibicao + retorno + tag, enquanto
  a antiga so verificava que os tres valores apareciam juntos numa frase.
Task 10: controlador confirmou suite raiz 352 passed (era 1 failed + 351) e grep zerado.
Task 10: complete (commits ce4df43..09f2137, review clean apos 2 rodadas)

TODAS AS TAREFAS CONCLUIDAS. 12 unidades (10 do plano, com a 2 e a 7 divididas em duas cada).
Revisao final do branch inteiro despachada no modelo mais capaz.

REVISAO FINAL DO BRANCH: nao pronto para merge. 1 critico, 2 importantes, 6 menores, mais a triagem
  dos 13 diferidos (3 marcados para corrigir antes do merge). Nenhum ruling contestado.

CRITICO confirmado por mim: gerar-backlog-azure-boards/scripts/validate_backlog.py e uma TERCEIRA
  copia do contrato, nunca tocada pelo branch, com SECTION_NAMES de cinco entradas. O passo 10 do
  proprio SKILL.md (inalterado) manda rodar esse validador e "corrigir violacoes estruturais" -- ou
  seja, o arquivo manda emitir tags dez linhas acima e manda rodar o gate que as recusa, cuja
  correcao obvia para um agente e apagar as tags. Os READMEs das duas publicadoras dizem que essa e a
  copia CANONICA e que as outras a seguem; o branch mudou as copias e deixou a canonica atras.
  A spec tambem errou: a tabela "Alcance da mudanca -> Skills" omite scripts/validate_backlog.py.
  O pre-flight scan enumerou pares de tarefas que compartilham arquivo, mas ninguem perguntou quantas
  copias do contrato existem no repositorio. E o tipo de coisa que revisao por tarefa nao ve.

Ruling: UMA onda de correcao, como o processo manda, com a lista completa. Entram: o Critico (portar
  os tres campos E as validacoes, nao so os nomes -- senao o gate aceita sem validar), os dois
  Importantes, os tres diferidos marcados para corrigir, e quatro Menores baratos (#4, #5, #7, #9)
  mais o comentario da ordem das checagens da Task 5.
  FICAM DE FORA, com motivo: Menor #6 (mostrar os IDs reaproveitados na tela de autorizacao) -- e
  ponto legitimo de usabilidade, mas e acrescimo de feature no portao final, e verificar_item_existente
  ja roda antes da autorizacao, entao e legibilidade e nao seguranca; Menor #8 (assinatura_plano e
  codigo morto e desatualizado) -- pre-existente, nao introduzido por este branch, merece commit
  proprio. Os dois vao para o usuario decidir.
  Custo se errado: o usuario recebe duas sugestoes de melhoria em vez de codigo pronto.

Onda de correcao final despachada (opus -- portar validacao para uma terceira copia sem teste de
  sincronia e onde errar significa o gate aceitar sem validar).

Onda final: DONE (commits 2bac182, 16b30b9, 551c596). O implementador foi alem do pedido de forma
  bem julgada: em vez de copiar as regras a mao para a terceira copia, reescreveu validate_backlog.py
  como ESPELHO MECANICO do corpo de contrato_backlog.py entre marcadores, e criou
  tests/test_sincronia_do_contrato.py. Argumento dele, melhor que minha instrucao: comparar so
  SECTION_NAMES passaria por acaso justamente no caso "aceita sem validar".
  Ele ainda achou o que a revisao final nao viu: o gate antigo tinha um SEGUNDO modo de falha,
  engolindo a secao desconhecida e dizendo "estrutura valida"; e a fixture maior revelou DOIS testes
  que passariam VAZIOS em vez de falhar, porque liam [-1] de uma lista que mudou de tamanho.

Controlador verificou o Critico por prova direta, nao por relatorio: montou um backlog invalido de
  proposito e o validador canonico recusou as tres violacoes com as mensagens certas (Depende de em
  Feature, tag com ponto-e-virgula, Azure Boards ID em Historia), exit 1.

Re-revisao final: TODOS os itens enderecados. Pronto para voltar ao humano. O re-revisor testou o
  mecanismo do marcador sob SEIS adulteracoes -- nenhuma passa em silencio -- e provou a neutralidade
  do espelhamento de Implementation Evidence rodando o gate antigo e o novo sobre os cinco documentos
  de backlog do repositorio: zero erro novo, zero erro resolvido.

ACHADO OPERACIONAL do re-revisor, relevante para quem for integrar: `uv run pytest` da RAIZ nao roda
  as suites das publicadoras -- elas estao fora do testpaths do pyproject. Logo a raiz nao executa
  test_sincronia_com_origem.py. Total real medido pelo controlador: 372 (raiz) + 209 (solta) +
  306 (Demanda) = 887 testes, zero falhas.

Tres asperezas registradas como debito, nao bloqueantes: BACKLOG_FEATURE_COM_ID_VAZIO definido depois
  do teste que o usa; a assercao _SECOES == SECTION_NAMES e tautologica hoje (alias, nao copia), mas
  impede a reintroducao de um set literal; e a raiz nao fecha o triangulo de sincronia das tres copias.

Ruling: o workspace NAO e apagado, contra o passo final padrao da skill. Este repositorio versiona
  ledger e relatorios de execucao SDD -- commit b4e520b, "versiona o ledger e os relatorios desta
  execucao", e o .gitignore em .superpowers/sdd/ mantem os .md sob controle de versao de proposito.
  Custo se errado: o repositorio ganha ~20 arquivos de registro que o usuario pode remover num commit.

---
name: especificar-telas-ux-ui
description: Use quando uma spec de produto ou software precisa ser analisada, antes da geração do backlog, para identificar quais requisitos exigem tela nova ou fluxo de tela alterado em front-end web e/ou mobile, produzindo conteúdo em linguagem de UX-UI rastreável ao código-fonte.
---

# Especificar telas para UX-UI a partir da Spec

## Objetivo

Identificar, por inspeção somente leitura do código de front-end já existente — nunca por interpretação
do texto de negócio —, quais requisitos de uma Spec exigem que a equipe de UX-UI especifique uma tela
nova ou um fluxo de tela alterado, em front-end web e/ou em aplicativo mobile, antes que a implementação
funcional possa avançar. A saída é um briefing que a equipe de UX-UI consegue usar sem abrir o código e
sem conhecer o processo que o gerou, rastreável ao requisito de origem, mais uma anotação na própria
Spec para consumo opcional por `gerar-backlog-azure-boards`.

## Para quem a saída é escrita

Quem lê o documento gerado é gente de UX-UI que não abre o código, não conhece esta skill e não
participou da entrevista que fechou a spec. O briefing precisa bastar por si:

- **Sem vocabulário de processo no briefing:** `Brownfield-UI`, `Greenfield-UI`, `Status de cobertura`,
  `Impossível validar`, "esta skill", "comissionar item", nome de skill nenhum aparecem na parte lida
  pela equipe de UX-UI.
- **Sem `caminho:linha` no briefing:** quem desenha não abre `.ts`, `.dart` nem `.tsx`.
- **Padrão existente descrito em linguagem de design:** o que aparece na tela, onde, com que ação e em
  que estado — nunca "componente X importado no arquivo Y".
- **Cada afirmação precisa mudar uma decisão de desenho.** Frase que não muda nada no desenho não entra.
- Modo, matriz de evidência, caminhos de código e nomes de skill ficam **todos** na seção final de
  rastreabilidade, declarada como seção que não é para a equipe de UX-UI.

Economia de texto é requisito da saída, não estilo: um campo repetido em quatro seções, um item inteiro
escrito por referência a outro e um parágrafo de hedge sobre uma regra simples custam atenção da equipe
e não pagam nada.

## Escopo

Trate cada requisito da spec com faceta de UI, por plataforma aplicável, independentemente. Esta skill
não decompõe a spec em Épico, Feature ou item de folha — isso continua sendo papel de
`gerar-backlog-azure-boards`. Não decide texto final de interface (título, label, CTA, mensagem de
sucesso/erro/vazio, tooltip) — isso é escopo de `revisar-textos-requisitos`.

## Modo, por plataforma

Declare o Modo de web e de mobile **separadamente**, porque as duas plataformas podem estar em estágios
de maturidade diferentes:

- **Greenfield-UI:** nenhum código de front-end relevante acessível para aquela plataforma. Todo
  requisito com faceta de UI aplicável a ela é tratado como "necessita especificação de tela", porque não
  há nada para comparar. Registre a ausência e não exija uma inspeção inexistente.
- **Brownfield-UI:** há código acessível para aquela plataforma. Inspecione somente leitura — rotas,
  páginas, telas, componentes — em busca de uma tela ou fluxo equivalente ao requisito.
- Presença ambígua em qualquer plataforma → trate como Brownfield-UI conservador para ela, registre a
  incerteza e os limites da busca; nunca conclua ausência de tela pela falta de investigação.
- Se o produto genuinamente não tiver uma das plataformas no seu escopo, registre `Não aplicável` para
  ela — diferente de `Impossível validar` (a plataforma existe, mas não foi possível inspecionar o código
  correspondente).

A skill não recebe caminho de projeto como parâmetro: investigue a partir do diretório onde está
instalada e de seus repositórios irmãos, procurando sinais convencionais de cada stack (por exemplo,
front-end web via framework de rotas/páginas; mobile via projeto React Native, Flutter ou nativo
Android/iOS). Registre quais repositórios parecem relevantes a cada plataforma e quais foram descartados,
com o motivo — mesmo padrão de "Repositórios considerados" de `redigir-spec-pedido-negocio`.

## Fluxo

1. **Leia a spec inteira** e monte um inventário de requisitos, preservando origem (seção/âncora).
2. **Descubra os repositórios candidatos** de web e de mobile e declare o Modo de cada plataforma.
3. **Para cada requisito, determine a(s) plataforma(s) aplicável(is):** se a spec especificar explicitamente uma plataforma, use essa; caso contrário, o requisito se aplica a todas as plataformas que existirem no produto (uma plataforma `Não aplicável` fica de fora).
4. **Confirme a faceta de UI** do requisito a partir do texto da spec. Também tem faceta de UI o
   requisito que muda **o que uma tela existente passa a mostrar** — volume, origem, escopo ou
   procedência do que é listado — mesmo que a spec não peça tela nova: ampliar o que um perfil enxerga
   é faceta de UI. Sem faceta de UI, ignore — não inspecione código nenhum para esse requisito. Se o
   único impacto identificado for texto/copy (sem tela nova nem fluxo alterado), também ignore e
   registre `revisar-textos-requisitos` na rastreabilidade como próximo passo manual opcional.
5. **Nunca conclua cobertura por omissão.** Todo requisito com faceta de UI vira uma linha classificada,
   inclusive quando a conclusão é que a tela existente já resolve: nesse caso registre a conclusão com a
   evidência que a sustenta. Um requisito com faceta de UI que some do documento é falha de cobertura,
   não decisão de escopo.
6. **Para cada par (requisito, plataforma) com faceta de UI estrutural**, antes de inspecionar, leia e
   siga [references/ui-brownfield-validation.md](references/ui-brownfield-validation.md): inspeção
   somente leitura, formato de evidência `caminho:linha` e o vocabulário de status.
7. **Classifique** cada par com exatamente um destes status: `Implementado`, `Parcialmente implementado`, `Não encontrado`, `Impossível validar`, `Não aplicável`. Ausência de evidência nunca é serializada como `Implementado`. Em Greenfield-UI, classifique todo par como `Não encontrado`, registrando a ausência de código de front-end como motivo; `Impossível validar` pressupõe uma plataforma que existe mas não pôde ser inspecionada.
8. **Gere um item de design somente quando o status não for `Implementado` nem `Não aplicável` e a
   plataforma for necessária.** Sempre um item por plataforma necessária —
   nunca agrupe web e mobile no mesmo item de design, mesmo quando o requisito funcional
   correspondente for único para as duas plataformas. Uma plataforma só é necessária quando a spec
   a declara ou quando o produto tem precedente de tela daquela natureza nela. Se a spec silencia **e** a plataforma não tem nenhum
   precedente daquele tipo de tela (por exemplo, um app sem nenhuma tela administrativa recebendo um
   cadastro administrativo), a necessidade **não está confirmada**: registre uma pergunta aberta única
   no item da plataforma que tem precedente e não gere um item vazio para a outra. Um item de design
   cujo roteiro, copy e padrão visual são todos "iguais aos do outro item" não é um item — é uma
   pergunta aberta.
9. **Escreva o roteiro de tela** de cada item gerado: lista numerada, em linguagem simples,
   sem sintaxe Gherkin (sem `Dado/Quando/Então`, sem `Funcionalidade`/`Cenário`) — o que a pessoa
   quer fazer e o que ela vê acontecer, na voz de quem usa, nunca na voz do sistema. Rastreie cada item do roteiro a uma
   regra ou trecho do requisito de origem. O roteiro precisa cobrir obrigatoriamente:
   - o **primeiro uso**, com a base vazia, e como se cria o primeiro registro (inclusive o registro
     raiz, quando houver hierarquia);
   - o **ponto de entrada**: de onde a pessoa chega à tela e quem enxerga esse caminho;
   - **toda ação pressuposta por alguma regra**. Se uma regra fala em mover, reordenar, vincular ou
     desfazer, o roteiro precisa dizer como se faz isso — ou registrar a interação como pergunta aberta.
     Regra sem ação correspondente é lacuna, não detalhe de implementação.
10. **Desenhe o fluxo em diagrama Mermaid** sempre que a tela tiver mais de um caminho ou algum
    bloqueio; tela de caminho único não precisa de diagrama. Use `flowchart TD` para a navegação —
    ponto de entrada, tela principal, formulários, decisões de validação, bloqueios e volta — e
    `stateDiagram-v2` quando algum objeto da tela tiver ciclo de vida próprio. Convenções obrigatórias:
    - caminho já decidido em linha cheia; caminho ainda pendente de decisão em linha tracejada
      (`-.->`), para a lacuna ficar visível no desenho em vez de sumir dentro dele;
    - cada bloqueio como nó próprio, numerado igual ao texto correspondente em "Textos a definir";
    - rótulo de aresta na forma `-->|Sim|`, rótulo de nó entre aspas e quebra de linha com `<br/>`,
      que são as formas de sintaxe mais amplamente suportadas pelos renderizadores de Markdown;
    - o diagrama não substitui o roteiro nem a tabela de regras: ele mostra a forma do fluxo, e elas
      carregam o detalhe.
    Depois de desenhar, confira se todo estado e toda ação citados pelas regras têm entrada e saída no
    diagrama. **Caminho sem origem, sem volta ou sem interação definida é lacuna** — registre em
    "Perguntas abertas" em vez de completar o desenho por plausibilidade.
11. **Separe regra de fluxo.** As validações e bloqueios não entram no roteiro como passos: vão para uma
    tabela própria, dizendo em que momento a pessoa esbarra na regra e se ela exige um texto de
    interface. Assim a equipe lê o caminho feliz de uma vez e trata os bloqueios como um conjunto.
12. **Liste os campos e os estados.** Campos: nome, exemplo, obrigatoriedade e observação, incluindo os
    que a spec cita sem decidir (marque como pergunta aberta em vez de omitir). Estados: vazio,
    carregando, erro, sem permissão e os estados próprios do domínio (registro inativo, vínculo sem
    efeito). Sem campos e sem estados, ninguém consegue desenhar formulário nem tela.
13. **Registre o volume esperado.** Quantos registros, quantos níveis, com que frequência de uso. Quando
    a spec indicar que o exemplo é só um trecho e o cadastro será progressivo, isso vira pergunta aberta
    explícita: volume decide busca, colapso, carregamento por demanda e navegação, e é a variável que
    mais muda o layout.
14. **Registre a necessidade de copy** de cada item gerado quando o roteiro envolver texto voltado ao
    usuário (label, mensagem, CTA, estado vazio/erro): liste os pontos e não defina o texto final. A
    indicação de `revisar-textos-requisitos` como próximo passo manual opcional vai na rastreabilidade,
    não no briefing.
15. **Feche as perguntas abertas em tabela**, com o que cada uma trava no desenho e, quando houver uma
    opção segura, a recomendação provisória para a equipe não ficar parada.
    Pergunta aberta sem consequência declarada é ruído.
16. **Anote a Spec** com a seção `## Necessidade de especificação de tela` e **salve o documento separado** `Spec: Telas UX-UI — <contexto>`, no formato de [Formato das saídas](#formato-das-saídas). Se a spec já tiver essa seção de uma rodada anterior, substitua-a por inteiro — nunca acrescente uma segunda seção duplicada. Quem chama pode informar um **diretório de destino**; nesse caso grave o documento nele com o nome exato `telas-ux-ui.md`. **Sem diretório de destino informado, salve como sempre fez.** O título do documento identifica-o nos dois casos.
17. **Pare.** Não invoque nenhuma outra skill. Reporte ao usuário os caminhos salvos e sugira
    `gerar-backlog-azure-boards` como próximo passo manual.

## Formato das saídas

### Anotação na Spec

```markdown
## Necessidade de especificação de tela
| Requisito | Plataforma | Status de cobertura | Referência |
|---|---|---|---|
| [seção/âncora do requisito] | Web \| Mobile | Não encontrado \| Parcialmente implementado \| Impossível validar | TL-01 |
```

Sem nenhum requisito sinalizado, registre exatamente `Nenhuma necessidade de tela identificada` em vez de
omitir a seção.

### Documento separado — `Spec: Telas UX-UI — <contexto>`

O documento tem duas partes e a ordem importa: primeiro o briefing, escrito para a equipe de UX-UI;
depois a rastreabilidade, escrita para quem mantém a spec.

```markdown
# Spec: Telas UX-UI — <contexto>

**Para:** equipe de UX-UI · **Plataforma:** <Web | Mobile> · **Origem:** <spec, seção>

## TL-01 — <título curto, com a plataforma no nome>

### Plataforma
<Web | Mobile — valor único; um item de design nunca cobre as duas>

### Por que esta tela existe
<2 a 4 frases: o que hoje não dá para fazer, o que passa a dar, e o que trava enquanto a tela não
existe. Sem repetir a frase do requisito em outras quatro seções.>

### Quem usa
<perfil, o que o distingue de perfis parecidos do produto e com que frequência usa a tela>

### Onde fica
<ponto de entrada real: menu, seção, vizinhança; e quem enxerga esse caminho>

### O que a pessoa precisa fazer
1. <o que a pessoa quer fazer> → <o que ela vê acontecer>
   (inclui primeiro uso com base vazia e toda ação pressuposta por alguma regra)

### Fluxo da tela
<diagrama Mermaid da navegação, com caminho pendente tracejado e bloqueios numerados; mais uma ou duas
frases sobre o que o desenho torna evidente>

### Regras que a tela precisa honrar
| Regra | Quando a pessoa esbarra nela | Precisa de texto de interface? |
|---|---|---|
| <regra> | <momento concreto> | Sim, texto N \| Não |

### Campos
| Campo | Exemplo | Obrigatório | Observação |
|---|---|---|---|

### Estados da tela
<vazio, carregando, erro, sem permissão e os estados do domínio>

### Volume e escala
<quantos registros, quantos níveis, frequência de uso; e a tensão de layout que isso cria>

### Referência de padrão no produto
<tela existente equivalente, descrita em linguagem de design: o que aparece, onde, com que ação e em
que estado. Distinga padrão em uso de componente apenas disponível e nunca usado; ou "Nenhuma
referência confiável disponível">

### Textos a definir
<pontos de texto voltado ao usuário, numerados para casar com a tabela de regras; ou "Não identificada">

### Perguntas abertas
| # | Pergunta | O que trava no desenho |
|---|---|---|

### Fora do escopo desta tela, mas afetado pelo mesmo requisito
<telas existentes que mudam de comportamento por causa do requisito e ainda não têm decisão de design;
ou "Nada identificado">

### O que se espera desta especificação
<entregável concreto: fluxo, wireframes de quais estados, textos, comportamento responsivo>

## Rastreabilidade — não é para a equipe de UX-UI
| Plataforma | Repositório considerado | Relevante? | Motivo |
|---|---|---|---|

- Modo Web: Greenfield-UI | Brownfield-UI
- Modo Mobile: Greenfield-UI | Brownfield-UI

| Item | Requisito de origem (seção/âncora) | Plataforma | Status de cobertura | Evidência `caminho:linha` |
|---|---|---|---|---|
| TL-01 | ... | Web | Não encontrado | ... |

<próximos passos manuais opcionais, incluindo revisar-textos-requisitos quando houver texto de interface
a definir>
```

Repita a seção do item para cada par (requisito, plataforma) sinalizado. Use `TL-01`, `TL-02` apenas como
chaves documentais deste documento; elas não são IDs de work items nem chaves `E.F.S` do backlog.

A subseção `### Plataforma` é o único lugar onde a plataforma do item é campo estruturado, com valor
único `Web` ou `Mobile`. O cabeçalho do documento e o título em prosa de cada item continuam existindo
para quem lê, mas `gerar-backlog-azure-boards` nunca deve depender de parsing de título ou de cabeçalho
para decidir a tag `plataforma-web`/`plataforma-mobile` de um item de design — só desta subseção.

## Boundaries

- Skill-folha: nunca invoque nenhuma outra skill deste repositório; ao terminar, sugira
  `gerar-backlog-azure-boards` como próximo passo manual do usuário.
- Não acesse Figma nem qualquer ferramenta de design externa; toda a análise é Spec + código-fonte.
- Não decida nem escreva copy final de interface; registre `revisar-textos-requisitos` como revisão
  manual opcional na rastreabilidade quando o roteiro de tela envolver texto voltado ao usuário.
- Não execute build, testes, servidores ou o aplicativo; inspeção somente leitura, sem autorização
  explícita para qualquer execução.
- Não invente componente ou padrão de Design System sem origem confirmada na Spec ou no código, e não
  apresente como padrão adotado um componente apenas disponível no projeto e não usado por nenhuma tela.
- Não feche um caminho no diagrama para ele parecer completo: caminho não decidido vai tracejado e
  vira pergunta aberta.
- Não escreva o briefing na voz do sistema ("o sistema bloqueia", "o sistema exibe") — isso é critério de
  aceite, não roteiro de tela.
- Não repita o mesmo enunciado em título, card, origem e bloqueio; uma vez basta.
- Não deixe requisito com faceta de UI fora do documento: silêncio não é cobertura.
- Não decida prontidão nem produza Conversation, Card, Gherkin ou prontidão geral — o roteiro de tela é
  insumo para a 3C, não um veredito.
- Não crie, atualize ou publique work items no Azure Boards.
- Nunca serializa `Implementado` por ausência de evidência de código.
- Não crie item do tipo Task nem Bug para necessidade de tela — sempre uma User Story de design nova.
- Não divida o item funcional por plataforma — só multiplica o item de design quando necessário.

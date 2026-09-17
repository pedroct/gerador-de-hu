---
name: especificar-telas-ux-ui
description: Use quando uma spec de produto ou software precisa ser analisada, antes da geração do backlog, para identificar quais requisitos exigem tela nova ou fluxo de tela alterado em front-end web e/ou mobile, produzindo conteúdo em linguagem de UX-UI rastreável ao código-fonte.
---

# Especificar telas para UX-UI a partir da Spec

## Objetivo

Identificar, por inspeção somente leitura do código de front-end já existente — nunca por interpretação
do texto de negócio —, quais requisitos de uma Spec exigem que a equipe de UX-UI especifique uma tela
nova ou um fluxo de tela alterado, em front-end web e/ou em aplicativo mobile, antes que a implementação
funcional possa avançar. A saída é conteúdo em linguagem acessível à equipe de UX-UI, sem sintaxe Gherkin, rastreável ao requisito de origem, mais uma anotação na própria Spec para consumo opcional por
`gerar-backlog-azure-boards`.

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
4. **Confirme a faceta de UI** do requisito a partir do texto da spec. Sem faceta de UI, ignore — não inspecione código nenhum para esse requisito. Se o único impacto identificado for texto/copy (sem tela nova nem fluxo alterado), também ignore e indique `revisar-textos-requisitos` como próximo passo manual opcional.
5. **Para cada par (requisito, plataforma) com faceta de UI estrutural**, antes de inspecionar, leia e aplique [references/ui-brownfield-validation.md](references/ui-brownfield-validation.md): inspeção somente leitura, formato de evidência `caminho:linha` e o vocabulário de status.
6. **Classifique** cada par com exatamente um destes status: `Implementado`, `Parcialmente implementado`, `Não encontrado`, `Impossível validar`, `Não aplicável`. Ausência de evidência nunca é serializada como `Implementado`.
7. **Gere um item de design somente quando o status não for `Implementado` nem `Não aplicável`.** Sempre um item por plataforma necessária — nunca agrupe web e mobile no mesmo item de design, mesmo quando o requisito funcional correspondente for único para as duas plataformas.
8. **Escreva o roteiro de tela** de cada item gerado: lista numerada, em linguagem simples, sem sintaxe Gherkin (sem `Dado/Quando/Então`, sem `Funcionalidade`/`Cenário`) — situação → ação do usuário → o que muda na tela. Rastreie cada item do roteiro a uma regra ou trecho do requisito de origem.
9. **Registre a necessidade de copy** de cada item gerado quando o roteiro envolver texto voltado ao usuário (label, mensagem, CTA, estado vazio/erro): liste os pontos e indique `revisar-textos-requisitos` como próximo passo manual opcional — não defina o texto final.
10. **Anote a Spec** com a seção `## Necessidade de especificação de tela` e **salve o documento separado** `Spec: Telas UX-UI — <contexto>`, no formato de [Formato das saídas](#formato-das-saídas).
11. **Pare.** Não invoque nenhuma outra skill. Reporte ao usuário os caminhos salvos e sugira
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

```markdown
# Spec: Telas UX-UI — <contexto>

## Contexto e origem
<spec de origem, seção ou demanda relacionada>

## Descoberta de plataformas
| Plataforma | Repositório considerado | Relevante? | Motivo |
|---|---|---|---|
| Web | [nome ou "nenhum encontrado"] | Sim/Não | [justificativa] |
| Mobile | [nome ou "nenhum encontrado"] | Sim/Não | [justificativa] |

## Modo
- Modo Web: Greenfield-UI | Brownfield-UI
- Modo Mobile: Greenfield-UI | Brownfield-UI

## Resumo priorizado
| Item | Requisito de origem | Plataforma | Status de cobertura |
|---|---|---|---|
| TL-01 | ... | Web | Não encontrado |

## TL-01 — <título curto, com a plataforma no nome>
### Título
<título curto, acionável, sem ID do Azure Boards>
### Origem
<seção/âncora da Spec>
### Plataforma
Web ou Mobile
### Card
Como equipe de UX-UI, quero especificar a tela <plataforma> de <resultado>, para permitir a
implementação de <requisito de origem>.
### Evidência de código
- Status: Implementado | Parcialmente implementado | Não encontrado | Impossível validar | Não aplicável
- Referência: `caminho:linha`, ou o motivo quando não houver referência
### Roteiro de tela
1. <situação> → <ação do usuário> → <o que muda na tela>
### Necessidade de copy
<pontos de texto voltado ao usuário, indicando revisar-textos-requisitos como próximo passo manual
opcional; ou "Não identificada">
### Referências ao Design System
<componente/padrão já conhecido pela spec ou pelo código; ou "Nenhuma referência confiável disponível">
### Bloqueia
<referência ao requisito funcional de origem por seção/âncora da Spec>
### Lacunas
<perguntas ou decisões pendentes>
```

Repita a seção do item para cada par (requisito, plataforma) sinalizado. Use `TL-01`, `TL-02` apenas como
chaves documentais deste documento; elas não são IDs de work items nem chaves `E.F.S` do backlog.

## Boundaries

- Skill-folha: nunca invoque nenhuma outra skill deste repositório; ao terminar, sugira
  `gerar-backlog-azure-boards` como próximo passo manual do usuário.
- Não acesse Figma nem qualquer ferramenta de design externa; toda a análise é Spec + código-fonte.
- Não decida nem escreva copy final de interface; indique `revisar-textos-requisitos` como revisão manual
  opcional quando o roteiro de tela envolver texto voltado ao usuário.
- Não execute build, testes, servidores ou o aplicativo; inspeção somente leitura, sem autorização
  explícita para qualquer execução.
- Não invente componente ou padrão de Design System sem origem confirmada na Spec ou no código.
- Não decida prontidão nem produza Conversation, Card, Gherkin ou prontidão geral — o roteiro de tela é
  insumo para a 3C, não um veredito.
- Não crie, atualize ou publique work items no Azure Boards.
- Nunca serializa `Implementado` por ausência de evidência de código.
- Não crie item do tipo Task nem Bug para necessidade de tela — sempre uma User Story de design nova.
- Não divida o item funcional por plataforma — só multiplica o item de design quando necessário.

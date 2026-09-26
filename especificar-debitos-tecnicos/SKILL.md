---
name: especificar-debitos-tecnicos
description: Use when um débito técnico é identificado durante o entendimento, refinamento ou análise de uma demanda e precisa ser registrado como trabalho rastreável para o backlog do Azure Boards.
---

# Especificar débitos técnicos para Azure Boards

## Objetivo

Transforme débitos técnicos observados durante uma conversa de requisito ou uma inspeção
Brownfield em uma spec Markdown revisável. A saída deve permitir que
`gerar-backlog-azure-boards` gere um item de folha, mas não deve criar ou alterar
   work items no Azure Boards; não cria nem altera work items.

## Fluxo

1. Registre cada débito como um item independente e preserve sua origem: demanda, decisão,
   evidência `caminho:linha`, log, teste ou observação explicitamente fornecida. Código sem relação
   com a demanda é achado incidental, não débito automaticamente.
2. Categorize cada item como `Código`, `Arquitetura`, `Testes`, `Dependências`, `Documentação` ou
   `Infraestrutura`. Explique o efeito concreto sobre entrega, operação, segurança, evolução ou
   confiabilidade.
3. Dê notas inteiras de 1 a 5 para Impacto, Risco e Esforço. Calcule a prioridade como
   **(Impacto + Risco) × (6 − Esforço)**; menor esforço recebe maior prioridade. Se uma nota não
   puder ser justificada, marque-a como estimativa e registre a lacuna.
4. Recomende o tipo por item:
   - `Bug` quando há um comportamento atual incorreto em relação a um requisito, contrato ou regra
     já estabelecida, e o dano é a correção do comportamento observado.
   - `User Story` quando se trata de melhoria de manutenibilidade, redução de risco ou capacidade
     técnica que ainda não existe, sem defeito observável a corrigir.
   Não transforme todo débito em Bug só porque é urgente, nem toda refatoração em User Story sem
   explicar o resultado esperado.
5. Escreva o resultado esperado como uma mudança verificável, delimite o que está fora do escopo e
   proponha uma fase de remediação compatível com o trabalho de produto. Não crie solução detalhada
   quando a evidência não a sustenta.
6. Liste dependências, riscos de não fazer e lacunas que exigem decisão. Critérios de aceite devem
   ser objetivos e só podem afirmar comportamento confirmado; pendências ficam em `Lacunas`, não
   viram regras inventadas.

## Priorização assistida (opcional)

Para pontuar muitos débitos de uma vez com a mesma régua, existe uma implementação dos passos 3 e
4 por modelo de decisão:

```bash
uv run python especificar-debitos-tecnicos/scripts/priorizar.py debito.md
```

Uma requisição devolve Impacto, Esforço, Probabilidade e Severidade como posições em escalas
ordenadas de cinco níveis, mais a categoria e a indicação de `Bug` ou `User Story`. O Risco da nota
final é a matriz probabilidade × severidade, e a fórmula `(Impacto + Risco) × (6 − Esforço)`
permanece em código. Requer `JEV_OPENROUTER_API` no `.env`.

As descrições dos níveis seguem o padrão BARS — situação observável por nível, nunca grau nem
número — e `scripts/retranslacao.py` verifica se cada âncora ainda atrai um exemplo do próprio
nível. Rode-o depois de editar qualquer descrição.

Duas ressalvas antes de usar:

- **As descrições dos cinco níveis não vêm desta skill.** O passo 3 pede notas de 1 a 5 sem dizer o
  que cada nota significa; as situações que definem cada nível foram redigidas em
  `scripts/priorizacao.py` e merecem revisão de quem conhece o contexto.
- **A fórmula é uma métrica de eficiência, e itens intoleráveis não competem por eficiência.**
  Um débito grave e caro afunda nela. Em vez de alterar a fórmula, o script classifica antes de
  ordenar, em três faixas:

  | Faixa | Quando | Como ordena |
  |---|---|---|
  | Restrição | severidade ≥ 4 e probabilidade ≥ 2 | por gravidade; o esforço não a adia |
  | A confirmar | confiança na severidade < 0,60 | por gravidade; decide quem prioriza |
  | Candidato | demais | pela fórmula da skill |

  `sinalizar_inversoes()` aponta inversões entre os candidatos, sem corrigi-las.

- **A `Faixa` registrada na spec é fotografia da geração, não obrigação recalculável.** Quando
  `gerar-backlog-azure-boards` publica um item nascido de um DT, a tag `dt-<faixa>` grava o valor
  presente nesta rodada. Uma reavaliação posterior que mude a `Faixa` aqui registrada não atualiza
  sozinha o work item já criado — a mudança só chega ao board com nova publicação ou edição manual.

- **Descreva o que acontece quando o débito se manifesta**, não apenas o que está errado. Sem isso
  a severidade é inferida e a confiança cai — num teste, acrescentar a consequência levou a
  severidade de 4 com confiança 0,50 para 5 com confiança 1,00, e o item saiu de *a confirmar*
  para *restrição*.

Medição e limites em [`references/medicao-priorizacao.md`](references/medicao-priorizacao.md).

## Formato da spec

Quem chama esta skill pode informar um **diretório de destino**. Nesse caso, grave a spec nele com o
nome exato `debitos-tecnicos.md`. **Sem diretório de destino informado, salve como sempre fez** e
relate o caminho ao usuário. O título do documento continua sendo `Spec: Débitos técnicos — <contexto>`
nos dois casos: é ele que identifica o documento, não o nome do arquivo.

```markdown
# Spec: Débitos técnicos — <contexto>

## Contexto e origem
<demanda, sessão de refinamento ou spec relacionada>

## Fonte da Demanda
[Se a spec, sessão ou conversa de origem tiver a seção `## Fonte da Demanda`, copie-a aqui exatamente
como está lá — mesmo `#<id>` e mesma URL. Caso contrário: `Não se aplica — a origem não é uma Demanda
de Negócio publicada.`]

**Nunca derive este valor do nome da pasta.** Um diretório `DN-14125-<slug>/` parece uma resposta e
não é: pode ter sido renomeado à mão, copiado de outra Demanda ou criado por engano. O único ID válido
é o que já estava escrito na seção `## Fonte da Demanda` da origem lida — sem essa seção na origem,
registre `Não se aplica`, nunca infira o número.

## Resumo priorizado
| Item | Categoria | Tipo sugerido | Impacto | Risco | Esforço | Prioridade | Faixa |
|---|---|---|---:|---:|---:|---:|---|
| DT-01 | ... | User Story/Bug | 1-5 | 1-5 | 1-5 | ... | Restrição \| Candidato \| A confirmar |

## DT-01 — <título acionável>
### Título
<título curto, acionável e sem ID do Azure Boards>
### Origem
<seção, conversa, decisão ou evidência que originou o débito>
### Tipo sugerido
User Story ou Bug — justificativa baseada no comportamento atual e esperado.
### Descrição
Como <ator afetado>, quero <resultado técnico>, para <impacto evitado ou valor entregue>.
### Problema e comportamento atual
<fato observado, sem inferências; evidências caminho:linha quando existirem>
### Comportamento esperado e escopo
<mudança verificável>; Fora do escopo: <limites>.
### Critérios de aceite
- <condição verificável>
- <condição verificável>
### Priorização
- Impacto: <1-5> — <justificativa>
- Risco: <1-5> — <justificativa>
- Esforço: <1-5> — <justificativa>
- Prioridade: `<cálculo>`
- Faixa: <Restrição | Candidato | A confirmar>
### Remediação faseada
1. <fase mínima>
2. <fase posterior, se aplicável>
### Dependências e risco de não fazer
<conteúdo>
### Evidências e origem
<referências rastreáveis>
### Lacunas
<perguntas ou decisões pendentes>
```

Repita a seção do item para cada débito. Use `DT-01`, `DT-02` apenas como chaves documentais;
elas não são IDs de work items. Para uma nota estimada ou evidência ausente, escreva `Não
confirmado` em vez de preencher por plausibilidade.

## Limites

- Não crie, atualize ou publique work items, nem invente ID, Area Path, Iteration Path, responsável,
  Story Points, prioridade do Azure ou data.
- Não invente evidência, impacto, notas, ator ou valor de negócio; use `Não confirmado` e registre a
  lacuna quando a fonte não sustentar uma conclusão.
- Não faça inspeção Brownfield além da autorizada pelo fluxo chamador; não execute testes, builds,
  migrações, servidores ou a aplicação sem autorização explícita.
- Não confunda consequência com causa: descreva a causa técnica somente quando houver evidência e
  mantenha o impacto de negócio separado.
- Não chame automaticamente 3W, 3C, Gherkin, entrevista de lacunas ou geração de backlog. Entregue
  a spec e indique a geração de backlog como próxima etapa manual.
- A recomendação de tipo não é decisão irrevogável: o backlog pode revisá-la por item quando a spec
  trouxer evidência adicional.
- Nunca derive `## Fonte da Demanda` do nome da pasta que contém esta spec; copie-a só da origem que
  a declara, e registre `Não se aplica` quando a origem não a declarar.
- Quando esta spec declarar `## Fonte da Demanda`, indique ainda assim `publicar-backlog-azure-boards`
  (a publicadora solta) como próxima etapa manual do backlog gerado a partir dela — nunca
  `publicar-backlog-demanda-azure-boards`. Esta última herdaria da Demanda o `Iteration Path`, e o
  débito nasceria na sprint da Demanda: exatamente a sprint em que ele não será pago.

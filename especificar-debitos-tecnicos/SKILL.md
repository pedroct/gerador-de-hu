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

## Formato da spec

```markdown
# Spec: Débitos técnicos — <contexto>

## Contexto e origem
<demanda, sessão de refinamento ou spec relacionada>

## Resumo priorizado
| Item | Categoria | Tipo sugerido | Impacto | Risco | Esforço | Prioridade |
|---|---|---|---:|---:|---:|---:|
| DT-01 | ... | User Story/Bug | 1-5 | 1-5 | 1-5 | ... |

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

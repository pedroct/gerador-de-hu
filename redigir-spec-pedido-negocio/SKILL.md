---
name: redigir-spec-pedido-negocio
description: Use quando um pedido de negócio, como e-mail, ticket ou mensagem, descreve informalmente um problema ou demanda sem spec escrita e o código-fonte local está disponível para fundamentá-lo antes da geração do backlog.
---

# Redigir spec a partir de pedido de negócio

## Objetivo

Transformar um pedido informal de negócio (e-mail, ticket, mensagem) em uma spec em Markdown, apoiada
em investigação somente leitura do código-fonte já presente onde esta skill está instalada. A spec
resultante é a entrada que `gerar-backlog-azure-boards` já aceita hoje; esta skill não
decompõe em Épico, Feature ou História e não gera Acceptance Criteria.

## Escopo

Trate o pedido inteiro como uma única unidade de escopo; nunca o divida em múltiplos itens. Isso vale
mesmo quando o pedido parecer pequeno demais ou incompleto.

## Fluxo

1. **Leia o pedido por completo**, preservando a formulação original ao citá-lo na spec.
2. **Descubra os repositórios candidatos.** A skill não recebe caminho de projeto como parâmetro:
   investigue a partir do diretório onde está instalada e de seus repositórios irmãos. Registre quais
   parecem relevantes ao vocabulário do pedido e quais foram descartados, com o motivo.
3. **Antes de investigar, leia e aplique**
   [references/business-request-investigation.md](references/business-request-investigation.md):
   inspeção somente leitura, formato de evidência `caminho:linha` e separação entre afirmação do
   pedido, evidência de código e lacuna.
4. **Redija a spec** no template abaixo, preenchendo cada seção só com o que foi confirmado pelo
   pedido ou evidenciado pelo código.
5. **Encaminhe débitos técnicos, se identificados:** quando a investigação encontrar um débito
   relacionado ao escopo ou explicitamente relevante para a demanda, **REQUIRED OPTIONAL SUB-SKILL:**
   use `especificar-debitos-tecnicos`, fornecendo evidência, origem e contexto. Anexe
   a spec de débitos como seção separada; não misture o débito ao requisito de negócio.
6. **Feche lacunas por entrevista, se disponível:** se a skill `entrevistar-lacunas-requisito` estiver instalada, use-a para fechar o máximo possível das lacunas antes de salvar o arquivo; caso não esteja, salve com as lacunas documentadas normalmente.
7. **Salve o documento em arquivo e pare. Não invoque nenhuma outra skill.** Essa proibição cobre o
   restante do pipeline (3W, 3C, Gherkin, geração de backlog); as únicas exceções são os Passos 5 e 6.
   Informe ao
   usuário o caminho salvo e um resumo das lacunas e perguntas encontradas. Se a spec salva ainda tiver
   itens em `## Lacunas e perguntas abertas`, sugira explicitamente rodar `entrevistar-lacunas-requisito`
   (quando instalada) como próximo passo manual, antes de a spec seguir para
   `gerar-backlog-azure-boards`. Se houver copy voltada ao usuário na spec, indique
   também, como próximo passo manual opcional, a skill `revisar-textos-requisitos` (quando
   instalada), sem chamá-la diretamente. Se a spec tiver requisitos com faceta de interface, indique também, como próximo passo manual opcional, a skill `especificar-telas-ux-ui` (quando instalada), sem chamá-la diretamente.

## Ausência de repositório relevante

Se nenhum repositório candidato tiver relação com o pedido, registre essa ausência e produza a spec
apenas com o conteúdo do pedido, equivalente ao modo Greenfield da quarta skill — sem travar a entrega
do documento.

## Classificação do pedido

Classifique o pedido comparando `Comportamento atual` com `Comportamento esperado`:

- **Defeito**: a evidência de código mostra o sistema fazendo algo que o próprio pedido, ou uma regra
  já estabelecida no código, trata como incorreto — por exemplo, permitir uma ação que deveria ser
  bloqueada. O sistema hoje se comporta de um jeito que ele mesmo (ou o pedido) reconhece como errado.
- **Melhoria**: o pedido descreve uma capacidade ou resultado que hoje não existe, sem que o
  comportamento atual esteja incorreto em si — apenas incompleto ou ausente.
- **Outro**: a evidência não permite decidir com confiança entre as duas opções acima. Registre a
  incerteza em vez de escolher por plausibilidade.

Essa classificação é metadado da spec, para apoiar decisões de tipo de work item mais adiante; esta skill não cria, seleciona nem sugere tipo de work item específico (ex.: Bug) — isso continua fora do seu escopo.

## Template da spec

```markdown
# Spec: <título curto>

## Fonte do pedido
Texto original (citado ou anexado) e canal de origem.

## Escopo
Tratado como item único; nenhuma decomposição foi aplicada.

## Repositórios considerados
| Repositório | Relevante? | Motivo |
|---|---|---|
| [nome] | Sim/Não | [justificativa] |

## Problema relatado
Síntese fiel do que o pedido descreve, sem inferências.

## Comportamento atual (evidência no código)
| Afirmação/observação | Evidência `caminho:linha` | Confiança |
|---|---|---|
| ... | ... | Alta/Média/Baixa |

## Comportamento esperado
- Afirmado explicitamente pelo pedido: ...
- Inferido (marcado como inferência, não fato confirmado): ...

## Classificação
- **Tipo**: Defeito | Melhoria | Outro
- **Justificativa**: evidência que sustenta a classificação, referenciando Comportamento atual e
  Comportamento esperado.

## Atores e vocabulário identificados no código
Lista de atores, entidades e termos de domínio encontrados, com evidência.

## Lacunas e perguntas abertas
Tudo que não pôde ser confirmado nem pelo pedido nem pelo código.
```

## Boundaries

- Somente leitura; não execute scripts, testes, build, servidores, migrações ou a aplicação sem
  autorização explícita.
- Nunca decomponha o pedido em múltiplos itens.
- Nunca invente ator, regra, critério de aceite ou decisão de negócio a partir do código; código
  existente não cria requisito nem confirma decisão de negócio.
- Não produza Épico, Feature, História, Description nem Acceptance Criteria para a demanda principal;
  isso continua sendo responsabilidade de `gerar-backlog-azure-boards` e da 3C. A
  exceção é a spec separada de débito técnico produzida pela subskill opcional.
- Não encadeie automaticamente a geração do backlog; a spec fica pronta para uso manual do usuário.
- Classifique o pedido (Defeito, Melhoria ou Outro) com justificativa, mas não decida nem crie tipo de
  work item para a demanda principal. A subskill de débito pode recomendar `User Story` ou `Bug` para
  cada débito, sempre como saída separada e sem criar o work item.

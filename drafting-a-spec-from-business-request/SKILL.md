---
name: drafting-a-spec-from-business-request
description: Use when a business request such as an email, ticket, or chat message describes a problem or demand informally, without a written spec, and the local application source code is available to ground it before backlog generation.
---

# Drafting A Spec From Business Request

## Objetivo

Transformar um pedido informal de negócio (e-mail, ticket, mensagem) em uma spec em Markdown, apoiada
em investigação somente leitura do código-fonte já presente onde esta skill está instalada. A spec
resultante é a entrada que `generating-azure-boards-backlog-from-spec` já aceita hoje; esta skill não
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
5. **Salve o documento em arquivo e pare. Não invoque nenhuma outra skill.** Informe ao usuário o
   caminho salvo e um resumo das lacunas e perguntas encontradas.

## Ausência de repositório relevante

Se nenhum repositório candidato tiver relação com o pedido, registre essa ausência e produza a spec
apenas com o conteúdo do pedido, equivalente ao modo Greenfield da quarta skill — sem travar a entrega
do documento.

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
- Não produza Épico, Feature, História, Description nem Acceptance Criteria; isso continua sendo
  responsabilidade de `generating-azure-boards-backlog-from-spec` e da 3C.
- Não encadeie automaticamente a geração do backlog; a spec fica pronta para uso manual do usuário.

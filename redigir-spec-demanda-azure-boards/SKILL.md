---
name: redigir-spec-demanda-azure-boards
description: Use quando houver o ID de uma Demanda de Negócio no Azure Boards e for necessário redigir uma Spec rastreável, com investigação local somente leitura, antes do backlog.
---

# Redigir Spec a partir de Demanda no Azure Boards

## Objetivo

Transforme uma Demanda de Negócio já registrada no Azure Boards em uma Spec Markdown rastreável. A
fonte é a síntese estruturada da Demanda, e não o texto original enviado pela área. A skill preserva
essa distinção, investiga o código somente em leitura e salva a Spec com documentos companheiros para
revisão manual posterior.

## Fluxo obrigatório

1. Receba o ID numérico da Demanda e, a partir da raiz desta skill, execute
   `uv run python scripts/consultar_demanda.py <id>`. Se o diretório atual não for essa raiz, resolva
   explicitamente a raiz da skill antes de executar a CLI; não interprete `scripts/` em relação ao
   repositório investigado. Se a consulta falhar, se o tipo não for `Demanda de Negócio` ou se o contrato
   de campos estiver inválido, interrompa o fluxo e informe o erro; não redija uma Spec parcial por
   plausibilidade. A CLI escreve o JSON em `stdout` e qualquer erro em `stderr`, com código de saída 1.
2. Destino e credencial seguem a precedência argumento, `--config` (TOML), `--env-file` e variáveis de
   ambiente:

   | Dado | Argumento | Variável de ambiente |
   |---|---|---|
   | Organização | `--organizacao` | `AZURE_DEVOPS_ORGANIZACAO` |
   | Projeto | `--projeto` | `AZURE_DEVOPS_PROJETO` |
   | Credencial | — (não existe argumento) | `AZURE_DEVOPS_TOKEN` |

   A credencial vem exclusivamente de `AZURE_DEVOPS_TOKEN` ou da entrada segura solicitada em terminal
   interativo. Nunca a passe por argumento, nunca a registre no comando executado e nunca a reproduza na
   Spec, em exemplo ou em log. Quando a CLI responder `Erro [configuração]`, ela nomeia o que faltou:
   corrija a variável indicada e execute de novo, sem tentar adivinhar organização ou projeto.
3. Registre a fonte como `Demanda de Negócio #ID`, sua URL, o tipo validado e uma tabela com conteúdo
   da Spec, campo remoto e valor registrado. Use `System.Title` e os campos
   `Custom.DemandaAreaSolicitante`, `Custom.DemandaPublicoAlvo`,
   `Custom.DemandaValorEsperado`, `Custom.DemandaDoraResolver` e
   `Custom.DemandaRegraseRestricoes`.
4. Converta cada valor `null`, vazio ou lista vazia em uma pergunta objetiva em **Lacunas e perguntas
   abertas**. Nunca atribua `EXPLICITO` ou `INFERIDO` ao pedido original: os campos são apenas valores
   registrados na Demanda de Negócio.
5. Antes de investigar, leia e aplique
   [references/investigacao-demanda-azure-boards.md](references/investigacao-demanda-azure-boards.md).
   Descubra repositórios irmãos, investigue somente leitura e classifique a demanda em `Defeito`,
   `Melhoria` ou `Outro` pela comparação entre o registrado e a evidência de comportamento atual.
6. Preencha e salve a Spec-base completa usando o **Template da Spec** antes de chamar qualquer skill
   especializada. Use Área solicitante e Público-alvo como insumos da seção **Atores e vocabulário
   identificados no código**; use Valor esperado e Regras e restrições como insumos de
   **Comportamento esperado**. Registre todos como conteúdo registrado na Demanda, sem promovê-los a
   requisito confirmado. Inclua também a fonte, o problema, a evidência de código, a classificação, os
   repositórios considerados e as lacunas.
7. Chame `especificar-debitos-tecnicos` somente quando houver evidência de débito técnico ligada ao
   escopo. Forneça a evidência `caminho:linha`, a origem na Demanda e o contexto da Spec; preserve a
   saída como documento separado, sem misturá-la ao requisito de negócio.
8. Chame `especificar-telas-ux-ui` sempre depois de concluir a Spec-base completa. Preserve a anotação
   da Spec e, quando aplicável, o briefing de telas como documento separado.
9. Somente se houver copy exibida ao usuário na Demanda, na Spec-base ou no briefing de telas, chame
   `revisar-textos-requisitos` depois da análise de telas. Salve o parecer com os trechos, diagnósticos,
   sugestões e decisões pendentes; a orquestradora não aceita uma sugestão nem reescreve requisitos
   automaticamente.
10. Salve a Spec principal e os documentos companheiros, registrando eventual indisponibilidade de uma
   skill especializada como lacuna. Em seguida, pare: não chamar entrevista, geração ou publicação de backlog.
   A geração ou publicação de backlog é uma etapa manual controlada pelo usuário.

## Limites de leitura e de decisão

- A consulta ao Azure Boards usa somente `GET`; não execute POST, não execute PATCH, não execute PUT e
  não execute DELETE.
- Não crie, atualize, mova, comente, relacione ou exclua work items, nem altere a Demanda de Negócio.
- Não execute a aplicação, testes, build, servidor ou migrações durante a investigação do código.
- Não trate a síntese da GEPRO como prova de palavras originais da área, decisão de produto ou requisito
  confirmado além do que estiver registrado na Demanda.
- Não gere Épico, Feature, História, Description, Acceptance Criteria nem qualquer backlog. A skill não
  encadeia geração ou publicação de backlog.
- Não substitua a saída de débitos, telas ou copy por texto inventado quando a skill especializada não
  estiver disponível.

## Template da Spec

```markdown
# Spec: <System.Title>

## Fonte da Demanda
- Azure Boards: Demanda de Negócio #<id> — <URL>
- Tipo validado: Demanda de Negócio

| Conteúdo da Spec | Campo remoto | Valor registrado |
|---|---|---|
| Título | System.Title | ... |
| Área solicitante | Custom.DemandaAreaSolicitante | ... |
| Público-alvo | Custom.DemandaPublicoAlvo | ... |
| Valor esperado | Custom.DemandaValorEsperado | ... |
| Dor a resolver | Custom.DemandaDoraResolver | ... |
| Regras e restrições | Custom.DemandaRegraseRestricoes | ... |

## Escopo
Tratado como item único; nenhuma decomposição foi aplicada.

## Repositórios considerados
| Repositório | Relevante? | Motivo |
|---|---|---|
| ... | Sim/Não | ... |

## Problema relatado
Registrado na Demanda: <síntese fiel de Custom.DemandaDoraResolver>.

## Comportamento atual (evidência no código)
| Afirmação ou observação | Evidência `caminho:linha` | Confiança |
|---|---|---|
| ... | ... | Alta/Média/Baixa |

## Comportamento esperado
- Registrado na Demanda: ...
- Evidenciado pelo código: ...
- Lacuna: ...

## Classificação
- **Tipo**: Defeito | Melhoria | Outro
- **Justificativa**: ...

## Atores e vocabulário identificados no código
- Registrado na Demanda: ...
- Evidenciado pelo código: ...
- Lacuna: ...

## Lacunas e perguntas abertas
- <pergunta objetiva para cada campo null, divergência ou limite de investigação>
```

## Como preencher o template

O bloco acima é o documento a emitir: copie a estrutura, não estas explicações.

- Em **Comportamento esperado**, `Registrado na Demanda` recebe Valor esperado
  (`Custom.DemandaValorEsperado`) e Regras e restrições (`Custom.DemandaRegraseRestricoes`). Esses
  insumos não são requisito confirmado: preserve sua origem e não complete a seção por plausibilidade.
- Em **Atores e vocabulário identificados no código**, `Registrado na Demanda` recebe Área solicitante
  (`Custom.DemandaAreaSolicitante`) e Público-alvo (`Custom.DemandaPublicoAlvo`). Nenhum dos dois
  comprova ator ou vocabulário no código; são insumos registrados na Demanda, não requisito confirmado.
- Não apresente ausência de evidência como comportamento confirmado. Quando o código e a Demanda
  divergirem, registre ambos e mantenha a decisão como lacuna.

## Valores já convertidos pelo leitor

Alguns campos da Demanda são declarados `html` no Azure Boards e chegam da API com marcação
(`<div>`, `<br>`, `<li>`, `&nbsp;`). **A CLI já converte esses campos em texto** antes de devolver o
JSON: você recebe texto legível, com listas em `- ` e parágrafos separados por quebra de linha.

Por isso:

- **Não converta HTML você mesmo, e não espere tags no JSON.** Se encontrar uma tag no valor recebido,
  é conteúdo literal que o autor digitou, não marcação — preserve como está.
- O leitor decide o que converter pelo tipo declarado no campo remoto, consultado a cada execução. Não
  presuma quais campos são `html`: isso é configuração do Azure Boards e pode mudar.
- Um campo cujo tipo remoto não for textual (identidade, picklist, número, data) interrompe o fluxo
  antes da Spec, com erro de contrato. Não contorne: o contrato mudou e precisa ser revisto.
- Um campo `html` que contenha só marcação vazia vira lacuna, como qualquer campo sem valor.

O que **continua sendo sua responsabilidade** é a tabela **Fonte da Demanda**, porque o texto convertido
ainda pode ter várias linhas ou o caractere `|`, que quebram uma tabela Markdown:

- Substitua quebras de linha por espaço e escape `|` como `\|` dentro de qualquer célula.
- Quando o valor for longo ou estruturado (lista, vários parágrafos), coloque na célula um resumo fiel de
  uma linha e reproduza o valor integral em uma subseção de **Fonte da Demanda**, fora da tabela.
- O resumo na célula nunca substitui o valor integral: ele existe para a tabela caber, e o texto completo
  precisa aparecer em algum lugar da Spec.

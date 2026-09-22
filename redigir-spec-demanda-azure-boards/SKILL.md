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

## Normalização dos valores registrados

Três campos são declarados `html` no tipo remoto e **sempre podem** voltar com marcação (`<div>`,
`<br>`, `<li>`, `&nbsp;`), mesmo que uma Demanda específica traga texto simples:

| Campo | Tipo declarado | Consequência |
|---|---|---|
| `Custom.DemandaValorEsperado` | `html` | alimenta **Comportamento esperado** |
| `Custom.DemandaDoraResolver` | `html` | alimenta **Problema relatado** |
| `Custom.DemandaRegraseRestricoes` | `html` | alimenta **Comportamento esperado** |

`System.Title`, `Custom.DemandaAreaSolicitante` e `Custom.DemandaPublicoAlvo` são `string` de linha
única e não precisam de conversão. Nunca conclua que um campo `html` é seguro porque uma Demanda veio
sem marcação: verifique o valor recebido, não o exemplo anterior.

HTML, quebras de linha e o caractere `|` destroem uma tabela Markdown. Antes de escrever a tabela
**Fonte da Demanda**:

- Converta o HTML em texto legível, preservando o sentido; não invente conteúdo que o HTML não continha.
- Substitua quebras de linha por espaço e escape `|` como `\|` dentro de qualquer célula.
- Quando o valor for longo ou estruturado (lista, vários parágrafos), coloque na célula um resumo fiel de
  uma linha e reproduza o valor integral em uma subseção de **Fonte da Demanda**, fora da tabela.
- Se um campo vier em formato que você não consegue converter com fidelidade, trate-o como lacuna e
  registre a limitação — não escreva uma paráfrase por plausibilidade.

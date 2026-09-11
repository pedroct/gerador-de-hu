# Validação Brownfield da spec contra o projeto

Leia esta referência somente quando houver código-fonte relevante ou quando sua presença for ambígua. O objetivo é descrever o estado atual com evidência verificável antes de decompor a mudança pedida pela spec.

## Inspeção segura

1. Registre a raiz analisada, os limites de escopo e qualquer incerteza sobre qual projeto implementa a spec.
2. Faça somente leitura segura: inventário com `rg` (incluindo `rg --files`) ou `find`, estado do repositório com `git status`, leitura de arquivos de código e testes e leitura de arquivos de configuração. Use a ferramenta menos abrangente que responda à pergunta.
3. Não execute scripts, testes, builds, servidores, migrações ou a aplicação sem autorização explícita. Não altere arquivos, dependências, banco de dados, serviços nem configuração como parte da validação.
4. Inspecione pontos de entrada, regras de domínio, persistência, interfaces e testes somente quando forem relevantes aos requisitos inventariados da spec. O nome de um arquivo, símbolo ou teste isolado não prova o comportamento completo.

Se o projeto não puder ser localizado ou lido com segurança, mantenha o modo Brownfield, registre o limite e classifique o que não pôde ser determinado como `Impossível validar`; não preencha lacunas com plausibilidade.

## Regra de comparação

Compare o código somente com requisitos da spec. Código existente não confirma valor nem decisão de negócio e não cria regra. Ele descreve apenas evidência do estado atual. Propostas, hipóteses e comportamentos encontrados sem origem na spec permanecem fora de itens e de Acceptance Criteria; quando forem relevantes para revisão, registre-os como observação fora do backlog acionável.

Para cada requisito rastreável da spec:

- procure evidência direta da capacidade e de cada restrição relevante;
- cite cada evidência útil como caminho relativo à raiz e linha inicial, por exemplo `src/diligencias/reopen_service.py:42`;
- distinga código de produção, configuração e testes na síntese; teste existente pode aumentar confiança, mas não substitui evidência do comportamento implementado;
- registre `Nenhuma evidência encontrada` quando a busca relevante estiver concluída, ou `Evidência indisponível: [motivo]` quando não foi possível validar. Nunca invente caminho ou linha.

Ausência de evidência não significa `Implementado`. Use exatamente um destes status por requisito:

| Status | Quando usar |
|---|---|
| `Implementado` | Evidência direta sustenta a capacidade e as restrições exigidas pela spec no escopo analisado. |
| `Parcialmente implementado` | Parte do comportamento existe, mas falta uma capacidade, regra, restrição ou caso exigido pela spec. |
| `Divergente` | A evidência mostra comportamento incompatível com o requisito da spec. |
| `Não encontrado` | A inspeção relevante foi concluída e não encontrou implementação do requisito. |
| `Impossível validar` | A raiz, arquivos ou evidência necessários não estavam acessíveis, o escopo permaneceu ambíguo ou a leitura segura não permite concluir. |

`Confiança` qualifica a conclusão (`Alta`, `Média` ou `Baixa`) e não substitui o status. Explique no impacto o que falta, diverge ou não pôde ser validado e como isso afeta o trabalho solicitado.

## Matriz obrigatória

Produza uma linha para cada requisito da spec. Divida requisitos compostos quando partes possam ter status diferentes.

| Requisito | Evidência `caminho:linha` | Status | Impacto | Confiança |
|---|---|---|---|---|
| [requisito e origem na spec] | [uma ou mais referências, nenhuma evidência ou motivo da indisponibilidade] | [status exato] | [efeito sobre a mudança/backlog] | [Alta, Média ou Baixa] |

A matriz é cobertura analítica, não uma fonte de novos requisitos e não um gate de Confirmation. Preserve o vínculo entre cada linha e sua origem na spec.

## Política de itens

- `Parcialmente implementado`, `Divergente` e `Não encontrado`: crie item somente para a lacuna, correção ou mudança rastreável pedida pela spec.
- `Impossível validar`: crie item de produto apenas quando a spec já exigir mudança acionável; caso contrário, registre a incerteza e a pergunta necessária sem fabricar escopo.
- `Implementado`: mantenha na matriz e na síntese de cobertura; requisitos já implementados não geram itens duplicados por padrão.
- Se o usuário pedir para documentar comportamento existente, um item pode representar o requisito `Implementado`; marque que ele documenta estado atual e não é trabalho novo.

Não transforme componentes, decisões técnicas ou comportamentos incidentais descobertos no código em Épico, Feature, História, Who, What, Why, valor ou regra de aceitação.

## Handoff ao refinamento e ao documento

Forneça a evidência Brownfield à 3C como contexto rotulado de estado atual. A 3W pode consultá-la sem derivar ator, necessidade ou valor. A Gherkin continua usando apenas o comportamento desejado confirmado na Conversation; implementação atual não confirma a regra.

No Markdown final:

- sintetize a matriz em `## Validation Summary`;
- associe evidência relevante a cada item em `##### Implementation Evidence` ou em síntese explicitamente rotulada na Description/Conversation;
- mantenha toda evidência de implementação fora de `Acceptance Criteria`.

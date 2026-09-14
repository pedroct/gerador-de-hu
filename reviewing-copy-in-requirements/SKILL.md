---
name: reviewing-copy-in-requirements
description: Use when requisitos, histórias de usuário, critérios de aceitação, especificações ou fluxos contêm textos voltados ao usuário e precisam de revisão de clareza, benefício, tom, ação ou consistência. Não use para escrever campanhas ou revisar apenas gramática.
---

# Revisar copy em requisitos

## Objetivo

Revisar a copy que aparece em requisitos e especificações para que ela seja compreensível,
útil e orientada à ação para a pessoa que usará o produto. A skill aponta problemas e orienta
decisões; não deve reescrever silenciosamente o requisito nem inventar contexto de negócio.

## Escopo

Inclua textos de interface e comunicação do produto: títulos, labels, botões, CTAs, mensagens de
sucesso, erro e vazio, instruções, notificações, confirmações, tooltips, descrições de benefícios e
textos de critérios de aceitação que serão exibidos ao usuário.

Não transforme a análise em campanha, landing page, manifesto de marca ou revisão gramatical
desconectada do comportamento do produto. Se o problema for estratégia de página ou oferta, registre
essa fronteira como uma decisão pendente em vez de preencher por suposição.

## Fluxo de revisão

1. Leia o requisito completo e separe texto exibido ao usuário de texto técnico interno.
2. Para cada trecho de copy, identifique, quando disponível: público, momento do fluxo, intenção,
   ação esperada, resultado prometido e restrições de tom, idioma ou canal.
3. Aponte problemas observáveis usando as heurísticas de
   [references/copy-review-framework.md](references/copy-review-framework.md).
4. Classifique cada achado como `Crítico`, `Importante` ou `Aperfeiçoamento`:
   - `Crítico`: pode levar a erro, perda de confiança, interpretação incompatível ou ação sem
     consentimento claro.
   - `Importante`: reduz entendimento, percepção de valor ou conclusão do fluxo.
   - `Aperfeiçoamento`: melhora concisão, naturalidade, tom ou consistência sem bloquear o uso.
5. Sugira uma alternativa somente quando houver contexto suficiente. Separe claramente fatos,
   inferências e decisões que o produto ainda precisa tomar.

## Princípios

- Clareza antes de criatividade; prefira palavras que o usuário reconhece.
- Benefício e consequência antes de descrever a implementação.
- Especificidade antes de adjetivos vagos como “inovador”, “completo” ou “otimizado”.
- Voz ativa, frases curtas e uma ideia principal por mensagem.
- CTA com verbo e resultado esperado; evite rótulos genéricos quando o resultado puder ser dito.
- Linguagem do usuário antes da linguagem interna da empresa ou da equipe.
- Tom consistente com o contexto, sem exagero, falsa urgência, métricas ou provas inventadas.
- Não trate uma preferência de estilo como defeito crítico.

## Formato da saída

Comece com um resumo: `Copy pronta`, `Copy pronta com ressalvas` ou `Copy não pronta`, explicando
os principais motivos. Depois use uma tabela ou blocos com:

```text
Trecho: <texto exato e localização no requisito>
Classificação: <Crítico | Importante | Aperfeiçoamento>
Diagnóstico: <o que está obscuro, fraco, inconsistente ou arriscado>
Impacto: <o que o usuário ou o produto pode sofrer>
Recomendação: <mudança orientada à decisão>
Sugestão de copy: <alternativa; ou “não sugerida — falta contexto”>
Dúvida/decisão pendente: <pergunta objetiva, se houver>
```

Quando houver várias opções, ofereça no máximo três e explique a diferença de intenção entre elas.
Preserve no diagnóstico o vínculo com o requisito e não altere regras funcionais apenas para tornar
a frase mais persuasiva.

## Limites e colaboração

- Não invente público, benefício, prazo, garantia, métrica, depoimento ou comportamento do produto.
- Não considere código, design ou implementação como prova de que uma promessa de valor é verdadeira.
- Se faltar contexto essencial, faça perguntas objetivas antes de recomendar copy definitiva.
- Dúvidas de negócio devem permanecer explícitas em `Dúvida/decisão pendente`.
- Para uma página de marketing completa, esta skill não é suficiente: o pedido está fora deste escopo.

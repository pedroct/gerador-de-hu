# Medição do gate 3W assistido

Registro de como o gate desta skill foi implementado com o modelo **Jev (TypeSafe)**, chamado pela
**Decisions API do OpenRouter**, e de quanto ele acertou.

O gate em prosa, que é o contrato da skill, está em [`../SKILL.md`](../SKILL.md). O script é um
apoio opcional; este documento é referência, não instrução.

## Por que este gate cabe num modelo de decisão

A skill 3W já especifica, por escrito, três julgamentos estreitos e independentes sobre o mesmo
texto — `Who`, `What` e `Why`, cada um classificado como `Confirmado`, `Fraco` ou `Pendente` —
e tabela os sinais de fraqueza de cada W. Isso é exatamente o formato de um `choice` do Jev, com
os critérios prontos. A skill ainda traz um exemplo com a resposta esperada, o que dá **gabarito
vindo do próprio repositório** em vez de gabarito inventado para o teste.

## Contrato usado

| | |
|---|---|
| Endpoint | `POST https://openrouter.ai/api/alpha/decisions` |
| Model ID | `typesafe/jev-1.13` |
| Auth | `Authorization: Bearer $JEV_OPENROUTER_API` |
| Corpo | `{"model": ..., "state": ..., "questions": {...}}` |

As três perguntas são independentes sobre o mesmo `state` e por isso vão numa **única
requisição**, avaliadas em paralelo pelo modelo.

## Divisão entre modelo e código

O modelo devolve o julgamento por W, com `probabilities` e `confidence`. A regra
"`Completo` só quando os três Ws passam" fica em `aplicar_gate()`, determinística. Assim a
política pode mudar sem reexecutar inferência, e a confiança entra como insumo da decisão,
nunca como substituto da regra.

## Como rodar

```bash
uv run python refinar-historias-3w/scripts/avaliar_gate_3w.py
```

Requer `JEV_OPENROUTER_API` no ambiente ou no `.env` da raiz.

## Resultado medido em 2026-09-24

**15/15 julgamentos corretos** nos 5 casos (reproduzido em duas execuções).

| Caso | Sinal isolado | Resultado |
|---|---|---|
| `exemplo-da-skill` | os três Ws fracos (gabarito na própria skill) | 3/3 |
| `historia-completa` | história que passa no gate | 3/3 |
| `what-orientado-a-solucao` | What nomeia tela/componente | 3/3 |
| `why-circular` | Why repete o What | 3/3 |
| `why-ausente` | W ausente do texto | 3/3 |

Custo: **US$ 0,000053 por história** (três julgamentos), ~1.260 tokens de entrada por requisição.
Ao preço de US$ 0,042/M de entrada, refinar as 11 solicitações da fila custa menos de US$ 0,001.

## Observação sobre a confiança

A confiança acompanhou a dificuldade real do caso, o que é um bom sinal de calibração: 0,97–1,00
nos sinais de fraqueza evidentes, e 0,41–0,58 no `What` dos casos em que o verbo de domínio é
defensável como capacidade ou como tarefa. Ou seja, **o acerto veio acompanhado de dúvida onde
havia dúvida legítima**.

Consequência prática: um limiar de confiança separaria bem o que pode seguir automático do que
merece revisão humana. Antes de fixar esse limiar, medir sobre histórias reais do backlog — cinco
casos escolhidos por mim não bastam, e os casos foram construídos para isolar um sinal por vez,
o que é mais fácil que texto real ambíguo.

## Limites da medição

- 5 casos, todos sintéticos ou tirados da própria skill; não é validação de domínio.
- Só o gate 3W. As rubricas 3C e Gherkin não foram testadas.
- `alpha` no caminho do endpoint: o contrato pode mudar sem aviso.

# Baseline brownfield sem instruções novas

## Escopo e evidência disponível

A spec informa que uma diligência pode ser reaberta em até 24 horas. Para o baseline, foram fornecidas estas evidências de código:

- `src/diligencias/reopen_service.py:42`: implementa a reabertura, mas sem validação do prazo.
- `src/diligencias/status.py:18`: define `EM_ANALISE`.
- `tests/diligencias/test_reopen.py:10`: cobre somente o caso dentro do prazo.

O estado `EM_ANALISE` confirma a existência de um estado de domínio, mas não demonstra a aplicação da janela de 24 horas. O teste dentro da janela também não demonstra o comportamento no limite ou fora dele.

## O que as skills atuais exigem

| Aspecto do baseline | Exigido pelas quatro skills? | Conclusão |
|---|---|---|
| Inspeção do código/projeto antes do backlog | Não | A skill de backlog exige ler a spec inteira e inventariar requisitos, origens, conflitos e lacunas; não exige inspeção do repositório ou comparação com a implementação. |
| Evidência com caminho e linha | Não como formato obrigatório | 3W/3C/Gherkin exigem preservar evidências e a skill de backlog exige rastreabilidade/origem, mas nenhuma exige referências `caminho:linha` para código. |
| Classificação `implementado`, `parcial`, `divergente`, `não encontrado` | Não | As classificações existentes são as dos gates 3W (`Confirmado`, `Fraco`, `Pendente`), Gherkin/Confirmation (`Ausente`, `Parcial`, `Completa`) e 3C/prontidão. Não há classificação de cobertura da implementação com esses quatro rótulos. |
| Bloqueio antes de gerar o backlog por causa do baseline | Não explicitamente | Não existe gate brownfield que interrompa a geração por divergência entre spec e código. Há, porém, o gate de prontidão da 3C: uma história só fica `Pronta` com Card estruturado, Conversation suficiente e Confirmation completa, sem decisão bloqueadora. |

## Leitura do cenário

Se a classificação de implementação for aplicada como uma análise adicional — e não como exigência das skills — o resultado é:

- **Capacidade de reabrir:** parcial; o caminho de reabertura existe.
- **Regra do prazo:** divergente para reaberturas após 24 horas, pois o serviço não valida a janela.
- **Evidência de testes:** insuficiente para afirmar cobertura da regra completa; há apenas o caso dentro do prazo.

Essa conclusão deve permanecer como evidência/risco do baseline. Não se deve convertê-la automaticamente em regra adicional ou detalhe técnico nos Acceptance Criteria; regras e exemplos precisam ser confirmados na Conversation e expressos em Gherkin conforme a 3C.

## Veredito

Com as skills atuais, **não há exigência de inspeção brownfield, de evidência por caminho/linha, nem da classificação de implementação solicitada**. Também **não há bloqueio brownfield obrigatório antes do backlog**.

O backlog ainda precisa seguir o fluxo definido: ler a spec inteira, manter a rastreabilidade, usar 3C para cada história e deixar a história `Não pronta`/`Acceptance Criteria` vazio quando os gates de Conversation ou Confirmation não forem satisfeitos. A divergência observada no código, por si só, não cria um bloqueio adicional segundo essas skills.

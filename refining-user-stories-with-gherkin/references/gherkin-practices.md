# Práticas de Gherkin para refinamento

Base normativa: [Gherkin Reference](https://cucumber.io/docs/gherkin/reference) e o [dialeto português oficial](https://github.com/cucumber/gherkin/blob/main/gherkin-languages.json).

## Forma correta

| Elemento | Uso no refinamento |
|---|---|
| `Funcionalidade` | Capacidade de alto nível; somente uma por arquivo `.feature`. |
| `Regra` | Uma regra de negócio, agrupando um ou mais exemplos que a ilustram. |
| `Cenário` / `Exemplo` | Um exemplo concreto e verificável; almeje 3–5 passos. |
| `Dado` | Contexto inicial conhecido, não uma interação do usuário. |
| `Quando` | Evento ou ação que dispara o comportamento. |
| `Então` | Resultado observável, não estado interno ou detalhe de implementação. |
| `E` / `Mas` | Continuação sem mudar a fase semântica do passo anterior. |
| `Contexto` | `Dado`s realmente comuns a todos os exemplos seguintes. Mantenha curto; acima de quatro linhas, reavalie ou divida. |
| `Esquema do Cenário` + `Exemplos` | Mesma lógica executada com combinações diferentes de dados. Cada linha, exceto o cabeçalho, gera um exemplo. |
| Tabela de dados / Doc String | Dados extensos que pertencem a um único passo, não decoração tabular. |

O texto dos passos deve formar linguagem de domínio clara. Como as palavras-chave não distinguem definições de passos, evite reutilizar o mesmo texto após palavras-chave diferentes.

## Sintaxe executável em português

Quando produzir um documento Gherkin em português, comece a primeira linha com `# language: pt`; sem o cabeçalho, Cucumber assume inglês. Use os termos do dialeto oficial, por exemplo:

```gherkin
# language: pt
Funcionalidade: Consultar um agendamento

  Regra: Um agendamento confirmado fica disponível para consulta

    Cenário: Consultar agendamento confirmado
      Dado que Ana possui um agendamento confirmado
      Quando ela consulta seus agendamentos
      Então o agendamento deve ser apresentado com sua data e seu valor
```

Use dois espaços para indentação. `Funcionalidade:`, `Regra:`, `Cenário:`, `Contexto:`, `Esquema do Cenário:` e `Exemplos:` recebem dois-pontos; os passos `Dado`, `Quando`, `Então`, `E` e `Mas` não recebem.

Entregue cada bloco como documento completo: cabeçalho de idioma quando necessário, `Funcionalidade` e exemplos executáveis. Uma `Regra` contém um ou mais cenários. Regra pendente, cenário vazio e comentário descrevendo trabalho futuro pertencem à lista de dúvidas, não ao bloco Gherkin.

Se o documento estiver em outro idioma, use o idioma dos usuários e especialistas do domínio. Para um arquivo executável não inglês, confirme o código e as palavras-chave na [lista oficial de idiomas](https://cucumber.io/docs/gherkin/languages).

## Escolhas estruturais

- Use `Regra` quando ela tornar explícita a relação entre vários exemplos e uma decisão de negócio; não crie agrupamentos vazios.
- Use `Contexto` apenas para precondições repetidas e relevantes ao leitor. Há no máximo um por `Funcionalidade` ou `Regra`.
- Use `Esquema do Cenário` quando somente os dados variarem. Se evento, regra ou resultado mudar, escreva cenários separados.
- Use `*` apenas quando uma lista for mais natural que `E`/`Mas`.
- Comentários começam com `#` em uma nova linha. Gherkin não oferece comentário de bloco.

## Exemplo de refinamento sem fabricar regras

Entrada: “O cliente pode agendar uma transferência. Pode haver saldo insuficiente, limite excedido, destinatário inválido e repetição.”

Fatos confirmados: existe agendamento; as quatro condições são relevantes. Ainda não estão definidos o momento das validações, o efeito de cada falha, a semântica da repetição nem os estados apresentados ao cliente. Não complete essas lacunas por plausibilidade.

Exemplo que pode ser escrito após confirmar o comportamento:

```gherkin
# language: pt
Funcionalidade: Agendar transferência

  Regra: Um pedido aceito fica disponível para consulta

    Cenário: Agendar uma transferência válida
      Dado que Ana informou destinatário, valor e data futura aceitos pelo banco
      Quando ela solicita o agendamento da transferência
      Então o agendamento deve ser confirmado
      E Ana deve receber uma identificação para consultá-lo
```

Perguntas que permanecem: quando saldo, limite e destinatário são validados; qual resultado observável ocorre em cada falha; o que “repetição” significa; como pedidos duplicados devem ser percebidos. Até essas decisões serem tomadas, não crie cenários afirmando respostas.

## Checklist de revisão

- A história expressa valor e tem escopo coeso?
- Toda regra declarada veio de uma fonte ou está marcada como hipótese?
- Cada regra possui ao menos um exemplo representativo?
- Os exemplos incluem somente variações justificadas pelo contexto?
- Cada `Dado` é estado, cada `Quando` é evento e cada `Então` é observável?
- Os cenários evitam interface e implementação?
- Termos vagos foram quantificados ou registrados como dúvida?
- A sintaxe, o idioma, os dois-pontos e a indentação estão corretos?
- Cada bloco está completo, sem regras ou cenários usados como placeholders?
- As decisões pendentes e o estado local da Confirmation (`Ausente`, `Parcial` ou `Completa`) estão explícitos?

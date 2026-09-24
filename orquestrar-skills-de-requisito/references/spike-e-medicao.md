# Medição do roteador

Registro de como o roteador foi construído e medido, mantido junto da skill porque explica **por
que as perguntas estão escritas do jeito que estão** — e o que acontece quando não estão.

A skill em si está em [`../SKILL.md`](../SKILL.md). Este documento é referência, não instrução.

## O desenho, e por que não é um classificador plano

As skills deste repositório não são alternativas mutuamente exclusivas — formam um pipeline com
pontos de entrada, folhas e duas publicadoras. Um `choice` sobre os 12 nomes seria errado.

A divisão adotada:

- **O Jev julga o que o material É** e em que estado está — julgamento semântico sobre texto.
- **O código deriva qual skill chamar**, pela tabela em `scripts/roteamento.py`, transcrita do fluxo do
  README do repositório.

Esse fluxo é regra conhecida e acíclica. Mantê-lo em código significa que mudar o pipeline é
editar uma tabela, sem reexecutar inferência nem recalibrar nada.

## As perguntas

Sete perguntas independentes sobre o mesmo `state`, numa **única requisição** (padrão
*speculative fan-out*): várias valem só para alguns tipos de entrada, e o código consome apenas as
aplicáveis. A incerteza nas perguntas de ramos não usados é irrelevante e é ignorada.

| Pergunta | Tipo | Serve para |
|---|---|---|
| `tipo_de_entrada` | choice (8) | rota principal |
| `tem_lacunas_abertas` | noul | spec → entrevista ou backlog |
| `ja_existe_demanda_no_board` | noul | qual das duas publicadoras |
| `descreve_interacao_de_tela` | noul | sugerir UX-UI |
| `tem_copy_de_interface` | noul | sugerir revisão de copy |
| `menciona_debito_tecnico` | noul | sugerir spec de débitos |
| `lacuna_de_refinamento` | choice (4) | 3W, 3C ou Gherkin |

## Como usar

```bash
uv run python orquestrar-skills-de-requisito/scripts/rotear.py material.md
cat material.md | uv run python orquestrar-skills-de-requisito/scripts/rotear.py - --json
uv run python orquestrar-skills-de-requisito/scripts/avaliar_roteador.py
```

## Resultado medido em 2026-09-24

| Conjunto | Rota principal | Companheiras |
|---|---|---|
| 11 casos de calibração | 11/11 | 11/11 |
| 8 casos **hold-out** (escritos após o ajuste) | **8/8** | 7/8 |

Custo: **US$ 0,000093 por roteamento** (sete julgamentos numa requisição).

O número que importa é o hold-out, não o 11/11: as perguntas foram corrigidas depois de ver as
falhas nos 11 primeiros, o que é ajuste sobre o conjunto de teste.

### O que a primeira rodada revelou

A primeira execução deu 10/11 na rota e **7/11 nas companheiras**. Os dois erros tinham causas
diferentes, e nenhuma era limiar mal escolhido:

**`especificar-telas-ux-ui` disparava em quase tudo.** Os valores brutos ficaram entre 0,43 e 0,91,
sem discriminar. A pergunta original — "isto provavelmente exige tela nova?" — é quase tautológica
num sistema web. Pior: o README diz que essa skill decide *por inspeção de código, nunca pelo texto
de negócio*, então pedir ao modelo essa conclusão contradiz o contrato da própria skill. A correção
foi mudar o que se pergunta: o modelo agora julga apenas se **o texto descreve** interação de tela,
e a skill continua sendo quem confirma, por código.

**Regras confirmadas caíam em `pedido_informal_negocio`.** Não era erro do modelo: `regras de
negócio já acordadas` não existia na lista de opções, e o modelo não pode escolher um valor
omitido. Virou o oitavo tipo de entrada.

Em contraste, `tem_copy_de_interface` funcionou desde a primeira versão — 0,90 no verdadeiro
positivo contra 0,03–0,29 no resto — o que mostra que o problema das outras era redação da
pergunta, não o modelo.

## Limites

- **19 casos, todos escritos por mim.** Não substitui medição sobre material real do backlog.
- **O limiar das companheiras (0,75) está sensível.** Dois pedidos quase idênticos sobre filtrar
  uma listagem caíram em lados opostos dele. As companheiras são sugestões opcionais, então o custo
  do erro é baixo, mas o limiar não deve ser tratado como calibrado.
- **Um gabarito meu é discutível:** esperei `especificar-telas-ux-ui` para "trocar o texto do aviso
  do formulário", e o modelo não sugeriu. Trocar uma mensagem é copy, não tela nova — provavelmente
  o gabarito é que está errado. Ficou registrado em vez de corrigido para o teste passar.
- **`LIMIAR_CONFIANCA` = 0,60 é provisório.** Um caso do hold-out passou com 0,61, raspando.
- `alpha` no caminho do endpoint: o contrato pode mudar sem aviso.

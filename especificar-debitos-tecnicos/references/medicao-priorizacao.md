# Medição da priorização assistida

Como os passos 3 e 4 desta skill foram implementados com o modelo **Jev (TypeSafe)**, quais
práticas estabelecidas foram aplicadas, e o que a medição revelou — inclusive sobre a fórmula da
própria skill.

## Os três primitivos numa requisição

| Pergunta | Primitivo | Por quê |
|---|---|---|
| Impacto | `score`, 5 níveis | posição numa dimensão ordenada |
| Probabilidade | `score`, 5 níveis | chance de ocorrer em doze meses |
| Severidade | `score`, 5 níveis | estrago caso ocorra |
| Esforço | `score`, 5 níveis | alcance da mudança |
| Categoria | `choice`, 6 opções | rótulos discretos, sem ordem entre si |
| Há defeito observável | `noul` | condição que vale ou não vale |

Todas independentes sobre o mesmo `state`, numa requisição só. A aritmética fica em código: o
modelo posiciona, ele não multiplica.

## Procedência da rubrica

**Transcritos do `SKILL.md`:** as seis categorias, a fórmula `(Impacto + Risco) × (6 − Esforço)`,
o critério de `Bug` contra `User Story` e a escala de 1 a 5.

**Redigidas aqui:** as descrições dos níveis. A skill pede notas de 1 a 5 sem definir o que cada
nota significa. Esta é a parte que mais merece revisão de quem conhece o contexto.

## Práticas aplicadas

**BARS — Behaviorally Anchored Rating Scales.** Prática estabelecida para escalas ordinais: cada
nível recebe uma **âncora** descrevendo situação observável, em vez de um grau ("moderado", "alto")
ou um número. Coincide com o que a documentação do primitivo `score` exige, e com o motivo: o
modelo avalia cada nível isoladamente, sem ver os vizinhos. Um teste em `tests/test_priorizacao.py`
impede que as âncoras voltem a ser graus.

**Retranslação.** O passo de validação do BARS: examinadores que não escreveram as âncoras
reclassificam exemplos concretos, e só se mantêm as âncoras com concordância forte.
`scripts/retranslacao.py` automatiza isso — cada nível recebe um exemplar **com redação diferente
da âncora**, e se verifica se ele volta para o próprio nível. Foi o que localizou os dois defeitos
descritos abaixo.

**Matriz de risco (ISO 31000, CVSS).** Risco é probabilidade × severidade, não uma escala só.
Aplicado depois que a retranslação mostrou por que a escala única não funcionava.

## O que a retranslação encontrou

Primeira rodada, escala de risco única: **12/15 âncoras** atraíram o próprio exemplar.

- **Esforço: 1,00 / 2,02 / 3,01 / 4,02 / 5,00**, confiança de 0,92 a 1,00. É a dimensão mais fácil
  de ancorar, porque se descreve por alcance da mudança — quantas partes do sistema ela toca —, o
  que é contável e não opinativo.
- **Impacto:** tudo dentro de ±0,38.
- **Risco: quebrado na ponta baixa.** Níveis 1, 2 e 3 puxavam para cima (+0,59 a +0,88), com
  confiança entre 0,38 e 0,60.

Confiança baixa concentrada num trecho da escala é o sintoma que a documentação do `score` nomeia:
**pergunta multidimensional**. As âncoras misturavam *probabilidade* ("já houve incidente") com
*severidade* ("exposição de segurança, perda de dado"), e cada uma trazia um "ou" juntando duas
bases diferentes de julgamento.

Depois de separar em probabilidade e severidade, e de dar à probabilidade uma **janela explícita de
doze meses** — sem horizonte, "nunca ocorreu mas é iminente" não cabia em nível nenhum:

| Rodada | Âncoras aderentes |
|---|---|
| escala de risco única | 12/15 (80%) |
| probabilidade × severidade | 16/20 (80%) |
| probabilidade com janela de doze meses | 18/20 (90%) |
| probabilidade reduzida a quatro níveis | 17/19 (89%) |
| cinco níveis, exemplares com contexto operacional | **19/20 (95%)** |

**Severidade e esforço saíram limpos.** Probabilidade foi a dimensão difícil, e o caminho até
entendê-la vale registro porque a primeira explicação estava errada.

A hipótese inicial foi que os níveis 1 e 2 descreviam a mesma situação e deveriam ser fundidos.
Reduzir a escala para quatro níveis **não melhorou nada** — 89% contra 90% —, o que refutou a
hipótese: o problema não era contagem de níveis. A escala voltou a cinco, porque manter uma
mudança sem ganho medido é pior que não mudá-la.

A explicação que se sustentou é a outra causa que a documentação do `score` lista para confiança
baixa: **estado insuficiente**. Estimar "isto vai acontecer?" exige evidência operacional —
frequência de mudança naquela área, tráfego, histórico de chamado — que a descrição de um débito
normalmente não carrega. Um teste direto confirmou, com o mesmo débito e a mesma âncora:

| | distribuição nos níveis | confiança |
|---|---|---|
| sem contexto operacional | 0,40 / 0,48 / 0,11 / 0,01 | 0,45 |
| com contexto operacional | **0,60** / 0,37 / 0,03 / 0,00 | **0,56** |

O efeito é real e na direção certa, mas modesto: a probabilidade continua sendo a nota que mais
merece ser marcada como estimativa quando a evidência não existe — o que o passo 3 da skill já
prevê.

## Medição fim a fim

Seis débitos.

| Métrica | Escala de risco única | Matriz probabilidade × severidade |
|---|---|---|
| Notas exatas | 9/18 (50%) | 10/24 (42%) |
| Notas dentro de ±1 | 18/18 (100%) | 20/24 (83%) |
| Categoria (`choice`) | 6/6 | 6/6 |
| Tipo `Bug`/`User Story` (`noul`) | 6/6 | 6/6 |

**Os dois números não são comparáveis**, e vale dizer por quê: o gabarito mudou junto com a
implementação. As expectativas de probabilidade e severidade foram atribuídas rapidamente, com
menos cuidado que as originais, e o denominador passou de 18 para 24. Medir o modelo e mudar o alvo
na mesma rodada não mede nada. O sinal confiável aqui é a retranslação, que é autoconsistente e
melhorou de 80% para 90%.

Na primeira medição, todas as nove divergências foram **+1**, nenhuma **−1**. Desvio sistemático
numa direção não é ruído, e ao reler os casos a explicação mais provável é que o gabarito estivesse
errado: o nível 2 de Impacto diz "custa tempo ocasional a quem mexe naquela área", que é exatamente
o que um comentário desatualizado faz, e eu esperava nível 1. Escrevi as âncoras e depois escrevi
expectativas que não batiam com elas — que é precisamente o erro que a retranslação existe para
pegar.

## O achado que não é sobre o modelo

A fórmula `(Impacto + Risco) × (6 − Esforço)` deixa o esforço dominar. O fator `(6 − Esforço)` varia
de 1 a 5, multiplicando ou dividindo o resultado por cinco, enquanto `(Impacto + Risco)` varia só de
2 a 10.

| # | Débito | Escala única | Matriz | I | R | E |
|---|---|---:|---:|---:|---:|---:|
| | arredondamento contra o contrato | 27 | 27 | 5 | 4 | 3 |
| | query duplicada sem teste | 18 | 18 | 3 | 3 | 3 |
| | comentário desatualizado | **20** | **15** | 2 | 1 | 1 |
| | integração sem observabilidade | 24 | 14 | 4 | 3 | 4 |
| | dependência cíclica | 14 | 12 | 4 | 2 | 4 |
| | framework sem suporte de segurança | **10** | **9** | 5 | 4 | 5 |

A matriz melhorou o insumo — o comentário desatualizado caiu de Risco 2 para Risco 1, porque
probabilidade × severidade de um comentário que mente é de fato quase zero. Mas o framework fora de
suporte de segurança, com Impacto 5, continua em **último**. Isso confirma que a patologia é
estrutural da fórmula, não dos números que entram nela.

`sinalizar_inversoes()` aponta os pares invertidos. Ela **não corrige a fórmula**: a fórmula é o
contrato publicado desta skill, e alterá-la é decisão de produto.

### Por que trocar a fórmula não resolve

A primeira intuição foi trocar por **WSJF** (SAFe), que divide pelo tamanho do trabalho em vez de
multiplicar por `(6 − Esforço)`. Calculado sobre as mesmas notas, o resultado é pior:

| Débito | Fórmula atual | Posição | WSJF | Posição |
|---|---:|---:|---:|---:|
| arredondamento contra o contrato | 27 | 1ª | 3,00 | 2ª |
| comentário desatualizado | 15 | 3ª | 3,00 | **1ª** |
| framework sem suporte de segurança | 9 | 6ª | 1,80 | 4ª |

O WSJF coloca o comentário desatualizado em **primeiro lugar**. Não é defeito do WSJF: tanto ele
quanto a fórmula atual são métricas de **eficiência**, e favorecer ganho barato é exatamente o que
uma métrica de eficiência serve para fazer. O problema não é a aritmética — é aplicar ordenação por
eficiência a itens que não são todos opcionais. Um framework fora de suporte de segurança não
compete por eficiência; ele é restrição, não candidato.

A prática estabelecida para isso não é trocar a fórmula, é **classificar antes de ordenar**:
classes de serviço no Kanban, e o uso operacional do CVSS, em que severidade crítica define prazo
de remediação independentemente do esforço. Itens acima de um limiar de severidade saem da fila de
eficiência; o resto continua ordenado pela fórmula da skill, que para eles funciona bem.

### Por que o SQALE não se aplica aqui

Tentador, porque o repositório já tem SonarQube configurado e o SQALE está por baixo dele. Mas o
SonarQube estima tempo de remediação para as **regras que ele próprio detecta estaticamente**, e
os débitos que esta skill trata nascem de conversa e refinamento: "o framework saiu de suporte",
"a equipe evita mexer nessa área", "a atualização quebra a API de sessão". Nenhum deles é um
achado de análise estática. O SQALE segue útil para a saúde do código no que o Sonar mede — não
como substituto da nota de esforço desta skill.

### A correção adotada: classificar antes de ordenar

A fórmula continua intacta. O que mudou é que ela deixou de ser a única fila.
`separar_em_faixas()` distribui os itens em três:

- **Restrição** — severidade ≥ 4 **e** probabilidade ≥ 2. Não compete por eficiência: o esforço
  não a adia. Ordena por gravidade (risco, severidade, impacto).
- **A confirmar** — a confiança na severidade ficou abaixo de 0,60. Não é um meio-termo de
  gravidade: é a recusa de decidir com evidência insuficiente.
- **Candidato** — segue na fórmula da skill, que para estes funciona. `sinalizar_inversoes()`
  passou a operar só aqui.

É faixa e não linha porque severidade alta com probabilidade no piso descreve algo sem caminho
conhecido para acontecer; tratar isso como obrigatório esvaziaria a distinção.

### Por que a confiança entrou no portão

A primeira versão do portão classificava só por severidade e probabilidade, e capturou **4 de 6**
itens como restrição — o que não é portão, é maioria. Ao investigar, a causa não era o limiar: a
confiança da severidade nos débitos reais estava em **0,14 a 0,51**, enquanto na retranslação das
âncoras ela ficava entre 0,63 e 1,00.

A diferença entre os dois conjuntos explica tudo. Os exemplares da retranslação começavam por
"Quando acontece, …" — **diziam a consequência**. As descrições de débito real relatam o defeito e
deixam a consequência implícita, então a severidade tem de ser inferida. A âncora estava boa; o
texto é que não trazia a evidência.

Classificar como obrigatório a partir de um julgamento de confiança 0,14 daria ao número uma
autoridade que ele não tem. Por isso o portão passou a respeitar a confiança.

### A prescrição, verificada

Se a causa é a consequência ausente, dizê-la deveria resolver. Testado com o mesmo débito, mudando
só o texto:

| Débito | sem consequência | com consequência |
|---|---|---|
| framework sem suporte de segurança | sev 4, confiança 0,50 → *a confirmar* | **sev 5, confiança 1,00 → restrição** |
| arredondamento contra o contrato | sev 4, confiança 0,15 → *a confirmar* | sev 4, confiança 0,56 → *a confirmar* |

No primeiro caso é decisivo, e o item que motivou toda esta investigação — o framework fora de
suporte, que a fórmula enterrava em último — passa a sair classificado como restrição.

No segundo, a confiança subiu 3,7 vezes mas não cruzou o limiar, e o motivo é uma sobreposição
real entre âncoras: um erro de cálculo que viola contrato é ao mesmo tempo "quebra de obrigação
contratual" (nível 5) e "dados incorretos que exigem correção coordenada" (nível 4). As duas
descrições precisam ser desambiguadas — é a próxima âncora a revisar.

**Orientação prática que sai daí:** a descrição de um débito deve dizer o que acontece quando ele
se manifesta, não só o que está errado. O passo 1 da skill já pede a evidência de origem; isto é o
complemento natural dela.

## Limites

- Seis débitos e vinte exemplares, todos escritos por quem implementou. Não é validação de domínio.
- O gabarito das notas é discutível, como as seções acima admitem. A métrica confiável é a
  retranslação, não o acerto exato.
- A retranslação usa um único examinador (o próprio modelo). O BARS pressupõe vários examinadores
  independentes; concordância de um examinador consigo mesmo é o piso, não o teto.
- `alpha` no caminho do endpoint do OpenRouter: o contrato pode mudar sem aviso.

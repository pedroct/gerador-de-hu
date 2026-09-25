# Relatório da onda única de correções — `feat/pastas-por-demanda-e-audiencia`

Base: `aaa40e8`. Onze achados atacados; **dez corrigidos por completo**, um (`#8`) corrigido conforme a
instrução literal mas com um resíduo documentado (item T4(7) do ledger), detalhado abaixo.

Suíte: **333 passed → 344 passed** (11 testes novos), 109 subtests.

---

## #1 — gate silencioso quando o formato deriva

**Onde:** `redigir-spec-demanda-azure-boards/scripts/verificar_lacunas.py:26` (constante
`SECAO_LACUNAS`) e `:126-137` (`main`).

- `main()` passa a contar: a saída de sucesso é `f"{len(lacunas)} lacunas rotuladas verificadas,
  nenhum vazamento."` em vez de `"Nenhum vazamento de vocabulário técnico em lacunas de negócio."`.
  Um verde agora diz **quantas** lacunas foram efetivamente reconhecidas, então `0` denuncia a deriva.
- Quando `SECAO_LACUNAS` (`## Lacunas e perguntas abertas`) está no texto e `extrair_lacunas` devolve
  zero, sai um aviso em `stderr` nomeando o formato esperado — **mantendo código 0**. Spec antiga sem
  rótulos continua não sendo violação.
- O aviso é condicionado à presença da seção: um arquivo sem a seção não gera ruído.

**Testes:** `tests/test_verificar_lacunas.py::test_cli_relata_quantas_lacunas_rotuladas_verificou`,
`::test_cli_avisa_quando_a_secao_existe_e_nenhuma_lacuna_foi_reconhecida` e
`::test_spec_sem_a_secao_de_lacunas_nao_gera_aviso` (este último fecha a porta para o aviso virar
ruído genérico).

**Smoke manual (a partir da raiz da skill):**

```
$ uv run python scripts/verificar_lacunas.py <spec com N1 e T1>
2 lacunas rotuladas verificadas, nenhum vazamento.
rc=0
$ uv run python scripts/verificar_lacunas.py <spec com "- **N1 . Negócio** - deriva">
aviso: a seção '## Lacunas e perguntas abertas' existe, mas nenhuma lacuna rotulada foi reconhecida. …
0 lacunas rotuladas verificadas, nenhum vazamento.
rc=0
```

## #2 — comando do passo 10 não rodava como escrito

**Onde:** `redigir-spec-demanda-azure-boards/SKILL.md:68-69`.

Antes: `Execute \`uv run python scripts/verificar_lacunas.py\` sobre a spec`.
Agora: `Execute, a partir da raiz desta skill, \`uv run python scripts/verificar_lacunas.py <caminho
completo de spec.md>\``, alinhado com `:213-217`.

**Teste:** `tests/test_skill_integration.py::test_passo_10_roda_o_verificador_com_raiz_e_caminho_explicitos`
(afirma sobre a fatia `10. Confirme` … `## Pasta da Demanda`, normalizada por `sem_quebras`, para não
depender do reflow).

## #3 — teste vacuamente verdadeiro

**Onde:** `redigir-spec-demanda-azure-boards/tests/test_verificar_lacunas.py:41-45`.

`assert all(... for v in verificar(SPEC))` sobre lista vazia virou a asserção de conteúdo pedida:
conta a lacuna `Técnico`, exige `.java` na pergunta dela e só então afirma `verificar(SPEC) == []`.

## #4 — spec parcialmente rotulada sumindo da fronteira

**Onde:** `entrevistar-lacunas-requisito/SKILL.md:37-40` (passo 2).

Frase acrescentada: *"**Lacuna sem rótulo numa spec que tem outras rotuladas entra em toda rodada** e é
relatada ao usuário como rótulo faltante; ela nunca é pulada por não casar com o escopo, sob pena de a
decisão sumir nas duas rodadas."*

**Teste:** `entrevistar-lacunas-requisito/tests/test_skill_integration.py::test_lacuna_sem_rotulo_entra_em_toda_rodada`.

## #5 — `negocio.md` nunca reprojetado

**Onde:**
- `redigir-spec-demanda-azure-boards/SKILL.md:229-233` — parágrafo novo no `## Template de negocio.md`:
  `negocio.md` é **descartável e sempre regerado a partir de `spec.md`**, uma cópia desatualizada
  **nunca é fonte**, e regerar precede cada rodada de negócio; nunca editar à mão nem reconciliar.
- `entrevistar-lacunas-requisito/SKILL.md:68-71` (passo 6) — ao encerrar uma rodada de escopo
  `negócio`, a skill **avisa o usuário** de que `negocio.md` ficou desatualizado e precisa ser regerado
  a partir de `spec.md`. A frase diz explicitamente que **esta skill não regenera `negocio.md` nem chama
  quem o gera**: a entrevista continua skill-folha, sem nomear nenhuma skill (o guard
  `assert_has_no_named_skill_invocation` continua verde).

**Testes:** `redigir…::test_negocio_md_e_descartavel_e_sempre_regerado` e
`entrevistar…::test_rodada_de_negocio_avisa_que_negocio_md_ficou_desatualizado`.

## #6 — companheiros achados pela pasta sem consequência nomeada

**Onde:** `gerar-backlog-azure-boards/SKILL.md:21` (passo 2).

A consequência entrou **na mesma frase** do vocabulário fechado: *"…procure os companheiros ali pelo
vocabulário fechado: `telas-ux-ui.md`, que alimenta este passo, e `debitos-tecnicos.md` e
`revisao-textos.md`, que são contexto rotulado, nunca origem de item de backlog."* A oração relativa
foi escolhida para não separar `Fora desse caso, localize-os pelo título…` do seu referente (a pasta),
o que uma frase interposta faria.

A busca por título como **fallback permanente** ficou intacta — `test_atalho_por_pasta_nao_substitui_a_busca_por_titulo`
continua verde.

**Teste:** `gerar-backlog-azure-boards/tests/test_skill_integration.py::test_companheiros_da_pasta_nao_viram_item_de_backlog`.

## #7 — `Spec de origem` com o caminho completo até `spec.md`

**Onde:** `gerar-backlog-azure-boards/references/backlog-markdown-contract.md:79` (template) e `:171`
(bullet novo em `## Metadados mínimos`).

- Template: `- Spec de origem: [caminho completo até \`spec.md\`, ou documento, versão ou localização]`.
- Prosa: registra o caminho completo incluindo a pasta da Demanda
  (`docs/specs/DN-14125-emissao-de-convites/spec.md`), explica que é o elo de volta à pasta, preserva a
  compatibilidade ("o campo sempre aceitou documento, versão ou localização") e reafirma que o campo é
  **rótulo de origem e nunca fonte do ID da Demanda**, que só vem de `## Fonte da Demanda`.

**Conferência de fixtures/testes que afirmam sobre essa linha (pedida na tarefa):**

```
$ grep -rn "Spec de origem" --include="*.md" --include="*.py" . | grep -v "^./docs/superpowers" | grep -v ".claude/worktrees"
README.md:454:- Spec de origem: seção 2 da spec de diligências
publicar-backlog-azure-boards/tests/fixtures/valid-backlog.md:5:- Spec de origem: `docs/specs/spec-exemplo.md`
publicar-backlog-azure-boards/tests/test_interpretar_markdown.py:39: "…- Spec de origem: `x`\n"
publicar-backlog-demanda-azure-boards/tests/test_interpretar_markdown.py:39: "…- Spec de origem: `x`\n"
publicar-backlog-demanda-azure-boards/tests/fixtures/valid-backlog.md:5:- Spec de origem: `docs/specs/spec-exemplo.md`
orquestrar-skills-de-requisito/scripts/avaliar_roteador.py:73,86
gerar-backlog-azure-boards/references/backlog-markdown-contract.md:79
```

Nenhum deles afirma sobre o **texto do placeholder** do contrato; todos usam valores concretos, e
`gerar-backlog-azure-boards/scripts/validate_backlog.py` não valida esse campo
(`grep -n "origem" …/validate_backlog.py` → nenhuma linha). **Nenhum ajuste mecânico foi necessário** —
exatamente o que a spec de Fase 1 previa ao dizer que nenhum fixture se invalida.

**Teste:** `gerar-backlog-azure-boards/tests/test_skill_integration.py::test_spec_de_origem_registra_o_caminho_completo_ate_spec_md`.

## #8 — `NOVO_BLOCO` reconhecia só `- ` e `#`

**Onde:** `redigir-spec-demanda-azure-boards/scripts/verificar_lacunas.py:25`.

`^(?:- |#)` → `^(?:[-*+] |\d+\. |#|>|\||---)`. Linha de tabela, `* item`, `+ item`, `1. item`, `> nota`
e `---` deixam de ser absorvidos pela lacuna anterior, então a violação não sai mais com o
identificador errado.

**Teste:** `::test_marcador_de_bloco_fecha_a_lacuna_anterior`, que percorre os seis marcadores e afirma,
para cada um, que a lacuna fecha com a pergunta exata e que o vizinho não gera violação sob o ID dela.

**Resíduo honesto — T4(7) NÃO foi resolvido por esta mudança.** O parêntese do achado afirma que
estender `NOVO_BLOCO` também resolve "cabeçalho indentado absorvido pela lacuna anterior". Não resolve,
e eu conferi antes de escrever isto: `_e_continuacao` devolve `True` **antes** de consultar
`NOVO_BLOCO` para qualquer linha indentada (`verificar_lacunas.py:57-58`), de propósito — é isso que
mantém subitem indentado e comentário de evidência dentro da lacuna, e é isso que faz o vazamento de um
subitem chegar ao gate. Evidência com o código já corrigido:

```
$ uv run python -c "…extrair_lacunas('- **N1 · Negócio** — Pergunta limpa?\n  - **N2 · Negócio** — Outra citando X.java:12\n')"
[('N1', 'Pergunta limpa? - **N2 · Negócio** — Outra citando X.java:12')]
```

Os dois caminhos para fechar isso são decisões de design com trade-off real, e nenhum foi autorizado
pela tarefa:

1. Fazer `CABECALHO` aceitar indentação — resolve com o ID certo, mas passa a reconhecer como lacuna
   algo que o achado #1 lista explicitamente como caso que **deve** cair no aviso ("lacuna indentada
   dentro de subitem").
2. Fazer linha indentada que casa `CABECALHO` fechar a lacuna aberta — some com o ID errado, mas o
   corpo da lacuna indentada é **descartado**, e o vazamento escapa do gate em silêncio: pior que o
   estado atual.

Segui a instrução literal (a regex) e deixo a escolha para o controlador. Hoje o caso é parcialmente
coberto pelo #1: se a lacuna indentada for a única da spec, o aviso dispara.

## #9 — docstring prometia mais do que os padrões entregam

**Onde:** `redigir-spec-demanda-azure-boards/scripts/verificar_lacunas.py:3-8`.

A docstring (que o `argparse` imprime no `--help`) agora diz que a regra por extenso vive no
`SKILL.md`, que o verificador cobre o **subconjunto automatizável** — caminho de arquivo, número de
linha, chamada de método e identificador pontuado — e nomeia os casos que passam limpos
(`prazoVigente`, `DemandaValorEsperado`, `EM_ANALISE`), dizendo que dependem de revisão humana.

## #10 — exclusividade do `padrao` dependia da ordem da tupla

**Onde:** `redigir-spec-demanda-azure-boards/scripts/verificar_lacunas.py:29-30`, comentário de duas
linhas imediatamente acima de `PADROES`, dizendo que `verificar` para no primeiro padrão que casa e que
reordenar a tupla muda `Violacao.padrao`.

## #11 — três correções de uma linha

- `redigir-spec-demanda-azure-boards/tests/test_skill_integration.py:171-174` — `extrair_lacunas`
  importado junto de `verificar` e `assert len(extrair_lacunas(template())) == 2` antes de
  `assert verificar(template()) == []`.
- `redigir-spec-demanda-azure-boards/SKILL.md:91` — `**sem hífen final**` →
  `**sem hífen inicial nem final**`. Consequência mecânica: `tests/test_skill_integration.py:275`
  afirmava `"sem hífen final"`; ajustado para a frase nova (`"sem hífen inicial nem final"` contém a
  antiga apenas como sufixo, então a asserção antiga continuaria passando por acidente — por isso foi
  reescrita, não duplicada).
- `redigir-spec-demanda-azure-boards/SKILL.md:257-258` — a prosa passa a citar o cabeçalho real do
  template, `## Comportamento atual (evidência no código)`, coberta por
  `::test_prosa_do_negocio_md_cita_o_cabecalho_real_do_template`.

---

## Prova de que cada asserção nova falha contra `aaa40e8`

Asserções de string — contagem no conteúdo de `aaa40e8` (normalizado por `" ".join(texto.split())`
quando o teste também normaliza, e recortado à mesma fatia que o teste usa quando o teste recorta):

```
0  #1 script: 'lacunas rotuladas verificadas'
0  #1 script: 'nenhuma lacuna rotulada foi reconhecida'
0  #8 script: novo NOVO_BLOCO  ^(?:[-*+] |\d+\. |#|>|\||---)
0  #10 script: 'A ordem importa'
0  #9 script: 'subconjunto automatizável'
0  #2 passo10 (fatia "10. Confirme"…"## Pasta da Demanda"): 'a partir da raiz desta skill'
0  #2 passo10: 'scripts/verificar_lacunas.py <caminho completo de spec.md>'
0  #5 template negocio.md: 'descartável e sempre regerado a partir de `spec.md`'
0  #5 template negocio.md: 'Uma cópia desatualizada nunca é fonte'
0  #11c template negocio.md: '`## Comportamento atual (evidência no código)`'
0  #11b Pasta da Demanda: 'sem hífen inicial nem final'
0  #4 entrevista: 'Lacuna sem rótulo numa spec que tem outras rotuladas entra em toda'
0  #4 entrevista: 'nunca é pulada por não casar com o escopo'
0  #5 entrevista: '`negocio.md` ficou desatualizado'
0  #5 entrevista: 'Esta skill não regenera `negocio.md`'
0  #6 gerador: '…são contexto rotulado, nunca origem de item de backlog'
0  #7 contrato: '- Spec de origem: [caminho completo até `spec.md`, ou documento, versão ou localização]'
0  #7 contrato: 'docs/specs/DN-14125-emissao-de-convites/spec.md'
0  #7 contrato: 'nunca fonte do ID da Demanda'
```

(A asserção do `#2` sobre `a partir da raiz desta skill` dá `1` se procurada no arquivo inteiro — a
frase já existia no passo 1 e em `:213`. Por isso o teste recorta o passo 10, e é sobre a fatia
recortada que o `0` acima foi medido.)

Prova executável, que é a mais forte: os arquivos de teste novos foram copiados para um worktree
destacado em `aaa40e8` e rodados lá.

```
$ git worktree add --detach $WT aaa40e8
$ cp <4 arquivos de teste> $WT/… && cd $WT && uv run pytest … -q
FAILED …test_verificar_lacunas.py::test_cli_relata_quantas_lacunas_rotuladas_verificou
FAILED …test_verificar_lacunas.py::test_cli_avisa_quando_a_secao_existe_e_nenhuma_lacuna_foi_reconhecida
FAILED …test_verificar_lacunas.py::test_marcador_de_bloco_fecha_a_lacuna_anterior
FAILED …redigir…/test_skill_integration.py::test_slug_degenerado_nao_produz_nome_quebrado
FAILED …redigir…/test_skill_integration.py::test_passo_10_roda_o_verificador_com_raiz_e_caminho_explicitos
FAILED …redigir…/test_skill_integration.py::test_negocio_md_e_descartavel_e_sempre_regerado
FAILED …redigir…/test_skill_integration.py::test_prosa_do_negocio_md_cita_o_cabecalho_real_do_template
FAILED …entrevistar…::test_lacuna_sem_rotulo_entra_em_toda_rodada
FAILED …entrevistar…::test_rodada_de_negocio_avisa_que_negocio_md_ficou_desatualizado
FAILED …gerar…::test_companheiros_da_pasta_nao_viram_item_de_backlog
FAILED …gerar…::test_spec_de_origem_registra_o_caminho_completo_ate_spec_md
```

Onze falhas contra `aaa40e8` — uma por asserção nova. Worktree removido em seguida
(`git worktree remove --force` + `git worktree prune`).

**Duas asserções fortalecidas passam contra `aaa40e8` de propósito, e isso é o desfecho correto:**
`test_lacuna_tecnica_pode_citar_codigo` (#3) e `test_lacunas_do_template_nao_violam_o_proprio_verificador`
(#11a). Elas não descrevem comportamento novo; elas deixam de ser vácuo. Antes passariam com
`verificar(SPEC) == []` e com um template vazio; agora exigem, respectivamente, uma lacuna `Técnico`
com `.java` na pergunta e duas lacunas extraídas do template. A tarefa pediu exatamente essa forma.

## Quebras de linha movidas (nenhuma palavra alterada)

| Arquivo | Onde | Por quê |
|---|---|---|
| `redigir-spec-demanda-azure-boards/SKILL.md:68-70` | passo 10 | a frase do comando ficou mais longa; reflow para caber em 100 colunas |
| `redigir-spec-demanda-azure-boards/SKILL.md:90-91` | slug | `sem hífen inicial nem final` estourou a linha |
| `redigir-spec-demanda-azure-boards/SKILL.md:229-232` | parágrafo novo de `negocio.md` | reflow do próprio parágrafo novo |
| `redigir-spec-demanda-azure-boards/SKILL.md:257-260` | prosa de **Como funciona hoje** | o cabeçalho completo alongou a linha; o parágrafo inteiro foi refluído |
| `entrevistar-lacunas-requisito/SKILL.md:68-71` | passo 6 | reflow do próprio trecho novo |

Todas as asserções que tocam texto refluído usam `sem_quebras`/`" ".join(...split())`, então o reflow
não as quebra — é por isso que foram escritas assim.

## Evidência de verificação

```
$ uv run pytest -q
344 passed, 109 subtests passed in 0.32s        (base aaa40e8: 333 passed, 109 subtests)

$ uv run ruff check .
All checks passed!

$ uv run ruff format --check .
95 files already formatted

$ uv run mypy            (como o pre-commit invoca)
Success: no issues found in 15 source files

$ uv run pre-commit run --all-files
trim trailing whitespace.................................................Passed
fix end of files.........................................................Passed
check yaml...............................................................Passed
check toml...............................................................Passed
check for merge conflicts................................................Passed
check for added large files..............................................Passed
ruff (lint + autofix)....................................................Passed
ruff (format)............................................................Passed
mypy (strict)............................................................Passed
bandit (SAST Python).....................................................Passed
```

Nota: `uv run mypy --strict .` (com o `.` explícito) falha com
`Duplicate module named "test_skill_integration"` — é condição **pré-existente** do repositório, não
regressão: há um `tests/test_skill_integration.py` por skill sem `__init__.py`. O pre-commit invoca
`uv run mypy` sem argumentos, que usa as `files` do `pyproject.toml`, e esse passa.

## Arquivos alterados

- `redigir-spec-demanda-azure-boards/scripts/verificar_lacunas.py` (#1, #8, #9, #10)
- `redigir-spec-demanda-azure-boards/tests/test_verificar_lacunas.py` (#1, #3, #8)
- `redigir-spec-demanda-azure-boards/SKILL.md` (#2, #5, #11b, #11c)
- `redigir-spec-demanda-azure-boards/tests/test_skill_integration.py` (#2, #5, #11a, #11b, #11c)
- `entrevistar-lacunas-requisito/SKILL.md` (#4, #5)
- `entrevistar-lacunas-requisito/tests/test_skill_integration.py` (#4, #5)
- `gerar-backlog-azure-boards/SKILL.md` (#6)
- `gerar-backlog-azure-boards/references/backlog-markdown-contract.md` (#7)
- `gerar-backlog-azure-boards/tests/test_skill_integration.py` (#6, #7)

## Achados da auto-revisão (li o diff inteiro)

1. **#6 estava com o referente solto.** A primeira redação interpunha uma frase entre o vocabulário
   fechado e `Fora desse caso, localize-os pelo título…`, afastando o `desse caso` da pasta. Reescrevi
   como oração relativa dentro da frase original e ajustei a asserção correspondente.
2. **Duas linhas Markdown novas passaram de 100 colunas** (`SKILL.md` de `redigir-spec` e de
   `entrevistar`). Refluí; nenhuma palavra mudou.
3. **`#11b` não podia ser asserção aditiva.** `"sem hífen inicial nem final"` **contém**
   `"hífen final"` como sufixo, então acrescentar uma asserção nova sem reescrever a antiga deixaria a
   antiga passando por acidente e nada provaria. Reescrevi a asserção existente.
4. **O aviso do #1 podia virar ruído.** Sem o guard, ele dispararia para qualquer arquivo sem lacunas.
   Condicionei à presença da seção e escrevi `test_spec_sem_a_secao_de_lacunas_nao_gera_aviso` para
   pinar isso.
5. **A frase do #5 na entrevista não podia nomear skill.** `assert_has_no_named_skill_invocation`
   reprova verbo de invocação na mesma linha de um nome de skill. Escrevi "não regenera `negocio.md`
   nem chama quem o gera" — sem nome próprio. Verde.
6. **`"Nenhum vazamento de vocabulário técnico em lacunas de negócio."` aparece em
   `docs/superpowers/plans/2026-09-24-pastas-por-demanda-e-audiencia.md:660`.** É o plano versionado,
   registro histórico do que foi planejado; não o editei. Se a convenção do repositório for manter o
   plano em dia com o código, isso é um ajuste de uma linha que sobra para o controlador.
7. **Restrição "spec antiga sem rótulos continua funcionando" conferida nos dois lados:** o verificador
   devolve `0` com aviso e sem violação (`test_spec_sem_rotulos_de_audiencia_nao_gera_violacao` e
   `test_cli_avisa_…` seguem verdes), e a entrevista mantém intacto
   `test_spec_sem_rotulos_pergunta_tudo`. A frase do #4 fala só de spec **que tem outras rotuladas**,
   então não cria requisito de formato.
8. **`#7` não fez o nome da pasta virar fonte de ID:** o bullet novo reafirma o contrário, e
   `test_contrato_proibe_o_nome_da_pasta_como_fonte_do_id` segue verde.

## Não corrigido

- **T4(7) do ledger** (cabeçalho de lacuna indentado absorvido pela lacuna anterior), que o achado #8
  afirmava vir de brinde com a regex. Não vem — evidência e as duas saídas possíveis estão na seção do
  #8. Não escolhi nenhuma porque ambas contradizem alguma decisão já registrada nos achados, e a tarefa
  manda não adivinhar.

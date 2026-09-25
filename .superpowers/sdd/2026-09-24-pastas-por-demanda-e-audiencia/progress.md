# SDD ledger — plan: docs/superpowers/plans/2026-09-24-pastas-por-demanda-e-audiencia.md

Branch: feat/pastas-por-demanda-e-audiencia (criada a partir de main @8331640, por escolha do usuário — sem worktree)
Baseline: 291 passed, 109 subtests (uv run pytest -q)

## Varredura de pré-voo

### Pares que compartilham arquivo ou interface

| Par | Produz → Consome | Achado |
|---|---|---|
| T1 → T2 | contrato "diretório de destino" + nomes fixos → orquestradora repassa o caminho | de acordo; T2 usa os mesmos literais |
| T2 → T3 | `docs/specs/DN-<id>-<slug>/` → atalho por pasta + `telas-ux-ui.md` | de acordo |
| T2 → T6 | `## Pasta da Demanda` e passos 6–10 → T6 emenda a seção e SUBSTITUI o passo 10 | dependência de ordem, não contradição → Ruling R3 |
| T2 / T5 / T6 | todos editam `redigir-spec-demanda-azure-boards/SKILL.md` | regiões distintas: T2 = passos 6–10 + nova seção; T5 = passo 4 + template + `## Audiência das lacunas`; T6 = passo 10 + `## Template de negocio.md` |
| T4 → T5 | parser aceita `- **N1 · Negócio** — ` e `<!-- evidência: ... -->` → template emite exatamente isso | de acordo, literal por literal |
| T5 → T6 | formato de lacuna com audiência → projeção em `negocio.md` | de acordo |
| T5 → T7 | `- **N3 · Negócio** — ` → filtro de escopo | de acordo |
| T7 → T8 | escopos `negócio`/`técnico` → sugestão da rodada | de acordo |
| T3 / T8 | ambos editam `gerar-backlog-azure-boards/SKILL.md`, seus testes e o `README.md` | sem sobreposição: passo 2 vs passo 11; bullet "Drafting" (README:111) vs bullet "Entrevista de lacunas" (README:112) |
| T4 / pyproject | `[tool.coverage.run] source` e `testpaths` | já cobrem `redigir-spec-demanda-azure-boards` → Ruling R2 |

### Auto-consistência de cada tarefa

| Tarefa | Achado |
|---|---|
| T1 | testes do plano em estilo pytest com `SKILL` global; os 3 arquivos são `unittest.TestCase` com `cls.skill` → Ruling R1 (o próprio plano autoriza) |
| T2 | arquivo-alvo é estilo pytest com `SKILL` global — consistente |
| T3 | mesmo descasamento de T1; arquivo usa `cls.backlog` → Ruling R1 (plano silencioso) |
| T4 | arquivos novos, autoconsistentes; exige padrões mutuamente exclusivos (cada exemplo produz exatamente 1 `padrao`) — o código vem literal no plano |
| T5 | consistente |
| T6 | consistente |
| T7 | mesmo descasamento; arquivo usa `cls.interviewing`; `sem_quebras` precisa ser copiada → Ruling R1 |
| T8 | mesmo descasamento; arquivo usa `cls.backlog` e `cls.readme`, `Path` já importado → Ruling R1 |

### Rulings de pré-voo

Ruling R1 (T1, T3, T7, T8): os testes do plano viram métodos da `unittest.TestCase` já existente em cada arquivo, usando o atributo local (`self.skill`, `self.backlog`, `self.interviewing`, `self.readme`) e `self.assertIn`. Os literais das asserções ficam verbatim. — Motivo: os arquivos-alvo não têm `SKILL` no escopo de módulo; o plano já manda adaptar em T1 e o mesmo descasamento existe em T3/T7/T8. — Custo se errado: estilo de teste diferente do que o plano imaginou; asserções e cobertura idênticas, retrabalho no máximo cosmético.

Ruling R2 (T4): nenhuma edição em `pyproject.toml`. — Motivo: `[tool.coverage.run] source`, `[tool.mypy] files` e `testpaths` já incluem `redigir-spec-demanda-azure-boards`; o próprio passo diz "se ainda não cobrir". — Custo se errado: nenhum; um revisor pode estranhar a ausência de diff no `pyproject.toml`.

Ruling R3 (T2/T6): T2 escreve o passo 10 como o plano manda e T6 o substitui depois, na ordem. — Motivo: o plano sequencia assim de propósito; antecipar em T2 deixaria T2 irreviável contra sua própria spec. — Custo se errado: uma frase obsoleta no SKILL entre T2 e T6, pega pela revisão de T6.

## Progresso

Ruling R4: `bash scripts/task-brief` do skill não acha "Tarefa N" (procura "Task N"); briefs extraídos com `awk` para `<workspace>/task-N-brief.md`, mesma convenção de nome. — Motivo: o plano é pt-BR por exigência do projeto. — Custo se errado: nenhum; o conteúdo do brief é o mesmo recorte do plano.

Ruling R5: `.superpowers/sdd/.gitignore` foi restaurado com `git checkout --` depois que o script `sdd-workspace` o sobrescreveu, apagando a convenção do repositório (versiona só os `.md` na raiz de cada wave). — Motivo: convenção deliberada do projeto vence o default do script. — Custo se errado: os artefatos desta wave voltam a ser rastreáveis pelo git; ficam sem stage até o fim e o usuário decide se commita.

Task 1: complete (commits 8331640..1f49d6e, review clean)
Task 1: minor (deferred): os testes novos são `assertIn` de string, não verificam a posição do parágrafo em relação ao bloco ```markdown — mesmo padrão dos demais testes do arquivo, não é regressão desta tarefa.

Ruling R6 (T2): o trailer de co-autoria é `Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>`, literal, em todos os commits deste plano. O implementador da T2 usou `Claude Sonnet 5` seguindo o lembrete de atribuição do harness; foi retomado e fez `--amend` (12f2703 → 22656ca, diff idêntico). — Motivo: a restrição global está no plano versionado no repositório, portanto é instrução do usuário e sobrepõe o default do harness; a T1 já usava Opus 5 e o branch tem de ficar consistente. — Custo se errado: o trailer nomeia um modelo diferente do que de fato escreveu 6 dos 8 commits; corrigível com rebase interativo.

Task 2: complete (commits 1f49d6e..22656ca, review clean)
Task 2: ⚠️ resolvido pelo controlador — a orquestradora repassa "a pasta da Demanda como diretório de destino", casando com o literal "diretório de destino" que a T1 gravou nas três especializadas.
Task 2: minor (deferred): os testes de "Reexecução" e "slug degenerado" afirmam presença de texto, não comportamento executável — inerente a um SKILL.md, não é lacuna real de cobertura.

Task 3: complete (commits 22656ca..ef597b5, review clean)
Task 3: ⚠️ resolvido pelo controlador — a raiz `docs/specs/` do texto novo do README bate com o que a T2 gravou em `## Pasta da Demanda` (confirmado na revisão da T2).
--- FASE 1 concluída: 3/3 tarefas, revisões limpas, 301 testes passando ---

## FASE 2

Ruling R7 (T4): mantido o desvio do brief que faz a CLI sair com código 2 (em vez de traceback) quando a spec é ilegível, isolado no commit 3c40ad6. — Motivo: o brief fixa só a semântica 0/1 (`0` sem violações, `1` com), que continua intacta; deixar `FileNotFoundError` escapar sairia com 1, tornando "arquivo faltando" indistinguível de "achei violações" justamente num gate que a T5 manda rodar antes de entregar a Spec. O padrão `main(argv=None)` + `except OSError` → código 2 já existe e é testado em `gerar-backlog-azure-boards/scripts/validate_backlog.py`. — Custo se errado: um código de saída a mais que o plano não nomeou; `git revert 3c40ad6` desfaz sozinho, sem tocar em 22be79a.

Ruling R8 (T4): aceita a renomeação de `l` para `lacuna` nas comprehensions transcritas do brief. — Motivo: `E741` está no `select` do ruff deste repositório e não tem autofix; o commit seria rejeitado pelo pre-commit. Nenhuma asserção mudou. — Custo se errado: nenhum; é renomeação de variável local.

Ruling R9 (T4, achado Importante 1, plan-mandated): o padrão `numero-de-linha` transcrito do brief ganha lookbehind `(?<!\d)`. — Motivo: como estava, `23:59`, `8:00` e `1:3` viram violação, e o domínio desta skill é prazo/expiração — "a diligência expira às 23:59?" é a pergunta de negócio mais natural que existe aqui, e o gate a reprovaria dizendo que cita código. A spec manda impedir vazamento técnico, não reprovar pergunta de negócio legítima; a spec vence o literal do plano. O caso `:140-145` do teste continua pego (espaço antes do `:`). — Custo se errado: um vazamento na forma `porta:8080` deixa de ser sinalizado; continua pego por `caminho-de-arquivo` quando há extensão.

Ruling R10 (T4, achado Importante 2, plan-mandated): continuação de item Markdown deixa de exigir indentação. — Motivo: com a regra do brief, `- **N1 · Negócio** — pergunta` seguida de linha não indentada citando `X.java:12` trunca a pergunta em silêncio e o vazamento **não** é sinalizado — bypass silencioso do único gate executável do plano, exatamente o modo de falha que a tarefa existe para impedir. Continuação preguiçosa é Markdown válido e nada no pre-commit normaliza isso. — Custo se errado: texto de prosa logo após a última lacuna pode ser absorvido no corpo dela e gerar falso positivo; mitigado por parar em linha vazia, novo item e título.

Task 4: minor (deferred): (3) a exclusividade do `padrao` depende da ordem da tupla `PADROES`, sem comentário que diga isso; (4) a docstring promete cobrir classe/campo/enum/variável, que nenhum padrão sinaliza — o verificador cobre um subconjunto automatizável; (5) `test_lacuna_tecnica_pode_citar_codigo` afirma sobre lista vazia (vacuamente verdadeiro); (6) `linha` e `trecho` nunca são afirmados, e os testes de CLI não conferem `stderr`; (7) cabeçalho indentado é absorvido pela lacuna anterior e a violação sai com o identificador errado; (8) `md` fora de `EXTENSOES` — mantido de propósito.

Task 4: fix round 1/5 (2 addressed, 0 open — numero-de-linha ganhou lookbehind `(?<!\d)`; continuação preguiçosa passou a entrar no gate via `_e_continuacao`; commits 3c40ad6..8923e4f)
Task 4: complete (commits ef597b5..8923e4f, review clean, 318 testes)
Task 4: minor (deferred, da re-revisão): `(?<!\d)` também suprime `pagina2:15` (dígito antes do `:`), caso artificial sem extensão de arquivo; `NOVO_BLOCO` só reconhece `- ` e `#` como fechamento de continuação, não `> `, `1. ` nem `---`.

Task 5: minor (deferred): (2) `test_lacunas_do_template_nao_violam_o_proprio_verificador` tem poder de detecção hoje, mas é auto-vacuante — se o formato do template derivar e `CABECALHO` parar de casar, `verificar()` volta a `[]` e o teste fica verde sem checar nada; sugerido `assert len(extrair_lacunas(template())) == 2` antes; (3) as fatias `SKILL[SKILL.index("## Audiência das lacunas"):]` vão até o fim do arquivo, não até o próximo cabeçalho — sem vacuidade hoje, fragilidade latente, padrão pré-existente no arquivo, plan-mandated; (4) o Passo 3 removeu "divergência ou limite de investigação" como gatilho de lacuna do template — sobrevive em `SKILL.md:175` e nas referências, plan-mandated.

Task 5: fix round 1/5 (1 addressed, 0 open — a asserção do passo 4 passou a pinar `classificada por audiência conforme **Audiência das lacunas**`, que não existe no base; commits 6bb9efc..c96c469)
Task 5: complete (commits 8923e4f..c96c469, review clean)

Task 6: complete (commits c96c469..933df99, review clean, 326 testes)
Task 6: minor (deferred): a linha 71 do SKILL.md ficou curta (~48 col) contra o reflow ~88-90 do resto do arquivo, consequência do ajuste de quebra de linha; o texto novo cita `## Comportamento atual` enquanto o cabeçalho real é `## Comportamento atual (evidência no código)` — plan-mandated, copiado verbatim do brief.

Ruling R11 (T7, achado Importante, plan-mandated): a asserção `assertIn("escopo", ...)` que o brief manda virou `assertIn("escopo de audiência", ...)`. — Motivo: "escopo" minúsculo já existia no SKILL.md antigo ("para um escopo mais estreito"), então a asserção do brief passava contra o arquivo anterior e não cobria nada do que a tarefa produziu. Comprovado: `grep -c` dá 0 no base 933df99 e 1 no arquivo atual. — Custo se errado: nenhum; a asserção nova é estritamente mais forte e os literais vizinhos não mudaram.

Task 7: fix round 1/5 (1 addressed, 0 open — asserção do escopo passou a pinar frase que não existe no base; commits c30bb2d..9f0dda3)
Task 7: complete (commits 933df99..9f0dda3, review clean, 331 testes)

Task 8: complete (commits 9f0dda3..aaa40e8, review clean, 333 testes, pre-commit --all-files limpo)
--- FASE 2 concluída: 5/5 tarefas. Plano inteiro: 8/8 ---

## Revisão final do branch (8331640..aaa40e8, 12 commits)

Correção de R9: o "custo se errado" registrado estava factualmente errado. `porta:8080` **continua** sendo sinalizado (`numero-de-linha`, trecho `:8080`) — o `:` é precedido por `a`, não por dígito. O custo real é só o caso `pagina2:15`, estritamente menor.

Sem achados Críticos. Sete Importantes e vários Menores, todos corrigidos numa onda só (commits aaa40e8..a09efdf: 6bbac81, 471bd08, a09efdf). Re-revisão com escopo: 11/11 ADDRESSED, nenhuma quebra nova Crítica ou Importante. Verificado pelo controlador: 344 passed + 109 subtests, ruff, ruff format, mypy strict e pre-commit --all-files todos limpos.

Quatro dos sete Importantes eram lacunas do **plano**, não da execução — #4 (lacuna sem rótulo em spec parcialmente rotulada), #5 (`negocio.md` nunca reprojetado), #6 (companheiros achados sem consequência nomeada) e #7 (`Spec de origem` com caminho completo). #5 e #7 contradiziam texto vinculante das specs de design.

### Adjudicação dos resíduos (a revisão final não tem segunda onda)

Task 4: parked — cabeçalho de lacuna indentado continua absorvido pela lacuna anterior, e a violação sai sob o ID errado (`verificar_lacunas.py:62`). Ruling: o código fica. `_e_continuacao` devolve `True` para linha indentada antes de consultar `NOVO_BLOCO`, e é esse ramo que faz o vazamento de um subitem chegar ao gate. As duas saídas possíveis contradizem decisões já registradas: aceitar indentação no `CABECALHO` contradiz o caso que o achado #1 manda cair no aviso; fechar a lacuna descartaria o corpo e o vazamento sairia do gate em silêncio. O estado atual é rotulagem errada, não vazamento invisível — o vazamento É sinalizado. Nada a jusante constrói sobre isso. — Custo se errado: quem lê "linha 12: N1" reescreve a lacuna errada numa spec com lacunas aninhadas; o template gerado é flush-left, então o arranjo não aparece no caminho normal.

Task 4: parked — deriva parcial não dispara o aviso do achado #1: com 3 rótulos bons e 1 derivado, só a contagem denuncia, e só para quem sabe o número esperado. Ruling: aceito. O aviso cobre o caso total, que é o perigoso (gate verde sem ter checado nada); o parcial ainda verifica o que parseou. — Custo se errado: uma lacuna derivada passa despercebida numa spec grande.

Task 4: parked — plural fixo em `verificar_lacunas.py:136` ("1 lacunas rotuladas verificadas") e perda de cobertura do gate em continuação preguiçosa iniciada por marcador de bloco (`:26`), onde antes o vazamento chegava com ID errado e agora não chega. Ruling: ambos ficam. O plural é cosmético; a segunda é a leitura literal do achado #8 e o comportamento desejado, mas o trade-off não está registrado em texto nenhum. — Custo se errado: vazamento numa continuação preguiçosa que começa com `>`, `|`, `* ` ou `1. ` escapa do gate.

Ruling R12: o workspace desta wave NÃO é apagado. — Motivo: o skill manda apagar porque "o histórico do git é o registro agora", mas aqui não é — o `.superpowers/sdd/.gitignore` deste repositório versiona deliberadamente os `.md` na raiz de cada wave (a wave de 2026-09-22 tem o seu `final-fix-report.md` commitado), e estes relatórios nunca foram commitados. Apagar destruiria artefatos que a convenção do repositório manda guardar. — Custo se errado: sobra um diretório de ~15 arquivos que o usuário pode apagar com um comando.

--- PLANO CONCLUÍDO: 8/8 tarefas, revisão final limpa, 15 commits ---

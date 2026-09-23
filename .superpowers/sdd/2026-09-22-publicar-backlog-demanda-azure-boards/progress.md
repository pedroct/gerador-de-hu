# SDD ledger — plan: docs/superpowers/plans/2026-09-22-publicar-backlog-demanda-azure-boards.md

Spec: docs/superpowers/specs/2026-09-22-publicar-backlog-demanda-azure-boards-design.md (presente, legível)
Worktree: /Volumes/DOCK/Projetos/pessoal/gerador-hu/.claude/worktrees/publicar-backlog-demanda
Branch: feat/publicar-backlog-demanda-azure-boards (criada de b45863d)
Baseline: publicar-backlog-azure-boards — 126 testes, 0 falhas.

## Scan de pré-voo

### Pares de tarefas que compartilham arquivo ou interface

| Tarefas | Arquivo/interface | Produz × consome | Achado |
|---|---|---|---|
| T1 → T2 | pacote inteiro × `MODULOS_ESPELHADOS` | T1 faz `sed` global do nome do pacote em `src/` | `interpretar_markdown.py` e `validacao_estrutural.py` importam `publicar_backlog_azure_boards`; o `sed` os faz divergir byte a byte. **Sem conflito**: o teste da T2 normaliza com `.replace("publicar_backlog_azure_boards", "publicar_backlog_demanda_azure_boards")` antes de comparar. |
| T1 → T3..T13 | `src/*`, `tests/*` | T1 produz a API pública idêntica à origem | Coerente. |
| T3 → T4 | `montar_titulo(item)` | T3 produz; T4 consome | Assinaturas batem. |
| T4 → T5 | `planejar_publicacao.py` | T4 muda `_criar_operacao`; T5 muda `_calcular_hash` | Mesmo arquivo, funções distintas, ordem sequencial. Sem conflito. |
| T5 → T6 | `demanda_id`, `criar_frase_confirmacao`, `Manifesto` | T5 produz; T6 só testa | Coerente. |
| T5 → T7 | `Demanda` (modelos.py) | T5 produz a dataclass; T7 a devolve | Campos batem (`id`, `titulo`, `area_path`, `iteration_path`, `url`). |
| T5 → T8 | `ConfiguracaoPublicacao.demanda_id` | T5 produz; T8 consome em `_verificar_preliminar` | Coerente. |
| T5 → T9 | `ConfiguracaoPublicacao.demanda_id` | T5 produz; T9 usa como pai do Épico | `executar_publicacao.py:90` hoje devolve `id_pai=None` para item sem `chave_pai`; é exatamente o ponto que T9 altera. Coerente. |
| T5 → T10 | `configuracao.py`, `cli.py` | T5 acrescenta `demanda_id`/`--demanda`; T10 remove `area_path`/`iteration_path` e a property `publicacao` | Mesmos arquivos, mudanças sequenciais e complementares. Sem conflito. |
| T7 → T8 | `_verificar_status` em `cliente_azure_devops.py` | T7 importa a função privada; T8 modifica o módulo | T8 mexe em `validar_operacao`, não em `_verificar_status`. `ruff` com `select = ["E","F","I","B","UP","S"]` **não** inclui `SLF001`, então a importação privada não quebra o lint. Sem conflito. |
| T7 → T10 | `ler_demanda(...)` | T7 produz; T10 consome | Assinatura da T7 bate com o uso previsto na T10. |
| T8 → T9 | `validar_operacao(operacao, id_pai=None)` | T8 muda a assinatura com padrão | `criar_item` já aceitava `id_pai`; o padrão `None` mantém compatibilidade. Sem conflito. |
| T8 → T10 | `cli.py::_verificar_preliminar` | T8 acerta o pai na verificação; T10 troca como a configuração nasce | **Risco real**: T10 reescreve a construção do destino e pode quebrar os testes que T8 criou no Step 4b. T10 Step 6 roda a suíte inteira, o que fecha o buraco. Sem ruling necessário; vigiar na revisão da T10. |
| T10 → T11 | `cli.py`, `Demanda` derivada, `tests/test_skill_integration.py` | T10 produz o destino derivado; T11 exibe a origem | Mesmo arquivo de teste, tarefas sequenciais. Sem conflito. |
| T12 → T1 | `test_documentacao_operacional.py` | T1 corrige o nome; T12 reescreve as afirmações | Coerente. |
| T13 → tudo | `test_integracao_final.py` | T1 herda, T4 corrige títulos, T13 acrescenta caso ponta a ponta | Coerente. |

### Autoconsistência de cada tarefa

| Tarefa | Achado |
|---|---|
| T1 | Consistente. Steps cobrem cópia, renomeação, pyproject, prog da CLI e suíte verde. |
| T2 | Consistente. O Step 3 prova que o teste pega divergência de verdade (não é teste que não afirma nada). |
| T3 | Consistente. Testes antes da implementação. |
| T4 | Consistente. O Step 4 antecipa os testes herdados que afirmam o título datado. |
| T5 | **Files incompleto**: o Step 4 edita `planejar_publicacao.py` e o Step 1 cria `tests/test_demanda_no_destino.py`, e nenhum dos dois aparece na lista **Files**. Os Steps são exaustivos e corretos. |
| T6 | Consistente. Tarefa só de teste, declarada como tal. |
| T7 | Consistente. A nota sobre `_verificar_status` evita duplicar lógica de status. |
| T8 | Consistente. Step 4b cobre a escolha do pai na verificação preliminar. |
| T9 | Consistente. |
| T10 | Consistente. Muda a semântica de `--simulacao` e o Step 4b prova uma leitura e nenhuma escrita. |
| T11 | Consistente. |
| T12 | Consistente. |
| T13 | Consistente. O Step 7 (publicação real) é conduzido pelo usuário, fora do escopo automatizável. |

### Rulings de pré-voo

- **Ruling: todo caminho absoluto `/Volumes/DOCK/Projetos/pessoal/gerador-hu` no plano lê-se como `/Volumes/DOCK/Projetos/pessoal/gerador-hu/.claude/worktrees/publicar-backlog-demanda`.** — o plano foi escrito supondo o checkout principal, e o usuário escolheu executar em worktree isolado; usar o caminho literal escreveria na `main`. — Custo se errado: nenhum comportamento muda; só o local dos arquivos. Ao integrar a branch, os caminhos voltam a coincidir.
- **Ruling: na Task 5, os Steps mandam sobre a lista Files.** `planejar_publicacao.py` e `tests/test_demanda_no_destino.py` fazem parte da tarefa, embora a seção **Files** os omita. — a lista Files é resumo, os Steps são a especificação executável, e sem o Step 4 o hash não distinguiria duas Demandas (o risco central da tarefa). — Custo se errado: um arquivo a mais no diff da T5 do que a seção Files anuncia.
- **Ruling: o workspace do SDD (`.superpowers/sdd/<plano>/*.md`) não será apagado no fim.** — o `.gitignore` deste repositório versiona explicitamente `.superpowers/sdd/*/*.md` (commit e2d9558, "versiona os relatórios do superpowers com regra explícita"); apagar contraria uma decisão registrada do usuário. — Custo se errado: ledger e relatórios ficam no repositório em vez de só no histórico do git.
- **Ruling: `Step 7` da Task 13 (publicação real contra o Azure DevOps) não será executado por mim.** — exige token real e escrita em sistema externo; é uma das quatro classes que param a execução. — Custo se errado: nenhum; será apresentado ao usuário no fim.

## Progresso

Task 1: complete (commits b45863d..0452db7, review clean — spec ✅, qualidade Aprovada)
Task 1: minor (deferred): `references/auditoria-dependencias.md:9` mantém o nome do diretório de origem; correto como registro histórico, mas sem nota que explique a herança ao leitor futuro.
Task 1: minor (deferred): `agents/openai.yaml` — `display_name`/`short_description` ainda descrevem a skill de origem. Coberto pela Task 12 (Step 3), que atualiza esse arquivo.
Task 2: complete (commits 0452db7..1559aa3, review clean — spec ✅, qualidade Aprovada, zero achados)
Ruling: o script `sdd-workspace` sobrescreveu `.superpowers/sdd/.gitignore` (que o repositório versiona) por um `*` cego; restaurei a versão do repositório com `git checkout --`. — o arquivo é decisão explícita do usuário (commit e2d9558) e o `*` cego descartaria os relatórios que ele quis versionar. — Custo se errado: nenhum; se o script precisar do `*`, o sintoma seria arquivos do workspace aparecendo como não rastreados, que é justamente o comportamento desejado aqui.
Task 3: complete (commits 1559aa3..1768065, review clean — spec ✅, qualidade Aprovada)
Task 3: ⚠️ resolvido pelo controlador — o relatório só trazia a saída do arquivo de teste novo; rodei `uv run pytest` no pacote e obtive 148 passed, 0 falhas. Não era lacuna real.
Task 3: minor (deferred): `titulo_hierarquico.py` usa `int(componente)` sem `isdigit()` antes; `int()` aceita espaços nas bordas e `_` entre dígitos, entao `" 1.0.0"` ou `"1_0.0.0"` passariam onde o teste pretende `ValueError`. Risco baixo (a chave é produzida internamente), mas fecharia com `componente.isdigit()`.
Task 4: complete (commits 1768065..f75582a, review clean — spec ✅, qualidade Aprovada, zero achados; suíte 148 → 150)
Task 5: revisão 1 — spec ✅, qualidade "Precisa de correções". 1 Importante (rotulado mandado-pelo-plano), 4 Menores.
Task 5: Ruling: o achado Importante #1 (três guardas novas sem teste: manifesto.py:390, configuracao.py:58-62, configuracao.py:171) entra no loop de correção, apesar de rotulado `mandado-pelo-plano`. — o Step 1 do plano fixou um conjunto de testes sem casos negativos, mas não proibiu outros; a spec é a autoridade vinculante e sua garantia central é que uma autorização não atravessa Demandas, que é exatamente o que essas três guardas produzem. Guarda sem teste é guarda que some no próximo refactor sem ninguém notar. Acrescentar testes completa o plano, não o contradiz. — Custo se errado: três testes a mais do que o plano previa, num arquivo que o plano já manda existir.
Task 5: minor (deferred): `configuracao.py:192-193` — `demanda_id` <= 0 chega ao usuário como "A configuração do Azure DevOps é inválida", porque o `ValidationError` do Pydantic é engolido por um `except ValueError` genérico pré-existente; a mensagem do validador ("deve ser um inteiro positivo") se perde. Inconsistente com o caminho do ID não numérico, que tem mensagem precisa.
Task 5: minor (deferred): `tests/test_demanda_no_destino.py:38-47` (texto literal do plano) só afirma que a dataclass devolve o que recebeu; não guarda que `Demanda` é congelada. Uma linha com `pytest.raises(FrozenInstanceError)` viraria guarda real.
Task 5: minor (deferred): `tests/test_autorizacao.py:117-135` — o `parametrize` de destino divergente não tem caso para `demanda_id`. A Task 6 existe justamente para cobrir esse invariante; verificar na revisão da Task 6 se ficou coberto.
Task 5: minor (deferred): relatório do implementador diz 301 linhas em `configuracao.py`; o arquivo tem 298. Sem consequência prática.
Task 5: fix round 1/5 (3 atendidos, 0 abertos — guardas de manifesto/ID não positivo/ID não numérico agora cobertas, com sabotagem individual provando a falha; commits a6a19d2..579dad1)
Task 5: complete (commits f75582a..579dad1, review clean — spec ✅, todos os achados atendidos na rodada 1; suíte 150 → 156)
Task 6: revisão 1 — spec ✅ com ressalva, qualidade "Precisa de correções". 1 Importante (rotulado mandado-pelo-plano), 2 Menores.
Task 6: Ruling: o achado Importante entra no loop, apesar de o teste defeituoso ser cópia literal do plano. `test_manifesto_de_uma_demanda_nao_retoma_sob_outra` é interceptado pela checagem de hash (`manifesto.py:166`) e nunca alcança a checagem de destino (`manifesto.py:168`); remover `demanda_id` só da comparação de destino do manifesto deixaria o teste passando. — a spec é a autoridade vinculante e exige que um manifesto de uma Demanda não retome sob outra; o plano é o argumento dela, e neste ponto o argumento não prova a tese. O quarto ponto de aplicação do vínculo ficaria sem teste que o isole do hash. — Decidi **acrescentar** um teste que iguala `hash_plano` e varia só a configuração, em vez de reescrever o teste do plano: o teste do plano segue válido como regressão ponta a ponta, e assim completo o plano em vez de contradizê-lo. — Custo se errado: um teste a mais do que o plano previa no arquivo que o plano já manda existir.
Task 6: minor (deferred): os 5 testes não têm mensagem de `assert` customizada; para o teste de hash, uma mensagem pouparia quem depurar de ler o SHA-256 bruto.
Task 6: minor (deferred): `test_frase_de_uma_demanda_nao_autoriza_outra` mistura dois sinais (texto "DEMANDA" e hash) na mesma asserção; aceitável porque hash e frase já têm teste isolado próprio.
Task 6: fix round 1/5 (1 atendido, 0 abertos — teste novo `test_validacao_de_manifesto_rejeita_divergencia_de_demanda_mesmo_com_hash_igual` iguala o hash e alcança de fato `manifesto.py:168`, com sabotagem provando; commits 8547391..59eafdf)
Task 6: minor (deferred): `tests/test_autorizacao_vinculada_a_demanda.py:100-108` — `dataclasses.replace` redundante (o `Manifesto` não é frozen e o `hash_plano` já é passado no construtor); indireção desnecessária, sem efeito no isolamento.
Task 6: complete (commits 579dad1..59eafdf, review clean — spec ✅, achado atendido na rodada 1; suíte 156 → 162)
Task 7: implementada e commitada (commit 9749733, suíte 162 → 171), **revisão da tarefa ainda NÃO foi despachada**.
Task 7: BASE para o pacote de revisão = 59eafdf; HEAD = 9749733. O implementador relata que NÃO promoveu `_verificar_status` (o ruff deste projeto não seleciona SLF001, a importação privada passou limpa) e que `cliente_azure_devops.py` ficou intocado — verificar isso na revisão, porque a Task 8 também mexe nesse módulo.
Task 7: ponto que o implementador levantou e que a revisão deve julgar — o conjunto de 9 testes prescrito pelo plano não inclui caso dedicado a "URL inutilizável"; a validação existe no código, sem teste próprio. Ele seguiu o plano literalmente e não acrescentou teste por conta própria (decisão correta: é ruling meu, não dele).

## PAUSA SOLICITADA PELO USUÁRIO — 2026-09-22

Motivo: o usuário vai reiniciar o computador.

**Para retomar:** a execução para no meio do loop da Task 7 — implementação pronta e commitada, revisão pendente. O próximo passo é gerar o pacote de revisão com
`bash <skill>/scripts/review-package docs/superpowers/plans/2026-09-22-publicar-backlog-demanda-azure-boards.md 59eafdf HEAD`
e despachar o revisor da Task 7. Tasks 8 a 13 seguem sem começar.

Estado da árvore na pausa: limpa; só o diretório deste workspace aparece como não rastreado.
Worktree: /Volumes/DOCK/Projetos/pessoal/gerador-hu/.claude/worktrees/publicar-backlog-demanda (branch feat/publicar-backlog-demanda-azure-boards). O worktree **não** foi removido — é onde o trabalho vive.

NOTA RECORRENTE: o script `sdd-workspace` sobrescreve `.superpowers/sdd/.gitignore` toda vez que roda. Restaurar com `git checkout -- .superpowers/sdd/.gitignore` depois de cada chamada.

## RETOMADA — troca de executor para inline

Baseline reconferido na retomada: `uv run pytest -q` → 171 passed, 0 falhas. Bate com o ledger.

Ruling: a execução passa de subagent-driven para inline (superpowers:executing-plans), por escolha do usuário na retomada. — o modo inline não tem revisor por tarefa; tem uma revisão única de toda a branch no fim. — Custo se errado: as Tasks 8–13 recebem revisão só no fim, e não tarefa a tarefa; o ledger e o TDD continuam sendo o portão por tarefa.

Ruling: a revisão pendente da Task 7 não será despachada isoladamente; ela é absorvida pela revisão final de toda a branch. — despachar um revisor só para a Task 7 reintroduziria o custo por tarefa que o modo inline existe para evitar, e o diff da Task 7 estará integralmente dentro do pacote da revisão final. — Custo se errado: um achado da Task 7 aparece mais tarde, junto dos demais, em vez de isolado; nenhum achado se perde.

Ruling: o ponto aberto da Task 7 — a validação de "URL inutilizável" em `leitor_demanda.py` não tem teste dedicado, porque o plano prescreveu nove testes e nenhum a cobre — vira teste agora, junto da Task 8. — a spec lista a URL entre os campos que o leitor valida, e guarda sem teste some no próximo refactor sem ninguém notar; é o mesmo critério já aplicado nos rulings das Tasks 5 e 6. — Custo se errado: um teste a mais do que o plano previa, no arquivo que o plano já manda existir.

Task 8: complete (commits 9749733..030e245, tests: uv run pytest -q → 179 passed, 0 falhas; suíte 171 → 179)
Task 8: RED observado nos dois pontos previstos — `TypeError: validar_operacao() got an unexpected keyword argument 'id_pai'` no cliente, e `{'1.0.0': None} != {'1.0.0': 13959}` na verificação preliminar. Step 5 quebrou os clientes falsos exatamente como o brief antecipou; os três ganharam `id_pai` e passaram a registrar o par (chave, id_pai) em vez de descartá-lo com `del`.
Task 8: nota — `test_validar_operacao_sem_pai_nao_envia_relacao` passou de imediato (guarda o caminho sem pai, que já funcionava). Mantido como regressão, não como prova de comportamento novo.
Task 8: a guarda de URL do leitor (ruling da retomada) ficou coberta por 5 casos; sabotagem de `leitor_demanda.py:81` derrubou os 5 e a restauração devolveu verde.
Task 9: complete (commits 030e245..0d4df54, tests: uv run pytest -q → 182 passed, 0 falhas; suíte 179 → 182)
Task 9: RED observado — `assert None == 13959`, os Épicos subiam sem pai. `test_feature_e_historia_mantem_os_pais_do_backlog` passou de imediato: guarda que a mudança não quebrou a resolução pelo manifesto.
Task 10: complete (commits 0d4df54..162ee9f, tests: uv run pytest -q → 185 passed, 0 falhas; suíte 182 → 185)
Task 10: Ruling: o teste `test_a_cli_nao_oferece_mais_os_caminhos_manuais`, escrito no plano sobre `construir_parser().format_help()`, não testa o que afirma — a ajuda de topo do argparse não lista flags de subcomando, então os dois `assert ... not in ajuda` passariam vazios com os argumentos ainda existindo. Troquei por `parse_args(["planejar", ..., "--area-path", ...])` dentro de `pytest.raises(SystemExit)`, que falha de verdade enquanto o argumento existe (RED observado: "DID NOT RAISE"). Acrescentei `test_a_cli_aceita_a_demanda` para cobrir o lado positivo que o assert `"--demanda" in ajuda` pretendia. — a spec exige que os caminhos manuais deixem de ser oferecidos; um teste que passa vazio não prova isso. — Custo se errado: dois testes no lugar de um, ambos no arquivo que o plano já manda tocar.
Task 10: Ruling: `test_simulacao_sem_token_nao_instancia_cliente_http` foi substituído, não corrigido. A premissa dele ("simulação não pede token e não faz HTTP") é exatamente a semântica que a spec mudou de propósito. O substituto `test_simulacao_le_a_demanda_uma_vez_e_nao_instancia_cliente_de_escrita` afirma `metodos == ["GET"]`, que nenhum cliente de escrita é instanciado e que o manifesto não é criado — realizando o critério 2 da spec. — manter o teste antigo exigiria manter a simulação offline, que a seção "Simulação deixa de ser offline" da spec descarta explicitamente. — Custo se errado: perde-se a garantia de que a simulação roda sem credencial, que a spec já declarou abrir mão.
Task 10: Ruling: `test_multiplos_area_paths_exigem_escolha_explicita` foi removido, conforme o Step 6 do brief; a seleção entre múltiplos Area Paths deixou de existir junto de `_obter_area_path` e `AZURE_DEVOPS_AREA_PATHS`. `test_area_path_relativo_e_normalizado_com_o_projeto` virou `test_area_path_da_demanda_e_normalizado_com_o_projeto` e passou a provar a normalização sobre o caminho vindo da Demanda, nos dois campos. — a normalização continua existindo e continua merecendo guarda; o que sumiu foi a fonte do caminho. — Custo se errado: nenhum; a normalização segue coberta.
Task 10: Ruling: o brief mandava ramificar por `cliente is not None`, mas isso não estreita o tipo para o mypy strict (`_ConfiguracaoLocal` não tem `projeto`, `demanda_id`, `tipo_demanda` nem `publicacao_para`). Usei `isinstance(configuracao, _ConfiguracaoLocal)`, que é a condição real: destino pronto vindo de cliente injetado, sem token para ler a Demanda. — mesma semântica, e é o próprio tipo que responde pela pergunta. — Custo se errado: um cliente injetado junto de argumentos de configuração passaria a ler a Demanda; nenhum teste exercita esse caso hoje.
Task 11: complete (commits 162ee9f..2ae1a0b, tests: uv run pytest -q → 187 passed, 0 falhas; suíte 185 → 187)
Task 11: RED observado — o cabeçalho não existia; a saída ia direto de "Plano de publicação" para "Organização". Acrescentei um segundo teste além do brief, `test_plano_nomeia_a_demanda_lida_com_seu_titulo`, porque o ramo `demanda is not None` (que traz o título) não é exercitado por cliente injetado, único caminho que o teste do brief percorre.
Task 12: complete (commits 2ae1a0b..69a57ec, tests: uv run pytest -q → 195 passed, 0 falhas; suíte 187 → 195)
Task 12: Ruling: o Step 4 do brief mandava passar a contagem do README raiz de "nove capacidades" para dez. Não fiz: as nove capacidades são as skills de spec e refinamento, e a publicação já vive em seção própria — `publicar-backlog-azure-boards` nunca esteve nessa contagem nem na tabela "Skills disponíveis". Em vez disso, acrescentei à seção "Fluxo de publicação autorizada" uma tabela comparando as duas publicadoras (onde a hierarquia nasce, de onde vêm os caminhos, formato dos títulos), um diagrama com os dois ramos e os comandos de cada uma. — mudar o número para dez tornaria o texto falso, porque a lista de bullets logo abaixo continuaria com nove itens. — Custo se errado: a skill nova não aparece na tabela "Skills disponíveis"; aparece na seção de publicação, junto da irmã.
Task 12: os oito testes novos de documentação nasceram RED (8 failed) e fecharam verdes. Um deles pegou um defeito real de redação: a frase "zero chamadas de criação" tinha sido quebrada por uma quebra de linha no meio, e `test_skill_declara_confirmacao_antes_de_escrita` derrubou o SKILL.md por isso.
Task 13: complete (commits 69a57ec..cc66834, tests: uv run pytest -q → 196 passed, 0 falhas; suíte 195 → 196)
Task 13: o teste ponta a ponta passou de primeira (todo o comportamento já vinha das Tasks 8–12). Sabotei `executar_publicacao.py` trocando `cliente.configuracao.demanda_id` por `None` e ele falhou; restaurado e verde.
Task 13: verificações finais — ruff check limpo, ruff format sem pendência (35 arquivos), mypy strict sem achados em 15 módulos, bandit 0 issues em todas as severidades, `pre-commit run --all-files` com os 10 hooks passando.
Task 13: `git diff --stat main -- publicar-backlog-azure-boards` vazio: a skill de origem permaneceu intocada, como a restrição global exige.
Task 13: Step 7 (publicação real contra a Demanda 13959) NÃO executado — é escrita em sistema externo com token real, uma das quatro classes que param a execução. Fica como entrega ao usuário.

## Revisão final (contexto fresco, modelo Opus)

Veredito: spec cumprida nas seis garantias centrais, com uma omissão (data de geração não exibida no plano). Qualidade "precisa de correções". Nenhum achado põe em risco escrita indevida — todos são fail-closed.

Final: Ruling: re-classifiquei o achado #7 de Menor para Importante. `int(str(bruto).strip().lstrip("#"))` aceita separador `_` e dígitos não-ASCII, então `--demanda 1_3` e `--demanda ١٣` viram 13. Por efeito, isso publica sob outro work item em silêncio sempre que o ID resultante existir e for do tipo certo — e colar ID de página renderizada em outro locale é gesto comum. O revisor graduou pela probabilidade; a régua é o que o usuário recebe se acontecer. — Custo se errado: uma validação a mais num caminho que já falharia adiante na maioria dos casos.
Final: Ruling: o achado #6 (ID não positivo perde a mensagem precisa) entra na rodada junto do #7, porque a mesma checagem ASCII fecha os dois, e a tabela "Validações e erros" da spec nomeia o caso explicitamente. — Custo se errado: nenhum; é mensagem de erro melhor.
Final: entram na rodada única de correção — #1 (httpx.RequestError escapa e derruba a CLI com traceback), #2 (--help promete simulação offline que a spec eliminou), #3 (data de geração ausente do plano, contra requisito em negrito da spec), #4 (leitura da Demanda sem retentativa e com todos os modos de falha achatados numa mensagem que culpa o ID), #6+#7 (validação ASCII do --demanda).
Final: fixed #1 (httpx.RequestError escapava) — test_falha_de_transporte_vira_erro_tratavel_pela_cli RED→GREEN, suíte 218/218
Final: fixed #4 (sem retentativa, erros achatados) — test_status_transitorio_e_retentado_antes_de_desistir[6 casos], test_status_transitorio_que_se_resolve_devolve_a_demanda, test_credencial_recusada_nao_e_confundida_com_id_errado, test_permissao_negada_nao_e_confundida_com_id_errado, test_corpo_que_nao_e_json_vira_erro_nomeado RED→GREEN, suíte 218/218
Final: fixed #2 (--help prometia simulação offline) — test_ajuda_da_simulacao_nao_promete_execucao_offline RED→GREEN, suíte 218/218
Final: fixed #3 (data de geração ausente do plano) — test_plano_exibe_a_data_de_geracao_do_backlog RED→GREEN, suíte 218/218
Final: fixed #6+#7 (validação ASCII do --demanda) — test_id_de_demanda_invalido_nomeia_o_problema[6 casos] RED→GREEN, suíte 218/218
Final: Ruling: o caso `--demanda ""` NÃO foi tratado como erro nomeado. Valor vazio é "não informado" em toda a camada de configuração — igual a organização e projeto vazios — e cai na pergunta interativa; a mensagem resultante ("A entrada interativa foi encerrada antes da configuração") nomeia a causa real. Corrigi a expectativa do meu teste, não o código. — quebrar essa uniformidade só para o campo da Demanda criaria um caso especial sem motivo. — Custo se errado: quem passa `--demanda ""` num script não interativo recebe erro sobre entrada, não sobre o argumento.
Final: Ruling: `test_demanda_id_nao_positivo_e_rejeitado` (escrito na Task 5) afirmava a mensagem enterrada em `excinfo.value.__cause__` — justamente o Menor #6 da revisão. A correção trouxe a mensagem para a própria exceção, então movi a asserção. — o teste afirmava o comportamento pior; mantê-lo travaria a melhoria. — Custo se errado: nenhum; a mensagem continua coberta, num lugar melhor.

### Menores adiados (não entraram na rodada)

Final: minor (deferred): #5 — `numerar()` produz numeração silenciosamente errada para chave fora do contrato (`0.0.0` → `00`, `1.0.5` → `01.00.05`). Inalcançável pelo fluxo da CLI: `interpretar_markdown` e `_validar_chave_e_nivel` rejeitam antes. Defesa em profundidade; `componente.isdigit()` fecharia junto com a guarda de zero à direita.
Final: minor (deferred): #8 — cliente injetado junto de argumentos de configuração é ramo morto (fail-closed), mas diagnostica como "credencial obrigatória" o que é erro de combinação de argumentos.
Final: minor (deferred): #9 — `leitor_demanda` não faz `quote()` de organização e projeto, ao contrário de `ClienteAzureDevOps`. O httpx normaliza e o Azure proíbe os caracteres perigosos em nome de projeto; é inconsistência, não defeito.
Final: minor (deferred): #10 (parcial) — as lacunas de teste de transporte, status transitório e corpo não-JSON foram fechadas pela rodada; permanece sem teste próprio o ramo de `_objeto` para raiz não-dict, agora coberto por `test_raiz_da_resposta_precisa_ser_objeto` e `test_fields_ausente_e_recusado`.
Final: minor (deferred): manifesto da skill de origem no mesmo diretório (as duas usam `manifesto-publicacao.json` como padrão) é recusado corretamente, mas a mensagem não diz que o manifesto é da outra publicadora.
Final: minor (deferred), herdado da Task 1: `references/auditoria-dependencias.md:9` mantém o nome do diretório de origem sem nota explicando a herança.
Final: minor (deferred), herdado da Task 5: `tests/test_demanda_no_destino.py` não guarda que `Demanda` é congelada.

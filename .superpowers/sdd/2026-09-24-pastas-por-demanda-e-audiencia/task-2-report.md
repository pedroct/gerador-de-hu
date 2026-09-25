# Relatório — Tarefa 2: A orquestradora cria a pasta da Demanda

## O que foi implementado

- `redigir-spec-demanda-azure-boards/SKILL.md`:
  - Nova seção `## Pasta da Demanda`, inserida entre o fim do `## Fluxo obrigatório` (passo 10) e o
    cabeçalho `## Limites de leitura e de decisão`. Define: convenção de nome `DN-<id>-<slug>` (regras
    de slug, truncamento em 60 caracteres, fallback `DN-<id>` sem hífen final quando o título não
    produz caractere aproveitável); raiz padrão `docs/specs/` com possibilidade de raiz customizada
    pelo usuário; vocabulário fechado de arquivos (`spec.md`, `debitos-tecnicos.md`, `telas-ux-ui.md`,
    `revisao-textos.md`); reexecução reaproveitando a pasta existente sem criar duplicata nem abortar;
    e a regra de que o nome da pasta é rótulo — o ID que vale é o de `## Fonte da Demanda` em `spec.md`.
  - Passos 6 a 10 do `## Fluxo obrigatório` reescritos exatamente como o brief especificou verbatim:
    - Passo 6: passa a começar criando a pasta da Demanda e salvando a Spec-base nela como `spec.md`.
    - Passo 7: acrescenta "Informe a pasta da Demanda como diretório de destino." ao chamar
      `especificar-debitos-tecnicos`.
    - Passo 8: passa a informar a pasta da Demanda como diretório de destino ao chamar
      `especificar-telas-ux-ui`.
    - Passo 9: passa a informar a pasta da Demanda como diretório de destino ao chamar
      `revisar-textos-requisitos`.
    - Passo 10: reescrito para confirmar que a pasta contém `spec.md` e os companheiros gerados,
      informar ao usuário o caminho completo da pasta, e preservar a proibição existente de encadear
      entrevista, geração ou publicação de backlog (texto mantido literalmente).
  - Nenhuma menção a `negocio.md` foi antecipada no passo 10, conforme a nota de sequenciamento do
    controlador (isso é trabalho da Tarefa 6).

- `redigir-spec-demanda-azure-boards/tests/test_skill_integration.py`:
  - Acrescentados os 4 testes do brief (`test_skill_define_a_pasta_da_demanda_e_o_vocabulario_fechado`,
    `test_pasta_existente_e_reaproveitada`, `test_slug_degenerado_nao_produz_nome_quebrado`,
    `test_skill_informa_o_caminho_usado`) ao final do arquivo.
  - Atualizados os dois marcadores em `test_fluxo_estatico_preserva_ordem_gatilhos_e_lacunas` — de
    `"Preencha e salve a Spec-base"` para `"Crie a pasta da Demanda"`, e de `"Salve a Spec principal"`
    para `"Confirme que a pasta da Demanda"` — preservando a ordem da tupla, exatamente como instruído
    no Passo 5 do brief.

## O que foi testado e resultados

### Evidência de TDD

**RED** — comando rodado após o Passo 1 (só os 4 testes novos acrescentados, sem tocar no SKILL.md):

```
uv run pytest redigir-spec-demanda-azure-boards/tests -v
```

Saída relevante: `4 failed, 84 passed`.

- `test_skill_define_a_pasta_da_demanda_e_o_vocabulario_fechado`: `AssertionError: assert 'DN-<id>-<slug>' in SKILL` — falha esperada porque a seção `## Pasta da Demanda` ainda não existia no SKILL.md, então nenhum dos textos do vocabulário fechado estava presente.
- `test_pasta_existente_e_reaproveitada`: `ValueError: substring not found` em `SKILL.index("## Pasta da Demanda")` — falha esperada, seção inexistente.
- `test_slug_degenerado_nao_produz_nome_quebrado`: mesmo `ValueError: substring not found` — falha esperada, mesma causa.
- `test_skill_informa_o_caminho_usado`: `AssertionError: assert 'informe ao usuário o caminho' in ...` — falha esperada, o passo 10 antigo dizia "Salve a Spec principal..." sem a frase de informar o caminho ao usuário.

Isso bate exatamente com o esperado no Passo 2 do brief ("4 falhas, sendo as três primeiras `ValueError: substring not found`").

**GREEN** — comando rodado após os Passos 3 e 4 (seção nova + reescrita dos passos 6-10) e após corrigir os dois marcadores do Passo 5:

```
uv run pytest redigir-spec-demanda-azure-boards/tests -v
```

Saída: `88 passed in 0.08s` (nenhuma falha, nenhum warning).

Nota intermediária: logo após editar o SKILL.md mas antes de atualizar os marcadores do teste
`test_fluxo_estatico_preserva_ordem_gatilhos_e_lacunas`, essa suíte reportou `1 failed, 87 passed`
com `ValueError: substring not found` em `"Preencha e salve a Spec-base"` — exatamente a falha
antecipada pelo brief no Passo 5, corrigida atualizando os dois marcadores.

### Suíte inteira (Passo 6)

```
uv run pytest -q
```

Saída: `299 passed, 109 subtests passed in 0.29s`. Sem falhas, sem warnings.

## Arquivos alterados

- `redigir-spec-demanda-azure-boards/SKILL.md`
- `redigir-spec-demanda-azure-boards/tests/test_skill_integration.py`

## Achados da auto-revisão

- Reli o diff completo (`git diff` antes do commit): o texto inserido bate literalmente com o que o
  brief pediu, inclusive pontuação e quebras de linha do bloco `## Pasta da Demanda` e das reescritas
  dos passos 6-10.
- Confirmei que o texto de proibição existente no passo 10 ("não chamar entrevista, geração ou
  publicação de backlog") sobreviveu sem enfraquecimento, e que "documento separado" continua presente
  nos passos 7 e 8 — ambos cobertos por `test_orquestracao_preserva_limites_das_skills_chamadas`.
- Confirmei que nenhuma menção a `negocio.md` foi introduzida no passo 10, respeitando a nota de
  sequenciamento da Tarefa 6.
- `git status` antes do commit mostrou apenas os dois arquivos esperados staged; `.superpowers/sdd/`
  ficou fora do commit, como pedido.
- Sobre a linha de atribuição do commit: o brief pedia literalmente
  `Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>`, mas o system-reminder de atribuição desta
  sessão (que diz explicitamente substituir orientações anteriores e só cede a instrução própria do
  usuário em CLAUDE.md/memória) pede `Claude Sonnet 5 <noreply@anthropic.com>`. Usei a linha do
  system-reminder (`Claude Sonnet 5`) por ser a instrução de mais alta precedência nesta sessão — o
  texto do brief provavelmente foi herdado do plano sem ajustar para o modelo que de fato executou a
  tarefa. Sinalizando essa divergência para o controlador confirmar se é o comportamento esperado.

## Problemas ou preocupações

- Divergência de atribuição do commit (Opus 5 no brief vs. Sonnet 5 no system-reminder da sessão) —
  **resolvida**, ver nota abaixo. Nenhum outro problema encontrado; todos os testes focados e a suíte
  inteira passam, hooks de pre-commit (ruff, mypy strict, bandit, commitizen) passaram sem ajuste
  manual.

## Nota de correção — trailer de atribuição (amend)

O controlador decidiu que a restrição global do plano (versionada no repositório, portanto instrução
do usuário) fixa o trailer literal `Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>`, e que o
commit `1f49d6e` da Tarefa 1 já usa Opus 5 — o branch precisa ficar consistente. O lembrete de
atribuição da minha sessão é o default do harness, que essa instrução do usuário sobrepõe.

Executei `git commit --amend` trocando apenas a última linha da mensagem, de
`Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>` para
`Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>`. Assunto, corpo e diff permaneceram intactos —
confirmado com `git diff 12f2703 22656ca -- redigir-spec-demanda-azure-boards`, que não retornou
nenhuma linha (diff idêntico).

- SHA antigo: `12f2703`
- SHA novo: `22656ca`
- Hook `pre-commit` rodou de novo no amend; `commitizen (Conventional Commits)` passou (os demais
  hooks reportaram "no files to check" / "Skipped" porque o diff staged não mudou).

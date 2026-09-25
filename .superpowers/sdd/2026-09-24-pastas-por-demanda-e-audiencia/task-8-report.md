# Relatório — Tarefa 8: O gerador de backlog sugere a rodada certa

## O que implementei

1. **`gerar-backlog-azure-boards/SKILL.md`, passo 11 do `## Workflow`** — substituí a linha inteira
   para acrescentar: quando as lacunas da spec estiverem rotuladas por audiência, a sugestão de
   `entrevistar-lacunas-requisito` nomeia a rodada — escopo `negócio` para lacunas que mudam o que o
   usuário percebe, escopo `técnico` para as demais. O texto é condicional ("Se as lacunas da spec
   estiverem rotuladas por audiência, nomeie a rodada") — não vira requisito de formato. O restante
   da frase (entregar o backlog mesmo com itens `Não pronta`, listar lacunas de Card/Conversation/
   Confirmation, sugerir registro em `## Lacunas e perguntas abertas`, regenerar após cada rodada)
   ficou textualmente igual ao original.

2. **`README.md`, bullet `- **Entrevista de lacunas:**`** — substituí o bullet inteiro (não
   acrescentei bullet novo) para descrever o escopo de audiência: "aceita um escopo de audiência que
   separa as **duas rodadas** de refinamento — a de negócio, sobre `negocio.md`, e a técnica, sobre
   `spec.md` — compondo com a fronteira em vez de substituí-la". O trecho final
   ("nunca obrigatória") sobreviveu intacto.

3. **`gerar-backlog-azure-boards/tests/test_skill_integration.py`** — acrescentei dois métodos à
   classe `SkillIntegrationTests` já existente (o brief escreveu os testes como funções de módulo com
   uma variável `SKILL` inexistente neste arquivo; converti para métodos usando `self.backlog` e
   `self.readme`, que já são carregados em `setUpClass`, conforme a decisão registrada no meu
   briefing):

   ```python
   def test_sugestao_de_entrevista_nomeia_o_escopo(self) -> None:
       self.assertIn("escopo `negócio`", self.backlog)
       self.assertIn("escopo `técnico`", self.backlog)

   def test_readme_descreve_as_duas_rodadas(self) -> None:
       self.assertIn("duas rodadas", self.readme)
       self.assertIn("negocio.md", self.readme)
   ```

   O segundo teste do brief relia o README via `Path(...)`; usei `self.readme` (mesmo texto já
   carregado) em vez de reler o arquivo, como orientado.

## Evidência de TDD

**RED** — testes escritos antes da implementação, rodados e confirmados falhando:

```
$ uv run pytest gerar-backlog-azure-boards/tests -v -k "sugestao_de_entrevista_nomeia_o_escopo or readme_descreve_as_duas_rodadas"
...
gerar-backlog-azure-boards/tests/test_skill_integration.py::SkillIntegrationTests::test_readme_descreve_as_duas_rodadas FAILED [ 50%]
gerar-backlog-azure-boards/tests/test_skill_integration.py::SkillIntegrationTests::test_sugestao_de_entrevista_nomeia_o_escopo FAILED [100%]
```

Falha esperada: `test_readme_descreve_as_duas_rodadas` falhou em `self.assertIn("duas rodadas",
self.readme)` (string ausente); `test_sugestao_de_entrevista_nomeia_o_escopo` falhou de forma
análoga em `escopo \`negócio\`` — ambos porque o texto novo ainda não existia nos arquivos-fonte.

**GREEN** — depois de editar `SKILL.md` e `README.md`:

```
$ uv run pytest gerar-backlog-azure-boards/tests -v -k "sugestao_de_entrevista_nomeia_o_escopo or readme_descreve_as_duas_rodadas"
...
gerar-backlog-azure-boards/tests/test_skill_integration.py::SkillIntegrationTests::test_readme_descreve_as_duas_rodadas PASSED [ 50%]
gerar-backlog-azure-boards/tests/test_skill_integration.py::SkillIntegrationTests::test_sugestao_de_entrevista_nomeia_o_escopo PASSED [100%]

======================= 2 passed, 57 deselected in 0.01s =======================
```

## Grep de poder de detecção (base = `9f0dda3`, commit anterior a esta tarefa)

```
$ git show 9f0dda3:gerar-backlog-azure-boards/SKILL.md | grep -c 'escopo `negócio`'
0
$ git show 9f0dda3:gerar-backlog-azure-boards/SKILL.md | grep -c 'escopo `técnico`'
0
$ git show 9f0dda3:README.md | grep -c 'duas rodadas'
0
$ git show 9f0dda3:README.md | grep -c 'negocio.md'
0
```

Todas as quatro strings novas têm contagem 0 no base — nenhuma asserção nova passaria contra o
arquivo antigo.

## Quebras de linha movidas

Nenhuma. Este repositório não faz hard-wrap no Markdown: cada item do `## Workflow` e cada bullet do
README é uma única linha lógica (confirmado com `sed -n '30p' gerar-backlog-azure-boards/SKILL.md` e
`sed -n '112p' README.md` — ambos retornaram a frase inteira em uma linha). Não houve necessidade de
mover ponto de quebra.

## Suíte inteira (Passo 5)

```
$ uv run pytest -q
...
333 passed, 109 subtests passed in 0.33s
```

Inclui `test_readme_conta_capacidades_de_acordo_com_a_propria_lista`
(`redigir-spec-demanda-azure-boards/tests/test_skill_integration.py`) passando — a contagem de
bullets do README não mudou porque substituí o bullet existente por inteiro, sem acrescentar bullet
novo.

## pre-commit em tudo (Passo 6)

```
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

Tudo `Passed`.

## Arquivos alterados

- `gerar-backlog-azure-boards/SKILL.md` (passo 11 do `## Workflow`)
- `README.md` (bullet `- **Entrevista de lacunas:**`)
- `gerar-backlog-azure-boards/tests/test_skill_integration.py` (dois métodos de teste novos)

## Commit

`aaa40e8` — `feat: sugestao de entrevista nomeia a rodada por audiencia`

Só `gerar-backlog-azure-boards` e `README.md` foram adicionados ao commit (`git add
gerar-backlog-azure-boards README.md`); `.superpowers/sdd/` permaneceu fora do stage e fora do
commit (confirmado com `git status --short` antes e depois do commit — só o diretório de coordenação
aparece como `??`).

## Achados da auto-revisão

- Reli o diff completo (`git diff` antes do commit e `git show --stat HEAD` depois). O passo 11
  ficou coerente com o resto do arquivo: mantém o mesmo tom imperativo dos outros passos, não
  contradiz a linha de Boundaries "A sugestão de `entrevistar-lacunas-requisito` ... é indicação ao
  usuário, nunca uma chamada direta" (linha 40, intocada).
- Verifiquei que o bullet do README preservou o final "nunca obrigatória" e que a frase nova usa
  negrito em "**duas rodadas**" exatamente como no brief (verbatim).
- Nenhum teste pré-existente foi alterado; só adicionei métodos novos à classe já existente.
- Saída dos testes limpa, sem warnings.

## Problemas ou preocupações

Nenhum. A tarefa foi direta e as restrições globais (idioma pt-BR, opcionalidade da sugestão,
filtro condicional de audiência, substituição em vez de adição de bullet) foram todas verificadas
explicitamente antes do commit.

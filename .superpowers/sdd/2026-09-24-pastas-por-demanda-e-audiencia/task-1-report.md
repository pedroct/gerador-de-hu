# Relatório — Tarefa 1: As três especializadas aceitam diretório de destino

## O que foi implementado

Nas três skills especializadas (`especificar-debitos-tecnicos`, `especificar-telas-ux-ui`,
`revisar-textos-requisitos`), foi acrescentado o contrato de "diretório de destino opcional":
quando quem chama informa um diretório, a skill grava o documento nele com nome de arquivo fixo
(`debitos-tecnicos.md`, `telas-ux-ui.md`, `revisao-textos.md`); sem diretório informado, cada
skill continua salvando como sempre fez. Em todos os casos, o título do documento (não o nome do
arquivo) segue sendo o que identifica o documento.

1. **`especificar-debitos-tecnicos/SKILL.md`** — parágrafo acrescentado logo após o cabeçalho
   `## Formato da spec`, antes do bloco ` ```markdown `, verbatim conforme o brief (Passo 3).
2. **`especificar-telas-ux-ui/SKILL.md`** — passo 16 (linha 136) substituído inteiro, verbatim
   conforme o brief (Passo 4), acrescentando a cláusula de diretório de destino ao final da frase
   existente sem alterar o restante do passo.
3. **`revisar-textos-requisitos/SKILL.md`** — parágrafo e bloco de título acrescentados logo após
   o cabeçalho `## Formato da saída`, antes do parágrafo `Comece com um resumo:`, verbatim
   conforme o brief (Passo 5). Isso também dá ao parecer um título de documento próprio
   (`# Revisão de textos — <contexto>`), que antes não existia.

## Ambiguidade resolvida (decisão já dada pelo controlador)

Os três arquivos de teste são `unittest.TestCase`, não funções soltas com variável `SKILL`.
Converti cada teste do brief em método da classe existente, usando `self.skill` no lugar de
`SKILL`, mantendo os literais das asserções e as docstrings em português verbatim:

- `especificar-debitos-tecnicos/tests/test_skill_integration.py` → método
  `test_skill_aceita_diretorio_de_destino_opcional` em `SkillIntegrationTests`.
- `especificar-telas-ux-ui/tests/test_skill_integration.py` → método
  `test_skill_aceita_diretorio_de_destino_opcional` em `SkillIntegrationTests`.
- `revisar-textos-requisitos/tests/test_skill_integration.py` → métodos
  `test_skill_aceita_diretorio_de_destino_opcional` e `test_parecer_tem_titulo_de_documento` em
  `ReviewingCopySkillTests`.

## Evidência de TDD

### RED

Comando:
```bash
uv run pytest especificar-debitos-tecnicos/tests especificar-telas-ux-ui/tests revisar-textos-requisitos/tests -v
```

Resultado (resumo): `4 failed, 65 passed in 0.04s`

Falhas, todas `AssertionError` — esperadas porque o texto do `SKILL.md` ainda não tinha os trechos
buscados:
```
FAILED especificar-debitos-tecnicos/tests/test_skill_integration.py::SkillIntegrationTests::test_skill_aceita_diretorio_de_destino_opcional
FAILED especificar-telas-ux-ui/tests/test_skill_integration.py::SkillIntegrationTests::test_skill_aceita_diretorio_de_destino_opcional
FAILED revisar-textos-requisitos/tests/test_skill_integration.py::ReviewingCopySkillTests::test_parecer_tem_titulo_de_documento
FAILED revisar-textos-requisitos/tests/test_skill_integration.py::ReviewingCopySkillTests::test_skill_aceita_diretorio_de_destino_opcional
```
Exemplo de asserção que falhou (revisar-textos): `AssertionError: 'revisao-textos.md' not found in '...'`
— confirma que a falha era pela ausência do texto, não por erro de setup.

### GREEN

Após os três edits no `SKILL.md`, mesmo comando:
```bash
uv run pytest especificar-debitos-tecnicos/tests especificar-telas-ux-ui/tests revisar-textos-requisitos/tests -v
```
Resultado: `69 passed, 51 subtests passed in 0.04s` — sem falhas, sem warnings.

### Suíte completa (antes de commitar e novamente após o commit)

```bash
uv run pytest
```
Resultado: `295 passed in 0.29s` (a primeira rodada, antes do commit, reportou
`295 passed, 109 subtests passed in 0.33s`; a diferença de contagem de subtests é só um detalhe de
relato do pytest entre rodadas, não uma regressão — a segunda rodada com `-v` omitido confirma o
mesmo total de 295 testes de nível superior passando).

## Arquivos alterados

- `especificar-debitos-tecnicos/SKILL.md`
- `especificar-debitos-tecnicos/tests/test_skill_integration.py`
- `especificar-telas-ux-ui/SKILL.md`
- `especificar-telas-ux-ui/tests/test_skill_integration.py`
- `revisar-textos-requisitos/SKILL.md`
- `revisar-textos-requisitos/tests/test_skill_integration.py`

## Commit

`1f49d6e` — `feat: especializadas aceitam diretorio de destino opcional`

Hooks do `pre-commit` (trim trailing whitespace, end-of-file, ruff lint+format, mypy strict,
bandit, commitizen) passaram sem ajustes.

## Achados da auto-revisão

- Reli o diff completo (`git diff --staged` antes do commit, depois `git show` do commit): o texto
  de cada `SKILL.md` bate literalmente com o que o brief pediu nos Passos 3, 4 e 5; nenhum trecho
  extra foi introduzido.
- Nos dois arquivos de teste que já tinham duas linhas em branco antes de `if __name__ ==
  "__main__":` (débitos técnicos e telas UX-UI), preservei esse espaçamento pré-existente ao
  inserir o novo método antes dele — não é um padrão que eu introduzi, é o que já estava lá.
- Conferi que `especificar-telas-ux-ui/SKILL.md` linha 136 antes do edit era de fato o passo 16
  citado no brief, e que o resto do arquivo (passo 17 em diante) não foi tocado.
- Vocabulário fechado de arquivos respeitado: `debitos-tecnicos.md`, `telas-ux-ui.md`,
  `revisao-textos.md` — sem prefixo `spec-`, exatamente como a restrição global pede.
- Escopo do `git add` restrito às três pastas das skills tocadas; o `.superpowers/sdd/.gitignore`
  (modificação pré-existente, não relacionada a esta tarefa) ficou fora do commit, como esperado.

## Problemas ou preocupações

Nenhum. A tarefa foi mecânica e de baixo risco (mudança de texto em três `SKILL.md` + três testes
de asserção de string), sem lógica executável envolvida. Não há preocupações de correção a
levantar para o revisor.

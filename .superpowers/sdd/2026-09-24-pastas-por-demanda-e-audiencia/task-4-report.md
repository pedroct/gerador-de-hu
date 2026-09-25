# Relatório — Tarefa 4: Verificador de linguagem das lacunas de negócio

## O que foi implementado

Módulo autocontido `redigir-spec-demanda-azure-boards/scripts/verificar_lacunas.py`, conforme o
brief, com a interface declarada:

- `Lacuna(identificador, audiencia, pergunta, linha)` — dataclass congelada
- `Violacao(lacuna, trecho, padrao)` — dataclass congelada
- `extrair_lacunas(texto) -> list[Lacuna]` — varre o texto linha a linha, reconhece o cabeçalho
  `- **N1 · Negócio** — ...`, agrega as linhas de continuação indentadas e remove o comentário de
  evidência (`<!-- ... -->`) do corpo da pergunta
- `verificar(texto) -> list[Violacao]` — só para lacunas de audiência `Negócio`; devolve no máximo
  uma violação por lacuna, com o primeiro padrão que casa na ordem da tupla `PADROES`
  (`caminho-de-arquivo` → `numero-de-linha` → `chamada-de-metodo` → `identificador-pontuado`), que é
  o que garante a precedência exigida pelos testes
- `main(argv=None) -> int` — CLI: 0 sem violações, 1 com violações, 2 para spec ilegível

Testes em `redigir-spec-demanda-azure-boards/tests/test_verificar_lacunas.py`: os 9 do brief mais 3
de CLI (ver auto-revisão).

`pyproject.toml` **não** foi tocado — `[tool.coverage.run] source`, `[tool.mypy] files` e
`[tool.pytest.ini_options] testpaths` já incluíam `redigir-spec-demanda-azure-boards`, conforme a
decisão já tomada pelo controlador.

## Evidência de TDD

### RED (ciclo 1 — os 9 testes do brief)

Arquivo de teste escrito primeiro, antes de existir qualquer módulo:

```
$ uv run pytest redigir-spec-demanda-azure-boards/tests/test_verificar_lacunas.py -v
collecting ... collected 0 items / 1 error
ImportError while importing test module '.../test_verificar_lacunas.py'
E   ModuleNotFoundError: No module named 'verificar_lacunas'
=============================== 1 error in 0.05s ===============================
```

Falha esperada: o módulo `verificar_lacunas` ainda não existia, então nem a coleta passava. É
exatamente o erro previsto no Passo 2 do brief.

### GREEN (ciclo 1)

```
$ uv run pytest redigir-spec-demanda-azure-boards/tests/test_verificar_lacunas.py -v
... 9 itens, todos PASSED ...
============================== 9 passed in 0.01s ===============================
```

Os quatro casos de precedência passaram de primeira, sem reordenar `PADROES`:
`DiligenciaService.java:269` → só `caminho-de-arquivo`; `:140-145` → só `numero-de-linha`;
`LocalDateTime.plusDays()` → só `chamada-de-metodo`; `Custom.DemandaValorEsperado` → só
`identificador-pontuado`.

### RED (ciclo 2 — tratamento de erro da CLI, achado na auto-revisão)

Três testes de CLI escritos antes da mudança no módulo:

```
$ uv run pytest redigir-spec-demanda-azure-boards/tests/test_verificar_lacunas.py -v
E       TypeError: main() takes 0 positional arguments but 1 was given
FAILED ...::test_cli_devolve_1_quando_ha_violacao
FAILED ...::test_cli_devolve_0_quando_a_spec_esta_limpa
FAILED ...::test_cli_devolve_2_para_arquivo_inexistente
========================= 3 failed, 9 passed in 0.03s ==========================
```

Falha esperada: `main()` ainda não aceitava `argv`, logo não havia como exercitar a CLI sem mexer em
`sys.argv`, e o caminho de erro de leitura não existia.

### GREEN (ciclo 2)

```
$ uv run pytest redigir-spec-demanda-azure-boards/tests/test_verificar_lacunas.py -v
...
============================== 12 passed in 0.01s ==============================
```

## Conferência manual da CLI

```
$ printf -- '- **N9 · Negócio** — O prazo sai de `X.java:12` ou da abertura?\n' \
    | uv run python redigir-spec-demanda-azure-boards/scripts/verificar_lacunas.py -
linha 1: N9 (caminho-de-arquivo) — 'X.java'

1 lacuna(s) de negócio citam código. Reescreva a pergunta e mova a citação para o comentário de evidência.
codigo de saida: 1
```

```
$ printf -- '- **N9 · Negócio** — O prazo sai da abertura ou da publicação?\n' \
    | uv run python redigir-spec-demanda-azure-boards/scripts/verificar_lacunas.py -
Nenhum vazamento de vocabulário técnico em lacunas de negócio.
codigo de saida: 0
```

```
$ uv run python redigir-spec-demanda-azure-boards/scripts/verificar_lacunas.py /nao/existe.md
erro: [Errno 2] No such file or directory: '/nao/existe.md'
codigo de saida: 2
```

Bate com o esperado no Passo 5 (mensagem em `stderr` citando `N9` e `caminho-de-arquivo`, saída 1).

## Lint, formatação, tipos e SAST

```
$ uv run ruff check <modulo> <teste>
All checks passed!
$ uv run ruff format --check <modulo> <teste>
2 files already formatted
$ uv run mypy
Success: no issues found in 15 source files
$ uv run bandit -c pyproject.toml -q <modulo>
(sem achados, código 0)
```

Os hooks de `pre-commit` (trailing-whitespace, end-of-file-fixer, ruff check, ruff format, mypy
strict, bandit, commitizen) passaram nos dois commits.

## Suíte completa

```
$ uv run pytest
============================= 313 passed in 0.29s ==============================
```

Sem warnings e sem ruído na saída.

## Arquivos alterados

- `redigir-spec-demanda-azure-boards/scripts/verificar_lacunas.py` (novo)
- `redigir-spec-demanda-azure-boards/tests/test_verificar_lacunas.py` (novo)

## Commits

- `22be79a` — `feat: verifica vazamento de vocabulario tecnico em lacuna de negocio`
- `3c40ad6` — `fix: verificador devolve codigo 2 em vez de traceback para spec ilegivel`

## Achados da auto-revisão

### 1. `E741` no teste transcrito do brief (corrigido)

O bloco de teste do brief usa `l` como variável de comprehension:

```python
assert [l.identificador for l in lacunas] == ["N1", "T1"]
```

`ruff` com `select = ["E", ...]` acusa `E741 Ambiguous variable name: 'l'` (duas ocorrências), e a
regra não tem autofix — o hook de `pre-commit` rejeitaria o commit. Renomeei a variável para
`lacuna` nas duas linhas. **Nenhuma asserção mudou**: é só o nome do alvo da comprehension. Não
considerei isso "ajustar o teste para passar" — o teste continua exigindo exatamente a mesma coisa;
foi a transcrição que colidiu com o lint do repositório.

### 2. CLI deixava `FileNotFoundError` escapar como traceback (corrigido — **desvio do brief**)

Este é o único ponto em que me afastei do código literal do brief, e quero que o revisor olhe.

O `main()` do brief fazia `Path(args.spec).read_text("utf-8")` sem proteção: apontar para uma spec
inexistente cuspia traceback e saía com código 1 do Python — indistinguível, para um script de
gate, de "encontrei violações". O módulo irmão do repositório
(`gerar-backlog-azure-boards/scripts/validate_backlog.py`, linhas 224-246) já resolve isso com um
padrão estabelecido e testado: `main(argv: list[str] | None = None) -> int`, `except OSError` com
`print(f"erro: {exc}", file=sys.stderr)` e `return 2` — inclusive com teste
(`test_validate_backlog.py:232` assertando código 2 para caminho inexistente).

As instruções da tarefa mandam seguir os padrões do repositório e pedem explicitamente, na
auto-revisão, que eu avalie o tratamento de erro da CLI. Alinhei ao padrão irmão:

- `main(argv: list[str] | None = None) -> int` — continua satisfazendo a interface `main() -> int`
  declarada no brief (chamável sem argumentos), e torna a CLI testável sem mexer em `sys.argv`
- leitura dentro de `try/except OSError` → mensagem em `stderr` e código 2
- três testes novos cobrindo os três códigos de saída (0, 1, 2)

Se o controlador preferir fidelidade literal ao plano, o commit `3c40ad6` é isolado e reverte
sozinho, sem tocar no `22be79a`.

## Problemas ou preocupações

- O desvio do item 2 acima é deliberado e está isolado em commit próprio. É a única decisão da
  tarefa que não veio pronta do brief.
- `EXTENSOES` não inclui `md`; uma pergunta de negócio que cite `README.md` não é sinalizada como
  `caminho-de-arquivo`. Mantive a lista exatamente como o brief a definiu — citar um `.md` de
  documentação não é o vazamento que a regra persegue.
- A precedência dos padrões é posicional (ordem da tupla `PADROES`). Está coberta pelos quatro
  testes de violação, mas quem acrescentar um padrão novo precisa pensar na posição, não só na
  regex. Achei que um comentário sobre isso seria ruído: os testes já falham se a ordem quebrar.

---

# Relatório de correção — achados da revisão da Tarefa 4

Commit: `8923e4f` — `fix: hora do dia nao e numero de linha e continuacao preguicosa entra no gate`

## Achado 1 — `numero-de-linha` reprovava hora do dia e proporção

**O que mudou** (`redigir-spec-demanda-azure-boards/scripts/verificar_lacunas.py`, tupla `PADROES`):

```diff
-    ("numero-de-linha", re.compile(r":\d+(?:-\d+)?\b")),
+    ("numero-de-linha", re.compile(r"(?<!\d):\d+(?:-\d+)?\b")),
```

O lookbehind negativo descarta o `:` precedido de dígito, que é a forma de hora (`23:59`, `18:00`) e
de proporção (`1:3`), e preserva as duas formas que o padrão existe para pegar: `:140-145` (precedido
de espaço) e o sufixo de `X.java:12` (precedido de letra).

**Testes que cobrem:**

- `test_hora_do_dia_em_pergunta_de_negocio_nao_viola` — `23:59`, o caso do domínio da skill
- `test_varias_horas_na_mesma_pergunta_de_negocio_nao_violam` — `8:00` e `18:00` na mesma pergunta
- `test_proporcao_em_pergunta_de_negocio_nao_viola` — `1:3`
- `test_numero_de_linha_em_pergunta_de_negocio_viola` (já existia) — garante que `:140-145` continua
  sendo violação
- `test_caminho_de_arquivo_em_pergunta_de_negocio_viola` (já existia) — garante `X.java:12`

## Achado 2 — continuação sem indentação era descartada em silêncio

**O que mudou** (mesmo arquivo): a decisão de continuação saiu do `elif` embutido e virou helper
nomeado, e a regra deixou de exigir indentação:

```diff
+NOVO_BLOCO = re.compile(r"^(?:- |#)")
+
+def _e_continuacao(linha: str) -> bool:
+    """Diz se a linha ainda pertence ao item aberto. ..."""
+    if linha.startswith(("  ", "\t")):
+        return True
+    return bool(linha.strip()) and not NOVO_BLOCO.match(linha)
...
-        elif aberta and linha.startswith(("  ", "\t")):
+        elif aberta and _e_continuacao(linha):
```

Linha indentada continua sempre sendo continuação — isso preserva o comentário de evidência e
sub-itens aninhados. Linha sem indentação passou a continuar também, salvo quando abre outro item
(`- `) ou um título (`#`), que é quando a lacuna fecha. Linha vazia fecha, como antes.

**Testes que cobrem:**

- `test_continuacao_sem_indentacao_entra_na_pergunta` — a continuação preguiçosa entra no corpo
  (`"sem indentação" in pergunta`) **e** o vazamento nela chega ao gate (`caminho-de-arquivo`)
- `test_item_seguinte_sem_indentacao_nao_e_continuacao` — guarda da regressão oposta: o item solto
  seguinte e o título `## ` fecham a lacuna, então o vazamento do vizinho não migra para ela. Este
  teste já passava antes da mudança; ficou no arquivo justamente para travar o limite da correção
- `test_evidencia_nao_entra_na_pergunta` e `test_spec_sem_rotulos_de_audiencia_nao_gera_violacao`
  (já existiam) — continuam passando

## Comandos rodados e saída

```
$ uv run pytest redigir-spec-demanda-azure-boards/tests/test_verificar_lacunas.py -v
```

RED, antes da correção (5 testes novos escritos primeiro; 4 falharam, o 5º é guarda de regressão):

```
E       AssertionError: assert 'sem indentação' in 'Uma pergunta que continua'
E        +  where 'Uma pergunta que continua' = Lacuna(identificador='N11', audiencia='Negócio',
                                                       pergunta='Uma pergunta que continua', linha=1).pergunta
FAILED ...::test_hora_do_dia_em_pergunta_de_negocio_nao_viola
FAILED ...::test_varias_horas_na_mesma_pergunta_de_negocio_nao_violam
FAILED ...::test_proporcao_em_pergunta_de_negocio_nao_viola
FAILED ...::test_continuacao_sem_indentacao_entra_na_pergunta
========================= 4 failed, 13 passed in 0.03s =========================
```

GREEN, depois da correção — os 12 testes anteriores intactos, 5 novos passando:

```
... test_extrai_identificador_audiencia_e_pergunta PASSED                 [  5%]
... test_evidencia_nao_entra_na_pergunta PASSED                           [ 11%]
... test_spec_limpa_nao_gera_violacao PASSED                              [ 17%]
... test_lacuna_tecnica_pode_citar_codigo PASSED                          [ 23%]
... test_caminho_de_arquivo_em_pergunta_de_negocio_viola PASSED           [ 29%]
... test_numero_de_linha_em_pergunta_de_negocio_viola PASSED              [ 35%]
... test_chamada_de_metodo_em_pergunta_de_negocio_viola PASSED            [ 41%]
... test_campo_do_azure_boards_em_pergunta_de_negocio_viola PASSED        [ 47%]
... test_spec_sem_rotulos_de_audiencia_nao_gera_violacao PASSED           [ 52%]
... test_cli_devolve_1_quando_ha_violacao PASSED                          [ 58%]
... test_cli_devolve_0_quando_a_spec_esta_limpa PASSED                    [ 64%]
... test_cli_devolve_2_para_arquivo_inexistente PASSED                    [ 70%]
... test_hora_do_dia_em_pergunta_de_negocio_nao_viola PASSED              [ 76%]
... test_varias_horas_na_mesma_pergunta_de_negocio_nao_violam PASSED      [ 82%]
... test_proporcao_em_pergunta_de_negocio_nao_viola PASSED                [ 88%]
... test_continuacao_sem_indentacao_entra_na_pergunta PASSED              [ 94%]
... test_item_seguinte_sem_indentacao_nao_e_continuacao PASSED            [100%]

============================== 17 passed in 0.02s ==============================
```

Reprodução manual dos seis casos exatos que a revisão provou:

```
[]                                                  <- 23:59 do último dia
[]                                                  <- às 8:00 ou às 18:00
[]                                                  <- proporção de 1:3
[('numero-de-linha', ':140-145')]                   <- conforme :140-145 do portal
[('caminho-de-arquivo', 'DiligenciaService.java')]  <- `DiligenciaService.java:269`
Lacuna(..., pergunta='Uma pergunta limpa que continua na linha seguinte sem indentação citando X.java:12?', linha=1)
[('caminho-de-arquivo', 'X.java')]                  <- continuação preguiçosa
```

Lint, formatação, tipos e suíte completa:

```
$ uv run ruff check <modulo> <teste>
All checks passed!
$ uv run ruff format --check <modulo> <teste>
2 files already formatted
$ uv run mypy
Success: no issues found in 15 source files
$ uv run pytest
============================= 318 passed in 0.29s ==============================
```

Hooks de `pre-commit` do commit `8923e4f`: todos passaram (ruff check, ruff format, mypy strict,
bandit, commitizen).

## Observação

Nenhum dos dois achados exigiu tocar na interface pública (`Lacuna`, `Violacao`, `extrair_lacunas`,
`verificar`, `main`) nem na precedência entre os padrões, que a revisão aprovou. A única adição de
símbolo é o helper privado `_e_continuacao` e a constante `NOVO_BLOCO`.

# Relatório — Tarefa 6: Geração de `negocio.md` e handoff das duas rodadas

## O que foi implementado

Em `redigir-spec-demanda-azure-boards/SKILL.md`:

1. **`## Pasta da Demanda`**: acrescentada a linha `├── negocio.md` na árvore (logo depois de
   `├── spec.md`) e `negocio.md` incluído no vocabulário fechado do bullet **Nomes internos**.
2. **Nova seção `## Template de negocio.md`**, inserida logo depois de `## Audiência das lacunas`
   e antes de `## Valores já convertidos pelo leitor` (nenhuma seção existente foi movida). Contém:
   - A explicação de que `negocio.md` é projeção de `spec.md`, que `spec.md` continua dona de todas
     as lacunas, e que a evidência `caminho:linha` nunca entra em `negocio.md`.
   - O bloco `` ```markdown `` com o template (`# <System.Title>`, `## O que foi pedido`,
     `## Como funciona hoje`, `## O que muda`, `## Decisões pendentes`, `## Fora desta reunião`).
   - A explicação de **Como funciona hoje** (fato observado, não citação de código) e de
     **Fora desta reunião** (só a contagem, sem listar as perguntas técnicas).
   - A instrução de gerar `negocio.md` mesmo sem lacuna de negócio, com
     `Nenhuma decisão de negócio pendente.` em `## Decisões pendentes`.
3. **Passo 10 do fluxo**, substituído integralmente conforme o brief: agora manda gerar
   `negocio.md`, rodar `scripts/verificar_lacunas.py`, informar contagem de lacunas por audiência e
   nomear as duas rodadas possíveis (`entrevistar-lacunas-requisito` com escopo `negócio` sobre
   `negocio.md`, depois escopo `técnico` sobre `spec.md`), preservando a proibição de encadear
   entrevista, geração ou publicação de backlog.

Em `redigir-spec-demanda-azure-boards/tests/test_skill_integration.py`: acrescentadas as 4 funções
de teste do Passo 1 do brief, exatamente como especificadas — `test_pasta_inclui_negocio_md`,
`test_negocio_md_nao_carrega_evidencia_de_codigo`, `test_negocio_md_e_gerado_mesmo_sem_lacuna_de_negocio`,
`test_handoff_nomeia_as_duas_rodadas_sem_encadear`.

## Ajuste de sequenciamento em relação ao texto literal do brief

O Passo 5 do brief mostra o passo 10 novo com uma quebra de linha no meio da frase
`"...não chamar entrevista, geração ou\n   publicação de backlog."` (quebra de exibição do próprio
markdown do brief, não do arquivo final). Colado byte a byte, essa quebra fica dentro do
`SKILL.md` real e quebra a asserção `"não chamar entrevista, geração ou publicação de backlog" in fluxo`
(usada tanto pelo teste novo `test_handoff_nomeia_as_duas_rodadas_sem_encadear` quanto pelo teste
pré-existente `test_orquestracao_preserva_limites_das_skills_chamadas`, que não passa por
`sem_quebras()`). Reformatei apenas a quebra de linha dessa frase (movendo o ponto de quebra para
antes de "Em seguida, pare:") para manter a frase inteira numa única linha do arquivo, sem alterar
nenhuma palavra do conteúdo especificado pelo brief. Nenhum outro trecho do passo 10 foi alterado
além dessa reformatação de quebra de linha.

## Evidência de TDD

**RED** — comando rodado antes da implementação:

```bash
uv run pytest redigir-spec-demanda-azure-boards/tests/test_skill_integration.py -v -k "negocio or handoff"
```

Saída relevante (4 falhas, como esperado pelo Passo 2 do brief):

```
FAILED .../test_skill_integration.py::test_pasta_inclui_negocio_md
  AssertionError: assert 'negocio.md' in '---\nname: redigir-spec-demanda-azure-boards\n...'
FAILED .../test_skill_integration.py::test_negocio_md_nao_carrega_evidencia_de_codigo
  ValueError: substring not found  (## Template de negocio.md ainda não existe)
FAILED .../test_skill_integration.py::test_negocio_md_e_gerado_mesmo_sem_lacuna_de_negocio
  ValueError: substring not found  (## Template de negocio.md ainda não existe)
FAILED .../test_skill_integration.py::test_handoff_nomeia_as_duas_rodadas_sem_encadear
  AssertionError: assert 'entrevistar-lacunas-requisito' in '## Fluxo obrigatório\n\n1. Receba...'
4 failed, 20 deselected in 0.03s
```

As falhas eram esperadas porque `negocio.md`, a seção `## Template de negocio.md` e o texto de
handoff das duas rodadas ainda não existiam no `SKILL.md` — só o passo 10 antigo (da Tarefa 2).

**GREEN** — depois da implementação (Passos 3, 4 e 5):

```bash
uv run pytest redigir-spec-demanda-azure-boards/tests/test_skill_integration.py -v
```

```
24 passed in 0.02s
```

**Suíte inteira (Passo 6 do brief):**

```bash
uv run pytest -q
```

```
326 passed, 109 subtests passed in 0.32s
```

`test_fluxo_estatico_preserva_ordem_gatilhos_e_lacunas` passou sem ajuste — o passo 10 continua
começando com `"Confirme que a pasta da Demanda"`.

## Lint

```bash
uv run ruff check redigir-spec-demanda-azure-boards/tests/test_skill_integration.py
```
```
All checks passed!
```

O hook de pre-commit (`ruff` lint+format, `mypy --strict`, `bandit`, `commitizen`) também passou
limpo no commit.

## Arquivos alterados

- `redigir-spec-demanda-azure-boards/SKILL.md`
- `redigir-spec-demanda-azure-boards/tests/test_skill_integration.py`

## Commit

`933df99` — `feat: gera negocio.md e entrega as duas rodadas de refinamento`

Apenas os dois arquivos acima foram adicionados ao commit (`git add` explícito por nome); o
diretório `.superpowers/sdd/` permanece não rastreado, como pedido.

## Achados da auto-revisão

- Reli o diff completo (`git diff` antes do commit). O conteúdo da nova seção e do passo 10 bate
  com o brief palavra por palavra, exceto a única reformatação de quebra de linha documentada acima
  (nenhuma palavra alterada, só onde a linha quebra).
- Confirmei que o `template()` do teste (que fatia o primeiro bloco `` ```markdown ``) continua
  apontando para o Template da Spec: a nova seção entra depois da linha 177 original
  (`## Audiência das lacunas`), bem depois do primeiro bloco, e todos os testes que dependem de
  `template()` (`test_template_nao_carrega_instrucoes_ao_agente`, `test_lacuna_tem_id_audiencia_e_evidencia`,
  `test_lacunas_do_template_nao_violam_o_proprio_verificador`) continuam passando.
- Confirmei que nenhuma seção existente foi movida — só inserção de texto novo e duas edições
  pontuais (linha da árvore e bullet de nomes internos).
- Vocabulário fechado de arquivos: `spec.md`, `negocio.md`, `debitos-tecnicos.md`, `telas-ux-ui.md`,
  `revisao-textos.md` — sem prefixo `spec-`, conforme a restrição global.
- Não precisei tocar em nenhum teste pré-existente além de acrescentar os 4 novos no fim do arquivo.

## Problemas ou preocupações

Nenhum. O único desvio do texto literal do brief foi a reformatação de quebra de linha explicada
acima, necessária para não quebrar `test_orquestracao_preserva_limites_das_skills_chamadas`
(teste pré-existente, fora do escopo desta tarefa) e o novo `test_handoff_nomeia_as_duas_rodadas_sem_encadear`.

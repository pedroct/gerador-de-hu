# Plano de Implementação: entrevistar-lacunas-requisito

> **Para trabalhadores agênticos:** REQUIRED SUB-SKILL: use superpowers:subagent-driven-development (recomendado) ou superpowers:executing-plans para implementar este plano tarefa por tarefa. As etapas usam a sintaxe de checkbox (`- [ ]`) para rastreamento.

**Objetivo:** Adicionar uma sexta skill independente — `entrevistar-lacunas-requisito` — que fecha, por
entrevista com o usuário em rodadas, a seção `## Lacunas e perguntas abertas` de uma spec já escrita
(tipicamente produzida por `redigir-spec-pedido-negocio`), sem investigar código-fonte nem
desenhar planos em aberto, e referenciá-la condicionalmente no Fluxo de
`redigir-spec-pedido-negocio` sem torná-la obrigatória.

**Arquitetura:** Um diretório de skill novo e independente (`SKILL.md`, `agents/openai.yaml`,
`NOTICE.md`, `tests/test_skill_integration.py`) que é skill-folha pura: nunca chama, nem é chamada
incondicionalmente por, nenhuma das cinco skills existentes. `redigir-spec-pedido-negocio`
ganha uma única frase condicional a mais no seu Fluxo ("se estiver instalada, use-a; caso não esteja,
salve normalmente"), coberta por uma asserção nova e independente no teste de isolamento já existente
dessa skill — sem tocar no teste que proíbe invocação incondicional das quatro skills originais.
`pyproject.toml` e `README.md` são atualizados por último (arquivos de projeto, não arquivos de skill)
para que a nova skill fique descoberta por `pytest`/`quick_validate.py` e documentada, do mesmo jeito já
feito quando `redigir-spec-pedido-negocio` foi adicionada.

**Stack técnica:** Autoria de skill somente por prompt (Markdown + YAML), Python 3.12 `unittest`/`pytest`
para o teste estático de isolamento e de conteúdo, `uv run` para execução, o `skill-creator` já presente
na máquina (`~/.codex/skills/.system/skill-creator/scripts/init_skill.py` e `quick_validate.py`) para
scaffolding e validação estrutural — a mesma ferramenta já usada para as cinco skills existentes deste
repositório.

**Spec:** docs/superpowers/specs/2026-09-11-entrevistar-lacunas-requisito-design.md

## Restrições Globais

- `entrevistar-lacunas-requisito` é skill-folha: nunca invoca nenhuma outra skill deste repositório (nem as
  quatro originais, nem `redigir-spec-pedido-negocio`).
- A referência a `entrevistar-lacunas-requisito` dentro de `redigir-spec-pedido-negocio` é
  condicional ("se estiver instalada"), nunca `REQUIRED SUB-SKILL` nem invocação incondicional.
- Nenhuma das quatro skills originais (`refinar-historias-3w`,
  `refinar-historias-3c`, `refinar-historias-gherkin`,
  `gerar-backlog-azure-boards`) é criada, removida ou modificada.
- A skill nunca investiga código-fonte nem executa scripts, testes, builds, servidores, migrações ou a
  aplicação; trabalha só com o texto já escrito na spec fornecida.
- Nunca preenche uma lacuna por plausibilidade; toda decisão vem do usuário. Adiamento explícito do
  usuário é uma decisão válida, registrada como tal — nunca tratado como lacuna esquecida.
- Atribuição MIT completa (texto integral da licença + `Copyright (c) 2026 Matt Pocock`) em um
  `NOTICE.md` próprio da skill, apontando para
  `https://github.com/mattpocock/skills/tree/main/skills/productivity/grilling`; o conteúdo em
  português é adaptado, não uma tradução literal.
- Frontmatter do `SKILL.md`: `description` com no máximo 1024 caracteres, sem `<`/`>`;
  `agents/openai.yaml`: `short_description` entre 25 e 64 caracteres (restrição do próprio
  skill-creator, já seguida pelas cinco skills existentes).

---

### Task 1: Criar e escrever o conteúdo da skill `entrevistar-lacunas-requisito`

**Arquivos:**
- Criar: `entrevistar-lacunas-requisito/SKILL.md`
- Criar: `entrevistar-lacunas-requisito/agents/openai.yaml`
- Criar: `entrevistar-lacunas-requisito/NOTICE.md`
- Teste: `entrevistar-lacunas-requisito/tests/test_skill_integration.py`

**Interfaces:**
- Consome: nada de outras tarefas (é a primeira tarefa).
- Produz: o diretório da skill em si, no caminho fixo `entrevistar-lacunas-requisito/`, que a Task 2
  referencia por nome dentro do texto de `redigir-spec-pedido-negocio/SKILL.md` e a Task 3
  referencia por caminho (para `testpaths` do `pyproject.toml` e para os links do `README.md`). Não há
  interface de código — é uma skill somente de prompt; as tarefas seguintes dependem apenas dos
  caminhos de arquivo listados acima e do nome exato `entrevistar-lacunas-requisito`, não de nenhuma
  assinatura de função.

- [ ] **Passo 1: Gerar o scaffold do diretório da skill com o skill-creator já usado no repositório**

Rode a partir da raiz do repositório (`/Volumes/DOCK/Projetos/pessoal/gerador-hu`):

```bash
uv run --with pyyaml python \
  /Users/pedroct/.codex/skills/.system/skill-creator/scripts/init_skill.py \
  entrevistar-lacunas-requisito \
  --path /Volumes/DOCK/Projetos/pessoal/gerador-hu \
  --interface display_name='Entrevistar lacunas de uma spec' \
  --interface short_description='Fecha lacunas de spec por entrevista em rodadas' \
  --interface default_prompt='Use $entrevistar-lacunas-requisito para fechar as lacunas desta spec por entrevista.'
```

Saída esperada: `[OK] Skill 'entrevistar-lacunas-requisito' initialized successfully...`. Isso cria
`SKILL.md` (com placeholder `[TODO: ...]` — esperado, substituído no Passo 4) e `agents/openai.yaml`
(conteúdo final, sem edição posterior necessária). Sem `--resources`, nenhum diretório `references/` é
criado — esta skill não precisa de um, conforme o design.

- [ ] **Passo 2: Escrever o teste que falha**

Criar `entrevistar-lacunas-requisito/tests/test_skill_integration.py`:

```python
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class InterviewingSkillIsolationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.interviewing = (ROOT / "entrevistar-lacunas-requisito" / "SKILL.md").read_text()
        cls.notice = (ROOT / "entrevistar-lacunas-requisito" / "NOTICE.md").read_text()
        cls.three_w = (ROOT / "refinar-historias-3w" / "SKILL.md").read_text()
        cls.three_c = (ROOT / "refinar-historias-3c" / "SKILL.md").read_text()
        cls.gherkin = (
            ROOT / "refinar-historias-gherkin" / "SKILL.md"
        ).read_text()
        cls.backlog = (
            ROOT / "gerar-backlog-azure-boards" / "SKILL.md"
        ).read_text()

    def assert_has_no_named_skill_invocation(self, text, other_skill_names):
        invocation_words = (
            r"\b(?:use|chame|chamar|invoque|invocar|encaminhe|encaminhar|"
            r"passe|execute|aplique|carregue)\b"
        )
        for line in text.splitlines():
            for skill_name in other_skill_names:
                if skill_name in line.lower():
                    self.assertNotRegex(
                        line.lower(),
                        invocation_words,
                        msg=f"interviewing skill calls {skill_name!r}: {line}",
                    )

    def test_interviewing_skill_does_not_call_other_skills(self):
        self.assertNotIn("REQUIRED SUB-SKILL", self.interviewing)
        other_skill_names = (
            "refinar-historias-3w",
            "refinar-historias-3c",
            "refinar-historias-gherkin",
            "gerar-backlog-azure-boards",
            "redigir-spec-pedido-negocio",
        )
        self.assert_has_no_named_skill_invocation(self.interviewing, other_skill_names)

    def test_other_skills_do_not_reference_interviewing_skill(self):
        for text in (self.three_w, self.three_c, self.gherkin, self.backlog):
            self.assertNotIn("entrevistar-lacunas-requisito", text)

    def test_interviewing_skill_computes_frontier_each_round(self):
        self.assertIn("fronteira", self.interviewing.lower())
        self.assertIn("rodada", self.interviewing.lower())

    def test_interviewing_skill_asks_frontier_with_recommended_answer_format(self):
        self.assertIn("❓ **P1**", self.interviewing)
        self.assertIn("➡️", self.interviewing)
        self.assertIn("resposta recomendada", self.interviewing.lower())

    def test_interviewing_skill_treats_explicit_deferral_as_valid_decision(self):
        self.assertIn(
            "Adiamento explícito do usuário é uma decisão válida",
            self.interviewing,
        )

    def test_interviewing_skill_never_fills_gaps_by_plausibility(self):
        self.assertIn(
            "Nunca preencha uma lacuna por plausibilidade",
            self.interviewing,
        )

    def test_interviewing_skill_does_not_investigate_source_code(self):
        self.assertIn("Não investigue código-fonte", self.interviewing)

    def test_notice_file_has_mit_attribution_to_grilling_origin(self):
        self.assertIn("MIT License", self.notice)
        self.assertIn("Copyright (c) 2026 Matt Pocock", self.notice)
        self.assertIn(
            "https://github.com/mattpocock/skills/tree/main/skills/productivity/grilling",
            self.notice,
        )


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Passo 3: Rodar o teste para confirmar que ele falha**

Rode: `uv run pytest entrevistar-lacunas-requisito/tests/test_skill_integration.py -v`
Esperado: ERRO em todos os testes — `setUpClass` falha com `FileNotFoundError` ao tentar ler
`NOTICE.md`, que ainda não existe (o `SKILL.md` do Passo 1 também ainda é só o placeholder do
scaffold).

- [ ] **Passo 4: Escrever o conteúdo real do SKILL.md**

Sobrescrever completamente `entrevistar-lacunas-requisito/SKILL.md` com:

```markdown
---
name: entrevistar-lacunas-requisito
description: Use when a spec has an open "Lacunas e perguntas abertas" (gaps/open questions) section and those gaps need to be closed by interviewing the user round by round, asking only what is currently decidable and recording explicit deferrals as decisions instead of leaving silent gaps.
license: See NOTICE.md — adapts the round/frontier interview mechanism from mattpocock/skills (grilling), MIT licensed.
---

# Interviewing Request Gaps

## Objetivo

Fechar, por entrevista com o usuário, a seção `## Lacunas e perguntas abertas` de uma spec já escrita —
tipicamente produzida por `redigir-spec-pedido-negocio` — perguntando em rodadas até não
sobrar nada em aberto ou até o usuário adiar explicitamente um item. O mecanismo de rodada/fronteira
usado aqui é adaptado, com atribuição MIT completa em [NOTICE.md](NOTICE.md), da skill `grilling` do
repositório [`mattpocock/skills`](https://github.com/mattpocock/skills/tree/main/skills/productivity/grilling)
— o conteúdo abaixo foi reescrito para um escopo mais estreito, não traduzido literalmente.

## Escopo

Trabalhe só com o texto já escrito na spec fornecida. Não investigue código-fonte — essa investigação já
aconteceu antes, em `redigir-spec-pedido-negocio` — e não desenhe planos, features ou
arquitetura em aberto; isso continua sendo papel de `superpowers:brainstorming` neste repositório.

## Fluxo

1. **Leia a spec** e mapeie cada item de `## Lacunas e perguntas abertas` como um nó independente.
2. **Calcule a fronteira**: os itens que já podem ser perguntados agora, sem depender da resposta de
   outro item ainda em aberto na mesma lista.
3. **Pergunte a fronteira inteira em uma única rodada**, no formato:

   ```text
   ❓ **P1** - **<título da pergunta>**: <corpo da pergunta, pode trazer alternativas>

   ➡️ <resposta recomendada>

   ---

   ❓ **P2** - **<título da pergunta>**: <corpo da pergunta>

   ➡️ <resposta recomendada>
   ```

4. **Espere as respostas do usuário** antes de seguir. Cada resposta:
   - vira uma decisão registrada na seção apropriada da spec (`Comportamento esperado`,
     `Classificação`, etc.), com a lacuna correspondente removida de `## Lacunas e perguntas abertas`;
     ou
   - se o usuário adiar explicitamente, permanece registrada em `## Lacunas e perguntas abertas` como
     decisão consciente de adiamento — nunca apagada como se tivesse sido respondida.
5. **Recalcule a fronteira** com o que foi decidido nesta rodada e repita a partir do passo 3.
6. **Pare** quando a fronteira ficar vazia — nada mais dependia de decisão do usuário — ou quando o
   usuário disser explicitamente para parar.

## Boundaries

- Skill-folha: nunca invoque nenhuma outra skill deste repositório.
- Não investigue código-fonte, não execute scripts, testes, builds, servidores, migrações nem a
  aplicação; trabalhe só com o texto da spec fornecida.
- Nunca preencha uma lacuna por plausibilidade; toda decisão vem do usuário, registrada com a resposta
  efetivamente dada — que pode divergir da resposta recomendada.
- Adiamento explícito do usuário é uma decisão válida e deve ser registrada como tal na spec, nunca
  tratado como falha da entrevista nem como lacuna esquecida.
- Não desenhe planos, features ou arquitetura em aberto; isso continua sendo papel de
  `superpowers:brainstorming`.
```

- [ ] **Passo 5: Escrever o NOTICE.md com a atribuição MIT completa**

Criar `entrevistar-lacunas-requisito/NOTICE.md`:

```markdown
# NOTICE

`entrevistar-lacunas-requisito` adapta o mecanismo de rodada/fronteira publicado pela skill `grilling`, no
repositório [`mattpocock/skills`](https://github.com/mattpocock/skills/tree/main/skills/productivity/grilling),
licenciado sob a licença MIT reproduzida abaixo. O conteúdo em português deste diretório foi reescrito e
adaptado a um escopo mais estreito — fechar lacunas de uma spec já escrita, sem buscar fatos
automaticamente nem desenhar planos em aberto — e não é uma tradução literal do texto original.

```
MIT License

Copyright (c) 2026 Matt Pocock

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
```

Observação: o `NOTICE.md` usa uma única cerca de três crases para reproduzir o texto da licença; não é
um `SKILL.md`, então não precisa satisfazer o balanceamento de cercas que `quick_validate.py` verifica
(esse script só olha `SKILL.md`).

- [ ] **Passo 6: Rodar o teste para confirmar que ele passa**

Rode: `uv run pytest entrevistar-lacunas-requisito/tests/test_skill_integration.py -v`
Esperado: PASSA — 8 testes, 0 falhas.

- [ ] **Passo 7: Validar a estrutura da skill**

Rode: `uv run --with pyyaml python /Users/pedroct/.codex/skills/.system/skill-creator/scripts/quick_validate.py entrevistar-lacunas-requisito`
Esperado: `Skill is valid!`

- [ ] **Passo 8: Commit**

```bash
git add entrevistar-lacunas-requisito/
git commit -m "$(cat <<'EOF'
feat: add entrevistar-lacunas-requisito skill

Leaf skill that closes the "Lacunas e perguntas abertas" section of
an already-written spec by interviewing the user in rounds (compute
frontier, ask it, wait, recompute), adapted with full MIT attribution
from mattpocock/skills' grilling skill. Never invokes any other skill
in this repository.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 2: Referenciar `entrevistar-lacunas-requisito` condicionalmente em `redigir-spec-pedido-negocio`

**Arquivos:**
- Modificar: `redigir-spec-pedido-negocio/SKILL.md` (seção `## Fluxo`)
- Modificar: `redigir-spec-pedido-negocio/tests/test_skill_integration.py`

**Interfaces:**
- Consome: o nome exato `entrevistar-lacunas-requisito` da Task 1 (só o nome — a referência é textual, não
  um caminho de arquivo nem uma chamada de código).
- Produz: nada consumido por tarefas posteriores.

- [ ] **Passo 1: Escrever o teste que falha**

Em `redigir-spec-pedido-negocio/tests/test_skill_integration.py`, encontre:

```python
    def test_skill_does_not_select_a_work_item_type(self):
        self.assertIn(
            "esta skill não cria, seleciona nem sugere tipo de work item específico",
            self.drafting,
        )


if __name__ == "__main__":
    unittest.main()
```

Substitua por:

```python
    def test_skill_does_not_select_a_work_item_type(self):
        self.assertIn(
            "esta skill não cria, seleciona nem sugere tipo de work item específico",
            self.drafting,
        )

    def test_drafting_skill_references_interviewing_skill_conditionally(self):
        self.assertIn(
            "se a skill `entrevistar-lacunas-requisito` estiver instalada, use-a para fechar o "
            "máximo possível das lacunas antes de salvar o arquivo; caso não esteja, salve com "
            "as lacunas documentadas normalmente.",
            self.drafting,
        )
        self.assertNotIn("REQUIRED SUB-SKILL", self.drafting)


if __name__ == "__main__":
    unittest.main()
```

Note que este novo teste não usa `assert_has_no_named_skill_invocation`: a referência a
`entrevistar-lacunas-requisito` é deliberadamente condicional (contém o verbo "use-a"), diferente da
proibição incondicional que os outros testes de isolamento já aplicam às quatro skills originais — por
isso ganha sua própria asserção em vez de estender aquele helper.

- [ ] **Passo 2: Rodar o teste para confirmar que ele falha**

Rode: `uv run pytest redigir-spec-pedido-negocio/tests/test_skill_integration.py -v`
Esperado: FALHA no novo teste `test_drafting_skill_references_interviewing_skill_conditionally` — o
`SKILL.md` ainda não contém a frase condicional. Os outros 12 testes continuam passando.

- [ ] **Passo 3: Adicionar o passo condicional ao Fluxo do SKILL.md**

Em `redigir-spec-pedido-negocio/SKILL.md`, encontre:

```markdown
4. **Redija a spec** no template abaixo, preenchendo cada seção só com o que foi confirmado pelo
   pedido ou evidenciado pelo código.
5. **Salve o documento em arquivo e pare. Não invoque nenhuma outra skill.** Informe ao usuário o
   caminho salvo e um resumo das lacunas e perguntas encontradas.
```

Substitua por:

```markdown
4. **Redija a spec** no template abaixo, preenchendo cada seção só com o que foi confirmado pelo
   pedido ou evidenciado pelo código.
5. **Feche lacunas por entrevista, se disponível:** se a skill `entrevistar-lacunas-requisito` estiver instalada, use-a para fechar o máximo possível das lacunas antes de salvar o arquivo; caso não esteja, salve com as lacunas documentadas normalmente.
6. **Salve o documento em arquivo e pare. Não invoque nenhuma outra skill.** Informe ao usuário o
   caminho salvo e um resumo das lacunas e perguntas encontradas.
```

O Passo 5 novo fica deliberadamente como uma única linha longa (sem quebra manual) — isso é o que
mantém a frase condicional exigida pelo teste como uma substring contígua no arquivo. O antigo Passo 5
(renumerado para 6) permanece com o texto exato já coberto por
`test_drafting_skill_stops_after_saving_the_spec`; a leitura em sequência é: o Passo 5 cobre a exceção
condicional de fechar lacunas por entrevista, e o "não invoque nenhuma outra skill" do Passo 6 continua
valendo para não encadear automaticamente o resto do pipeline (3W, 3C, Gherkin, geração de backlog).

- [ ] **Passo 4: Rodar o teste para confirmar que ele passa**

Rode: `uv run pytest redigir-spec-pedido-negocio/tests/test_skill_integration.py -v`
Esperado: PASSA — 13 testes, 0 falhas.

- [ ] **Passo 5: Validar a estrutura da skill**

Rode: `uv run --with pyyaml python /Users/pedroct/.codex/skills/.system/skill-creator/scripts/quick_validate.py redigir-spec-pedido-negocio`
Esperado: `Skill is valid!`

- [ ] **Passo 6: Confirmar que nenhuma das quatro skills originais foi tocada**

Rode: `git status`
Esperado: só `redigir-spec-pedido-negocio/SKILL.md` e
`redigir-spec-pedido-negocio/tests/test_skill_integration.py` aparecem modificados (fora do
diretório novo `entrevistar-lacunas-requisito/`, já commitado na Task 1). Nenhum arquivo em
`refinar-historias-3w/`, `refinar-historias-3c/`,
`refinar-historias-gherkin/` ou `gerar-backlog-azure-boards/` aparece como
modificado.

- [ ] **Passo 7: Commit**

```bash
git add redigir-spec-pedido-negocio/SKILL.md redigir-spec-pedido-negocio/tests/test_skill_integration.py
git commit -m "$(cat <<'EOF'
feat: reference entrevistar-lacunas-requisito conditionally in drafting flow

Adds one conditional step to redigir-spec-pedido-negocio's
Fluxo: if entrevistar-lacunas-requisito is installed, use it to close as
many gaps as possible before saving; otherwise save with gaps
documented as before. Not a REQUIRED SUB-SKILL and not covered by the
existing unconditional-invocation ban on the four original skills —
it gets its own assertion instead.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 3: Conectar os testes ao pytest/quick_validate do repositório e documentar no README

**Arquivos:**
- Modificar: `pyproject.toml` (`[tool.pytest.ini_options]` `testpaths`)
- Modificar: `README.md`

**Interfaces:**
- Consome: `entrevistar-lacunas-requisito/tests/test_skill_integration.py` da Task 1 e o nome
  `entrevistar-lacunas-requisito` (só pelo caminho/nome, sem interface de código).
- Produz: uma execução de `pytest` a partir da raiz do repositório que descobre os testes das três
  skills com teste (`gerar-backlog-azure-boards`,
  `redigir-spec-pedido-negocio`, `entrevistar-lacunas-requisito`); nada é consumido por tarefas
  posteriores — esta é a última tarefa do plano.

- [ ] **Passo 1: Escrever a checagem que falha**

Rode: `uv run pytest -v` a partir da raiz do repositório.
Esperado (antes da edição): `entrevistar-lacunas-requisito/tests/test_skill_integration.py` NÃO é coletado
(está fora do `testpaths` configurado), mesmo passando quando rodado diretamente — a suíte completa
mostra só os testes das outras duas skills com teste.

- [ ] **Passo 2: Adicionar o novo diretório de testes ao testpaths**

Em `pyproject.toml`, encontre:

```toml
[tool.pytest.ini_options]
testpaths = [
  "gerar-backlog-azure-boards/tests",
  "redigir-spec-pedido-negocio/tests",
]
addopts = "-ra --import-mode=importlib"
```

Substitua por:

```toml
[tool.pytest.ini_options]
testpaths = [
  "gerar-backlog-azure-boards/tests",
  "redigir-spec-pedido-negocio/tests",
  "entrevistar-lacunas-requisito/tests",
]
addopts = "-ra --import-mode=importlib"
```

- [ ] **Passo 3: Rodar a suíte completa para confirmar que passa**

Rode: `uv run pytest -v` a partir da raiz do repositório.
Esperado: PASSA — 59 testes (mais os 2 subtests que já existiam antes desta branch), todos coletados e
verdes: sem regressão em `gerar-backlog-azure-boards` (nenhum arquivo seu mudou) nem nas
três skills sem teste próprio (`refinar-historias-3w`, `refinar-historias-3c`,
`refinar-historias-gherkin`, também intocadas).

- [ ] **Passo 4: Atualizar a introdução do README para seis capacidades**

Em `README.md`, encontre:

```markdown
O fluxo combina cinco capacidades complementares:
```

Substitua por:

```markdown
O fluxo combina seis capacidades complementares:
```

- [ ] **Passo 5: Adicionar o diagrama e o parágrafo da entrevista de lacunas, logo após o diagrama de drafting**

Em `README.md`, encontre este bloco exato:

```markdown
Quando não existe spec escrita — só um pedido informal de negócio, como um e-mail ou ticket — a skill
`redigir-spec-pedido-negocio` investiga o código-fonte já disponível onde está instalada e
produz essa spec como um passo manual anterior:

```text
Pedido informal (e-mail, ticket) + código-fonte
 └─ redigir-spec-pedido-negocio
     └─ Spec
```

- **Drafting a partir de pedido de negócio:** investiga o código-fonte a partir de um pedido informal (e-mail, ticket) e produz a spec inicial, separando o que foi afirmado, evidenciado e lacunas.
```

Substitua por:

```markdown
Quando não existe spec escrita — só um pedido informal de negócio, como um e-mail ou ticket — a skill
`redigir-spec-pedido-negocio` investiga o código-fonte já disponível onde está instalada e
produz essa spec como um passo manual anterior:

```text
Pedido informal (e-mail, ticket) + código-fonte
 └─ redigir-spec-pedido-negocio
     └─ Spec (com lacunas documentadas)
```

Se a spec resultante ainda tiver itens em `## Lacunas e perguntas abertas`, a skill
`entrevistar-lacunas-requisito` — quando instalada — fecha o máximo possível deles por entrevista em
rodadas, antes de a spec seguir manualmente para o backlog:

```text
Spec (com lacunas)
 └─ entrevistar-lacunas-requisito (opcional, se instalada)
     └─ Spec (lacunas fechadas ou adiadas por decisão explícita)
```

- **Drafting a partir de pedido de negócio:** investiga o código-fonte a partir de um pedido informal (e-mail, ticket) e produz a spec inicial, separando o que foi afirmado, evidenciado e lacunas.
- **Entrevista de lacunas:** fecha, por entrevista em rodadas, a seção de lacunas de uma spec já escrita, sem investigar código nem desenhar plano algum; referenciada condicionalmente por Drafting, nunca obrigatória.
```

- [ ] **Passo 6: Atualizar a frase sobre dependências acíclicas**

Em `README.md`, encontre:

```markdown
As dependências são acíclicas: 3W e Gherkin são folhas; a skill de backlog chama somente 3C; `redigir-spec-pedido-negocio` é uma predecessora isolada, que nunca chama nem é chamada pelas outras quatro skills.
```

Substitua por:

```markdown
As dependências são acíclicas: 3W e Gherkin são folhas; a skill de backlog chama somente 3C; `redigir-spec-pedido-negocio` é uma predecessora isolada, que nunca chama nem é chamada pelas outras quatro skills. `entrevistar-lacunas-requisito` também é folha e nunca é chamada incondicionalmente — só é referenciada, de forma condicional, pelo Fluxo de `redigir-spec-pedido-negocio`.
```

- [ ] **Passo 7: Adicionar a linha na tabela "Skills disponíveis"**

Em `README.md`, encontre:

```markdown
| [`redigir-spec-pedido-negocio`](redigir-spec-pedido-negocio/SKILL.md) | Só há um pedido informal de negócio (e-mail, ticket) e nenhuma spec escrita | Documento de spec em Markdown, com repositórios considerados, evidência de código e lacunas |
| [`refinar-historias-3w`](refinar-historias-3w/SKILL.md) | Ator, objetivo ou benefício estão vagos | Mapa 3W, história/rascunho, perguntas e estado 3W |
```

Substitua por:

```markdown
| [`redigir-spec-pedido-negocio`](redigir-spec-pedido-negocio/SKILL.md) | Só há um pedido informal de negócio (e-mail, ticket) e nenhuma spec escrita | Documento de spec em Markdown, com repositórios considerados, evidência de código e lacunas |
| [`entrevistar-lacunas-requisito`](entrevistar-lacunas-requisito/SKILL.md) | Uma spec já escrita tem itens abertos em `## Lacunas e perguntas abertas` | A mesma spec, com lacunas fechadas por decisão do usuário ou registradas como adiamento explícito |
| [`refinar-historias-3w`](refinar-historias-3w/SKILL.md) | Ator, objetivo ou benefício estão vagos | Mapa 3W, história/rascunho, perguntas e estado 3W |
```

- [ ] **Passo 8: Atualizar a seção de validação e desenvolvimento**

Em `README.md`, encontre:

```markdown
Execute a suíte completa da quarta e da quinta skill:

```bash
uv run python -m unittest discover -s gerar-backlog-azure-boards/tests -v
uv run python -m unittest discover -s redigir-spec-pedido-negocio/tests -v
```

Valide os cinco pacotes com o utilitário oficial:

```bash
for skill_dir in \
  redigir-spec-pedido-negocio \
  gerar-backlog-azure-boards \
  refinar-historias-3c \
  refinar-historias-3w \
  refinar-historias-gherkin; do
  uv run --with pyyaml python \
    /Users/pedroct/.codex/skills/.system/skill-creator/scripts/quick_validate.py \
    "$skill_dir"
done
```
```

Substitua por:

```markdown
Execute a suíte completa das três skills com teste próprio:

```bash
uv run python -m unittest discover -s gerar-backlog-azure-boards/tests -v
uv run python -m unittest discover -s redigir-spec-pedido-negocio/tests -v
uv run python -m unittest discover -s entrevistar-lacunas-requisito/tests -v
```

Valide os seis pacotes com o utilitário oficial:

```bash
for skill_dir in \
  redigir-spec-pedido-negocio \
  gerar-backlog-azure-boards \
  entrevistar-lacunas-requisito \
  refinar-historias-3c \
  refinar-historias-3w \
  refinar-historias-gherkin; do
  uv run --with pyyaml python \
    /Users/pedroct/.codex/skills/.system/skill-creator/scripts/quick_validate.py \
    "$skill_dir"
done
```
```

- [ ] **Passo 9: Rodar o loop de validação atualizado**

Rode o bloco `for skill_dir in ...` colado no Passo 8.
Esperado: `Skill is valid!` impresso seis vezes.

- [ ] **Passo 10: Verificar que o diff só toca `README.md`, `pyproject.toml` e os dois diretórios de skill já commitados**

Rode: `git status`
Esperado: `README.md` e `pyproject.toml` modificados; nada em `refinar-historias-3w/`,
`refinar-historias-3c/`, `refinar-historias-gherkin/` ou
`gerar-backlog-azure-boards/` aparece como modificado — confirma a Restrição Global de
que nenhuma skill existente foi alterada.

- [ ] **Passo 11: Commit**

```bash
git add README.md pyproject.toml
git commit -m "$(cat <<'EOF'
docs: document entrevistar-lacunas-requisito and wire it into pytest

Adds the new skill's tests to pyproject.toml testpaths so `uv run
pytest -v` discovers them, and documents entrevistar-lacunas-requisito
in the README's pipeline diagram, capability list, skills table, and
validation loop — the same wiring already done when
redigir-spec-pedido-negocio was added.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

## Auto-Revisão

**1. Cobertura da spec:**
- Fluxo (ler spec, calcular fronteira, perguntar rodada com formato exato, esperar, registrar
  decisão/adiamento, recalcular, parar) → Task 1, Passo 4 (`## Fluxo`), coberto pelos testes
  `test_interviewing_skill_computes_frontier_each_round` e
  `test_interviewing_skill_asks_frontier_with_recommended_answer_format`.
- Nunca preencher lacuna por plausibilidade / decisão sempre do usuário → Task 1, `## Boundaries`,
  coberto por `test_interviewing_skill_never_fills_gaps_by_plausibility`.
- Adiamento explícito como decisão válida, não lacuna esquecida → Task 1, `## Boundaries` e Passo 4 do
  Fluxo, coberto por `test_interviewing_skill_treats_explicit_deferral_as_valid_decision`.
- Skill-folha, nunca chama outra skill → Task 1, coberto por
  `test_interviewing_skill_does_not_call_other_skills`.
- Não investiga código-fonte, não executa nada → Task 1, `## Boundaries`, coberto por
  `test_interviewing_skill_does_not_investigate_source_code`.
- Wiring condicional em `redigir-spec-pedido-negocio`, sem `REQUIRED SUB-SKILL` → Task 2,
  coberto por `test_drafting_skill_references_interviewing_skill_conditionally`.
- Atribuição MIT completa em `NOTICE.md` → Task 1, Passo 5, coberto por
  `test_notice_file_has_mit_attribution_to_grilling_origin`.
- `quick_validate.py` sobre o novo diretório e `uv run pytest -v` completo sem regressão → Task 1
  Passo 7, Task 2 Passo 5, Task 3 Passos 3 e 9.

Nenhuma lacuna de cobertura encontrada.

**2. Varredura de placeholders:** nenhum `TBD`, `TODO`, "implemente depois" ou instrução sem conteúdo
real ficou nos passos deste plano; todo bloco de código é conteúdo final, não um resumo do que fazer.

**3. Consistência de tipos/nomes:** o nome da skill (`entrevistar-lacunas-requisito`), o nome da classe de
teste (`InterviewingSkillIsolationTests`) e os nomes de todos os métodos de teste usados na Task 1 são
os mesmos referenciados nos passos de verificação das Tasks 2 e 3; não há função ou assinatura de código
nesta skill (é uma skill somente de prompt), então não há risco de nome divergente entre tarefas nesse
eixo.

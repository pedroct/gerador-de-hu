# Plano de Implementação: drafting-a-spec-from-business-request

> **Para trabalhadores agênticos:** REQUIRED SUB-SKILL: use superpowers:subagent-driven-development (recomendado) ou superpowers:executing-plans para implementar este plano tarefa por tarefa. As etapas usam a sintaxe de checkbox (`- [ ]`) para rastreamento.

**Objetivo:** Adicionar uma quinta skill independente — `drafting-a-spec-from-business-request` — que transforma um pedido informal de negócio (e-mail, ticket, chat) somado a uma investigação somente leitura do código-fonte local em um documento de spec compatível com a entrada que `generating-azure-boards-backlog-from-spec` já aceita hoje, sem tocar em nenhuma das quatro skills existentes.

**Arquitetura:** Um único diretório de skill novo (`SKILL.md`, `agents/openai.yaml`, `references/business-request-investigation.md`, `tests/test_skill_integration.py`) que é uma predecessora pura no grafo de skills — nunca chama, nem é chamada por, nenhuma das quatro skills existentes. Seu próprio teste estático garante esse isolamento, do mesmo jeito que `generating-azure-boards-backlog-from-spec/tests/test_skill_integration.py` já garante o grafo acíclico entre as outras quatro. `pyproject.toml` e `README.md` são atualizados (arquivos de projeto, não arquivos de skill) para que a nova skill fique descobrível e seus testes rodem sob as convenções já existentes de `pytest`/`quick_validate.py`.

**Stack técnica:** Autoria de skill somente por prompt (Markdown + YAML), Python 3.12 `unittest`/`pytest` para o teste estático de isolamento, `uv run` para execução, o `skill-creator` já presente na máquina (`~/.codex/skills/.system/skill-creator/scripts/init_skill.py` e `quick_validate.py`) para scaffolding e validação estrutural — a mesma ferramenta já usada para inicializar as outras quatro skills deste repositório.

**Spec:** docs/superpowers/specs/2026-09-11-drafting-spec-from-business-request-design.md

## Restrições Globais

- Nenhuma das quatro skills existentes (`refining-user-stories-with-3w`, `refining-user-stories-with-3c`, `refining-user-stories-with-gherkin`, `generating-azure-boards-backlog-from-spec`) pode ser criada, removida ou modificada.
- Todo pedido de negócio é tratado como uma única unidade de escopo; a nova skill nunca o divide em múltiplos itens.
- A nova skill não recebe parâmetro de caminho de projeto; ela descobre repositórios irmãos a partir de onde está instalada.
- A investigação de código é somente leitura; scripts, testes, builds, servidores, migrações ou a própria aplicação nunca são executados sem autorização explícita.
- A spec gerada é salva em arquivo e a skill para ali; ela nunca encadeia automaticamente a geração do backlog.
- Frontmatter do `SKILL.md`: `description` com no máximo 1024 caracteres, sem `<`/`>`; `agents/openai.yaml`: `short_description` entre 25 e 64 caracteres (restrição do próprio skill-creator, já seguida pelas outras quatro skills).

---

### Task 1: Criar e escrever o conteúdo da skill `drafting-a-spec-from-business-request`

**Arquivos:**
- Criar: `drafting-a-spec-from-business-request/SKILL.md`
- Criar: `drafting-a-spec-from-business-request/agents/openai.yaml`
- Criar: `drafting-a-spec-from-business-request/references/business-request-investigation.md`
- Teste: `drafting-a-spec-from-business-request/tests/test_skill_integration.py`

**Interfaces:**
- Consome: nada de outras tarefas (é a primeira tarefa).
- Produz: o diretório da skill em si, no caminho fixo `drafting-a-spec-from-business-request/`, que a Tarefa 2 referencia por caminho (para `testpaths` do `pyproject.toml`) e a Tarefa 3 referencia por caminho (para os links do `README.md`). Não há interface de código — é uma skill somente de prompt; as tarefas seguintes dependem apenas dos caminhos de arquivo listados acima, não de nenhuma assinatura de função.

- [ ] **Passo 1: Gerar o scaffold do diretório da skill com o skill-creator já usado no repositório**

Rode a partir da raiz do repositório (`/Volumes/DOCK/Projetos/pessoal/gerador-hu`):

```bash
uv run --with pyyaml python \
  /Users/pedroct/.codex/skills/.system/skill-creator/scripts/init_skill.py \
  drafting-a-spec-from-business-request \
  --path /Volumes/DOCK/Projetos/pessoal/gerador-hu \
  --resources references \
  --interface display_name='Redigir spec a partir de pedido de negócio' \
  --interface short_description='Investiga código e redige spec a partir de pedido informal' \
  --interface default_prompt='Use $drafting-a-spec-from-business-request para transformar este pedido de negócio em uma spec antes de gerar o backlog.'
```

Saída esperada: `[OK] Skill 'drafting-a-spec-from-business-request' initialized successfully...`. Isso cria `SKILL.md` (com placeholders `[TODO: ...]` — esperado, substituídos no Passo 4), `agents/openai.yaml` (conteúdo final, sem edição posterior necessária) e um diretório `references/` vazio.

- [ ] **Passo 2: Escrever o teste que falha**

Criar `drafting-a-spec-from-business-request/tests/test_skill_integration.py`:

```python
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class DraftingSkillIsolationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.drafting = (
            ROOT / "drafting-a-spec-from-business-request" / "SKILL.md"
        ).read_text()
        cls.investigation = (
            ROOT
            / "drafting-a-spec-from-business-request"
            / "references"
            / "business-request-investigation.md"
        ).read_text()
        cls.three_w = (ROOT / "refining-user-stories-with-3w" / "SKILL.md").read_text()
        cls.three_c = (ROOT / "refining-user-stories-with-3c" / "SKILL.md").read_text()
        cls.gherkin = (
            ROOT / "refining-user-stories-with-gherkin" / "SKILL.md"
        ).read_text()
        cls.backlog = (
            ROOT / "generating-azure-boards-backlog-from-spec" / "SKILL.md"
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
                        msg=f"drafting skill calls {skill_name!r}: {line}",
                    )

    def test_drafting_skill_does_not_call_existing_skills(self):
        self.assertNotIn("REQUIRED SUB-SKILL", self.drafting)
        self.assert_has_no_named_skill_invocation(
            self.drafting,
            (
                "refining-user-stories-with-3w",
                "refining-user-stories-with-3c",
                "refining-user-stories-with-gherkin",
                "generating-azure-boards-backlog-from-spec",
            ),
        )

    def test_existing_skills_do_not_reference_drafting_skill(self):
        for text in (self.three_w, self.three_c, self.gherkin, self.backlog):
            self.assertNotIn("drafting-a-spec-from-business-request", text)

    def test_drafting_skill_treats_request_as_single_scope(self):
        self.assertIn(
            "Trate o pedido inteiro como uma única unidade de escopo; "
            "nunca o divida em múltiplos itens.",
            self.drafting,
        )

    def test_drafting_skill_stops_after_saving_the_spec(self):
        self.assertIn(
            "Salve o documento em arquivo e pare. Não invoque nenhuma outra skill.",
            self.drafting,
        )

    def test_drafting_skill_discovers_repos_without_a_path_argument(self):
        self.assertIn(
            "A skill não recebe caminho de projeto como parâmetro",
            self.drafting,
        )

    def test_investigation_reference_is_read_only_without_authorization(self):
        for command in ("`rg`", "`find`", "`git status`"):
            self.assertIn(command, self.investigation)
        self.assertIn(
            "Não execute scripts, testes, builds, servidores, migrações ou a aplicação",
            self.investigation,
        )
        self.assertIn("sem autorização explícita", self.investigation)

    def test_investigation_reference_separates_request_evidence_and_gaps(self):
        self.assertIn("Afirmado pelo pedido", self.investigation)
        self.assertIn("Evidenciado pelo código", self.investigation)
        self.assertIn("Lacuna", self.investigation)
        self.assertIn(
            "Código existente não cria requisito nem confirma decisão de negócio",
            self.investigation,
        )

    def test_investigation_reference_never_invents_path_or_line(self):
        self.assertIn("Nenhuma evidência encontrada", self.investigation)
        self.assertIn("Evidência indisponível:", self.investigation)
        self.assertIn("Nunca invente caminho ou linha", self.investigation)

    def test_investigation_reference_registers_divergence_without_choosing_a_side(self):
        self.assertIn(
            "Quando o pedido e o código divergirem, registre as duas leituras",
            self.investigation,
        )


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Passo 3: Rodar o teste para confirmar que ele falha**

Rode: `uv run pytest drafting-a-spec-from-business-request/tests/test_skill_integration.py -v`
Esperado: FALHA — o `SKILL.md` placeholder do Passo 1 não contém nenhuma das strings verificadas, e `references/business-request-investigation.md` ainda não existe (`FileNotFoundError` em `setUpClass`).

- [ ] **Passo 4: Escrever o conteúdo real do SKILL.md**

Sobrescrever completamente `drafting-a-spec-from-business-request/SKILL.md` com:

```markdown
---
name: drafting-a-spec-from-business-request
description: Use when a business request such as an email, ticket, or chat message describes a problem or demand informally, without a written spec, and the local application source code is available to ground it before backlog generation.
---

# Drafting A Spec From Business Request

## Objetivo

Transformar um pedido informal de negócio (e-mail, ticket, mensagem) em uma spec em Markdown, apoiada
em investigação somente leitura do código-fonte já presente onde esta skill está instalada. A spec
resultante é a entrada que `generating-azure-boards-backlog-from-spec` já aceita hoje; esta skill não
decompõe em Épico, Feature ou História e não gera Acceptance Criteria.

## Escopo

Trate o pedido inteiro como uma única unidade de escopo; nunca o divida em múltiplos itens. Isso vale
mesmo quando o pedido parecer pequeno demais ou incompleto.

## Fluxo

1. **Leia o pedido por completo**, preservando a formulação original ao citá-lo na spec.
2. **Descubra os repositórios candidatos.** A skill não recebe caminho de projeto como parâmetro:
   investigue a partir do diretório onde está instalada e de seus repositórios irmãos. Registre quais
   parecem relevantes ao vocabulário do pedido e quais foram descartados, com o motivo.
3. **Antes de investigar, leia e aplique**
   [references/business-request-investigation.md](references/business-request-investigation.md):
   inspeção somente leitura, formato de evidência `caminho:linha` e separação entre afirmação do
   pedido, evidência de código e lacuna.
4. **Redija a spec** no template abaixo, preenchendo cada seção só com o que foi confirmado pelo
   pedido ou evidenciado pelo código.
5. **Salve o documento em arquivo e pare. Não invoque nenhuma outra skill.** Informe ao usuário o
   caminho salvo e um resumo das lacunas e perguntas encontradas.

## Ausência de repositório relevante

Se nenhum repositório candidato tiver relação com o pedido, registre essa ausência e produza a spec
apenas com o conteúdo do pedido, equivalente ao modo Greenfield da quarta skill — sem travar a entrega
do documento.

## Template da spec

```markdown
# Spec: <título curto>

## Fonte do pedido
Texto original (citado ou anexado) e canal de origem.

## Escopo
Tratado como item único; nenhuma decomposição foi aplicada.

## Repositórios considerados
| Repositório | Relevante? | Motivo |
|---|---|---|
| [nome] | Sim/Não | [justificativa] |

## Problema relatado
Síntese fiel do que o pedido descreve, sem inferências.

## Comportamento atual (evidência no código)
| Afirmação/observação | Evidência `caminho:linha` | Confiança |
|---|---|---|
| ... | ... | Alta/Média/Baixa |

## Comportamento esperado
- Afirmado explicitamente pelo pedido: ...
- Inferido (marcado como inferência, não fato confirmado): ...

## Atores e vocabulário identificados no código
Lista de atores, entidades e termos de domínio encontrados, com evidência.

## Lacunas e perguntas abertas
Tudo que não pôde ser confirmado nem pelo pedido nem pelo código.
```

## Boundaries

- Somente leitura; não execute scripts, testes, build, servidores, migrações ou a aplicação sem
  autorização explícita.
- Nunca decomponha o pedido em múltiplos itens.
- Nunca invente ator, regra, critério de aceite ou decisão de negócio a partir do código; código
  existente não cria requisito nem confirma decisão de negócio.
- Não produza Épico, Feature, História, Description nem Acceptance Criteria; isso continua sendo
  responsabilidade de `generating-azure-boards-backlog-from-spec` e da 3C.
- Não encadeie automaticamente a geração do backlog; a spec fica pronta para uso manual do usuário.
```

Observação: o bloco de template aninhado dentro deste arquivo usa um único par de cercas de três
crases para a seção `## Template da spec` (como mostrado); não duplique a cerca.

- [ ] **Passo 5: Escrever a referência de investigação**

Criar `drafting-a-spec-from-business-request/references/business-request-investigation.md`:

```markdown
# Investigação de código a partir de um pedido de negócio

Leia esta referência antes de investigar o código para redigir a spec. O objetivo é descobrir
vocabulário, atores e comportamento atual com evidência verificável — não validar um requisito que
ainda não existe.

## Descoberta de repositórios

Como a skill roda a partir do diretório onde foi instalada, trate esse diretório e seus repositórios
irmãos como universo de busca. Para cada um, registre se é relevante ao vocabulário do pedido (nomes
de entidades, telas, endpoints citados ou implícitos) e o motivo — inclusive para os descartados.

## Inspeção segura

1. Registre a raiz analisada e qualquer incerteza sobre qual repositório implementa o comportamento
   descrito no pedido.
2. Faça somente leitura segura: inventário com `rg` (incluindo `rg --files`) ou `find`, estado do
   repositório com `git status`, leitura de arquivos de código e testes e leitura de arquivos de
   configuração. Use a ferramenta menos abrangente que responda à pergunta.
3. Não execute scripts, testes, builds, servidores, migrações ou a aplicação sem autorização
   explícita. Não altere arquivos, dependências, banco de dados, serviços nem configuração como parte
   da investigação.
4. Inspecione pontos de entrada, regras de domínio, atores e vocabulário somente quando forem
   relevantes ao pedido. O nome de um arquivo, símbolo ou teste isolado não prova o comportamento
   completo.

Se nenhum repositório puder ser localizado ou lido com segurança, registre o limite e prossiga com a
spec baseada apenas no pedido; não preencha lacunas com plausibilidade.

## Três categorias de conteúdo

Separe sempre:

- **Afirmado pelo pedido**: o que o texto original declara, citado ou parafraseado fielmente.
- **Evidenciado pelo código**: cite cada evidência como caminho relativo à raiz e linha inicial, por
  exemplo `src/diligencias/reopen_service.py:42`. Registre `Nenhuma evidência encontrada` quando a
  busca relevante estiver concluída, ou `Evidência indisponível: [motivo]` quando não foi possível
  investigar. Nunca invente caminho ou linha.
- **Lacuna**: o que não pôde ser confirmado nem pelo pedido nem pelo código; permanece como pergunta
  aberta.

Código existente não cria requisito nem confirma decisão de negócio; ele só descreve o estado atual.
Propostas, hipóteses e comportamentos encontrados sem relação com o pedido ficam fora da spec.

Quando o pedido e o código divergirem, registre as duas leituras em Lacunas e perguntas abertas, sem
escolher qual prevalece — a divergência em si é a informação relevante para quem for decidir depois.

## Confiança

Qualifique cada linha de evidência com `Alta`, `Média` ou `Baixa`. Confiança descreve o quanto a
evidência sustenta a observação; não substitui a distinção entre afirmado, evidenciado e lacuna.

## Handoff

Entregue a spec com as três categorias claramente identificadas. Quem for rodar
`generating-azure-boards-backlog-from-spec` sobre esse arquivo trata "Evidenciado pelo código" como
contexto Brownfield de estado atual, nunca como confirmação de valor ou decisão de negócio.
```

- [ ] **Passo 6: Rodar o teste para confirmar que ele passa**

Rode: `uv run pytest drafting-a-spec-from-business-request/tests/test_skill_integration.py -v`
Esperado: PASSA — 9 testes, 0 falhas.

- [ ] **Passo 7: Validar a estrutura da skill**

Rode: `uv run --with pyyaml python /Users/pedroct/.codex/skills/.system/skill-creator/scripts/quick_validate.py drafting-a-spec-from-business-request`
Esperado: `Skill is valid!`

- [ ] **Passo 8: Commit**

```bash
git add drafting-a-spec-from-business-request/
git commit -m "$(cat <<'EOF'
feat: add drafting-a-spec-from-business-request skill

Turns an informal business request (email, ticket) plus read-only
source inspection into a spec compatible with
generating-azure-boards-backlog-from-spec, without altering any of
the four existing skills.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 2: Conectar os testes da nova skill ao pytest/coverage do repositório

**Arquivos:**
- Modificar: `pyproject.toml:47-51` (`[tool.pytest.ini_options]` `testpaths`)

**Interfaces:**
- Consome: `drafting-a-spec-from-business-request/tests/test_skill_integration.py` da Tarefa 1 (só pelo caminho).
- Produz: uma execução de `pytest` a partir da raiz do repositório que descobre tanto os testes da skill existente quanto os da nova skill, para o passo de verificação da Tarefa 3.

- [ ] **Passo 1: Escrever a checagem que falha**

Rode: `uv run pytest -v` a partir da raiz do repositório.
Esperado (antes da edição): só os 2 arquivos de teste existentes em
`generating-azure-boards-backlog-from-spec/tests/` rodam;
`drafting-a-spec-from-business-request/tests/test_skill_integration.py` NÃO é coletado (está fora do
`testpaths` configurado), mesmo passando quando rodado diretamente. Isso confirma a lacuna de conexão.

- [ ] **Passo 2: Adicionar o novo diretório de testes ao testpaths**

Em `pyproject.toml`, encontre:

```toml
[tool.pytest.ini_options]
testpaths = [
  "generating-azure-boards-backlog-from-spec/tests",
]
addopts = "-ra"
```

Substitua por:

```toml
[tool.pytest.ini_options]
testpaths = [
  "generating-azure-boards-backlog-from-spec/tests",
  "drafting-a-spec-from-business-request/tests",
]
addopts = "-ra"
```

- [ ] **Passo 3: Rodar a suíte completa para confirmar que passa**

Rode: `uv run pytest -v` a partir da raiz do repositório.
Esperado: PASSA — os testes existentes mais os 9 novos testes de isolamento/conteúdo, todos coletados
e verdes (sem regressão nas quatro skills existentes, já que nenhum arquivo delas mudou).

- [ ] **Passo 4: Rodar de novo o quick_validate.py nas cinco skills**

Rode:

```bash
for skill_dir in \
  drafting-a-spec-from-business-request \
  generating-azure-boards-backlog-from-spec \
  refining-user-stories-with-3c \
  refining-user-stories-with-3w \
  refining-user-stories-with-gherkin; do
  uv run --with pyyaml python \
    /Users/pedroct/.codex/skills/.system/skill-creator/scripts/quick_validate.py \
    "$skill_dir"
done
```

Esperado: `Skill is valid!` impresso cinco vezes.

- [ ] **Passo 5: Commit**

```bash
git add pyproject.toml
git commit -m "$(cat <<'EOF'
test: discover drafting-a-spec-from-business-request tests in pytest

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 3: Documentar a nova skill no README.md

**Arquivos:**
- Modificar: `README.md` (três edições separadas e não adjacentes — ver abaixo)

**Interfaces:**
- Consome: o nome e o caminho da skill da Tarefa 1 (`drafting-a-spec-from-business-request/SKILL.md`), o padrão do loop de validação já presente no arquivo.
- Produz: nada consumido por tarefas posteriores — esta é a última tarefa de conteúdo.

- [ ] **Passo 1: Adicionar o ponto de entrada de pedido informal logo após o diagrama de pipeline existente**

Encontre este bloco exato (atualmente linhas 9–23 do `README.md`):

```markdown
```text
Spec
 └─ generating-azure-boards-backlog-from-spec
     └─ refining-user-stories-with-3c
         ├─ refining-user-stories-with-3w
         └─ refining-user-stories-with-gherkin
```

- **3W — Who, What, Why:** identifica ator, capacidade/resultado e valor, separando fatos de lacunas.
```

Insira um novo parágrafo e diagrama logo depois do fechamento ` ``` ` do diagrama de pipeline e antes
da lista `- **3W...`:

```markdown
Quando não existe spec escrita — só um pedido informal de negócio, como um e-mail ou ticket — a skill
`drafting-a-spec-from-business-request` investiga o código-fonte já disponível onde está instalada e
produz essa spec como um passo manual anterior:

```text
Pedido informal (e-mail, ticket) + código-fonte
 └─ drafting-a-spec-from-business-request
     └─ Spec
```
```

- [ ] **Passo 2: Adicionar uma linha à tabela "Skills disponíveis"**

Encontre:

```markdown
| Skill | Use quando | Saída principal |
|---|---|---|
| [`refining-user-stories-with-3w`](refining-user-stories-with-3w/SKILL.md) | Ator, objetivo ou benefício estão vagos | Mapa 3W, história/rascunho, perguntas e estado 3W |
```

Substitua por:

```markdown
| Skill | Use quando | Saída principal |
|---|---|---|
| [`drafting-a-spec-from-business-request`](drafting-a-spec-from-business-request/SKILL.md) | Só há um pedido informal de negócio (e-mail, ticket) e nenhuma spec escrita | Documento de spec em Markdown, com repositórios considerados, evidência de código e lacunas |
| [`refining-user-stories-with-3w`](refining-user-stories-with-3w/SKILL.md) | Ator, objetivo ou benefício estão vagos | Mapa 3W, história/rascunho, perguntas e estado 3W |
```

- [ ] **Passo 3: Adicionar a nova skill ao loop de validação e à lista de comandos do pytest**

Encontre:

```markdown
Execute a suíte completa da quarta skill:

```bash
uv run python -m unittest discover -s generating-azure-boards-backlog-from-spec/tests -v
```

Valide os quatro pacotes com o utilitário oficial:

```bash
for skill_dir in \
  generating-azure-boards-backlog-from-spec \
  refining-user-stories-with-3c \
  refining-user-stories-with-3w \
  refining-user-stories-with-gherkin; do
  uv run --with pyyaml python \
    /Users/pedroct/.codex/skills/.system/skill-creator/scripts/quick_validate.py \
    "$skill_dir"
done
```
```

Substitua por:

```markdown
Execute a suíte completa da quarta e da quinta skill:

```bash
uv run python -m unittest discover -s generating-azure-boards-backlog-from-spec/tests -v
uv run python -m unittest discover -s drafting-a-spec-from-business-request/tests -v
```

Valide os cinco pacotes com o utilitário oficial:

```bash
for skill_dir in \
  drafting-a-spec-from-business-request \
  generating-azure-boards-backlog-from-spec \
  refining-user-stories-with-3c \
  refining-user-stories-with-3w \
  refining-user-stories-with-gherkin; do
  uv run --with pyyaml python \
    /Users/pedroct/.codex/skills/.system/skill-creator/scripts/quick_validate.py \
    "$skill_dir"
done
```
```

- [ ] **Passo 4: Verificar que o diff só toca README.md, pyproject.toml e o novo diretório da skill**

Rode: `git status`
Esperado: `README.md` modificado; o novo diretório `drafting-a-spec-from-business-request/` (já
commitado na Tarefa 1); `pyproject.toml` (já commitado na Tarefa 2). Nenhum arquivo em
`refining-user-stories-with-3w/`, `refining-user-stories-with-3c/`, `refining-user-stories-with-gherkin/`
ou `generating-azure-boards-backlog-from-spec/` aparece como modificado — isso confirma a Restrição
Global de que nenhuma skill existente foi alterada.

- [ ] **Passo 5: Commit**

```bash
git add README.md
git commit -m "$(cat <<'EOF'
docs: document drafting-a-spec-from-business-request in README

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 4: Checagem manual de aceite contra o repositório Diligência

Esta tarefa é um exercício de verificação, não uma mudança de código no `gerador-hu` — seu resultado é
um julgamento registrado na conversa com o usuário, não um commit. Ela existe porque a estratégia de
testes da spec exige validar a skill contra o exemplo real que motivou o design (o cancelamento
duplicado do pré-Toaf) antes de considerar a funcionalidade concluída.

- [ ] **Passo 1: Instalar (ou usar um dry run) a skill onde ela de fato vai rodar**

A skill é pensada para viver dentro do próprio diretório da aplicação-alvo. Para esta checagem, copie
`drafting-a-spec-from-business-request/` para um local como `.claude/skills/` (ou equivalente) em
`/Users/pedroct/Projetos/sefaz/diligencia/` (a raiz do workspace que contém `diligencia-api`,
`diligencia-front`, `diligencia-mobile` como irmãos), ou siga as instruções da skill manualmente contra
esse caminho se ainda não houver mecanismo de instalação configurado. Confirme o `git status` do
`diligencia` antes, para não sobrescrever nada não commitado.

- [ ] **Passo 2: Rodar a skill contra o pedido real do P1**

Forneça à skill este texto de pedido de negócio, na íntegra:

```text
P1 - Título: Cancelamento do pre-toaf duplicado
O sistema esta permitindo dois cancelamentos seguidos do mesmo pre-toaf. Isso acontece quando o
usuário está trabalhando nas duas plataformas simultaneamente e esquece de atualizar a página. Nesse
cenário, ele pode cancelar um pre-toaf que já havia sido cancelado na outra plataforma sem que o
sistema gere um aviso. Nessa situação, o sistema deveria emitir uma mensagem de erro informando que o
pre-toaf já está cancelado, impedindo que o documento seja cancelado duas vezes. Após o fechamento da
mensagem o sistema deveria atualizar a página para que o usuário não consiga repetir a ação de
cancelamento.
```

- [ ] **Passo 3: Conferir a spec produzida contra esta checklist de aceite**

- [ ] A spec trata o pedido como um único escopo — sem divisão.
- [ ] `## Repositórios considerados` lista pelo menos `diligencia-api` como relevante (a lógica de
      cancelamento vive em `ToafService`/`DiligenciaController`, conforme o `grep` já feito nesta
      conversa), com um motivo declarado; `diligencia-front`/`diligencia-mobile` estão incluídos com
      motivo ou explicitamente marcados como não relevantes.
- [ ] `## Comportamento atual (evidência no código)` cita pelo menos um `caminho:linha` real dentro de
      `diligencia-api/src/main/java/br/gov/ce/sefaz/diligencia/...` (ex.: em `ToafService.java` ou
      `DiligenciaController.java`), não um caminho fabricado.
- [ ] `## Comportamento esperado` separa claramente o que o e-mail afirma explicitamente (mensagem de
      erro no cancelamento duplicado; atualização da página após o fechamento da mensagem) do que foi
      inferido.
- [ ] `## Lacunas e perguntas abertas` traz à tona os detalhes de fato indefinidos (ex.: texto exato da
      mensagem de erro, qual(is) papel(is) de ator são afetados, se "atualizar a página" significa um
      reload completo ou um re-fetch parcial) em vez de inventá-los.
- [ ] Nada no arquivo se parece com uma decomposição em Épico/Feature/História nem com
      `Acceptance Criteria` — isso permanece fora do escopo desta skill.

- [ ] **Passo 4: Reportar o resultado ao usuário**

Resuma, na conversa, se a checklist passou e — caso o pedido revele mais repositórios ou ambiguidade do
que o esperado — se isso muda a decisão de "sempre escopo único" tomada durante o brainstorming. Não
reinterprete essa decisão silenciosamente; se ela precisar ser revista, sinalize isso explicitamente e
peça a decisão do usuário antes de alterar a skill.

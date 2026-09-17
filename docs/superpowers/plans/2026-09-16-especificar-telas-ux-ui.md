# Especificar telas UX-UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Criar a skill `especificar-telas-ux-ui`, que roda sobre uma Spec antes da geração do backlog e identifica, por inspeção somente leitura do código de front-end (web e mobile) — nunca por interpretação do texto de negócio —, quais requisitos exigem tela nova ou fluxo de tela alterado, produzindo conteúdo em linguagem de UX-UI e uma anotação que `gerar-backlog-azure-boards` consome como input opcional para criar uma User Story de design dependente do item funcional.

**Architecture:** Skill-folha nova, no padrão já estabelecido pelo repositório (`SKILL.md` + `references/` + `agents/openai.yaml` + `tests/test_skill_integration.py`, testado por asserções de string sobre o conteúdo Markdown/YAML). `gerar-backlog-azure-boards` ganha um passo que lê a saída dessa skill nova como arquivo opcional (nunca como invocação) e um campo textual novo (`Depende de`/`Bloqueia`) no contrato do backlog. `redigir-spec-pedido-negocio` ganha uma sugestão condicional da skill nova, no mesmo padrão já usado para `entrevistar-lacunas-requisito` e `revisar-textos-requisitos`.

**Tech Stack:** Markdown (conteúdo das skills), YAML (`agents/openai.yaml`), Python 3.12 + `unittest`/`pytest` (testes de conteúdo), `uv` (execução), `pyproject.toml` (`testpaths`).

**Spec:** `docs/superpowers/specs/2026-09-16-especificar-telas-ux-ui-design.md`

## Global Constraints

- Todo conteúdo criado (SKILL.md, referências, testes, commits) é em português brasileiro — `CLAUDE.md` do projeto.
- A skill nova é folha: nunca contém `REQUIRED SUB-SKILL` e nunca invoca outra skill do repositório por nome com verbo de invocação (`use|chame|chamar|invoque|invocar|encaminhe|encaminhar|passe|execute|aplique|carregue`) — spec, seção *Boundaries da skill nova*.
- Nunca acessa Figma nem qualquer ferramenta de design externa; toda a análise é Spec + código-fonte — spec, *Fora de escopo*.
- Nunca define copy final de interface; sempre indica `revisar-textos-requisitos` como revisão manual opcional quando há texto voltado ao usuário — spec, *Fora de escopo*.
- Nunca cria item do tipo Task nem Bug para necessidade de tela; sempre uma User Story de design nova — spec, *Fora de escopo*.
- Sempre um item de design por plataforma necessária; nunca agrupa web e mobile no mesmo item — spec, *Regra de agrupamento em itens de design*.
- O campo `Depende de`/`Bloqueia` é só informativo: não substitui `Parent` e não altera a prontidão calculada pela 3C — spec, *Mudanças em `gerar-backlog-azure-boards`*.
- Nunca serializa `Implementado` por ausência de evidência de código — spec, *Classificação por requisito × plataforma*.
- Nenhuma skill cria, atualiza ou publica work items no Azure Boards.

---

## Task 1: Criar a skill `especificar-telas-ux-ui`

**Files:**
- Create: `especificar-telas-ux-ui/SKILL.md`
- Create: `especificar-telas-ux-ui/references/ui-brownfield-validation.md`
- Create: `especificar-telas-ux-ui/agents/openai.yaml`
- Test: `especificar-telas-ux-ui/tests/test_skill_integration.py`

**Interfaces:**
- Consumes: nada — skill-folha, primeiro artefato do pipeline novo.
- Produces (para a Task 2 consumir por referência textual, não por import):
  - Nome da skill: `especificar-telas-ux-ui`.
  - Nome da seção que ela escreve na Spec: `## Necessidade de especificação de tela`.
  - Nome do documento companheiro: `Spec: Telas UX-UI — <contexto>`.
  - Vocabulário de status: `Implementado`, `Parcialmente implementado`, `Não encontrado`, `Impossível validar`, `Não aplicável`.
  - Campo `Bloqueia` no item de design (texto livre nesta etapa; a Task 2 o transforma em chave real).

- [ ] **Step 1: Criar o diretório de testes e escrever o teste que falha**

Crie o arquivo `especificar-telas-ux-ui/tests/test_skill_integration.py`:

```python
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class SkillIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        skill_dir = ROOT / "especificar-telas-ux-ui"
        cls.skill = (skill_dir / "SKILL.md").read_text()
        cls.reference = (
            skill_dir / "references" / "ui-brownfield-validation.md"
        ).read_text()
        cls.agent = (skill_dir / "agents" / "openai.yaml").read_text()

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
                        msg=f"leaf skill calls {skill_name!r}: {line}",
                    )

    def test_skill_has_discoverable_contract(self):
        self.assertIn("name: especificar-telas-ux-ui", self.skill)
        self.assertIn("Use quando", self.skill)
        self.assertIn("tela nova ou fluxo de tela alterado", self.skill)

    def test_skill_is_leaf_and_never_invokes_other_skills(self):
        self.assertNotIn("REQUIRED SUB-SKILL", self.skill)
        other_skill_names = (
            "redigir-spec-pedido-negocio",
            "entrevistar-lacunas-requisito",
            "gerar-backlog-azure-boards",
            "refinar-historias-3c",
            "refinar-historias-3w",
            "refinar-historias-gherkin",
            "especificar-debitos-tecnicos",
            "revisar-textos-requisitos",
            "publicar-backlog-azure-boards",
        )
        self.assert_has_no_named_skill_invocation(self.skill, other_skill_names)

    def test_skill_declares_mode_per_platform(self):
        self.assertIn("Modo Web", self.skill)
        self.assertIn("Modo Mobile", self.skill)
        self.assertIn("Greenfield-UI", self.skill)
        self.assertIn("Brownfield-UI", self.skill)
        self.assertIn("Não aplicável", self.skill)

    def test_skill_delegates_copy_to_revisar_textos_requisitos(self):
        self.assertIn("revisar-textos-requisitos", self.skill)
        self.assertIn("não defina o texto final", self.skill)

    def test_skill_never_creates_task_or_bug_for_screen_need(self):
        self.assertIn(
            "Não crie item do tipo Task nem Bug para necessidade de tela",
            self.skill,
        )
        self.assertIn("sempre uma User Story de design nova", self.skill)

    def test_skill_groups_one_design_item_per_platform(self):
        self.assertIn("Sempre um item por plataforma necessária", self.skill)
        self.assertIn(
            "nunca agrupe web e mobile no mesmo item de design", self.skill
        )

    def test_screen_script_avoids_gherkin_syntax(self):
        self.assertIn("sem sintaxe Gherkin", self.skill)
        self.assertIn("sem `Dado/Quando/Então`", self.skill)

    def test_reference_defines_matrix_and_exact_statuses(self):
        self.assertIn(
            "| Requisito | Plataforma | Evidência `caminho:linha` | Status | Confiança |",
            self.reference,
        )
        expected_statuses = (
            "`Implementado`",
            "`Parcialmente implementado`",
            "`Não encontrado`",
            "`Impossível validar`",
            "`Não aplicável`",
        )
        for status in expected_statuses:
            self.assertIn(status, self.reference)
        self.assertIn(
            "Ausência de evidência não significa `Implementado`", self.reference
        )

    def test_reference_inspection_is_read_only_without_authorization(self):
        for command in ("`rg`", "`find`", "`git status`"):
            self.assertIn(command, self.reference)
        self.assertIn("sem autorização explícita", self.reference)

    def test_reference_never_creates_requirement_from_incidental_code(self):
        self.assertIn(
            "Compare o código somente com a necessidade de tela do requisito da spec",
            self.reference,
        )

    def test_skill_has_openai_metadata_in_portuguese(self):
        self.assertIn('display_name: "Especificar telas UX-UI"', self.agent)
        self.assertIn("$especificar-telas-ux-ui", self.agent)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Rodar o teste e confirmar a falha**

Run: `uv run python -m unittest especificar-telas-ux-ui.tests.test_skill_integration -v`
Expected: erro `FileNotFoundError` (ou `ModuleNotFoundError`), porque `especificar-telas-ux-ui/SKILL.md` ainda não existe.

- [ ] **Step 3: Escrever `especificar-telas-ux-ui/SKILL.md`**

```markdown
---
name: especificar-telas-ux-ui
description: Use quando uma spec de produto ou software precisa ser analisada, antes da geração do backlog, para identificar quais requisitos exigem tela nova ou fluxo de tela alterado em front-end web e/ou mobile, produzindo conteúdo em linguagem de UX-UI rastreável ao código-fonte.
---

# Especificar telas para UX-UI a partir da Spec

## Objetivo

Identificar, por inspeção somente leitura do código de front-end já existente — nunca por interpretação
do texto de negócio —, quais requisitos de uma Spec exigem que a equipe de UX-UI especifique uma tela
nova ou um fluxo de tela alterado, em front-end web e/ou em aplicativo mobile, antes que a implementação
funcional possa avançar. A saída é conteúdo em linguagem acessível à equipe de UX-UI, sem sintaxe
Gherkin, rastreável ao requisito de origem, mais uma anotação na própria Spec para consumo opcional por
`gerar-backlog-azure-boards`.

## Escopo

Trate cada requisito da spec com faceta de UI, por plataforma aplicável, independentemente. Esta skill
não decompõe a spec em Épico, Feature ou item de folha — isso continua sendo papel de
`gerar-backlog-azure-boards`. Não decide texto final de interface (título, label, CTA, mensagem de
sucesso/erro/vazio, tooltip) — isso é escopo de `revisar-textos-requisitos`.

## Modo, por plataforma

Declare o Modo de web e de mobile **separadamente**, porque as duas plataformas podem estar em estágios
de maturidade diferentes:

- **Greenfield-UI:** nenhum código de front-end relevante acessível para aquela plataforma. Todo
  requisito com faceta de UI aplicável a ela é tratado como "necessita especificação de tela", porque não
  há nada para comparar. Registre a ausência e não exija uma inspeção inexistente.
- **Brownfield-UI:** há código acessível para aquela plataforma. Inspecione somente leitura — rotas,
  páginas, telas, componentes — em busca de uma tela ou fluxo equivalente ao requisito.
- Presença ambígua em qualquer plataforma → trate como Brownfield-UI conservador para ela, registre a
  incerteza e os limites da busca; nunca conclua ausência de tela pela falta de investigação.
- Se o produto genuinamente não tiver uma das plataformas no seu escopo, registre `Não aplicável` para
  ela — diferente de `Impossível validar` (a plataforma existe, mas não foi possível inspecionar o código
  correspondente).

A skill não recebe caminho de projeto como parâmetro: investigue a partir do diretório onde está
instalada e de seus repositórios irmãos, procurando sinais convencionais de cada stack (por exemplo,
front-end web via framework de rotas/páginas; mobile via projeto React Native, Flutter ou nativo
Android/iOS). Registre quais repositórios parecem relevantes a cada plataforma e quais foram descartados,
com o motivo — mesmo padrão de "Repositórios considerados" de `redigir-spec-pedido-negocio`.

## Fluxo

1. **Leia a spec inteira** e monte um inventário de requisitos, preservando origem (seção/âncora).
2. **Descubra os repositórios candidatos** de web e de mobile e declare o Modo de cada plataforma.
3. **Para cada requisito, determine a(s) plataforma(s) aplicável(is):** se a spec especificar
   explicitamente uma plataforma, use essa; caso contrário, o requisito se aplica a todas as plataformas
   que existirem no produto (uma plataforma `Não aplicável` fica de fora).
4. **Confirme a faceta de UI** do requisito a partir do texto da spec. Sem faceta de UI, ignore — não
   inspecione código nenhum para esse requisito. Se o único impacto identificado for texto/copy (sem tela
   nova nem fluxo alterado), também ignore e indique `revisar-textos-requisitos` como próximo passo
   manual opcional.
5. **Para cada par (requisito, plataforma) com faceta de UI estrutural**, antes de inspecionar, leia e
   aplique [references/ui-brownfield-validation.md](references/ui-brownfield-validation.md): inspeção
   somente leitura, formato de evidência `caminho:linha` e o vocabulário de status.
6. **Classifique** cada par com exatamente um destes status: `Implementado`, `Parcialmente implementado`,
   `Não encontrado`, `Impossível validar`, `Não aplicável`. Ausência de evidência nunca é serializada como
   `Implementado`.
7. **Gere um item de design somente quando o status não for `Implementado` nem `Não aplicável`.** Sempre
   um item por plataforma necessária — nunca agrupe web e mobile no mesmo item de design, mesmo quando o
   requisito funcional correspondente for único para as duas plataformas.
8. **Escreva o roteiro de tela** de cada item gerado: lista numerada, em linguagem simples, sem sintaxe
   Gherkin (sem `Dado/Quando/Então`, sem `Funcionalidade`/`Cenário`) — situação → ação do usuário → o que
   muda na tela. Rastreie cada item do roteiro a uma regra ou trecho do requisito de origem.
9. **Registre a necessidade de copy** de cada item gerado quando o roteiro envolver texto voltado ao
   usuário (label, mensagem, CTA, estado vazio/erro): liste os pontos e indique `revisar-textos-requisitos`
   como próximo passo manual opcional — não defina o texto final.
10. **Anote a Spec** com a seção `## Necessidade de especificação de tela` e **salve o documento
    separado** `Spec: Telas UX-UI — <contexto>`, no formato de
    [Formato das saídas](#formato-das-saídas).
11. **Pare.** Não invoque nenhuma outra skill. Reporte ao usuário os caminhos salvos e sugira
    `gerar-backlog-azure-boards` como próximo passo manual.

## Formato das saídas

### Anotação na Spec

```markdown
## Necessidade de especificação de tela
| Requisito | Plataforma | Status de cobertura | Referência |
|---|---|---|---|
| [seção/âncora do requisito] | Web \| Mobile | Não encontrado \| Parcialmente implementado \| Impossível validar | TL-01 |
```

Sem nenhum requisito sinalizado, registre exatamente `Nenhuma necessidade de tela identificada` em vez de
omitir a seção.

### Documento separado — `Spec: Telas UX-UI — <contexto>`

```markdown
# Spec: Telas UX-UI — <contexto>

## Contexto e origem
<spec de origem, seção ou demanda relacionada>

## Descoberta de plataformas
| Plataforma | Repositório considerado | Relevante? | Motivo |
|---|---|---|---|
| Web | [nome ou "nenhum encontrado"] | Sim/Não | [justificativa] |
| Mobile | [nome ou "nenhum encontrado"] | Sim/Não | [justificativa] |

## Modo
- Modo Web: Greenfield-UI | Brownfield-UI
- Modo Mobile: Greenfield-UI | Brownfield-UI

## Resumo priorizado
| Item | Requisito de origem | Plataforma | Status de cobertura |
|---|---|---|---|
| TL-01 | ... | Web | Não encontrado |

## TL-01 — <título curto, com a plataforma no nome>
### Título
<título curto, acionável, sem ID do Azure Boards>
### Origem
<seção/âncora da Spec>
### Plataforma
Web ou Mobile
### Card
Como equipe de UX-UI, quero especificar a tela <plataforma> de <resultado>, para permitir a
implementação de <requisito de origem>.
### Evidência de código
- Status: Implementado | Parcialmente implementado | Não encontrado | Impossível validar | Não aplicável
- Referência: `caminho:linha`, ou o motivo quando não houver referência
### Roteiro de tela
1. <situação> → <ação do usuário> → <o que muda na tela>
### Necessidade de copy
<pontos de texto voltado ao usuário, indicando revisar-textos-requisitos como próximo passo manual
opcional; ou "Não identificada">
### Referências ao Design System
<componente/padrão já conhecido pela spec ou pelo código; ou "Nenhuma referência confiável disponível">
### Bloqueia
<referência ao requisito funcional de origem por seção/âncora da Spec>
### Lacunas
<perguntas ou decisões pendentes>
```

Repita a seção do item para cada par (requisito, plataforma) sinalizado. Use `TL-01`, `TL-02` apenas como
chaves documentais deste documento; elas não são IDs de work items nem chaves `E.F.S` do backlog.

## Boundaries

- Skill-folha: nunca invoque nenhuma outra skill deste repositório; ao terminar, sugira
  `gerar-backlog-azure-boards` como próximo passo manual do usuário.
- Não acesse Figma nem qualquer ferramenta de design externa; toda a análise é Spec + código-fonte.
- Não decida nem escreva copy final de interface; indique `revisar-textos-requisitos` como revisão manual
  opcional quando o roteiro de tela envolver texto voltado ao usuário.
- Não execute build, testes, servidores ou o aplicativo; inspeção somente leitura, sem autorização
  explícita para qualquer execução.
- Não invente componente ou padrão de Design System sem origem confirmada na Spec ou no código.
- Não decida prontidão nem produza Conversation, Card, Gherkin ou prontidão geral — o roteiro de tela é
  insumo para a 3C, não um veredito.
- Não crie, atualize ou publique work items no Azure Boards.
- Nunca serializa `Implementado` por ausência de evidência de código.
- Não crie item do tipo Task nem Bug para necessidade de tela — sempre uma User Story de design nova.
- Não divida o item funcional por plataforma — só multiplica o item de design quando necessário.
```

- [ ] **Step 4: Escrever `especificar-telas-ux-ui/references/ui-brownfield-validation.md`**

```markdown
# Validação Brownfield de telas (web e mobile)

Leia esta referência somente quando houver código de front-end relevante para a plataforma em análise, ou
quando sua presença for ambígua. O objetivo é descrever a cobertura de tela atual com evidência
verificável, por plataforma, antes de decidir se a equipe de UX-UI precisa especificar algo novo.

## Inspeção segura

1. Registre a raiz analisada por plataforma, os limites de escopo e qualquer incerteza sobre qual
   repositório implementa o front-end web ou o app mobile do produto.
2. Faça somente leitura segura: inventário com `rg` (incluindo `rg --files`) ou `find`, estado do
   repositório com `git status`, leitura de arquivos de rotas/páginas/telas/componentes e de
   configuração. Use a ferramenta menos abrangente que responda à pergunta.
3. Não execute scripts, testes, builds, servidores, migrações, o aplicativo mobile nem o front-end web
   sem autorização explícita. Não altere arquivos, dependências nem configuração como parte da
   validação.
4. Inspecione rotas, páginas, telas, componentes e seus estados somente quando forem relevantes ao
   requisito inventariado da spec. O nome de um arquivo ou componente isolado não prova que o fluxo
   completo já está coberto.

Se o repositório de uma plataforma não puder ser localizado ou lido com segurança, mantenha o modo
Brownfield-UI para ela, registre o limite e classifique o que não pôde ser determinado como `Impossível
validar`; não preencha lacunas com plausibilidade.

## Regra de comparação

Compare o código somente com a necessidade de tela do requisito da spec. Código existente não confirma
valor, decisão de negócio nem regra de negócio — ele descreve apenas o estado atual da interface. Um
componente ou tela encontrados sem relação com o requisito não criam necessidade nem a descartam.

Para cada par (requisito, plataforma) com faceta de UI:

- procure evidência direta de uma tela ou fluxo equivalente ao que o requisito pede;
- cite cada evidência útil como caminho relativo à raiz e linha inicial, por exemplo
  `src/telas/Diligencia/ReaberturaScreen.tsx:18`;
- distinga tela/componente de produção de arquivos de teste ou storybook na síntese; um teste de
  interface existente pode aumentar confiança, mas não substitui evidência da tela implementada;
- registre `Nenhuma evidência encontrada` quando a busca relevante estiver concluída, ou `Evidência
  indisponível: [motivo]` quando não foi possível validar. Nunca invente caminho ou linha.

Ausência de evidência não significa `Implementado`. Use exatamente um destes status por par
(requisito, plataforma):

| Status | Quando usar |
|---|---|
| `Implementado` | A tela ou o fluxo já cobre a capacidade e os estados exigidos pelo requisito no escopo analisado. |
| `Parcialmente implementado` | A tela existe, mas falta um estado, campo, etapa ou variação exigida pelo requisito. |
| `Não encontrado` | A inspeção relevante foi concluída e não encontrou tela ou fluxo para o requisito. |
| `Impossível validar` | A raiz, os arquivos ou a evidência necessários não estavam acessíveis, ou o escopo permaneceu ambíguo. |
| `Não aplicável` | O produto genuinamente não tem essa plataforma no seu escopo. |

`Confiança` qualifica a conclusão (`Alta`, `Média` ou `Baixa`) e não substitui o status.

## Matriz obrigatória

Produza uma linha por par (requisito, plataforma) com faceta de UI.

| Requisito | Plataforma | Evidência `caminho:linha` | Status | Confiança |
|---|---|---|---|---|
| [requisito e origem na spec] | Web \| Mobile | [uma ou mais referências, nenhuma evidência ou motivo da indisponibilidade] | [status exato] | [Alta, Média ou Baixa] |

A matriz é insumo de análise; não decide sozinha o conteúdo do roteiro de tela nem substitui o Card da 3C
do item de design gerado depois pelo backlog.

## Política de geração de item

- `Parcialmente implementado`, `Não encontrado` e `Impossível validar` geram um item de design candidato,
  um por plataforma.
- `Implementado` não gera item — a tela já cobre o requisito naquela plataforma.
- `Não aplicável` não gera item — a plataforma não existe no escopo do produto.

Compare o código somente com a necessidade de tela do requisito da spec: não transforme componente,
decisão técnica ou tela incidental encontrada no código, sem relação com o requisito, em necessidade de
especificação de tela.
```

- [ ] **Step 5: Escrever `especificar-telas-ux-ui/agents/openai.yaml`**

```yaml
interface:
  display_name: "Especificar telas UX-UI"
  short_description: "Identifica necessidade de tela nova ou alterada, por código"
  default_prompt: "Use $especificar-telas-ux-ui para identificar, a partir da spec e do código de front-end, quais requisitos precisam de tela nova ou alterada para a equipe de UX-UI."
```

- [ ] **Step 6: Rodar o teste e confirmar que passa**

Run: `uv run python -m unittest especificar-telas-ux-ui.tests.test_skill_integration -v`
Expected: `OK` — as 11 asserções passam.

- [ ] **Step 7: Commit**

```bash
git add especificar-telas-ux-ui/
git commit -m "$(cat <<'EOF'
feat: cria a skill especificar-telas-ux-ui

Identifica, por inspeção somente leitura do código de front-end (web e
mobile), quando um requisito de uma Spec exige tela nova ou fluxo de tela
alterado, produzindo um brief em linguagem de UX-UI sem sintaxe Gherkin,
rastreável ao requisito de origem e à evidência de código.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 2: Conectar `gerar-backlog-azure-boards` ao input opcional de telas

**Files:**
- Modify: `gerar-backlog-azure-boards/SKILL.md`
- Modify: `gerar-backlog-azure-boards/references/backlog-markdown-contract.md`
- Modify: `gerar-backlog-azure-boards/tests/test_skill_integration.py`
- Modify: `README.md`

**Interfaces:**
- Consumes (de Task 1): nome da skill `especificar-telas-ux-ui`, nome da seção `## Necessidade de
  especificação de tela`, nome do documento `Spec: Telas UX-UI`.
- Produces (para a Task 3 e para publicação futura): heading `## Depende de e Bloqueia` (âncora
  `#depende-de-e-bloqueia`) em `backlog-markdown-contract.md`; nova numeração de passos do `## Workflow`
  de `gerar-backlog-azure-boards/SKILL.md` (1 a 12, era 1 a 11).

- [ ] **Step 1: Escrever os testes que falham**

Abra `gerar-backlog-azure-boards/tests/test_skill_integration.py` e acrescente estes métodos à classe
`SkillIntegrationTests` (após `test_contract_and_readme_document_both_modes`, antes do
`if __name__ == "__main__":`):

```python
    def test_backlog_consumes_telas_output_as_file_not_invocation(self):
        self.assertIn(
            "como input opcional por arquivo — nunca como invocação de "
            "`especificar-telas-ux-ui`",
            self.backlog,
        )
        self.assert_has_no_named_skill_invocation(
            self.backlog,
            ("especificar-telas-ux-ui",),
        )

    def test_backlog_pairs_design_item_and_fills_dependency_fields(self):
        self.assertIn(
            "crie a User Story de design correspondente como item-irmão do item funcional "
            "que ela bloqueia, sob a mesma Feature",
            self.backlog,
        )
        self.assertIn(
            "Um item de design nascido do passo 2 é sempre `User Story`", self.backlog
        )
        self.assertIn(
            "preencha `Depende de` no item funcional com a chave `E.F.S` do item de "
            "design, e `Bloqueia` no item de design com a chave `E.F.S` do item funcional",
            self.backlog,
        )

    def test_backlog_boundaries_mark_dependency_field_as_informative(self):
        self.assertIn(
            "O campo `Depende de`/`Bloqueia`, quando presente, é informativo",
            self.backlog,
        )

    def test_contract_documents_depende_de_and_bloqueia_as_informative(self):
        self.assertIn("## Depende de e Bloqueia", self.backlog_contract)
        self.assertIn(
            "Não altera a prontidão calculada pela 3C", self.backlog_contract
        )
        self.assertIn(
            "não é um novo nível hierárquico e não substitui `Parent`",
            self.backlog_contract,
        )

    def test_readme_documents_screen_spec_skill(self):
        self.assertIn("especificar-telas-ux-ui", self.readme)
        self.assertIn("Telas UX-UI", self.readme)
```

- [ ] **Step 2: Rodar os testes e confirmar a falha**

Run: `uv run python -m unittest gerar-backlog-azure-boards.tests.test_skill_integration -v`
Expected: 5 `FAIL` novos (os métodos acima), o restante continua `OK`.

- [ ] **Step 3: Atualizar o `## Workflow` de `gerar-backlog-azure-boards/SKILL.md`**

Substitua o bloco `## Workflow` inteiro (do `1. Leia a spec inteira...` até o final do item `11.`) por:

```markdown
## Workflow
1. Leia a spec inteira e crie um inventário de objetivos, atores, capacidades, regras, restrições, exemplos, conflitos e lacunas com suas origens.
2. Leia a seção `## Necessidade de especificação de tela` da spec e o documento companheiro `Spec: Telas UX-UI — <contexto>`, quando existirem, como input opcional por arquivo — nunca como invocação de `especificar-telas-ux-ui`. Sem esses arquivos, prossiga normalmente: a skill continua funcionando sem eles.
3. Detecte o modo. Em Brownfield, conclua a inspeção segura e a matriz `requisito | evidência caminho:linha | status | impacto | confiança` antes da decomposição. Em Greenfield, prossiga somente com a spec e registre que código relevante está ausente.
4. Agrupe objetivos amplos em Épicos; capacidades significativas em Features; resultados coesos para um ator em itens de folha (Histórias ou Bugs). Não crie itens para preencher níveis. Para cada par (requisito, plataforma) sinalizado no passo 2, crie a User Story de design correspondente como item-irmão do item funcional que ela bloqueia, sob a mesma Feature — nunca como Task, nunca como Bug.
5. Em Brownfield, gere trabalho acionável para lacunas, divergências e mudanças exigidas pela spec. Requisitos classificados como `Implementado` permanecem na cobertura e não geram itens duplicados por padrão. Se o usuário pedir documentação de comportamento existente, o item pode ser mantido como `Implementado`, explicitando que não representa trabalho novo. Para cada item de folha, decida o tipo por [references/backlog-markdown-contract.md](references/backlog-markdown-contract.md#política-de-tipo-user-story-vs-bug): use `Bug` quando a spec classifica aquele resultado específico como `Defeito` ou o status Brownfield é `Divergente`; use `User Story` nos demais casos, inclusive para capacidade nova dentro de uma spec classificada como `Defeito`. A decisão é por item, nunca herdada cegamente da classificação única da spec; registre o tipo escolhido e a justificativa junto à evidência do item. Um item de design nascido do passo 2 é sempre `User Story`, independentemente do tipo do item funcional que ele bloqueia.
6. Sugestões, propostas ou hipóteses não confirmadas nunca originam Épico, Feature, item de folha ou regra; registre-as somente em `Itens não cobertos` ou na Conversation de uma demanda confirmada, preservando origem e estado. Código existente também não cria requisito nem confirma decisão de negócio.
7. Para cada História ou Bug, **REQUIRED SUB-SKILL:** use refinar-historias-3c. Em Brownfield, forneça a evidência de implementação somente como contexto rotulado do estado atual. Consuma o resultado da 3C sem recalcular 3W, Conversation, Confirmation ou prontidão. Isso vale igualmente para Bugs: o Card de um Bug ainda usa 3W (Who é afetado pelo comportamento incorreto, What é o comportamento correto esperado, Why é o dano evitado). Para um item de design nascido do passo 2, forneça o roteiro de tela de `Spec: Telas UX-UI` como contexto rotulado de entrada para a Conversation/Gherkin da 3C — a 3C continua sendo a única dona da prontidão desse item também.
8. Numere `E.0.0`, `E.F.0`, `E.F.S`; preserve chaves existentes em atualizações. Declare cada relação no bloco `Parent`; posição e numeração não substituem o pai explícito. Histórias e Bugs sob a mesma Feature compartilham a mesma sequência `S` (são tipos irmãos de folha, não sequências separadas). Depois de numerar um par item funcional/item de design, preencha `Depende de` no item funcional com a chave `E.F.S` do item de design, e `Bloqueia` no item de design com a chave `E.F.S` do item funcional, conforme [references/backlog-markdown-contract.md](references/backlog-markdown-contract.md#depende-de-e-bloqueia).
9. Renderize apenas os metadados mínimos, a evidência necessária por item e a política de cobertura conforme [references/backlog-markdown-contract.md](references/backlog-markdown-contract.md). A matriz Brownfield é insumo de análise; não a reproduza como `Validation Summary` no Markdown final.
10. Execute `uv run python scripts/validate_backlog.py CAMINHO`; com backlog existente, acrescente `--update`. Corrija violações estruturais e revise semanticamente rastreabilidade, agrupamento, cobertura Brownfield e ausência de regras fabricadas.
11. Entregue o backlog mesmo com Histórias ou Bugs `Não pronta`. Para cada um, liste as lacunas de Card, Conversation e Confirmation que a bloqueiam e sugira ao usuário registrá-las em `## Lacunas e perguntas abertas` da spec de origem e rodar `entrevistar-lacunas-requisito` (quando instalada); depois de cada rodada de respostas, regenere o backlog e repita a sugestão até todos os itens de folha ficarem `Prontos` ou até o usuário adiar explicitamente uma lacuna.
12. Se houver copy voltada ao usuário nos requisitos ou nos itens de folha, indique ao usuário a skill `revisar-textos-requisitos` como revisão manual opcional. Essa indicação não bloqueia a geração, não cria trabalho novo e não é uma chamada direta à skill.
```

- [ ] **Step 4: Acrescentar a nova regra ao `## Boundaries` de `gerar-backlog-azure-boards/SKILL.md`**

Ao final do bloco `## Boundaries` (depois da linha que termina em "não decida por conveniência nem herde
cegamente a classificação única da spec quando ela cobrir mais de um resultado."), acrescente:

```markdown
- O campo `Depende de`/`Bloqueia`, quando presente, é informativo: nasce apenas do input opcional de `especificar-telas-ux-ui`, não substitui `Parent` e não altera a prontidão calculada pela 3C.
```

- [ ] **Step 5: Acrescentar a seção `## Depende de e Bloqueia` a `backlog-markdown-contract.md`**

Insira esta seção nova entre `## Numeração e atualização` e `## Template completo`:

```markdown
## Depende de e Bloqueia

Campo opcional, presente apenas quando o item nasceu do fluxo de `especificar-telas-ux-ui` (uma seção
`## Necessidade de especificação de tela` na spec de origem, com o documento companheiro `Spec: Telas
UX-UI`). Um item funcional (User Story ou Bug) que depende de tela declara `Depende de` com uma ou mais
chaves `E.F.S`, uma por plataforma que precisa de especificação; o item de design correspondente (sempre
`User Story`) declara `Bloqueia` com a chave `E.F.S` do item funcional que ele libera.

- É texto informativo dentro de `Description`, na mesma seção da Conversation — não é um novo nível
  hierárquico e não substitui `Parent`.
- Não altera a prontidão calculada pela 3C: um item pode estar `Pronto` segundo Card, Conversation e
  Confirmation mesmo com `Depende de` apontando para um item de design ainda não `Pronto`. A 3C continua
  sendo a única dona da prontidão geral.
- Não cria nem representa o link formal Predecessor/Sucessor do Azure Boards; essa relação, quando
  existir na importação, é responsabilidade de uma etapa de publicação futura.
- Sempre um item de design por plataforma necessária: um item funcional que depende de tela em web e em
  mobile declara `Depende de` com as duas chaves.
```

- [ ] **Step 6: Atualizar `README.md`**

6a. No parágrafo de abertura (linha que hoje diz `O fluxo combina sete capacidades complementares:`),
troque `sete` por `nove`.

6b. Depois do bloco de fluxo de `especificar-debitos-tecnicos` (o trecho que termina em
"`gerar-backlog-azure-boards (etapa manual)`" e antes da lista de bullets `- **Drafting a partir de
pedido de negócio:**...`), insira:

```markdown
Antes da geração do backlog, quando um requisito envolve tela nova ou fluxo de tela alterado em
front-end web ou mobile, `especificar-telas-ux-ui` identifica essa necessidade por inspeção de código —
nunca pelo texto de negócio — e anota a spec para consumo opcional do passo seguinte:

```text
Spec
 └─ especificar-telas-ux-ui (opcional, se instalada)
     └─ Spec anotada + Spec: Telas UX-UI — <contexto>
         └─ gerar-backlog-azure-boards (nova rodada, consome como arquivo opcional)
```
```

6c. Na lista de bullets de capacidades (depois do bullet `- **Spec de débitos técnicos:**...` e antes do
parágrafo `As dependências são acíclicas...`), insira:

```markdown
- **Telas UX-UI:** identifica, por inspeção somente leitura do código de front-end (web e mobile), quais requisitos exigem tela nova ou fluxo alterado; produz um brief em linguagem de UX-UI e uma anotação consumida opcionalmente por `gerar-backlog-azure-boards`, que cria uma User Story de design dependente do item funcional.
```

6d. No parágrafo `As dependências são acíclicas...`, ao final (depois da frase que termina em "quando um
débito for identificado e devolve sua spec separada para a geração manual do backlog."), acrescente a
frase:

```markdown
`especificar-telas-ux-ui` também é folha e nunca é chamada incondicionalmente; é referenciada, de forma condicional, por `redigir-spec-pedido-negocio` e consumida por `gerar-backlog-azure-boards` apenas como arquivo opcional, nunca como invocação.
```

6e. Na tabela `## Skills disponíveis`, acrescente uma linha depois da linha de
`gerar-backlog-azure-boards`:

```markdown
| [`especificar-telas-ux-ui`](especificar-telas-ux-ui/SKILL.md) | Um requisito da spec pode exigir tela nova ou fluxo de tela alterado em web e/ou mobile | Anotação de necessidade de tela na spec + `Spec: Telas UX-UI` com Card, roteiro de tela e evidência de código, por plataforma |
```

6f. Na seção `## Validação e desenvolvimento`, acrescente uma linha ao bloco de `uv run python -m
unittest discover`:

```markdown
uv run python -m unittest discover -s especificar-telas-ux-ui/tests -v
```

6g. Na lista `for skill_dir in ...` da mesma seção (o loop de `quick_validate.py`), acrescente
`especificar-telas-ux-ui` como novo item da lista, antes do `especificar-debitos-tecnicos;`.

- [ ] **Step 7: Rodar os testes e confirmar que passam**

Run: `uv run python -m unittest gerar-backlog-azure-boards.tests.test_skill_integration -v`
Expected: `OK` — todos os testes (os pré-existentes e os 5 novos) passam.

- [ ] **Step 8: Commit**

```bash
git add gerar-backlog-azure-boards/SKILL.md gerar-backlog-azure-boards/references/backlog-markdown-contract.md gerar-backlog-azure-boards/tests/test_skill_integration.py README.md
git commit -m "$(cat <<'EOF'
feat: gerar-backlog-azure-boards consome a saída de especificar-telas-ux-ui

Novo passo lê a anotação de telas da spec e a Spec: Telas UX-UI como
input opcional por arquivo, cria a User Story de design como item-irmão
do item funcional correspondente e preenche os campos textuais Depende
de/Bloqueia, sem alterar Parent nem a prontidão exclusiva da 3C.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 3: Sugerir a skill nova em `redigir-spec-pedido-negocio` e registrar o testpath

**Files:**
- Modify: `redigir-spec-pedido-negocio/SKILL.md`
- Modify: `redigir-spec-pedido-negocio/tests/test_skill_integration.py`
- Modify: `pyproject.toml`

**Interfaces:**
- Consumes (de Task 1): nome da skill `especificar-telas-ux-ui`.
- Produces: nenhuma interface nova para outras tarefas; é a última tarefa do plano.

- [ ] **Step 1: Escrever o teste que falha**

Abra `redigir-spec-pedido-negocio/tests/test_skill_integration.py` e acrescente este método à classe
`DraftingSkillIsolationTests` (depois de `test_drafting_skill_can_call_debt_skill_only_as_optional_appendix`,
antes do `if __name__ == "__main__":`):

```python
    def test_drafting_skill_suggests_screen_spec_skill_conditionally(self):
        self.assertIn(
            "Se a spec tiver requisitos com faceta de interface, indique também, como "
            "próximo passo manual opcional, a skill `especificar-telas-ux-ui` (quando "
            "instalada), sem chamá-la diretamente.",
            self.drafting,
        )
        self.assert_has_no_named_skill_invocation(
            self.drafting, ("especificar-telas-ux-ui",)
        )
```

- [ ] **Step 2: Rodar o teste e confirmar a falha**

Run: `uv run python -m unittest redigir-spec-pedido-negocio.tests.test_skill_integration -v`
Expected: 1 `FAIL` novo (o método acima), o restante continua `OK`.

- [ ] **Step 3: Atualizar o passo 7 de `redigir-spec-pedido-negocio/SKILL.md`**

Troque:

```markdown
7. **Salve o documento em arquivo e pare. Não invoque nenhuma outra skill.** Essa proibição cobre o
   restante do pipeline (3W, 3C, Gherkin, geração de backlog); as únicas exceções são os Passos 5 e 6.
   Informe ao
   usuário o caminho salvo e um resumo das lacunas e perguntas encontradas. Se a spec salva ainda tiver
   itens em `## Lacunas e perguntas abertas`, sugira explicitamente rodar `entrevistar-lacunas-requisito`
   (quando instalada) como próximo passo manual, antes de a spec seguir para
   `gerar-backlog-azure-boards`. Se houver copy voltada ao usuário na spec, indique
   também, como próximo passo manual opcional, a skill `revisar-textos-requisitos` (quando
   instalada), sem chamá-la diretamente.
```

Por:

```markdown
7. **Salve o documento em arquivo e pare. Não invoque nenhuma outra skill.** Essa proibição cobre o
   restante do pipeline (3W, 3C, Gherkin, geração de backlog); as únicas exceções são os Passos 5 e 6.
   Informe ao
   usuário o caminho salvo e um resumo das lacunas e perguntas encontradas. Se a spec salva ainda tiver
   itens em `## Lacunas e perguntas abertas`, sugira explicitamente rodar `entrevistar-lacunas-requisito`
   (quando instalada) como próximo passo manual, antes de a spec seguir para
   `gerar-backlog-azure-boards`. Se houver copy voltada ao usuário na spec, indique
   também, como próximo passo manual opcional, a skill `revisar-textos-requisitos` (quando
   instalada), sem chamá-la diretamente. Se a spec tiver requisitos com faceta de interface, indique também, como próximo passo manual opcional, a skill `especificar-telas-ux-ui` (quando instalada), sem chamá-la diretamente.
```

**Atenção à formatação:** a frase nova deve ficar inteira em uma única linha física do arquivo (sem
quebra de linha no meio dela), porque o teste do Step 1 usa `assertIn` com essa frase como uma única
string sem `\n`; uma quebra de linha no meio faria o `assertIn` falhar mesmo com o conteúdo semanticamente
correto.

- [ ] **Step 4: Registrar o testpath em `pyproject.toml`**

Em `[tool.pytest.ini_options]`, no array `testpaths`, acrescente uma linha depois de
`"especificar-debitos-tecnicos/tests",`:

```toml
  "especificar-telas-ux-ui/tests",
```

O array completo fica:

```toml
testpaths = [
  "gerar-backlog-azure-boards/tests",
  "redigir-spec-pedido-negocio/tests",
  "entrevistar-lacunas-requisito/tests",
  "revisar-textos-requisitos/tests",
  "especificar-debitos-tecnicos/tests",
  "especificar-telas-ux-ui/tests",
]
```

- [ ] **Step 5: Rodar o teste isolado e confirmar que passa**

Run: `uv run python -m unittest redigir-spec-pedido-negocio.tests.test_skill_integration -v`
Expected: `OK` — todos os testes, incluindo o novo, passam.

- [ ] **Step 6: Rodar a suíte completa via `pytest` e confirmar que não há regressão**

Run: `uv run pytest -v`
Expected: `OK` — todos os testes de todas as skills (incluindo `especificar-telas-ux-ui/tests`, agora
descoberto via `pyproject.toml`) passam, sem falhas nem erros.

- [ ] **Step 7: Commit**

```bash
git add redigir-spec-pedido-negocio/SKILL.md redigir-spec-pedido-negocio/tests/test_skill_integration.py pyproject.toml
git commit -m "$(cat <<'EOF'
feat: sugere especificar-telas-ux-ui a partir de redigir-spec-pedido-negocio

Acrescenta a sugestão condicional e manual da skill nova, no mesmo
padrão já usado para entrevistar-lacunas-requisito e
revisar-textos-requisitos, e registra o testpath da skill nova para a
suíte completa do repositório.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

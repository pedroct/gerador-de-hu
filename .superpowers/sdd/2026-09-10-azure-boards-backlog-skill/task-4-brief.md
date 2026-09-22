### Task 4: Tornar a integração estritamente acíclica

**Files:**
- Create: `generating-azure-boards-backlog-from-spec/tests/test_skill_integration.py`
- Modify: `refining-user-stories-with-3w/SKILL.md`
- Modify: `refining-user-stories-with-gherkin/SKILL.md`
- Modify: `refining-user-stories-with-3c/SKILL.md`

**Interfaces:**
- 3W produces: Card local e estado 3W; nenhuma chamada de sub-skill.
- Gherkin produces: regras, exemplos e estado local da Confirmation; nenhuma chamada de sub-skill.
- 3C consumes: 3W e Gherkin; produces prontidão geral.
- Backlog skill consumes: 3C; não chama 3W/Gherkin diretamente.

- [ ] **Step 1: Escrever teste estático que falha no estado atual**

Criar `tests/test_skill_integration.py`:

```python
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]


class SkillIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.three_w = (ROOT / "refining-user-stories-with-3w" / "SKILL.md").read_text()
        cls.gherkin = (ROOT / "refining-user-stories-with-gherkin" / "SKILL.md").read_text()
        cls.three_c = (ROOT / "refining-user-stories-with-3c" / "SKILL.md").read_text()
        cls.backlog = (ROOT / "generating-azure-boards-backlog-from-spec" / "SKILL.md").read_text()

    def test_leaf_skills_do_not_require_subskills(self):
        self.assertNotIn("REQUIRED SUB-SKILL", self.three_w)
        self.assertNotIn("REQUIRED SUB-SKILL", self.gherkin)

    def test_three_c_is_the_refinement_orchestrator(self):
        self.assertIn("REQUIRED SUB-SKILL:** use refining-user-stories-with-3w", self.three_c)
        self.assertIn("REQUIRED SUB-SKILL:** refining-user-stories-with-gherkin", self.three_c)
        self.assertIn("única prontidão geral", self.three_c)

    def test_backlog_calls_only_three_c(self):
        self.assertIn("REQUIRED SUB-SKILL:** use refining-user-stories-with-3c", self.backlog)
        self.assertNotIn("REQUIRED SUB-SKILL:** use refining-user-stories-with-3w", self.backlog)
        self.assertNotIn("REQUIRED SUB-SKILL:** use refining-user-stories-with-gherkin", self.backlog)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Executar e confirmar RED**

Run:

```bash
cd /Users/pedroct/skills/generating-azure-boards-backlog-from-spec
uv run python -m unittest tests/test_skill_integration.py -v
```

Expected: FAIL porque 3W e Gherkin ainda contêm `REQUIRED SUB-SKILL` e a 3C não declara textualmente a propriedade exclusiva da prontidão.

- [ ] **Step 3: Ajustar a skill 3W**

Remover o encaminhamento direto a Gherkin. O contrato final deve dizer:

```markdown
## Limite da skill

Esta é uma skill-folha. Entregue somente mapa 3W, história ou rascunho, perguntas e estado 3W. Não produza Conversation, Gherkin ou prontidão geral. Quando outra skill a invocar, devolva esses artefatos ao chamador.

Para Azure Boards, o conteúdo 3W pertence a `Description`, nunca a `Acceptance Criteria`.
```

- [ ] **Step 4: Ajustar a skill Gherkin**

Remover a chamada obrigatória a 3W e a prontidão geral. O contrato final deve dizer:

```markdown
## Entrada e limite da skill

Consuma a história, os fatos e as decisões fornecidos. Se o ator, o valor ou uma regra necessária estiver ausente, reporte a lacuna sem chamar outra skill.

Esta é uma skill-folha. Retorne regras confirmadas, exemplos e estado da Confirmation (`Ausente`, `Parcial` ou `Completa`). Não emita prontidão geral. Sob a 3C, aceite como confirmadas somente decisões da Conversation.
```

- [ ] **Step 5: Ajustar a skill 3C**

Preservar as duas chamadas de sub-skill e acrescentar:

```markdown
A 3C é a única dona da prontidão geral. Estados locais da 3W e Gherkin são insumos; não os trate como vereditos concorrentes.
```

- [ ] **Step 6: Executar e confirmar GREEN**

Run:

```bash
cd /Users/pedroct/skills/generating-azure-boards-backlog-from-spec
uv run python -m unittest tests/test_skill_integration.py -v
```

Expected: 3 tests, `OK`.

---

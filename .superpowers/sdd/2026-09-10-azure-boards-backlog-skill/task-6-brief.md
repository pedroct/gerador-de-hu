### Task 6: Verificação final das quatro skills

**Files:**
- Verify: `generating-azure-boards-backlog-from-spec/**`
- Verify: `refining-user-stories-with-3c/SKILL.md`
- Verify: `refining-user-stories-with-3w/SKILL.md`
- Verify: `refining-user-stories-with-gherkin/SKILL.md`

**Interfaces:**
- Produces: evidência final estrutural, automatizada e comportamental.

- [ ] **Step 1: Executar todos os testes Python**

Run:

```bash
cd /Users/pedroct/skills/generating-azure-boards-backlog-from-spec
uv run python -m unittest discover -s tests -v
```

Expected: 22 tests, `OK`.

- [ ] **Step 2: Validar os quatro pacotes de skill**

Run:

```bash
for skill_dir in \
  /Users/pedroct/skills/generating-azure-boards-backlog-from-spec \
  /Users/pedroct/skills/refining-user-stories-with-3c \
  /Users/pedroct/skills/refining-user-stories-with-3w \
  /Users/pedroct/skills/refining-user-stories-with-gherkin; do
  uv run --with pyyaml python \
    /Users/pedroct/.codex/skills/.system/skill-creator/scripts/quick_validate.py \
    "$skill_dir"
done
```

Expected: quatro ocorrências de `Skill is valid!`.

- [ ] **Step 3: Verificar scaffolds e links internos**

Run:

```bash
! rg -n '\[TODO|TODO:|TBD' \
  /Users/pedroct/skills/generating-azure-boards-backlog-from-spec \
  /Users/pedroct/skills/refining-user-stories-with-3c \
  /Users/pedroct/skills/refining-user-stories-with-3w \
  /Users/pedroct/skills/refining-user-stories-with-gherkin

test -f /Users/pedroct/skills/generating-azure-boards-backlog-from-spec/references/backlog-markdown-contract.md
test -f /Users/pedroct/skills/generating-azure-boards-backlog-from-spec/scripts/validate_backlog.py
```

Expected: exit 0 e nenhuma ocorrência de scaffold inacabado.

- [ ] **Step 4: Executar o validador em um exemplo final**

Usar a fixture válida criada na Task 2 e executar:

```bash
uv run python /Users/pedroct/skills/generating-azure-boards-backlog-from-spec/scripts/validate_backlog.py /Users/pedroct/skills/generating-azure-boards-backlog-from-spec/tests/fixtures/valid-backlog.md
```

Expected: `Backlog structure is valid`.

- [ ] **Step 5: Relatar o estado real**

Informar arquivos criados e modificados, contagem de testes, resultado do `quick_validate.py`, cenários comportamentais executados e a ausência de operações no Azure Boards. Não alegar commit, pois o workspace não possui repositório Git.

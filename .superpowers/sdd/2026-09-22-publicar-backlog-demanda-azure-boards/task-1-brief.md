### Task 1: Fork base do pacote

Copiar a skill de origem, renomear o pacote e deixar a suíte herdada verde antes de qualquer mudança
de comportamento. Nada aqui muda lógica: é o ponto de partida idêntico contra o qual as tarefas
seguintes vão divergir.

**Files:**
- Create: `publicar-backlog-demanda-azure-boards/` (cópia de `publicar-backlog-azure-boards/`)
- Create: `publicar-backlog-demanda-azure-boards/pyproject.toml`
- Create: `publicar-backlog-demanda-azure-boards/src/publicar_backlog_demanda_azure_boards/*`
- Test: `publicar-backlog-demanda-azure-boards/tests/*` (13 arquivos herdados)

**Interfaces:**
- Consumes: nada.
- Produces: o pacote `publicar_backlog_demanda_azure_boards` com a API pública idêntica à da origem —
  `criar_plano`, `executar_plano`, `criar_autorizacao`, `ler_manifesto`, `validar_manifesto`,
  `gravar_manifesto`, `carregar_configuracao`, `ClienteAzureDevOps`, `principal`.

- [ ] **Step 1: Copiar a árvore, sem artefatos de build**

```bash
cd /Volumes/DOCK/Projetos/pessoal/gerador-hu
rsync -a --exclude '.venv' --exclude '.mypy_cache' --exclude '.ruff_cache' \
      --exclude '.pytest_cache' --exclude '__pycache__' --exclude 'uv.lock' \
      publicar-backlog-azure-boards/ publicar-backlog-demanda-azure-boards/
git -C . status --short publicar-backlog-demanda-azure-boards | head
```

- [ ] **Step 2: Renomear o pacote e as importações**

```bash
cd /Volumes/DOCK/Projetos/pessoal/gerador-hu/publicar-backlog-demanda-azure-boards
mv src/publicar_backlog_azure_boards src/publicar_backlog_demanda_azure_boards
mv scripts/publicar_backlog.py scripts/publicar_backlog_demanda.py
grep -rl 'publicar_backlog_azure_boards' src scripts tests \
  | xargs sed -i '' 's/publicar_backlog_azure_boards/publicar_backlog_demanda_azure_boards/g'
grep -rn 'publicar_backlog_azure_boards' src scripts tests || echo "nenhuma referência antiga"
```

- [ ] **Step 3: Ajustar o `pyproject.toml`**

Trocar as quatro ocorrências do nome antigo, mantendo todo o resto idêntico:

```toml
[project]
name = "publicar-backlog-demanda-azure-boards"
version = "0.1.0"
description = "Publicador de backlogs Markdown vinculados a uma Demanda de Negócio no Azure Boards"

[project.scripts]
publicar-backlog-demanda-azure-boards = "publicar_backlog_demanda_azure_boards:main"

[tool.hatch.build.targets.wheel]
packages = ["src/publicar_backlog_demanda_azure_boards"]
```

- [ ] **Step 4: Ajustar as referências textuais ao nome da ferramenta**

```bash
cd /Volumes/DOCK/Projetos/pessoal/gerador-hu/publicar-backlog-demanda-azure-boards
sed -i '' 's/prog="publicar-backlog-azure-boards"/prog="publicar-backlog-demanda-azure-boards"/' \
  src/publicar_backlog_demanda_azure_boards/cli.py
grep -rn 'publicar_backlog\.py' tests src scripts || echo "nenhuma referência ao script antigo"
```

Onde `grep` apontar `scripts/publicar_backlog.py` em teste ou documentação, trocar por
`scripts/publicar_backlog_demanda.py`.

- [ ] **Step 5: Rodar a suíte herdada e confirmar que está verde**

```bash
cd /Volumes/DOCK/Projetos/pessoal/gerador-hu/publicar-backlog-demanda-azure-boards
uv sync
uv run pytest
```

Esperado: PASS em todos os testes herdados. Se `test_instalacao.py`,
`test_configuracao_projeto.py` ou `test_documentacao_operacional.py` falharem, é porque afirmam o
nome antigo do pacote, do script ou do projeto — corrigir a afirmação no teste para o nome novo,
nunca afrouxá-la.

- [ ] **Step 6: Commit**

```bash
cd /Volumes/DOCK/Projetos/pessoal/gerador-hu
git add publicar-backlog-demanda-azure-boards
git commit -m "feat: cria o fork base do publicador vinculado a Demanda"
```

---

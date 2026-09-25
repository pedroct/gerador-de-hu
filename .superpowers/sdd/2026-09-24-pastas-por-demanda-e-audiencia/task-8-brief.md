## Tarefa 8: O gerador de backlog sugere a rodada certa

**Arquivos:**
- Modificar: `gerar-backlog-azure-boards/SKILL.md` (passo 11 do `## Workflow`)
- Modificar: `README.md` (bullet `- **Entrevista de lacunas:**`)
- Testar: `gerar-backlog-azure-boards/tests/test_skill_integration.py`

**Interfaces:**
- Consome: da Tarefa 7, os escopos `negócio` e `técnico`.
- Produz: nada; encerra o plano.

- [ ] **Passo 1: Escrever os testes que falham**

Acrescente a `gerar-backlog-azure-boards/tests/test_skill_integration.py`:

```python
def test_sugestao_de_entrevista_nomeia_o_escopo() -> None:
    assert "escopo `negócio`" in SKILL
    assert "escopo `técnico`" in SKILL


def test_readme_descreve_as_duas_rodadas() -> None:
    readme = (Path(__file__).resolve().parents[2] / "README.md").read_text(encoding="utf-8")
    assert "duas rodadas" in readme
    assert "negocio.md" in readme
```

- [ ] **Passo 2: Rodar os testes e confirmar que falham**

```bash
uv run pytest gerar-backlog-azure-boards/tests -v
```

Esperado: 2 falhas.

- [ ] **Passo 3: Substituir o passo 11 do workflow**

Troque a linha do passo 11 inteira por:

```markdown
11. Entregue o backlog mesmo com Histórias ou Bugs `Não pronta`. Para cada um, liste as lacunas de Card, Conversation e Confirmation que a bloqueiam e sugira ao usuário registrá-las em `## Lacunas e perguntas abertas` da spec de origem e rodar `entrevistar-lacunas-requisito` (quando instalada). Se as lacunas da spec estiverem rotuladas por audiência, nomeie a rodada: escopo `negócio` para as que mudam o que o usuário percebe, escopo `técnico` para as demais. Depois de cada rodada de respostas, regenere o backlog e repita a sugestão até todos os itens de folha ficarem `Prontos` ou até o usuário adiar explicitamente uma lacuna.
```

- [ ] **Passo 4: Atualizar o README**

Troque o bullet `- **Entrevista de lacunas:**` inteiro por:

```markdown
- **Entrevista de lacunas:** fecha, por entrevista em rodadas, a seção de lacunas de uma spec já escrita, sem investigar código nem desenhar plano algum; aceita um escopo de audiência que separa as **duas rodadas** de refinamento — a de negócio, sobre `negocio.md`, e a técnica, sobre `spec.md` — compondo com a fronteira em vez de substituí-la; referenciada condicionalmente por Drafting e, após a geração do backlog, como sugestão para fechar Histórias `Não pronta` — nunca obrigatória.
```

- [ ] **Passo 5: Rodar a suíte inteira**

```bash
uv run pytest -q
```

Esperado: tudo PASS, inclusive `test_readme_conta_capacidades_de_acordo_com_a_propria_lista` — a contagem de bullets não mudou.

- [ ] **Passo 6: Rodar o pre-commit em tudo**

```bash
uv run pre-commit run --all-files
```

Esperado: tudo `Passed`.

- [ ] **Passo 7: Commit**

```bash
git add gerar-backlog-azure-boards README.md
git commit -m "feat: sugestao de entrevista nomeia a rodada por audiencia

Quem revisa o backlog passa a saber qual das duas reunioes fecha cada
lacuna, sem voltar a spec para descobrir.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

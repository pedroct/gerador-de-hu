## Tarefa 7: A entrevista ganha escopo de audiência

**Arquivos:**
- Modificar: `entrevistar-lacunas-requisito/SKILL.md` (frontmatter `description`; `## Objetivo`; passos 1, 2 e 4 do `## Fluxo`; `## Boundaries`)
- Testar: `entrevistar-lacunas-requisito/tests/test_skill_integration.py`

**Interfaces:**
- Consome: da Tarefa 5, o formato `- **N3 · Negócio** — <pergunta>`; da Tarefa 6, `negocio.md`.
- Produz: decisões gravadas em `spec.md` e, quando necessário, lacunas `T*` novas nascidas de respostas de negócio.

- [ ] **Passo 1: Escrever os testes que falham**

Acrescente a `entrevistar-lacunas-requisito/tests/test_skill_integration.py`:

```python
def test_escopo_filtra_por_audiencia() -> None:
    assert "escopo" in SKILL
    assert "Negócio" in SKILL
    assert "Técnico" in SKILL


def test_escopo_compoe_com_a_fronteira_em_vez_de_substitui_la() -> None:
    """Sem isso, a rodada técnica perguntaria algo que depende de decisão de negócio aberta."""
    texto = sem_quebras(SKILL)
    assert "compõe com a fronteira" in texto
    assert "fica fora da fronteira" in texto


def test_spec_sem_rotulos_pergunta_tudo() -> None:
    """Toda spec já escrita não tem rótulos; o escopo é filtro opcional, não requisito de formato."""
    texto = sem_quebras(SKILL)
    assert "Spec sem rótulos de audiência" in texto
    assert "pergunte todas as lacunas" in texto


def test_resposta_pode_criar_lacuna_nova() -> None:
    """Decisão de negócio que gera trabalho técnico não pode virar descoberta na implementação."""
    texto = sem_quebras(SKILL)
    assert "registrar uma lacuna nova" in texto


def test_description_nao_fixa_uma_unica_skill_de_origem() -> None:
    frontmatter = SKILL[: SKILL.index("---", 4)]
    assert "redigir-spec-demanda-azure-boards" in frontmatter or (
        "tipicamente produzida por `redigir-spec-pedido-negocio`" not in SKILL
    )
```

Se o arquivo de teste não tiver `sem_quebras`, copie a função de `redigir-spec-demanda-azure-boards/tests/test_skill_integration.py:142-144`.

- [ ] **Passo 2: Rodar os testes e confirmar que falham**

```bash
uv run pytest entrevistar-lacunas-requisito/tests -v
```

Esperado: 5 falhas.

- [ ] **Passo 3: Atualizar o frontmatter e o objetivo**

Troque a linha `description:` do frontmatter por:

```yaml
description: Use quando uma spec possui a seção aberta "Lacunas e perguntas abertas" e essas lacunas precisam ser fechadas por entrevista em rodadas, registrando adiamentos explícitos em vez de deixar decisões silenciosas. Aceita um escopo de audiência para separar o refinamento de negócio do técnico.
```

Na seção `## Objetivo`, troque `tipicamente produzida por \`redigir-spec-pedido-negocio\` — perguntando em rodadas` por:

```markdown
tipicamente produzida por `redigir-spec-demanda-azure-boards` ou `redigir-spec-pedido-negocio` —
perguntando em rodadas
```

- [ ] **Passo 4: Substituir os passos 1, 2 e 4 do fluxo**

Troque o passo 1 por:

```markdown
1. **Leia a spec** e mapeie cada item de `## Lacunas e perguntas abertas` como um nó independente. Uma
   lacuna pode vir rotulada no formato `- **N3 · Negócio** — <pergunta>`, onde a letra do ID e o rótulo
   indicam a audiência. **Spec sem rótulos de audiência é o caso normal de specs antigas: pergunte
   todas as lacunas, exatamente como antes.** O escopo é um filtro opcional, nunca um requisito de
   formato.
```

Troque o passo 2 por:

```markdown
2. **Calcule a fronteira**: os itens que já podem ser perguntados agora, sem depender da resposta de
   outro item ainda em aberto na mesma lista. Se o usuário informou um escopo (`negócio` ou `técnico`),
   ele **compõe com a fronteira** em vez de substituí-la: uma lacuna `Técnico` que depende de uma
   `Negócio` ainda aberta fica fora da fronteira mesmo na rodada técnica. Relate o que ficou bloqueado
   em vez de forçar uma resposta prematura. Na rodada de escopo `negócio`, o material de leitura do
   usuário é `negocio.md`; as decisões, porém, são sempre gravadas em `spec.md`.
```

Troque o passo 4, acrescentando um terceiro desfecho depois do bullet de adiamento:

```markdown
   - se a resposta criar uma decisão que ainda não existia, **registrar uma lacuna nova** em
     `## Lacunas e perguntas abertas`, com ID e audiência próprios, citando a lacuna que a originou.
     Decidir *"a diligência deve expirar sozinha"* cria *"como a rotina de expiração é disparada"*, que
     é da outra rodada. Sem isso, decisões de negócio gerariam trabalho técnico invisível, descoberto
     só na implementação.
```

- [ ] **Passo 5: Acrescentar um limite**

Ao fim de `## Boundaries`:

```markdown
- Não reclassifique a audiência de uma lacuna existente para encaixá-la na rodada atual. Se o rótulo
  estiver errado, diga isso ao usuário e siga adiante sem perguntá-la.
```

- [ ] **Passo 6: Rodar a suíte inteira**

```bash
uv run pytest -q
```

Esperado: tudo PASS.

- [ ] **Passo 7: Commit**

```bash
git add entrevistar-lacunas-requisito
git commit -m "feat: entrevista aceita escopo de audiencia

O escopo compoe com a fronteira em vez de substitui-la, e spec sem
rotulos continua perguntando tudo. Uma resposta agora pode criar lacuna
nova, para a rodada seguinte.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

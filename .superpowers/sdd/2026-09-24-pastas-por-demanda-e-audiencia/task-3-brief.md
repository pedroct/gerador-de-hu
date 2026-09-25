## Tarefa 3: O gerador de backlog ganha o atalho por pasta

**Arquivos:**
- Modificar: `gerar-backlog-azure-boards/SKILL.md` (passo 2 do `## Workflow`)
- Modificar: `gerar-backlog-azure-boards/references/backlog-markdown-contract.md:169`
- Modificar: `README.md` (bullet `- **Drafting a partir de Demanda no Azure Boards:**`)
- Testar: `gerar-backlog-azure-boards/tests/test_skill_integration.py`

**Interfaces:**
- Consome: da Tarefa 2, a pasta `DN-<id>-<slug>/` e o vocabulário fechado.
- Produz: nada que a Fase 2 dependa; encerra a Fase 1.

- [ ] **Passo 1: Escrever os testes que falham**

Acrescente ao fim de `gerar-backlog-azure-boards/tests/test_skill_integration.py`:

```python
from pathlib import Path

CONTRATO = (
    Path(__file__).resolve().parents[1] / "references" / "backlog-markdown-contract.md"
).read_text(encoding="utf-8")


def test_atalho_por_pasta_nao_substitui_a_busca_por_titulo() -> None:
    """A busca por título é fallback permanente: sem ela, toda spec antiga para de funcionar."""
    assert "DN-<id>-<slug>" in SKILL
    assert "telas-ux-ui.md" in SKILL
    assert "Spec: Telas UX-UI" in SKILL
    assert "fallback permanente" in SKILL


def test_contrato_proibe_o_nome_da_pasta_como_fonte_do_id() -> None:
    """Depois da convenção há um `DN-14125` a um basename de distância, e ele parece uma resposta."""
    assert "nome da pasta" in CONTRATO
    assert "DN-" in CONTRATO
```

Se o arquivo já importar `Path`, não duplique o import.

- [ ] **Passo 2: Rodar os testes e confirmar que falham**

```bash
uv run pytest gerar-backlog-azure-boards/tests -v
```

Esperado: 2 falhas, `AssertionError`.

- [ ] **Passo 3: Substituir o passo 2 do workflow**

Troque a linha do passo 2 inteira por:

```markdown
2. Leia a seção `## Necessidade de especificação de tela` da spec e o documento companheiro `Spec: Telas UX-UI — <contexto>`, quando existirem, como input opcional por arquivo — nunca como invocação de `especificar-telas-ux-ui`. Se a spec estiver numa pasta `DN-<id>-<slug>/`, procure os companheiros ali pelo vocabulário fechado: `telas-ux-ui.md`, `debitos-tecnicos.md` e `revisao-textos.md`. Fora desse caso, localize-os pelo título do documento — a busca por título é **fallback permanente**, não etapa de transição, e é o que mantém funcionando toda spec escrita antes da convenção de pastas. Sem esses arquivos, prossiga normalmente: a skill continua funcionando sem eles.
```

- [ ] **Passo 4: Endurecer o contrato**

Em `gerar-backlog-azure-boards/references/backlog-markdown-contract.md`, troque o fim da linha 169, de `Nunca infira o ID de outra fonte que não a spec, e nunca consulte o Azure Boards para descobri-lo.` para:

```markdown
Nunca infira o ID de outra fonte que não a spec, e nunca consulte o Azure Boards para descobri-lo. Isso inclui **o nome da pasta**: um diretório `DN-14125-<slug>/` parece uma resposta e não é. Uma pasta renomeada à mão, copiada de outra Demanda ou criada por engano produziria um backlog publicado sob a Demanda errada, e o erro só apareceria depois que os Épicos já estivessem pendurados no work item incorreto.
```

- [ ] **Passo 5: Atualizar o README**

Troque o bullet `- **Drafting a partir de Demanda no Azure Boards:**` acrescentando ao fim da frase, antes do ponto final:

```markdown
, e grava tudo numa pasta `DN-<id>-<slug>/` sob `docs/specs/`, com nomes de arquivo de vocabulário fechado
```

Não acrescente um novo bullet de capacidade: `test_readme_conta_capacidades_de_acordo_com_a_propria_lista` compara a contagem da lista com a palavra em `O fluxo combina dez capacidades`, e o dicionário `_NUMEROS_POR_EXTENSO` só vai até `doze`.

- [ ] **Passo 6: Rodar a suíte inteira**

```bash
uv run pytest -q
```

Esperado: tudo PASS.

- [ ] **Passo 7: Commit**

```bash
git add gerar-backlog-azure-boards README.md
git commit -m "feat: gerador de backlog acha companheiros pela pasta da Demanda

A busca por titulo fica como fallback permanente, o que mantem toda spec
anterior funcionando. O contrato passa a proibir nominalmente o nome da
pasta como fonte do ID.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

# FASE 2 — Separação de audiência

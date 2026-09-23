### Task 12: Documentação da skill

**Files:**
- Modify: `publicar-backlog-demanda-azure-boards/SKILL.md`
- Modify: `publicar-backlog-demanda-azure-boards/README.md`
- Modify: `publicar-backlog-demanda-azure-boards/agents/openai.yaml`
- Modify: `README.md` (raiz)
- Test: `tests/test_documentacao_operacional.py`

**Interfaces:**
- Consumes: o comportamento final das Tasks 3 a 11.
- Produces: nenhuma API.

- [ ] **Step 1: Escrever o `SKILL.md`**

Frontmatter:

```markdown
---
name: publicar-backlog-demanda-azure-boards
description: Use quando um backlog Markdown já revisado precisa ser publicado no Azure Boards vinculado a uma Demanda de Negócio existente, informada por ID, e somente após autorização textual explícita.
---
```

O corpo, em pt-BR, cobre: objetivo; fluxo obrigatório de nove passos da seção "Fluxo da skill" da
spec; os comandos da Task 10; a tabela de configuração com `AZURE_DEVOPS_DEMANDA` e
`AZURE_DEVOPS_TIPO_DEMANDA`; a tabela de validações da spec; e os limites, incluindo estes três, que
distinguem esta skill da de origem:

- a Demanda de Negócio nunca é escrita — o vínculo nasce do lado do Épico, no mesmo POST que o cria;
- `Area Path` e `Iteration Path` não são configuráveis: vêm da Demanda;
- `--simulacao` lê a Demanda e portanto exige token; só `validar` é totalmente offline.

- [ ] **Step 2: Escrever o `README.md` da skill**

Partir do README herdado e corrigir tudo que a Task 10 invalidou: os exemplos de comando ganham
`--demanda`, as variáveis de Area Path e Iteration Path saem, e a descrição da simulação passa a dizer
que há uma leitura. Acrescentar o exemplo real da hierarquia:

```text
Demanda de Negócio #13959
└─ [Epic]       01 Gestão do projeto
   └─ [Feature] 01.01 Gestão do projeto
      └─ [Story] 01.01.01 Análise de padrões de stacks
```

- [ ] **Step 3: Atualizar `agents/openai.yaml`**

Trocar nome, descrição e qualquer comando citado para os da skill nova.

- [ ] **Step 4: Atualizar o `README.md` da raiz**

```bash
cd /Volumes/DOCK/Projetos/pessoal/gerador-hu
grep -n "nove capacidades" README.md
grep -n "publicar-backlog-azure-boards" README.md
```

Passar a contagem de capacidades para dez, acrescentar a linha da skill nova na tabela de
"Skills disponíveis" e estender o diagrama do fluxo de publicação:

```text
gerar-backlog-azure-boards
  → backlog Markdown
  → revisão humana
  → publicar-backlog-demanda-azure-boards validar/planejar --demanda <id>
  → AUTORIZAR PUBLICAÇÃO ... DEMANDA <id> ...
  → Azure Boards (Épicos filhos da Demanda)
```

- [ ] **Step 5: Ajustar o teste de documentação operacional**

```bash
cd /Volumes/DOCK/Projetos/pessoal/gerador-hu/publicar-backlog-demanda-azure-boards
uv run pytest tests/test_documentacao_operacional.py -v
```

O teste herdado afirma a presença de trechos do README e do SKILL.md. Atualizar as afirmações para o
conteúdo novo e acrescentar uma que prove que a documentação **não** oferece mais os caminhos manuais:

```python
def test_documentacao_nao_oferece_caminhos_manuais() -> None:
    for caminho in (Path("README.md"), Path("SKILL.md")):
        texto = caminho.read_text(encoding="utf-8")
        assert "--area-path" not in texto
        assert "--iteration-path" not in texto
        assert "AZURE_DEVOPS_AREA_PATHS" not in texto
```

- [ ] **Step 6: Rodar e confirmar que passa**

```bash
cd /Volumes/DOCK/Projetos/pessoal/gerador-hu/publicar-backlog-demanda-azure-boards
uv run pytest tests/test_documentacao_operacional.py -v
```

Esperado: PASS.

- [ ] **Step 7: Commit**

```bash
cd /Volumes/DOCK/Projetos/pessoal/gerador-hu
git add publicar-backlog-demanda-azure-boards README.md
git commit -m "docs: descreve a publicacao vinculada a Demanda de Negocio"
```

---

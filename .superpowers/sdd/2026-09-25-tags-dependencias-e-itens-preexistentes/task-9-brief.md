## Tarefa 9: contrato Markdown

**Arquivos:**
- Modificar: `gerar-backlog-azure-boards/references/backlog-markdown-contract.md`

**Interfaces:**
- Consome: as regras implementadas nas Tarefas 1, 3 e 6 — a documentação descreve o que o código já
  recusa, nunca o contrário.
- Produz: o contrato normativo que a Tarefa 10 cita.

- [ ] **Passo 1: escrever as três seções novas**

Acrescente, depois de "Depende de e Bloqueia", uma seção `## Tags` com: formato (subseção no nível
das demais, vírgula como separador), opcionalidade, recusa de seção presente e vazia, proibição de
`,` e `;` dentro da tag, limite de 400 caracteres, dedup preservando ordem, validade em qualquer
item, e o mapeamento para `System.Tags` unido por `"; "`.

Reescreva "Depende de e Bloqueia" para declarar `Depende de` como **subseção estruturada** com chaves
documentais, mantendo `Bloqueia` como texto informativo e explicando que só `Depende de` gera o link
`System.LinkTypes.Dependency-Reverse`. Registre que backlog anterior com `Depende de` em prosa
continua válido e não ganha link.

Acrescente `## Azure Boards ID` com: só em Epic e Feature, exige ancestral também declarado, o item
não é criado e serve de pai, e a ressalva de que este é o único lugar do backlog onde um ID real
aparece — copiado do Boards, nunca inferido, nunca derivado da chave documental nem do nome da pasta.

Atualize o template completo com as três subseções e a tabela "Markdown de revisão e campos do Azure
Boards" com as linhas novas.

- [ ] **Passo 2: conferir contra o código**

```bash
cd publicar-backlog-azure-boards && uv run pytest tests/test_contrato_tags.py tests/test_contrato_dependencias.py tests/test_contrato_id_existente.py -q
```

Leia cada mensagem de erro afirmada nesses testes e confirme que o contrato descreve a mesma regra,
com o mesmo limite e o mesmo separador. Divergência entre os dois é defeito do contrato.

- [ ] **Passo 3: rodar a validação estrutural sobre o template**

```bash
cd publicar-backlog-azure-boards && uv run python scripts/publicar_backlog.py validar tests/fixtures/valid-backlog.md
```

Esperado: nenhum erro. A fixture continua sem os campos novos, e é isso que confirma que eles são
opcionais.

- [ ] **Passo 4: commitar**

```bash
git add gerar-backlog-azure-boards/references/backlog-markdown-contract.md
git commit -m "docs: contrato de Tags, Depende de estruturado e Azure Boards ID"
```

---

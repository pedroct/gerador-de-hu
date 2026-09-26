## Tarefa 10: skills de débitos, telas e geração de backlog

**Arquivos:**
- Modificar: `especificar-debitos-tecnicos/SKILL.md`
- Modificar: `especificar-telas-ux-ui/SKILL.md`
- Modificar: `gerar-backlog-azure-boards/SKILL.md`

**Interfaces:**
- Consome: o contrato da Tarefa 9.
- Produz: as regras de emissão do vocabulário reservado. Nenhum código do publicador conhece
  `debito-tecnico` ou `design-ux-ui` — para ele, tag é string opaca.

- [ ] **Passo 1: `especificar-debitos-tecnicos/SKILL.md`**

- Acrescente `Faixa` ao cabeçalho da tabela `Resumo priorizado` e uma linha `- Faixa: <Restrição |
  Candidato | A confirmar>` à seção `Priorização` de cada DT.
- Acrescente `## Fonte da Demanda` ao template, copiada da spec de origem, com a proibição explícita
  de derivá-la do nome da pasta — `DN-14125-<slug>/` parece uma resposta e não é.
- Acrescente a nota de que `dt-<faixa>` publicada é snapshot da geração: uma reavaliação não atualiza
  o work item já criado.

- [ ] **Passo 2: `especificar-telas-ux-ui/SKILL.md`**

Acrescente ao template do `TL-xx` uma subseção `### Plataforma` com valor único, `Web` ou `Mobile`.
Hoje a plataforma vive no cabeçalho do documento e no título em prosa; a tag não pode depender de
parsing de título.

- [ ] **Passo 3: `gerar-backlog-azure-boards/SKILL.md`**

- Reconheça `Spec: Débitos técnicos` como spec de entrada válida, e não apenas como companheiro de
  contexto. A regra atual, de que o `debitos-tecnicos.md` encontrado numa pasta de Demanda é contexto
  rotulado, permanece: companheiro é contexto, spec de entrada é origem.
- Emita nos itens de folha: `debito-tecnico` e a faixa nos itens vindos de DT; `design-ux-ui` e
  `plataforma-web`/`plataforma-mobile` nos itens de design; `dn-<id>` em todo item nascido de uma
  Demanda. Epic e Feature não recebem tags.
- Serialize `Depende de` como subseção estruturada.
- Registre que os critérios em bullets de um DT vão para a Conversation e que `Acceptance Criteria`
  fica em branco, como o contrato manda quando a Confirmation não está completa.
- **Num backlog de débitos, Epic e Feature nomeiam a capacidade de produto afetada**, não o débito
  nem sua categoria — é a decisão de 2026-09-12, e um Epic "Débito técnico" com Features por
  categoria seria contêiner do problema. A tag já dá a visão de débito; a hierarquia dá a de
  capacidade, e pendurar na capacidade preserva as duas.
- Indique a publicadora **solta** como próxima etapa de um backlog de débitos, mesmo quando ele
  declarar Demanda de origem: `publicar-backlog-demanda-azure-boards` herdaria da Demanda o
  `Iteration Path`, e o débito nasceria na sprint da Demanda — exatamente a sprint em que ele não
  será pago.

- [ ] **Passo 4: conferir a coerência entre as três**

```bash
grep -n "debito-tecnico\|design-ux-ui\|plataforma-\|dn-<id>" especificar-debitos-tecnicos/SKILL.md especificar-telas-ux-ui/SKILL.md gerar-backlog-azure-boards/SKILL.md
```

Confirme que cada tag aparece com a mesma grafia nos dois lados — quem emite e quem documenta. Uma
divergência de grafia só apareceria depois de publicada, quando a query voltasse vazia.

- [ ] **Passo 5: commitar**

```bash
git add especificar-debitos-tecnicos/SKILL.md especificar-telas-ux-ui/SKILL.md gerar-backlog-azure-boards/SKILL.md
git commit -m "docs: emissao do vocabulario de tags nas skills de origem"
```

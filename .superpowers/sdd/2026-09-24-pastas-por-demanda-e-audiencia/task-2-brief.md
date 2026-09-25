## Tarefa 2: A orquestradora cria a pasta da Demanda

**Arquivos:**
- Modificar: `redigir-spec-demanda-azure-boards/SKILL.md` (passos 6 a 10 do `## Fluxo obrigatório`; nova seção `## Pasta da Demanda`)
- Testar: `redigir-spec-demanda-azure-boards/tests/test_skill_integration.py`

**Interfaces:**
- Consome: da Tarefa 1, o contrato de diretório de destino das três especializadas.
- Produz: a pasta `docs/specs/DN-<id>-<slug>/` com `spec.md`, que a Tarefa 3 lê como atalho e a Fase 2 povoa com `negocio.md`.

- [ ] **Passo 1: Escrever os testes que falham**

Acrescente ao fim de `redigir-spec-demanda-azure-boards/tests/test_skill_integration.py`:

```python
def test_skill_define_a_pasta_da_demanda_e_o_vocabulario_fechado() -> None:
    for texto in (
        "DN-<id>-<slug>",
        "docs/specs/",
        "spec.md",
        "debitos-tecnicos.md",
        "telas-ux-ui.md",
        "revisao-textos.md",
    ):
        assert texto in SKILL


def test_pasta_existente_e_reaproveitada() -> None:
    """Regerar a mesma Demanda não pode criar uma segunda pasta nem abortar."""
    secao = sem_quebras(SKILL[SKILL.index("## Pasta da Demanda") :])
    assert "reaproveite a pasta existente" in secao
    assert "nunca crie uma segunda pasta" in secao


def test_slug_degenerado_nao_produz_nome_quebrado() -> None:
    """Título só com pontuação ou acentos não pode gerar `DN-14125-` nem hífen final."""
    secao = sem_quebras(SKILL[SKILL.index("## Pasta da Demanda") :])
    assert "sem hífen final" in secao
    assert "use apenas `DN-<id>`" in secao


def test_skill_informa_o_caminho_usado() -> None:
    assert "informe ao usuário o caminho" in sem_quebras(SKILL)
```

- [ ] **Passo 2: Rodar os testes e confirmar que falham**

```bash
uv run pytest redigir-spec-demanda-azure-boards/tests -v
```

Esperado: 4 falhas, sendo as três primeiras `ValueError: substring not found` em `SKILL.index("## Pasta da Demanda")`.

- [ ] **Passo 3: Acrescentar a seção `## Pasta da Demanda`**

Insira entre o fim do `## Fluxo obrigatório` (depois do passo 10) e o cabeçalho `## Limites de leitura e de decisão`:

````markdown
## Pasta da Demanda

Todos os documentos de uma Demanda ficam numa pasta própria:

```text
docs/specs/DN-14125-emissao-de-convites/
├── spec.md
├── debitos-tecnicos.md
├── telas-ux-ui.md
└── revisao-textos.md
```

- **Nome da pasta:** `DN-<id>-<slug>`. O `<id>` é o número do work item, sem zeros à esquerda. O
  `<slug>` deriva de `System.Title`: minúsculas, acentos removidos, espaços e pontuação viram hífen,
  hífens repetidos colapsam, truncado em 60 caracteres e **sem hífen final**. Se o título não produzir
  nenhum caractere aproveitável, use apenas `DN-<id>`.
- **Raiz:** `docs/specs/` por padrão, a partir da raiz do repositório investigado. Se o usuário indicar
  outra raiz, use a dele. Em qualquer caso, informe ao usuário o caminho completo que você gravou.
- **Nomes internos:** o vocabulário é fechado — `spec.md`, `debitos-tecnicos.md`, `telas-ux-ui.md` e
  `revisao-textos.md`. Nenhum outro nome, nenhum prefixo `spec-`.
- **Reexecução:** se a pasta já existir de uma rodada anterior, reaproveite a pasta existente e
  substitua apenas os arquivos que você regerar; nunca crie uma segunda pasta com sufixo, e nunca
  interrompa o fluxo por a pasta existir.
- **O nome da pasta é rótulo, nunca fonte.** O ID da Demanda que vale é o da seção `## Fonte da
  Demanda` dentro de `spec.md`.
````

- [ ] **Passo 4: Reescrever os passos 6 a 10 do fluxo**

Troque o passo 6 (linhas 48-53) para começar por criar a pasta:

```markdown
6. Crie a pasta da Demanda conforme **Pasta da Demanda** e salve nela a Spec-base completa como
   `spec.md`, usando o **Template da Spec**, antes de chamar qualquer skill especializada. Use Área
   solicitante e Público-alvo como insumos da seção **Atores e vocabulário
   identificados no código**; use Valor esperado e Regras e restrições como insumos de
   **Comportamento esperado**. Registre todos como conteúdo registrado na Demanda, sem promovê-los a
   requisito confirmado. Inclua também a fonte, o problema, a evidência de código, a classificação, os
   repositórios considerados e as lacunas.
```

Troque o fim do passo 7 (linha 56) de `preserve a saída como documento separado, sem misturá-la ao requisito de negócio.` para:

```markdown
   saída como documento separado, sem misturá-la ao requisito de negócio. Informe a pasta da Demanda
   como diretório de destino.
```

Troque o passo 8 (linhas 57-58) por:

```markdown
8. Chame `especificar-telas-ux-ui` sempre depois de concluir a Spec-base completa, informando a pasta
   da Demanda como diretório de destino. Preserve a anotação da Spec e, quando aplicável, o briefing de
   telas como documento separado.
```

Troque o fim do passo 9 (linha 60) de `Salve o parecer com os trechos, diagnósticos,` para:

```markdown
   `revisar-textos-requisitos` depois da análise de telas, informando a pasta da Demanda como diretório
   de destino. Salve o parecer com os trechos, diagnósticos,
```

Troque o passo 10 (linhas 63-65) por:

```markdown
10. Confirme que a pasta da Demanda contém `spec.md` e os companheiros gerados, registrando eventual
   indisponibilidade de uma skill especializada como lacuna. Informe ao usuário o caminho completo da
   pasta. Em seguida, pare: não chamar entrevista, geração ou publicação de backlog.
   A geração ou publicação de backlog é uma etapa manual controlada pelo usuário.
```

- [ ] **Passo 5: Rodar os testes e confirmar que passam**

```bash
uv run pytest redigir-spec-demanda-azure-boards/tests -v
```

Esperado: tudo PASS. Atenção a `test_fluxo_estatico_preserva_ordem_gatilhos_e_lacunas`, que exige que os marcadores `"Preencha e salve a Spec-base"` e `"Salve a Spec principal"` existam. Como o passo 6 deixou de começar com `Preencha e salve a Spec-base` e o passo 10 com `Salve a Spec principal`, **atualize os dois marcadores nessa tupla** para `"Crie a pasta da Demanda"` e `"Confirme que a pasta da Demanda"`, preservando a ordem.

- [ ] **Passo 6: Rodar a suíte inteira**

```bash
uv run pytest -q
```

Esperado: tudo PASS. Se `test_orquestracao_preserva_limites_das_skills_chamadas` falhar, confirme que `"documento separado"` e `"não chamar entrevista, geração ou publicação de backlog"` sobreviveram às edições.

- [ ] **Passo 7: Commit**

```bash
git add redigir-spec-demanda-azure-boards
git commit -m "feat: orquestradora cria a pasta DN-<id>-<slug> da Demanda

A pasta pertence a orquestradora; as especializadas so recebem o
diretorio. Reexecucao reaproveita a pasta e titulo degenerado cai para
DN-<id> sem hifen final.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

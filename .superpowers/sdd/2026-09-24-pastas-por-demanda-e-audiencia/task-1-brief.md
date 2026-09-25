## Tarefa 1: As três especializadas aceitam diretório de destino

As três mudam do mesmo jeito e um revisor as aprovaria ou rejeitaria junto.

**Arquivos:**
- Modificar: `especificar-debitos-tecnicos/SKILL.md` (seção `## Formato da spec`, antes do bloco ```` ```markdown ````)
- Modificar: `especificar-telas-ux-ui/SKILL.md:136` (passo 16)
- Modificar: `revisar-textos-requisitos/SKILL.md` (seção `## Formato da saída`)
- Testar: `especificar-debitos-tecnicos/tests/test_skill_integration.py`
- Testar: `especificar-telas-ux-ui/tests/test_skill_integration.py`
- Testar: `revisar-textos-requisitos/tests/test_skill_integration.py`

**Interfaces:**
- Consome: nada.
- Produz: o contrato que a Tarefa 2 usa ao chamar as três — cada uma aceita um diretório de destino e grava com nome fixo (`debitos-tecnicos.md`, `telas-ux-ui.md`, `revisao-textos.md`).

- [ ] **Passo 1: Escrever os testes que falham**

Acrescente ao fim de `especificar-debitos-tecnicos/tests/test_skill_integration.py`:

```python
def test_skill_aceita_diretorio_de_destino_opcional() -> None:
    """Com diretório, grava com nome fixo; sem diretório, segue como antes."""
    assert "debitos-tecnicos.md" in SKILL
    assert "diretório de destino" in SKILL
    assert "Sem diretório de destino" in SKILL
```

Acrescente ao fim de `especificar-telas-ux-ui/tests/test_skill_integration.py`:

```python
def test_skill_aceita_diretorio_de_destino_opcional() -> None:
    """Com diretório, grava com nome fixo; sem diretório, segue como antes."""
    assert "telas-ux-ui.md" in SKILL
    assert "diretório de destino" in SKILL
    assert "Sem diretório de destino" in SKILL
```

Acrescente ao fim de `revisar-textos-requisitos/tests/test_skill_integration.py`:

```python
def test_skill_aceita_diretorio_de_destino_opcional() -> None:
    """Com diretório, grava com nome fixo; sem diretório, segue como antes."""
    assert "revisao-textos.md" in SKILL
    assert "diretório de destino" in SKILL
    assert "Sem diretório de destino" in SKILL


def test_parecer_tem_titulo_de_documento() -> None:
    """Sem título, o parecer não é localizável por título como os outros companheiros."""
    assert "# Revisão de textos — <contexto>" in SKILL
```

Confira antes o nome da variável que cada arquivo usa para o texto do `SKILL.md`; se não for `SKILL`, ajuste as asserções ao nome local.

- [ ] **Passo 2: Rodar os testes e confirmar que falham**

```bash
uv run pytest especificar-debitos-tecnicos/tests especificar-telas-ux-ui/tests revisar-textos-requisitos/tests -v
```

Esperado: 4 falhas, `AssertionError`.

- [ ] **Passo 3: Acrescentar o parágrafo em `especificar-debitos-tecnicos/SKILL.md`**

Logo abaixo do cabeçalho `## Formato da spec` e antes do bloco ```` ```markdown ````:

```markdown
Quem chama esta skill pode informar um **diretório de destino**. Nesse caso, grave a spec nele com o
nome exato `debitos-tecnicos.md`. **Sem diretório de destino informado, salve como sempre fez** e
relate o caminho ao usuário. O título do documento continua sendo `Spec: Débitos técnicos — <contexto>`
nos dois casos: é ele que identifica o documento, não o nome do arquivo.
```

- [ ] **Passo 4: Substituir o passo 16 de `especificar-telas-ux-ui/SKILL.md`**

Troque a linha 136 inteira por:

```markdown
16. **Anote a Spec** com a seção `## Necessidade de especificação de tela` e **salve o documento separado** `Spec: Telas UX-UI — <contexto>`, no formato de [Formato das saídas](#formato-das-saídas). Se a spec já tiver essa seção de uma rodada anterior, substitua-a por inteiro — nunca acrescente uma segunda seção duplicada. Quem chama pode informar um **diretório de destino**; nesse caso grave o documento nele com o nome exato `telas-ux-ui.md`. **Sem diretório de destino informado, salve como sempre fez.** O título do documento identifica-o nos dois casos.
```

- [ ] **Passo 5: Acrescentar o parágrafo e o título em `revisar-textos-requisitos/SKILL.md`**

Logo abaixo do cabeçalho `## Formato da saída`, antes do parágrafo `Comece com um resumo:`:

````markdown
O parecer é um documento com título próprio:

```markdown
# Revisão de textos — <contexto>
```

Quem chama esta skill pode informar um **diretório de destino**. Nesse caso, grave o parecer nele com
o nome exato `revisao-textos.md`. **Sem diretório de destino informado, salve como sempre fez** e
relate o caminho ao usuário.
````

- [ ] **Passo 6: Rodar os testes e confirmar que passam**

```bash
uv run pytest especificar-debitos-tecnicos/tests especificar-telas-ux-ui/tests revisar-textos-requisitos/tests -v
```

Esperado: tudo PASS.

- [ ] **Passo 7: Commit**

```bash
git add especificar-debitos-tecnicos especificar-telas-ux-ui revisar-textos-requisitos
git commit -m "feat: especializadas aceitam diretorio de destino opcional

O nome do arquivo passa a ser fixo quando o diretorio e informado, e o
titulo do documento continua sendo a identidade em ambos os casos.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

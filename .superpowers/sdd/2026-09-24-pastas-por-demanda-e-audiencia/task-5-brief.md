## Tarefa 5: Lacunas ganham ID, audiência e evidência

**Arquivos:**
- Modificar: `redigir-spec-demanda-azure-boards/SKILL.md` (passo 4 do fluxo; `## Template da Spec`; nova seção `## Audiência das lacunas`)
- Testar: `redigir-spec-demanda-azure-boards/tests/test_skill_integration.py`

**Interfaces:**
- Consome: da Tarefa 4, o formato `- **N3 · Negócio** — <pergunta>` que `extrair_lacunas` reconhece, e o comentário `<!-- evidência: ... -->`.
- Produz: o formato de lacuna que a Tarefa 6 projeta em `negocio.md` e a Tarefa 7 filtra por escopo.

- [ ] **Passo 1: Escrever os testes que falham**

Acrescente a `redigir-spec-demanda-azure-boards/tests/test_skill_integration.py`:

```python
def test_lacuna_tem_id_audiencia_e_evidencia() -> None:
    corpo = template()
    assert "- **N1 · Negócio** —" in corpo
    assert "- **T1 · Técnico** —" in corpo
    assert "<!-- evidência:" in corpo


def test_criterio_de_audiencia_e_checavel() -> None:
    secao = sem_quebras(SKILL[SKILL.index("## Audiência das lacunas") :])
    assert "muda o que o usuário percebe" in secao
    assert "uma lacuna, uma decisão, uma audiência" in secao.lower()


def test_regra_de_traducao_proibe_codigo_na_pergunta() -> None:
    secao = sem_quebras(SKILL[SKILL.index("## Audiência das lacunas") :])
    assert "verificar_lacunas.py" in secao
    for proibido in ("arquivo", "classe", "método", "número de linha"):
        assert proibido in secao


def test_lacunas_do_template_nao_violam_o_proprio_verificador() -> None:
    """O exemplo do template não pode ser o primeiro a quebrar a regra que ensina."""
    sys.path.insert(0, str(RAIZ_SKILL / "scripts"))
    from verificar_lacunas import verificar

    assert verificar(template()) == []
```

Acrescente `import sys` ao topo do arquivo se ainda não existir.

- [ ] **Passo 2: Rodar os testes e confirmar que falham**

```bash
uv run pytest redigir-spec-demanda-azure-boards/tests/test_skill_integration.py -v
```

Esperado: 4 falhas.

- [ ] **Passo 3: Substituir a seção de lacunas no template**

Em `## Template da Spec`, troque as duas linhas finais do bloco:

```markdown
## Lacunas e perguntas abertas
- <pergunta objetiva para cada campo null, divergência ou limite de investigação>
```

por:

```markdown
## Lacunas e perguntas abertas
- **N1 · Negócio** — <pergunta em linguagem de negócio, sem citar código>
  <!-- evidência: <caminho:linha que sustenta a pergunta> -->
- **T1 · Técnico** — <pergunta para a equipe técnica, com a citação que ela precisa>
```

- [ ] **Passo 4: Acrescentar a seção `## Audiência das lacunas`**

Insira logo depois de `## Como preencher o template` e antes de `## Valores já convertidos pelo leitor`:

````markdown
## Audiência das lacunas

Cada lacuna é decidida por uma audiência só, e o refinamento acontece em duas reuniões separadas: uma
com a área de negócio, outra com a equipe técnica. Classificar errado manda a pergunta para a sala
errada.

**Critério:** a decisão muda o que o usuário percebe? Então é `Negócio`. Muda apenas como o sistema
guarda ou calcula, com o mesmo resultado percebido? Então é `Técnico`.

O vocabulário engana nas duas direções, e é por isso que o critério olha a consequência:

| Lacuna | Audiência | Por quê |
|---|---|---|
| A expiração deve ocorrer sozinha ou só quando alguém acessa | `Negócio` | expirar ou não é percebido |
| A renovação vale por diligência ou por executor | `Negócio` | muda quem consegue renovar |
| "Pendente" vira valor persistido ou é rótulo de exibição | `Técnico` | o usuário lê "pendente" nos dois casos |
| Onde o prazo vigente é persistido | `Técnico` | invisível |

**Uma lacuna, uma decisão, uma audiência.** Uma pergunta que funde duas decisões não classifica e vai
inteira para a reunião errada. *"Qual o valor exato da cor, e ele vale para portal e mobile?"* são
duas: o alcance nos canais é `Negócio`, o valor exato é detalhe visual e pertence ao documento de
telas. Divida em lacunas ligadas, citando a origem (`N7 origina T4`).

**Regra de tradução**, obrigatória para toda lacuna `Negócio`:

1. Não cite arquivo, classe, método, campo, enum, número de linha ou variável **na pergunta**.
2. Afirme o estado atual como fato observado — *"hoje o prazo conta 4 dias a partir do convite do
   executor"* — nunca como citação de código.
3. Termine em uma escolha concreta, com alternativas. Não em *"como deve ser?"*.
4. A evidência `caminho:linha` fica no comentário `<!-- evidência: ... -->` da própria lacuna.

Antes de encerrar, execute a partir da raiz desta skill:

```bash
uv run python scripts/verificar_lacunas.py <caminho da spec>
```

Saída 1 significa que alguma pergunta de negócio ainda cita código: reescreva-a e mova a citação para
o comentário de evidência. Não entregue a Spec com o verificador falhando.
````

- [ ] **Passo 5: Atualizar o passo 4 do fluxo**

Troque o passo 4 (linhas 41-43) por:

```markdown
4. Converta cada valor `null`, vazio ou lista vazia em uma pergunta objetiva em **Lacunas e perguntas
   abertas**, classificada por audiência conforme **Audiência das lacunas**. Nunca atribua `EXPLICITO`
   ou `INFERIDO` ao pedido original: os campos são apenas valores registrados na Demanda de Negócio.
```

- [ ] **Passo 6: Rodar os testes e confirmar que passam**

```bash
uv run pytest redigir-spec-demanda-azure-boards/tests -v
```

Esperado: tudo PASS. `test_template_nao_carrega_instrucoes_ao_agente` continua valendo — o texto novo do template usa apenas `<...>` como marcador, sem meta-instrução.

- [ ] **Passo 7: Commit**

```bash
git add redigir-spec-demanda-azure-boards
git commit -m "feat: lacunas ganham ID, audiencia e evidencia separada

O criterio olha a consequencia, nao o vocabulario: expiracao por rotina
soa tecnica e e de negocio; enum ou rotulo soa de negocio e e tecnica.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

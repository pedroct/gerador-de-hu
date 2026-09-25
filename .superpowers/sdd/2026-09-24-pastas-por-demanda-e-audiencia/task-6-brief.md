## Tarefa 6: Geração de `negocio.md` e handoff das duas rodadas

**Arquivos:**
- Modificar: `redigir-spec-demanda-azure-boards/SKILL.md` (passo 10; `## Pasta da Demanda`; nova seção `## Template de negocio.md`)
- Testar: `redigir-spec-demanda-azure-boards/tests/test_skill_integration.py`

**Interfaces:**
- Consome: da Tarefa 5, o formato de lacuna com audiência; da Tarefa 2, a pasta da Demanda.
- Produz: `negocio.md`, que a Tarefa 7 usa como material de leitura da rodada de negócio.

- [ ] **Passo 1: Escrever os testes que falham**

Acrescente a `redigir-spec-demanda-azure-boards/tests/test_skill_integration.py`:

```python
def test_pasta_inclui_negocio_md() -> None:
    assert "negocio.md" in SKILL


def test_negocio_md_nao_carrega_evidencia_de_codigo() -> None:
    secao = sem_quebras(SKILL[SKILL.index("## Template de negocio.md") :])
    assert "nunca entra em `negocio.md`" in secao
    assert "fato observado" in secao


def test_negocio_md_e_gerado_mesmo_sem_lacuna_de_negocio() -> None:
    """Sem o documento, a reunião de negócio fica sem pauta e ninguém percebe."""
    secao = sem_quebras(SKILL[SKILL.index("## Template de negocio.md") :])
    assert "gere `negocio.md` mesmo assim" in secao


def test_handoff_nomeia_as_duas_rodadas_sem_encadear() -> None:
    fluxo = SKILL[SKILL.index("## Fluxo obrigatório") : SKILL.index("## Pasta da Demanda")]
    assert "entrevistar-lacunas-requisito" in fluxo
    assert "escopo `negócio`" in fluxo
    assert "escopo `técnico`" in fluxo
    assert "não chamar entrevista, geração ou publicação de backlog" in fluxo
```

- [ ] **Passo 2: Rodar os testes e confirmar que falham**

```bash
uv run pytest redigir-spec-demanda-azure-boards/tests/test_skill_integration.py -v
```

Esperado: 4 falhas.

- [ ] **Passo 3: Acrescentar `negocio.md` à pasta**

Na seção `## Pasta da Demanda`, dentro do bloco ```` ```text ````, insira a linha depois de `├── spec.md`:

```text
├── negocio.md
```

E no bullet **Nomes internos**, troque `o vocabulário é fechado — `spec.md`, `debitos-tecnicos.md`,` por:

```markdown
- **Nomes internos:** o vocabulário é fechado — `spec.md`, `negocio.md`, `debitos-tecnicos.md`,
```

- [ ] **Passo 4: Acrescentar a seção `## Template de negocio.md`**

Insira logo depois da seção `## Audiência das lacunas`:

````markdown
## Template de negocio.md

`negocio.md` é uma **projeção** de `spec.md`, escrita para a reunião com a área de negócio. `spec.md`
continua dona de todas as lacunas; este documento mostra apenas as de audiência `Negócio`, e a
evidência `caminho:linha` **nunca entra em `negocio.md`**.

```markdown
# <System.Title>

**Demanda de Negócio #<id>** · para o refinamento de negócio

## O que foi pedido
<o conteúdo registrado na Demanda, em linguagem de negócio>

## Como funciona hoje
<o comportamento atual afirmado como fato observado, sem citar código>

## O que muda
<o comportamento esperado, em linguagem de negócio>

## Decisões pendentes
- **N1** — <pergunta, copiada de spec.md sem o comentário de evidência>
- **N2** — <pergunta>

## Fora desta reunião
<n> decisões técnicas serão tratadas no refinamento técnico.
```

Sobre **Como funciona hoje**: o que a área precisa saber de `## Comportamento atual` é o fato — *"hoje
o prazo conta 4 dias a partir do convite do executor, não 7 da abertura"* — e não a citação que o
sustenta. O fato é de negócio mesmo tendo sido descoberto no código.

Sobre **Fora desta reunião**: existe para que a área saiba que nada foi descartado, sem ser convidada
a opinar. Não liste as perguntas técnicas, apenas a contagem.

Se não houver nenhuma lacuna de audiência `Negócio`, **gere `negocio.md` mesmo assim**, com
`## Decisões pendentes` contendo `Nenhuma decisão de negócio pendente.`. Omitir o documento deixaria a
reunião sem pauta sem que ninguém percebesse.
````

- [ ] **Passo 5: Substituir o passo 10 do fluxo**

Troque o passo 10 inteiro por:

```markdown
10. Confirme que a pasta da Demanda contém `spec.md` e os companheiros gerados, registrando eventual
   indisponibilidade de uma skill especializada como lacuna. Gere `negocio.md` conforme **Template de
   negocio.md**. Execute `uv run python scripts/verificar_lacunas.py` sobre a spec e corrija o que ele
   apontar. Informe ao usuário o caminho completo da pasta, quantas lacunas existem de cada audiência e
   as duas rodadas possíveis: `entrevistar-lacunas-requisito` com escopo `negócio` sobre `negocio.md`,
   e depois com escopo `técnico` sobre `spec.md`. Em seguida, pare: não chamar entrevista, geração ou
   publicação de backlog. A geração ou publicação de backlog é uma etapa manual controlada pelo
   usuário.
```

- [ ] **Passo 6: Rodar a suíte inteira**

```bash
uv run pytest -q
```

Esperado: tudo PASS. Se `test_fluxo_estatico_preserva_ordem_gatilhos_e_lacunas` falhar no marcador do passo 10, confirme que ele ainda começa com `"Confirme que a pasta da Demanda"`.

- [ ] **Passo 7: Commit**

```bash
git add redigir-spec-demanda-azure-boards
git commit -m "feat: gera negocio.md e entrega as duas rodadas de refinamento

negocio.md e projecao de spec.md, sem evidencia de codigo. A
orquestradora nomeia as duas rodadas mas nao encadeia: a spec nasce ao
vivo, numa sala com varias pessoas, e quem decide o momento e o usuario.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

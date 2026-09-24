# Pastas por Demanda e separação de audiência — Plano de Implementação

> **Para trabalhadores agênticos:** REQUIRED SUB-SKILL: use superpowers:subagent-driven-development (recomendado) ou superpowers:executing-plans para implementar este plano tarefa a tarefa. Os passos usam `- [ ]` para rastreamento.

**Objetivo:** Agrupar os documentos de uma Demanda numa pasta própria e separar as lacunas por audiência, para que a área de negócio refine sem ler código e a equipe técnica refine em outro turno.

**Arquitetura:** Duas fases sequenciadas num plano só, porque `redigir-spec-demanda-azure-boards/SKILL.md` e `gerar-backlog-azure-boards/SKILL.md` aparecem nas duas e seriam editados duas vezes. A Fase 1 cria a pasta `DN-<id>-<slug>/` com vocabulário fechado de arquivos e é commitável sozinha. A Fase 2 acrescenta `negocio.md` como projeção de `spec.md`, classifica cada lacuna por audiência e dá escopo à entrevista. `spec.md` permanece fonte única em ambas.

**Stack:** Markdown (o artefato das skills), Python 3.12 com `uv`, `pytest`. Os testes deste repositório afirmam sobre o **texto** dos `SKILL.md`; só o verificador da Fase 2 tem lógica executável.

**Specs:**
- [`docs/superpowers/specs/2026-09-24-convencao-nomes-spec-demanda-design.md`](../specs/2026-09-24-convencao-nomes-spec-demanda-design.md) — Fase 1
- [`docs/superpowers/specs/2026-09-24-separar-refinamento-negocio-tecnico-design.md`](../specs/2026-09-24-separar-refinamento-negocio-tecnico-design.md) — Fase 2

## Restrições globais

- **Idioma:** todo conteúdo criado ou alterado é em português brasileiro, incluindo mensagens de commit. Vale para `SKILL.md`, referências, README, docstrings e nomes de teste.
- **Vocabulário fechado de arquivos na pasta:** exatamente `spec.md`, `negocio.md`, `debitos-tecnicos.md`, `telas-ux-ui.md`, `revisao-textos.md`. Sem prefixo `spec-`.
- **Nome da pasta:** `DN-<id>-<slug>`. `<id>` é o ID numérico sem zeros à esquerda; `<slug>` deriva de `System.Title` em kebab-case, sem acentos, truncado em 60 caracteres.
- **Raiz padrão:** `docs/specs/`, com o usuário podendo indicar outra na invocação. A skill sempre informa o caminho final usado.
- **A busca por título é fallback permanente**, não etapa de transição. `gerar-backlog-azure-boards` deve continuar achando `Spec: Telas UX-UI — <contexto>` pelo título quando não receber pasta.
- **O nome da pasta nunca é fonte do ID da Demanda.** O ID sai exclusivamente da seção `## Fonte da Demanda` de `spec.md`.
- **O escopo de audiência é filtro opcional, nunca requisito de formato.** Spec sem rótulos se comporta como hoje.
- **A orquestradora não encadeia entrevista, geração nem publicação de backlog.** A proibição existente permanece.
- **Testes:** `uv run pytest <caminho> -v`. Toda skill nova em `testpaths` do `pyproject.toml`.
- **Commits:** terminam com a linha `Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>`. O `pre-commit` roda commitizen e exige Conventional Commits.

## Foco de revisão

Casos que as specs implicam mas que nenhuma tarefa exercitaria por acidente. Cada linha tem seu teste fixado na tarefa que possui o código.

1. **Spec antiga, sem rótulos de audiência, entrando na entrevista** — deve perguntar tudo como hoje, nunca falhar nem devolver lista vazia. É o caso de todas as specs que o usuário já tem. → Tarefa 7.
2. **Segunda execução sobre a mesma Demanda, com a pasta já existente** — deve reaproveitar a pasta e substituir os arquivos que regerar, nunca criar `DN-14125-...-2` nem abortar. → Tarefa 2.
3. **Título que produz slug degenerado** (só pontuação, só acentos, ou vazio) — o nome da pasta não pode terminar em hífen nem virar `DN-14125-`. → Tarefa 2.
4. **Demanda sem nenhuma lacuna de negócio** — `negocio.md` ainda deve ser gerado, dizendo que não há decisão pendente de negócio, em vez de ser omitido e deixar a reunião sem pauta. → Tarefa 6.
5. **Nome de campo do Azure Boards dentro de uma pergunta de negócio** (`Custom.DemandaValorEsperado`) — é vocabulário técnico que o PO não reconhece; o verificador deve sinalizar. → Tarefa 4.

---

## Estrutura de arquivos

**Fase 1**

| Arquivo | Responsabilidade |
|---|---|
| `especificar-debitos-tecnicos/SKILL.md` | aceitar diretório de destino opcional; salvar como `debitos-tecnicos.md` |
| `especificar-telas-ux-ui/SKILL.md` | idem; salvar como `telas-ux-ui.md` |
| `revisar-textos-requisitos/SKILL.md` | ganhar título de documento; idem; salvar como `revisao-textos.md` |
| `redigir-spec-demanda-azure-boards/SKILL.md` | criar a pasta e repassar o caminho às três |
| `gerar-backlog-azure-boards/SKILL.md` | atalho por pasta, preservando busca por título |
| `gerar-backlog-azure-boards/references/backlog-markdown-contract.md` | proibir o nome da pasta como fonte do ID |

**Fase 2**

| Arquivo | Responsabilidade |
|---|---|
| `redigir-spec-demanda-azure-boards/scripts/verificar_lacunas.py` | extrair lacunas e detectar vazamento de vocabulário técnico |
| `redigir-spec-demanda-azure-boards/tests/test_verificar_lacunas.py` | testes do verificador |
| `redigir-spec-demanda-azure-boards/SKILL.md` | template de lacuna, critério de audiência, regra de tradução, `negocio.md`, handoff |
| `entrevistar-lacunas-requisito/SKILL.md` | escopo compondo com a fronteira; desfecho "criar lacuna nova" |
| `gerar-backlog-azure-boards/SKILL.md` | sugerir a rodada com o escopo correspondente |

---

# FASE 1 — Pastas por Demanda

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

## Tarefa 4: Verificador de linguagem das lacunas de negócio

Única parte do plano com lógica executável. Vem primeiro na fase porque é autocontida e a Tarefa 5 a referencia.

**Arquivos:**
- Criar: `redigir-spec-demanda-azure-boards/scripts/verificar_lacunas.py`
- Criar: `redigir-spec-demanda-azure-boards/tests/test_verificar_lacunas.py`
- Modificar: `pyproject.toml` (seção `[tool.coverage.run] source`, se ainda não cobrir `redigir-spec-demanda-azure-boards/scripts`)

**Interfaces:**
- Consome: nada.
- Produz:
  - `Lacuna(identificador: str, audiencia: str, pergunta: str, linha: int)` — dataclass congelada
  - `Violacao(lacuna: Lacuna, trecho: str, padrao: str)` — dataclass congelada
  - `extrair_lacunas(texto: str) -> list[Lacuna]`
  - `verificar(texto: str) -> list[Violacao]`
  - `main() -> int` — CLI, saída 1 com violações, 0 sem

- [ ] **Passo 1: Escrever os testes que falham**

Crie `redigir-spec-demanda-azure-boards/tests/test_verificar_lacunas.py`:

```python
import sys
from pathlib import Path

RAIZ_SKILL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ_SKILL / "scripts"))

from verificar_lacunas import extrair_lacunas, verificar  # noqa: E402

SPEC = """# Spec: Exemplo

## Lacunas e perguntas abertas

- **N1 · Negócio** — Hoje a data que o usuário vê não é a mesma que faz a diligência
  expirar. As duas devem virar uma só?
  <!-- evidência: MinhaDiligenciaDTO.java:76-78 vs DiligenciaService.java:269-270 -->
- **T1 · Técnico** — O prazo vigente deve ser persistido em `Diligencia.java:75` ou
  derivado na leitura?
"""


def test_extrai_identificador_audiencia_e_pergunta() -> None:
    lacunas = extrair_lacunas(SPEC)
    assert [l.identificador for l in lacunas] == ["N1", "T1"]
    assert [l.audiencia for l in lacunas] == ["Negócio", "Técnico"]
    assert "virar uma só?" in lacunas[0].pergunta


def test_evidencia_nao_entra_na_pergunta() -> None:
    """A evidência fica na spec, mas fora do corpo que vai para `negocio.md`."""
    lacunas = extrair_lacunas(SPEC)
    assert "MinhaDiligenciaDTO" not in lacunas[0].pergunta
    assert ".java" not in lacunas[0].pergunta


def test_spec_limpa_nao_gera_violacao() -> None:
    assert verificar(SPEC) == []


def test_lacuna_tecnica_pode_citar_codigo() -> None:
    """A regra de tradução vale só para `Negócio`; o dev precisa da citação."""
    assert all(v.lacuna.audiencia != "Técnico" for v in verificar(SPEC))


def test_caminho_de_arquivo_em_pergunta_de_negocio_viola() -> None:
    texto = "- **N2 · Negócio** — O prazo sai de `DiligenciaService.java:269` ou da abertura?\n"
    violacoes = verificar(texto)
    assert len(violacoes) == 1
    assert violacoes[0].lacuna.identificador == "N2"
    assert violacoes[0].padrao == "caminho-de-arquivo"


def test_numero_de_linha_em_pergunta_de_negocio_viola() -> None:
    texto = "- **N3 · Negócio** — Quem vê o rótulo, conforme :140-145 do portal?\n"
    assert [v.padrao for v in verificar(texto)] == ["numero-de-linha"]


def test_chamada_de_metodo_em_pergunta_de_negocio_viola() -> None:
    texto = "- **N4 · Negócio** — A contagem usa LocalDateTime.plusDays() ou data civil?\n"
    assert [v.padrao for v in verificar(texto)] == ["chamada-de-metodo"]


def test_campo_do_azure_boards_em_pergunta_de_negocio_viola() -> None:
    """Vocabulário técnico que o PO não reconhece, ainda que não seja código-fonte."""
    texto = "- **N5 · Negócio** — O valor de Custom.DemandaValorEsperado está completo?\n"
    assert [v.padrao for v in verificar(texto)] == ["identificador-pontuado"]


def test_spec_sem_rotulos_de_audiencia_nao_gera_violacao() -> None:
    """Spec antiga não é violação: o verificador simplesmente não encontra lacunas rotuladas."""
    antiga = "## Lacunas e perguntas abertas\n\n- Qual data ancora o prazo (`X.java:12`)?\n"
    assert extrair_lacunas(antiga) == []
    assert verificar(antiga) == []
```

- [ ] **Passo 2: Rodar os testes e confirmar que falham**

```bash
uv run pytest redigir-spec-demanda-azure-boards/tests/test_verificar_lacunas.py -v
```

Esperado: `ModuleNotFoundError: No module named 'verificar_lacunas'`.

- [ ] **Passo 3: Escrever o verificador**

Crie `redigir-spec-demanda-azure-boards/scripts/verificar_lacunas.py`:

```python
"""Verifica se lacunas de negócio vazaram vocabulário técnico.

A regra de tradução exige que uma pergunta destinada à área de negócio não cite arquivo, classe,
método, campo, enum, número de linha ou variável. A evidência `caminho:linha` continua na spec, em
comentário, mas fora do corpo da pergunta.

Uso:
    uv run python redigir-spec-demanda-azure-boards/scripts/verificar_lacunas.py spec.md
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

CABECALHO = re.compile(
    r"^- \*\*(?P<id>[NT]\d+) · (?P<audiencia>Negócio|Técnico)\*\* — (?P<inicio>.*)$"
)
EVIDENCIA = re.compile(r"<!--.*?-->", re.DOTALL)

EXTENSOES = "java|ts|tsx|js|jsx|dart|py|kt|swift|cs|rb|go|php|vue|html|scss|css|sql|xml|ya?ml|json"
PADROES: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("caminho-de-arquivo", re.compile(rf"[\w/.\-]+\.({EXTENSOES})\b")),
    ("numero-de-linha", re.compile(r":\d+(?:-\d+)?\b")),
    ("chamada-de-metodo", re.compile(r"\b[A-Za-z_][\w.]*\.[a-z]\w*\s*\(")),
    ("identificador-pontuado", re.compile(r"\b[A-Z][A-Za-z0-9]*\.[A-Za-z][A-Za-z0-9]*\b")),
)


@dataclass(frozen=True)
class Lacuna:
    identificador: str
    audiencia: str
    pergunta: str
    linha: int


@dataclass(frozen=True)
class Violacao:
    lacuna: Lacuna
    trecho: str
    padrao: str


def extrair_lacunas(texto: str) -> list[Lacuna]:
    """Devolve as lacunas rotuladas. Uma spec sem rótulos devolve lista vazia, não erro."""
    lacunas: list[Lacuna] = []
    identificador = ""
    audiencia = ""
    linha_inicial = 0
    corpo: list[str] = []
    aberta = False

    def fechar() -> None:
        nonlocal aberta
        if not aberta:
            return
        pergunta = " ".join(EVIDENCIA.sub(" ", " ".join(corpo)).split())
        lacunas.append(Lacuna(identificador, audiencia, pergunta, linha_inicial))
        aberta = False

    for numero, linha in enumerate(texto.splitlines(), start=1):
        encontrado = CABECALHO.match(linha)
        if encontrado:
            fechar()
            identificador = encontrado.group("id")
            audiencia = encontrado.group("audiencia")
            linha_inicial = numero
            corpo = [encontrado.group("inicio")]
            aberta = True
        elif aberta and linha.startswith(("  ", "\t")):
            corpo.append(linha.strip())
        elif aberta:
            fechar()
    fechar()
    return lacunas


def verificar(texto: str) -> list[Violacao]:
    """Sinaliza vocabulário técnico dentro de perguntas de negócio."""
    violacoes: list[Violacao] = []
    for lacuna in extrair_lacunas(texto):
        if lacuna.audiencia != "Negócio":
            continue
        for nome, padrao in PADROES:
            achado = padrao.search(lacuna.pergunta)
            if achado:
                violacoes.append(Violacao(lacuna=lacuna, trecho=achado.group(0), padrao=nome))
                break
    return violacoes


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spec", help="caminho da spec, ou '-' para a entrada padrão")
    args = parser.parse_args()

    texto = sys.stdin.read() if args.spec == "-" else Path(args.spec).read_text("utf-8")
    violacoes = verificar(texto)
    if not violacoes:
        print("Nenhum vazamento de vocabulário técnico em lacunas de negócio.")
        return 0

    for violacao in violacoes:
        print(
            f"linha {violacao.lacuna.linha}: {violacao.lacuna.identificador} "
            f"({violacao.padrao}) — {violacao.trecho!r}",
            file=sys.stderr,
        )
    print(
        f"\n{len(violacoes)} lacuna(s) de negócio citam código. "
        "Reescreva a pergunta e mova a citação para o comentário de evidência.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Passo 4: Rodar os testes e confirmar que passam**

```bash
uv run pytest redigir-spec-demanda-azure-boards/tests/test_verificar_lacunas.py -v
```

Esperado: 9 PASS. Se `test_chamada_de_metodo_em_pergunta_de_negocio_viola` devolver `identificador-pontuado`, confirme que `chamada-de-metodo` vem antes na tupla `PADROES` — a ordem define qual padrão reporta.

- [ ] **Passo 5: Conferir a CLI na mão**

```bash
printf -- '- **N9 · Negócio** — O prazo sai de `X.java:12` ou da abertura?\n' \
  | uv run python redigir-spec-demanda-azure-boards/scripts/verificar_lacunas.py -
echo "codigo de saida: $?"
```

Esperado: mensagem em `stderr` citando `N9` e `caminho-de-arquivo`, código de saída 1.

- [ ] **Passo 6: Rodar lint e tipos**

```bash
uv run ruff check redigir-spec-demanda-azure-boards/scripts/verificar_lacunas.py
uv run ruff format --check redigir-spec-demanda-azure-boards/scripts/verificar_lacunas.py
uv run mypy --strict redigir-spec-demanda-azure-boards/scripts/verificar_lacunas.py
```

Esperado: `All checks passed!`, `1 file already formatted` e `Success: no issues found`. Este código
já foi validado contra os três — se algum acusar, foi a transcrição que divergiu, não o desenho.

- [ ] **Passo 7: Commit**

```bash
git add redigir-spec-demanda-azure-boards/scripts/verificar_lacunas.py \
        redigir-spec-demanda-azure-boards/tests/test_verificar_lacunas.py pyproject.toml
git commit -m "feat: verifica vazamento de vocabulario tecnico em lacuna de negocio

Unica parte do desenho com verificacao executavel, e justamente a que
falhou na reuniao que originou a mudanca. Spec sem rotulos nao e
violacao: o verificador simplesmente nao encontra lacunas rotuladas.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

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

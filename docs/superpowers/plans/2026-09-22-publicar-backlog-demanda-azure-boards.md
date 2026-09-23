# Plano de implementação: publicar backlog vinculado a uma Demanda de Negócio

> **Para agentes executores:** REQUIRED SUB-SKILL: use superpowers:subagent-driven-development
> (recomendado) ou superpowers:executing-plans para implementar tarefa a tarefa. Os passos usam
> caixas de seleção (`- [ ]`) para acompanhamento.

**Goal:** Criar a skill `publicar-backlog-demanda-azure-boards`, que recebe o ID de uma Demanda de
Negócio e publica o backlog Markdown revisado como hierarquia filha dela no Azure Boards.

**Architecture:** Fork completo de `publicar-backlog-azure-boards` com pacote próprio. Quatro módulos
permanecem cópia literal, guardados por um teste de sincronia; os demais divergem para acomodar o pai
externo, a herança de caminhos, o título hierárquico e a vinculação do ID da Demanda ao hash, à frase
de autorização e ao manifesto.

**Tech Stack:** Python 3.12+, httpx, pydantic, pytest, ruff, mypy strict, bandit, uv.

**Spec:** [docs/superpowers/specs/2026-09-22-publicar-backlog-demanda-azure-boards-design.md](../specs/2026-09-22-publicar-backlog-demanda-azure-boards-design.md)

## Global Constraints

- Todo texto produzido — código, docstrings, mensagens de erro, testes, documentação e mensagens de
  commit — em **português brasileiro**.
- `requires-python = ">=3.12"`; `target-version = "py312"`.
- Dependências fixadas exatamente como na skill de origem: `httpx==0.28.1`,
  `markdown-it-py==4.2.0`, `pydantic==2.13.5`, `pydantic-settings==2.15.0`.
- `ruff` com `line-length = 100` e `select = ["E", "F", "I", "B", "UP", "S"]`; `mypy` em modo
  `strict` sobre `src`; `bandit` ignorando `tests`.
- O token **nunca** aparece em argumento de linha de comando, log, manifesto, plano, exemplo ou
  mensagem de erro. Ele vem só de `AZURE_DEVOPS_TOKEN` ou de entrada interativa sem eco.
- Nenhum teste faz chamada HTTP real: todo transporte é `httpx.MockTransport`.
- Commits seguem Conventional Commits (o hook `commitizen` bloqueia o que não seguir).
- Nenhuma tarefa altera a skill `publicar-backlog-azure-boards`.

## Desvio da spec descoberto no planejamento

A spec previa `obter_demanda` como método de `ClienteAzureDevOps`. Isso não funciona: o cliente é
construído recebendo uma `ConfiguracaoPublicacao` já pronta, e os caminhos dessa configuração passam
a vir justamente da Demanda que ainda não foi lida. A leitura vai para um módulo próprio,
`leitor_demanda.py`, com uma função livre que recebe organização, projeto e token diretamente. O teste
correspondente chama-se `test_leitor_demanda.py`, e não `test_obter_demanda.py`. O comportamento
exigido pela spec é idêntico; muda apenas onde ele mora.

## Estrutura de arquivos

| Arquivo | Responsabilidade |
|---|---|
| `src/.../contrato_backlog.py` | Regras estruturais do Markdown. **Cópia literal.** |
| `src/.../converter_para_html.py` | Conversão de Markdown para HTML. **Cópia literal.** |
| `src/.../interpretar_markdown.py` | Leitura dos itens e da data de geração. **Cópia literal.** |
| `src/.../validacao_estrutural.py` | Fachada de validação do documento. **Cópia literal.** |
| `src/.../modelos.py` | Dataclasses imutáveis, incluindo `Demanda` e o `demanda_id` do destino. |
| `src/.../titulo_hierarquico.py` | Converte a chave documental em numeração de título. |
| `src/.../leitor_demanda.py` | Lê a Demanda por `GET` e valida tipo, projeto e caminhos. |
| `src/.../planejar_publicacao.py` | Monta operações e hash a partir dos itens e do destino. |
| `src/.../executar_publicacao.py` | Executa o plano autorizado; pendura os Épicos na Demanda. |
| `src/.../cliente_azure_devops.py` | REST: verificação de destino, validação e criação. |
| `src/.../autorizacao.py` | Frase de confirmação e impressões vinculantes. |
| `src/.../manifesto.py` | Persistência atômica e validação da retomada. |
| `src/.../configuracao.py` | Precedência de configuração e derivação do destino. |
| `src/.../cli.py` | Orquestração dos comandos. |

---

### Task 1: Fork base do pacote

Copiar a skill de origem, renomear o pacote e deixar a suíte herdada verde antes de qualquer mudança
de comportamento. Nada aqui muda lógica: é o ponto de partida idêntico contra o qual as tarefas
seguintes vão divergir.

**Files:**
- Create: `publicar-backlog-demanda-azure-boards/` (cópia de `publicar-backlog-azure-boards/`)
- Create: `publicar-backlog-demanda-azure-boards/pyproject.toml`
- Create: `publicar-backlog-demanda-azure-boards/src/publicar_backlog_demanda_azure_boards/*`
- Test: `publicar-backlog-demanda-azure-boards/tests/*` (13 arquivos herdados)

**Interfaces:**
- Consumes: nada.
- Produces: o pacote `publicar_backlog_demanda_azure_boards` com a API pública idêntica à da origem —
  `criar_plano`, `executar_plano`, `criar_autorizacao`, `ler_manifesto`, `validar_manifesto`,
  `gravar_manifesto`, `carregar_configuracao`, `ClienteAzureDevOps`, `principal`.

- [ ] **Step 1: Copiar a árvore, sem artefatos de build**

```bash
cd /Volumes/DOCK/Projetos/pessoal/gerador-hu
rsync -a --exclude '.venv' --exclude '.mypy_cache' --exclude '.ruff_cache' \
      --exclude '.pytest_cache' --exclude '__pycache__' --exclude 'uv.lock' \
      publicar-backlog-azure-boards/ publicar-backlog-demanda-azure-boards/
git -C . status --short publicar-backlog-demanda-azure-boards | head
```

- [ ] **Step 2: Renomear o pacote e as importações**

```bash
cd /Volumes/DOCK/Projetos/pessoal/gerador-hu/publicar-backlog-demanda-azure-boards
mv src/publicar_backlog_azure_boards src/publicar_backlog_demanda_azure_boards
mv scripts/publicar_backlog.py scripts/publicar_backlog_demanda.py
grep -rl 'publicar_backlog_azure_boards' src scripts tests \
  | xargs sed -i '' 's/publicar_backlog_azure_boards/publicar_backlog_demanda_azure_boards/g'
grep -rn 'publicar_backlog_azure_boards' src scripts tests || echo "nenhuma referência antiga"
```

- [ ] **Step 3: Ajustar o `pyproject.toml`**

Trocar as quatro ocorrências do nome antigo, mantendo todo o resto idêntico:

```toml
[project]
name = "publicar-backlog-demanda-azure-boards"
version = "0.1.0"
description = "Publicador de backlogs Markdown vinculados a uma Demanda de Negócio no Azure Boards"

[project.scripts]
publicar-backlog-demanda-azure-boards = "publicar_backlog_demanda_azure_boards:main"

[tool.hatch.build.targets.wheel]
packages = ["src/publicar_backlog_demanda_azure_boards"]
```

- [ ] **Step 4: Ajustar as referências textuais ao nome da ferramenta**

```bash
cd /Volumes/DOCK/Projetos/pessoal/gerador-hu/publicar-backlog-demanda-azure-boards
sed -i '' 's/prog="publicar-backlog-azure-boards"/prog="publicar-backlog-demanda-azure-boards"/' \
  src/publicar_backlog_demanda_azure_boards/cli.py
grep -rn 'publicar_backlog\.py' tests src scripts || echo "nenhuma referência ao script antigo"
```

Onde `grep` apontar `scripts/publicar_backlog.py` em teste ou documentação, trocar por
`scripts/publicar_backlog_demanda.py`.

- [ ] **Step 5: Rodar a suíte herdada e confirmar que está verde**

```bash
cd /Volumes/DOCK/Projetos/pessoal/gerador-hu/publicar-backlog-demanda-azure-boards
uv sync
uv run pytest
```

Esperado: PASS em todos os testes herdados. Se `test_instalacao.py`,
`test_configuracao_projeto.py` ou `test_documentacao_operacional.py` falharem, é porque afirmam o
nome antigo do pacote, do script ou do projeto — corrigir a afirmação no teste para o nome novo,
nunca afrouxá-la.

- [ ] **Step 6: Commit**

```bash
cd /Volumes/DOCK/Projetos/pessoal/gerador-hu
git add publicar-backlog-demanda-azure-boards
git commit -m "feat: cria o fork base do publicador vinculado a Demanda"
```

---

### Task 2: Teste de sincronia com a skill de origem

Quatro módulos devem permanecer idênticos à origem. Este teste é a defesa acordada contra a
divergência silenciosa que o fork introduz.

**Files:**
- Create: `publicar-backlog-demanda-azure-boards/tests/test_sincronia_com_origem.py`

**Interfaces:**
- Consumes: o pacote criado na Task 1.
- Produces: `MODULOS_ESPELHADOS: tuple[str, ...]` — a lista canônica dos módulos de cópia literal,
  consultada por revisores e por tarefas futuras que alterarem esses arquivos.

- [ ] **Step 1: Escrever o teste**

```python
"""Garante que os módulos de cópia literal não divirjam da skill de origem."""

from pathlib import Path

import pytest

MODULOS_ESPELHADOS: tuple[str, ...] = (
    "contrato_backlog.py",
    "converter_para_html.py",
    "interpretar_markdown.py",
    "validacao_estrutural.py",
)

_RAIZ_SKILL = Path(__file__).resolve().parents[1]
_PACOTE_LOCAL = _RAIZ_SKILL / "src" / "publicar_backlog_demanda_azure_boards"
_PACOTE_ORIGEM = (
    _RAIZ_SKILL.parent / "publicar-backlog-azure-boards" / "src" / "publicar_backlog_azure_boards"
)


@pytest.mark.parametrize("modulo", MODULOS_ESPELHADOS)
def test_modulo_espelhado_e_identico_ao_da_origem(modulo: str) -> None:
    if not _PACOTE_ORIGEM.is_dir():
        pytest.skip(
            "A skill publicar-backlog-azure-boards não está presente; "
            "a comparação de sincronia não se aplica."
        )
    local = _PACOTE_LOCAL / modulo
    origem = _PACOTE_ORIGEM / modulo
    assert origem.is_file(), f"{modulo} não existe na skill de origem."
    esperado = origem.read_text(encoding="utf-8").replace(
        "publicar_backlog_azure_boards", "publicar_backlog_demanda_azure_boards"
    )
    assert local.read_text(encoding="utf-8") == esperado, (
        f"{modulo} divergiu da skill de origem. Ressincronize os dois lados antes de prosseguir."
    )


def test_modulos_espelhados_existem_no_pacote_local() -> None:
    ausentes = [modulo for modulo in MODULOS_ESPELHADOS if not (_PACOTE_LOCAL / modulo).is_file()]
    assert not ausentes, f"Módulos espelhados ausentes no pacote local: {ausentes}"
```

- [ ] **Step 2: Rodar e confirmar que passa**

```bash
cd /Volumes/DOCK/Projetos/pessoal/gerador-hu/publicar-backlog-demanda-azure-boards
uv run pytest tests/test_sincronia_com_origem.py -v
```

Esperado: PASS nos cinco casos (quatro parametrizados mais o de existência).

- [ ] **Step 3: Provar que o teste realmente pega uma divergência**

```bash
cd /Volumes/DOCK/Projetos/pessoal/gerador-hu/publicar-backlog-demanda-azure-boards
printf '\n# divergência proposital\n' >> src/publicar_backlog_demanda_azure_boards/contrato_backlog.py
uv run pytest tests/test_sincronia_com_origem.py -v
```

Esperado: FAIL em `contrato_backlog.py` com a mensagem "divergiu da skill de origem". Em seguida,
desfazer:

```bash
git checkout -- src/publicar_backlog_demanda_azure_boards/contrato_backlog.py
uv run pytest tests/test_sincronia_com_origem.py -q
```

Esperado: PASS de novo.

- [ ] **Step 4: Commit**

```bash
cd /Volumes/DOCK/Projetos/pessoal/gerador-hu
git add publicar-backlog-demanda-azure-boards/tests/test_sincronia_com_origem.py
git commit -m "test: guarda os modulos de copia literal contra divergencia"
```

---

### Task 3: Módulo de numeração hierárquica

**Files:**
- Create: `publicar-backlog-demanda-azure-boards/src/publicar_backlog_demanda_azure_boards/titulo_hierarquico.py`
- Test: `publicar-backlog-demanda-azure-boards/tests/test_titulo_hierarquico.py`

**Interfaces:**
- Consumes: `ItemBacklog` de `modelos.py` (campos `chave`, `titulo`, `titulo_curto`).
- Produces:
  - `numerar(chave: str) -> str`
  - `montar_titulo(item: ItemBacklog) -> str`

- [ ] **Step 1: Escrever os testes que falham**

```python
"""Numeração de título no formato praticado no board de destino."""

import pytest

from publicar_backlog_demanda_azure_boards.modelos import ItemBacklog, TipoItem
from publicar_backlog_demanda_azure_boards.titulo_hierarquico import montar_titulo, numerar


@pytest.mark.parametrize(
    ("chave", "esperado"),
    [
        ("1.0.0", "01"),
        ("1.1.0", "01.01"),
        ("1.1.1", "01.01.01"),
        ("2.3.4", "02.03.04"),
        ("10.0.0", "10"),
        ("10.11.12", "10.11.12"),
        ("100.0.0", "100"),
        ("1.1.112", "01.01.112"),
    ],
)
def test_numerar_converte_a_chave_documental(chave: str, esperado: str) -> None:
    assert numerar(chave) == esperado


@pytest.mark.parametrize("chave", ["", "1", "1.1", "1.1.1.1", "a.b.c", "1.-1.0"])
def test_numerar_rejeita_chave_fora_do_contrato(chave: str) -> None:
    with pytest.raises(ValueError):
        numerar(chave)


def test_montar_titulo_usa_o_titulo_curto_quando_existe() -> None:
    item = ItemBacklog(
        chave="1.1.1",
        tipo=TipoItem.HISTORIA_USUARIO,
        titulo="Análise de padrões de stacks em todos os repositórios",
        pai="1.1.0",
        descricao="",
        criterios_aceitacao="",
        titulo_curto="Análise de padrões de stacks",
    )
    assert montar_titulo(item) == "01.01.01 Análise de padrões de stacks"


def test_montar_titulo_cai_no_titulo_longo_sem_titulo_curto() -> None:
    item = ItemBacklog(
        chave="1.0.0",
        tipo=TipoItem.EPIC,
        titulo="Gestão do projeto",
        pai=None,
        descricao="",
        criterios_aceitacao="",
    )
    assert montar_titulo(item) == "01 Gestão do projeto"


def test_montar_titulo_nao_inclui_data() -> None:
    item = ItemBacklog(
        chave="1.1.0",
        tipo=TipoItem.FEATURE,
        titulo="Gestão do projeto",
        pai="1.0.0",
        descricao="",
        criterios_aceitacao="",
    )
    titulo = montar_titulo(item)
    assert titulo == "01.01 Gestão do projeto"
    assert "2026" not in titulo
```

- [ ] **Step 2: Rodar e confirmar a falha**

```bash
cd /Volumes/DOCK/Projetos/pessoal/gerador-hu/publicar-backlog-demanda-azure-boards
uv run pytest tests/test_titulo_hierarquico.py -v
```

Esperado: FAIL com `ModuleNotFoundError: No module named
'publicar_backlog_demanda_azure_boards.titulo_hierarquico'`.

- [ ] **Step 3: Implementar o módulo**

```python
"""Converte a chave documental do backlog na numeração usada no título do work item."""

from __future__ import annotations

from publicar_backlog_demanda_azure_boards.modelos import ItemBacklog

_LARGURA_MINIMA = 2


def numerar(chave: str) -> str:
    """Converte `E.F.S` na numeração hierárquica, descartando os níveis não usados.

    O contrato do backlog garante que um Épico seja `E.0.0` e uma Feature, `E.F.0`. Os
    componentes finais iguais a zero são, portanto, marcadores de nível ausente e não
    pertencem ao título: `1.0.0` vira `01` e `1.1.0` vira `01.01`.
    """
    componentes = chave.split(".")
    if len(componentes) != 3:
        raise ValueError(f"A chave {chave!r} não está no formato E.F.S.")
    try:
        numeros = [int(componente) for componente in componentes]
    except ValueError as erro:
        raise ValueError(f"A chave {chave!r} possui componente não numérico.") from erro
    if any(numero < 0 for numero in numeros):
        raise ValueError(f"A chave {chave!r} possui componente negativo.")
    while len(numeros) > 1 and numeros[-1] == 0:
        numeros.pop()
    return ".".join(str(numero).zfill(_LARGURA_MINIMA) for numero in numeros)


def montar_titulo(item: ItemBacklog) -> str:
    """Compõe o título publicado: numeração hierárquica seguida do texto do item."""
    return f"{numerar(item.chave)} {item.titulo_curto or item.titulo}"
```

- [ ] **Step 4: Rodar e confirmar que passa**

```bash
cd /Volumes/DOCK/Projetos/pessoal/gerador-hu/publicar-backlog-demanda-azure-boards
uv run pytest tests/test_titulo_hierarquico.py -v
```

Esperado: PASS nos 16 casos.

- [ ] **Step 5: Commit**

```bash
cd /Volumes/DOCK/Projetos/pessoal/gerador-hu
git add publicar-backlog-demanda-azure-boards/src/publicar_backlog_demanda_azure_boards/titulo_hierarquico.py \
        publicar-backlog-demanda-azure-boards/tests/test_titulo_hierarquico.py
git commit -m "feat: numera titulos no formato hierarquico do board"
```

---

### Task 4: O plano passa a usar o título hierárquico

**Files:**
- Modify: `publicar-backlog-demanda-azure-boards/src/publicar_backlog_demanda_azure_boards/planejar_publicacao.py`
- Test: `publicar-backlog-demanda-azure-boards/tests/test_planejar_publicacao.py`

**Interfaces:**
- Consumes: `montar_titulo(item)` da Task 3.
- Produces: `criar_plano(itens, configuracao, data_geracao)` com assinatura inalterada; muda apenas o
  conteúdo de `OperacaoCriacao.titulo`. `data_geracao` continua entrando no hash.

- [ ] **Step 1: Escrever o teste que falha**

Acrescentar a `tests/test_planejar_publicacao.py`:

```python
def test_titulo_usa_numeracao_hierarquica_sem_data(configuracao_exemplo) -> None:
    itens = [
        ItemBacklog(
            chave="1.0.0",
            tipo=TipoItem.EPIC,
            titulo="Gestão do projeto",
            pai=None,
            descricao="",
            criterios_aceitacao="",
        ),
        ItemBacklog(
            chave="1.1.1",
            tipo=TipoItem.HISTORIA_USUARIO,
            titulo="Análise de padrões de stacks",
            pai="1.1.0",
            descricao="",
            criterios_aceitacao="",
        ),
    ]
    plano = criar_plano(itens, configuracao_exemplo, "2026-09-22")
    titulos = {operacao.chave: operacao.titulo for operacao in plano.operacoes}
    assert titulos["1.0.0"] == "01 Gestão do projeto"
    assert titulos["1.1.1"] == "01.01.01 Análise de padrões de stacks"
    assert all("2026-09-22" not in titulo for titulo in titulos.values())


def test_data_de_geracao_continua_no_hash(configuracao_exemplo) -> None:
    itens = [
        ItemBacklog(
            chave="1.0.0",
            tipo=TipoItem.EPIC,
            titulo="Gestão do projeto",
            pai=None,
            descricao="",
            criterios_aceitacao="",
        )
    ]
    primeiro = criar_plano(itens, configuracao_exemplo, "2026-09-22")
    segundo = criar_plano(itens, configuracao_exemplo, "2026-09-23")
    assert primeiro.hash_plano != segundo.hash_plano
```

Onde `configuracao_exemplo` é a fixture de `ConfiguracaoPublicacao` já usada pelo arquivo. Se ela não
existir com esse nome, reutilizar a construção local que os testes existentes já fazem.

- [ ] **Step 2: Rodar e confirmar a falha**

```bash
cd /Volumes/DOCK/Projetos/pessoal/gerador-hu/publicar-backlog-demanda-azure-boards
uv run pytest tests/test_planejar_publicacao.py -v
```

Esperado: FAIL em `test_titulo_usa_numeracao_hierarquica_sem_data`, com o título recebido começando
por `2026-09-22`. Os testes herdados que afirmam o título datado também falham — eles serão corrigidos
no passo seguinte, porque afirmam o comportamento antigo.

- [ ] **Step 3: Trocar a montagem do título**

Em `planejar_publicacao.py`, acrescentar a importação e substituir a linha do título:

```python
from publicar_backlog_demanda_azure_boards.titulo_hierarquico import montar_titulo
```

```python
def _criar_operacao(
    item: ItemBacklog, configuracao: ConfiguracaoPublicacao, data_geracao: str
) -> OperacaoCriacao:
    return OperacaoCriacao(
        chave=item.chave,
        tipo=item.tipo,
        titulo=montar_titulo(item),
        descricao=converter_descricao(item.descricao),
        criterios_aceitacao=converter_criterios(item.criterios_aceitacao),
        chave_pai=item.pai,
        tipo_remoto=configuracao.mapeamento_tipos.nome_remoto(item.tipo),
    )
```

`data_geracao` deixa de ser usado por `_criar_operacao`, mas **permanece** no parâmetro de
`criar_plano` e dentro de `_calcular_hash`. Trocar a assinatura para
`_criar_operacao(item, configuracao)` e ajustar a chamada.

- [ ] **Step 4: Corrigir os testes herdados que afirmam o título datado**

```bash
cd /Volumes/DOCK/Projetos/pessoal/gerador-hu/publicar-backlog-demanda-azure-boards
grep -rn '2026-\|data_geracao' tests/*.py | grep -i titulo
```

Em cada afirmação encontrada, trocar o título esperado `"<data> <chave> <texto>"` pelo hierárquico
`"<numeração> <texto>"`. Não remover a afirmação: ela continua provando qual título é enviado.

- [ ] **Step 5: Rodar a suíte inteira**

```bash
cd /Volumes/DOCK/Projetos/pessoal/gerador-hu/publicar-backlog-demanda-azure-boards
uv run pytest
```

Esperado: PASS em tudo.

- [ ] **Step 6: Commit**

```bash
cd /Volumes/DOCK/Projetos/pessoal/gerador-hu
git add publicar-backlog-demanda-azure-boards
git commit -m "feat: publica titulos com numeracao hierarquica"
```

---

### Task 5: A Demanda entra no destino

Mudança atômica: `demanda_id` passa a fazer parte da identidade do destino e, por consequência, do
hash do plano, da impressão de autorização, da frase de confirmação e do manifesto. Tudo que constrói
ou serializa `ConfiguracaoPublicacao` precisa acompanhar na mesma tarefa, ou a suíte não fecha.

**Files:**
- Modify: `src/.../modelos.py`
- Modify: `src/.../autorizacao.py`
- Modify: `src/.../manifesto.py`
- Modify: `src/.../configuracao.py`
- Modify: `src/.../cli.py`
- Test: `tests/test_manifesto.py`, `tests/test_autorizacao.py`, `tests/test_configuracao_projeto.py`

**Interfaces:**
- Consumes: nada das tarefas anteriores.
- Produces:
  - `Demanda(id: int, titulo: str, area_path: str, iteration_path: str, url: str)` — dataclass
    congelada em `modelos.py`, consumida pela Task 7 e pela Task 10.
  - `ConfiguracaoPublicacao(..., demanda_id: int)` — campo obrigatório, sem valor padrão.
  - `ConfiguracaoAzureDevOps(..., demanda_id: int, tipo_demanda: str = "Demanda de Negócio")`.
  - Argumentos de CLI `--demanda` e `--tipo-demanda`.

- [ ] **Step 1: Escrever os testes que falham**

Criar `tests/test_demanda_no_destino.py`:

```python
"""O ID da Demanda faz parte da identidade do destino publicado."""

import pytest

from publicar_backlog_demanda_azure_boards.autorizacao import imprimir_destino
from publicar_backlog_demanda_azure_boards.modelos import (
    ConfiguracaoPublicacao,
    Demanda,
    MapeamentoTipos,
)


def _destino(demanda_id: int) -> ConfiguracaoPublicacao:
    return ConfiguracaoPublicacao(
        organizacao="contoso",
        projeto="CESOP-DILIGENCIA",
        area_path="CESOP-DILIGENCIA\\Sustentacao",
        iteration_path="CESOP-DILIGENCIA\\Sprint 18",
        demanda_id=demanda_id,
        mapeamento_tipos=MapeamentoTipos(),
    )


def test_demanda_id_e_obrigatorio_no_destino() -> None:
    with pytest.raises(TypeError):
        ConfiguracaoPublicacao(  # type: ignore[call-arg]
            organizacao="contoso",
            projeto="CESOP-DILIGENCIA",
            area_path="CESOP-DILIGENCIA\\Sustentacao",
            iteration_path="CESOP-DILIGENCIA\\Sprint 18",
        )


def test_destinos_com_demandas_diferentes_tem_impressoes_diferentes() -> None:
    assert imprimir_destino(_destino(13959)) != imprimir_destino(_destino(13970))


def test_demanda_carrega_titulo_e_caminhos_para_derivar_o_destino() -> None:
    demanda = Demanda(
        id=13959,
        titulo="PADRONIZAÇÃO E ATUALIZAÇÃO DAS STACKS DA APLICAÇÃO",
        area_path="CESOP-DILIGENCIA\\Sustentacao",
        iteration_path="CESOP-DILIGENCIA\\Sprint 18",
        url="https://dev.azure.com/contoso/_apis/wit/workItems/13959",
    )
    assert demanda.id == 13959
    assert demanda.area_path.endswith("Sustentacao")
```

- [ ] **Step 2: Rodar e confirmar a falha**

```bash
cd /Volumes/DOCK/Projetos/pessoal/gerador-hu/publicar-backlog-demanda-azure-boards
uv run pytest tests/test_demanda_no_destino.py -v
```

Esperado: FAIL com `ImportError: cannot import name 'Demanda'`.

- [ ] **Step 3: Acrescentar `Demanda` e `demanda_id` em `modelos.py`**

```python
@dataclass(frozen=True)
class Demanda:
    """Demanda de Negócio lida do Azure Boards, usada para derivar e exibir o destino.

    ``titulo`` e ``url`` existem apenas para apresentação no plano. Eles ficam de fora de
    hash, impressão de destino e manifesto de propósito: uma edição cosmética do título no
    Azure Boards invalidaria um manifesto válido e bloquearia uma retomada legítima.
    """

    id: int
    titulo: str
    area_path: str
    iteration_path: str
    url: str
```

Em `ConfiguracaoPublicacao`, acrescentar `demanda_id: int` **antes** de `mapeamento_tipos`, para que
continue sendo o único campo com valor padrão:

```python
@dataclass(frozen=True)
class ConfiguracaoPublicacao:
    """Representa o destino já validado para uma publicação vinculada a uma Demanda."""

    organizacao: str
    projeto: str
    area_path: str
    iteration_path: str
    demanda_id: int
    mapeamento_tipos: MapeamentoTipos = field(default_factory=MapeamentoTipos)
```

Em `assinatura_plano`, acrescentar a chave ao dicionário `configuracao`:

```python
        "configuracao": {
            "organizacao": configuracao.organizacao,
            "projeto": configuracao.projeto,
            "area_path": configuracao.area_path,
            "iteration_path": configuracao.iteration_path,
            "demanda_id": configuracao.demanda_id,
            "mapeamento_tipos": configuracao.mapeamento_tipos.como_dict(),
        },
```

- [ ] **Step 4: Incluir `demanda_id` no hash do plano**

Em `planejar_publicacao.py`, dentro de `_calcular_hash`, acrescentar a mesma chave ao dicionário
`configuracao`. Sem isso, o hash não distinguiria duas Demandas, que é exatamente o risco que esta
tarefa fecha.

```python
        "configuracao": {
            "organizacao": configuracao.organizacao,
            "projeto": configuracao.projeto,
            "area_path": configuracao.area_path,
            "iteration_path": configuracao.iteration_path,
            "demanda_id": configuracao.demanda_id,
            "mapeamento_tipos": configuracao.mapeamento_tipos.como_dict(),
        },
```

- [ ] **Step 5: Incluir `demanda_id` na impressão e na frase, em `autorizacao.py`**

```python
def imprimir_destino(configuracao: ConfiguracaoPublicacao) -> str:
    """Resume criptograficamente todos os campos que identificam o destino remoto."""
    conteudo = {
        "organizacao": configuracao.organizacao,
        "projeto": configuracao.projeto,
        "area_path": configuracao.area_path,
        "iteration_path": configuracao.iteration_path,
        "demanda_id": configuracao.demanda_id,
        "mapeamento_tipos": configuracao.mapeamento_tipos.como_dict(),
    }
    return _resumir(conteudo)
```

```python
def criar_frase_confirmacao(
    plano: PlanoPublicacao,
    chaves_autorizadas: Collection[str],
    numero_lote: int | None = None,
) -> str:
    """Gera a frase que vincula quantidade, Demanda, destino e código do plano completo."""
    configuracao = plano.configuracao
    inicio = "AUTORIZAR PUBLICAÇÃO" if numero_lote is None else f"AUTORIZAR LOTE {numero_lote}"
    return (
        f"{inicio} {len(chaves_autorizadas)} ITENS "
        f"DEMANDA {configuracao.demanda_id} {configuracao.projeto} "
        f"{configuracao.area_path} {configuracao.iteration_path} "
        f"{plano.hash_plano[:4].upper()}"
    )
```

- [ ] **Step 6: Persistir `demanda_id` no manifesto**

Em `manifesto.py`, `_serializar_configuracao`:

```python
def _serializar_configuracao(configuracao: ConfiguracaoPublicacao) -> dict[str, object]:
    return {
        "organizacao": configuracao.organizacao,
        "projeto": configuracao.projeto,
        "area_path": configuracao.area_path,
        "iteration_path": configuracao.iteration_path,
        "demanda_id": configuracao.demanda_id,
        "mapeamento_tipos": configuracao.mapeamento_tipos.como_dict(),
    }
```

E em `_configuracao`, exigir o campo em vez de assumir um padrão — um manifesto sem Demanda é um
manifesto de outro formato, e aceitar zero silenciosamente liberaria escrita sob a Demanda errada:

```python
def _configuracao(destino: dict[str, object]) -> ConfiguracaoPublicacao:
    campos = ("organizacao", "projeto", "area_path", "iteration_path")
    valores = [destino.get(campo) for campo in campos]
    if not all(isinstance(valor, str) and valor for valor in valores):
        raise ValueError("O destino do manifesto é inválido.")
    demanda_id = destino.get("demanda_id")
    if not isinstance(demanda_id, int) or isinstance(demanda_id, bool) or demanda_id <= 0:
        raise ValueError("O destino do manifesto não identifica a Demanda de Negócio.")
    mapeamento_dados = destino.get("mapeamento_tipos", {})
    if not isinstance(mapeamento_dados, dict):
        raise ValueError("O mapeamento de tipos do manifesto é inválido.")
    mapeamento = MapeamentoTipos(
        epic=_tipo_remoto(mapeamento_dados, "Epic", "Epic"),
        feature=_tipo_remoto(mapeamento_dados, "Feature", "Feature"),
        historia_usuario=_tipo_remoto(mapeamento_dados, "User Story", "User Story"),
        bug=_tipo_remoto(mapeamento_dados, "Bug", "Bug"),
    )
    organizacao, projeto, area_path, iteration_path = (cast(str, valor) for valor in valores)
    return ConfiguracaoPublicacao(
        organizacao=organizacao,
        projeto=projeto,
        area_path=area_path,
        iteration_path=iteration_path,
        demanda_id=demanda_id,
        mapeamento_tipos=mapeamento,
    )
```

- [ ] **Step 7: Carregar o ID pela configuração**

Em `configuracao.py`, acrescentar os campos a `ConfiguracaoAzureDevOps`:

```python
    demanda_id: int
    tipo_demanda: str = "Demanda de Negócio"
```

```python
    @field_validator("demanda_id")
    @classmethod
    def validar_demanda(cls, valor: int) -> int:
        """Rejeita um identificador de Demanda que não possa endereçar um work item."""
        if valor <= 0:
            raise ValueError("deve ser um inteiro positivo")
        return valor
```

Acrescentar `"tipo_demanda"` à lista do `field_validator` de texto obrigatório, incluir
`demanda_id` na construção de `ConfiguracaoPublicacao` dentro da property `publicacao`, e registrar
as chaves:

```python
_CHAVES = {
    ...
    "demanda_id": "AZURE_DEVOPS_DEMANDA",
    "tipo_demanda": "AZURE_DEVOPS_TIPO_DEMANDA",
}
```

Em `carregar_configuracao`, acrescentar `"demanda_id"` e `"tipo_demanda"` à tupla `campos`, aplicar o
padrão `"Demanda de Negócio"` a `tipo_demanda` junto dos demais tipos, e converter o ID:

```python
    bruto = valores["demanda_id"]
    if bruto is None:
        bruto = _perguntar("demanda_id", entrada_interativa, saida_interativa)
    try:
        demanda_id = int(str(bruto).strip().lstrip("#"))
    except ValueError as erro:
        raise ErroConfiguracao(
            "O ID da Demanda de Negócio deve ser um número inteiro."
        ) from erro
```

Acrescentar o rótulo ao dicionário de `_perguntar`:

```python
        "demanda_id": "ID da Demanda de Negócio",
```

E passar os dois campos na construção final, junto dos que já existem:

```python
        return ConfiguracaoAzureDevOps(
            organizacao=_exigir_valor(valores["organizacao"], "Organização do Azure DevOps"),
            projeto=_exigir_valor(valores["projeto"], "Projeto do Azure DevOps"),
            area_path=_exigir_valor(valores["area_path"], "Area Path"),
            iteration_path=_exigir_valor(valores["iteration_path"], "Iteration Path"),
            demanda_id=demanda_id,
            tipo_demanda=_exigir_valor(valores["tipo_demanda"], "Tipo remoto da Demanda"),
            token=(...),  # inalterado
            tipo_epic=_exigir_valor(valores["tipo_epic"], "Tipo remoto de Epic"),
            tipo_feature=_exigir_valor(valores["tipo_feature"], "Tipo remoto de Feature"),
            tipo_user_story=_exigir_valor(valores["tipo_user_story"], "Tipo remoto de User Story"),
            tipo_bug=_exigir_valor(valores["tipo_bug"], "Tipo remoto de Bug"),
        )
```

`area_path` e `iteration_path` continuam aqui nesta tarefa; a Task 10 é que os remove.

- [ ] **Step 8: Expor `--demanda` e `--tipo-demanda` na CLI**

Em `cli.py`, dentro de `_adicionar_opcoes_configuracao`:

```python
    parser.add_argument("--demanda", dest="demanda_id")
    parser.add_argument("--tipo-demanda")
```

E acrescentar `"demanda_id"` e `"tipo_demanda"` à tupla `nomes` de `_carregar_configuracao`.

- [ ] **Step 9: Corrigir a suíte herdada**

```bash
cd /Volumes/DOCK/Projetos/pessoal/gerador-hu/publicar-backlog-demanda-azure-boards
uv run pytest
```

Toda construção de `ConfiguracaoPublicacao` nos testes passa a exigir `demanda_id=13959` (ou outro
inteiro positivo). Toda afirmação sobre a frase de confirmação passa a incluir `DEMANDA <id>`. Todo
manifesto de fixture ganha `"demanda_id"` no objeto `destino`. Corrigir uma a uma até a suíte fechar.

- [ ] **Step 10: Commit**

```bash
cd /Volumes/DOCK/Projetos/pessoal/gerador-hu
git add publicar-backlog-demanda-azure-boards
git commit -m "feat: vincula o destino da publicacao a uma Demanda de Negocio"
```

---

### Task 6: Provar que a autorização não atravessa Demandas

Tarefa de teste. Ela existe porque é a garantia central do desenho: uma confirmação emitida para uma
Demanda não pode publicar sob outra.

**Files:**
- Create: `publicar-backlog-demanda-azure-boards/tests/test_autorizacao_vinculada_a_demanda.py`

**Interfaces:**
- Consumes: `ConfiguracaoPublicacao.demanda_id`, `criar_plano`, `criar_autorizacao`,
  `criar_frase_confirmacao`, `validar_manifesto`, `Manifesto` — todos da Task 5.
- Produces: nada consumido por tarefas seguintes.

- [ ] **Step 1: Escrever os testes**

```python
"""A autorização e o manifesto ficam presos à Demanda para a qual foram emitidos."""

import pytest

from publicar_backlog_demanda_azure_boards.autorizacao import (
    ModalidadeAutorizacao,
    criar_autorizacao,
    criar_frase_confirmacao,
)
from publicar_backlog_demanda_azure_boards.manifesto import Manifesto, validar_manifesto
from publicar_backlog_demanda_azure_boards.modelos import (
    ConfiguracaoPublicacao,
    ItemBacklog,
    MapeamentoTipos,
    RegistroManifesto,
    TipoItem,
)
from publicar_backlog_demanda_azure_boards.planejar_publicacao import criar_plano

_ITENS = [
    ItemBacklog(
        chave="1.0.0",
        tipo=TipoItem.EPIC,
        titulo="Gestão do projeto",
        pai=None,
        descricao="Contexto.",
        criterios_aceitacao="",
    )
]


def _destino(demanda_id: int) -> ConfiguracaoPublicacao:
    return ConfiguracaoPublicacao(
        organizacao="contoso",
        projeto="CESOP-DILIGENCIA",
        area_path="CESOP-DILIGENCIA\\Sustentacao",
        iteration_path="CESOP-DILIGENCIA\\Sprint 18",
        demanda_id=demanda_id,
        mapeamento_tipos=MapeamentoTipos(),
    )


def _plano(demanda_id: int):
    return criar_plano(_ITENS, _destino(demanda_id), "2026-09-22")


def test_trocar_a_demanda_muda_o_hash_do_plano() -> None:
    assert _plano(13959).hash_plano != _plano(13970).hash_plano


def test_a_frase_nomeia_a_demanda() -> None:
    frase = criar_frase_confirmacao(_plano(13959), ("1.0.0",))
    assert "DEMANDA 13959" in frase


def test_frase_de_uma_demanda_nao_autoriza_outra() -> None:
    frase_original = criar_frase_confirmacao(_plano(13959), ("1.0.0",))
    with pytest.raises(PermissionError):
        criar_autorizacao(
            _plano(13970),
            frase_original,
            frozenset({"1.0.0"}),
            modalidade=ModalidadeAutorizacao.INTEIRA,
        )


def test_autorizacao_valida_nao_vale_para_outro_destino() -> None:
    plano = _plano(13959)
    autorizacao = criar_autorizacao(
        plano,
        criar_frase_confirmacao(plano, ("1.0.0",)),
        frozenset({"1.0.0"}),
        modalidade=ModalidadeAutorizacao.INTEIRA,
    )
    assert autorizacao.valida_para(plano, _destino(13959))
    assert not autorizacao.valida_para(plano, _destino(13970))


def test_manifesto_de_uma_demanda_nao_retoma_sob_outra() -> None:
    plano_original = _plano(13959)
    manifesto = Manifesto(
        hash_plano=plano_original.hash_plano,
        configuracao=_destino(13959),
        itens={"1.0.0": RegistroManifesto(id=13969, tipo=TipoItem.EPIC, url="https://exemplo")},
        titulos={"1.0.0": plano_original.operacoes[0].titulo},
    )
    with pytest.raises(ValueError):
        validar_manifesto(manifesto, _plano(13970), _destino(13970))
```

- [ ] **Step 2: Rodar e confirmar que passam**

```bash
cd /Volumes/DOCK/Projetos/pessoal/gerador-hu/publicar-backlog-demanda-azure-boards
uv run pytest tests/test_autorizacao_vinculada_a_demanda.py -v
```

Esperado: PASS nos cinco testes. Se algum falhar, a Task 5 deixou `demanda_id` fora de um dos pontos
de vinculação — hash, impressão de destino, frase ou manifesto. Corrigir lá, não aqui.

- [ ] **Step 3: Commit**

```bash
cd /Volumes/DOCK/Projetos/pessoal/gerador-hu
git add publicar-backlog-demanda-azure-boards/tests/test_autorizacao_vinculada_a_demanda.py
git commit -m "test: prova que a autorizacao nao atravessa Demandas"
```

---

### Task 7: Leitor da Demanda

**Files:**
- Create: `publicar-backlog-demanda-azure-boards/src/publicar_backlog_demanda_azure_boards/leitor_demanda.py`
- Test: `publicar-backlog-demanda-azure-boards/tests/test_leitor_demanda.py`

**Interfaces:**
- Consumes: `Demanda` da Task 5; as classes de erro de `cliente_azure_devops.py`.
- Produces:
  ```python
  def ler_demanda(
      organizacao: str,
      projeto: str,
      token: str,
      id_demanda: int,
      tipo_esperado: str,
      *,
      transport: httpx.BaseTransport | None = None,
      timeout: float = 10.0,
  ) -> Demanda: ...
  ```
  Consumida pela Task 10.

- [ ] **Step 1: Escrever os testes que falham**

```python
"""Leitura somente leitura da Demanda de Negócio que ancora a publicação."""

import httpx
import pytest

from publicar_backlog_demanda_azure_boards.cliente_azure_devops import ErroDestinoInvalido
from publicar_backlog_demanda_azure_boards.leitor_demanda import ler_demanda

_URL = "https://dev.azure.com/contoso/CESOP-DILIGENCIA/_apis/wit/workItems/13959"


def _payload(**sobrescritas: object) -> dict[str, object]:
    campos: dict[str, object] = {
        "System.WorkItemType": "Demanda de Negócio",
        "System.TeamProject": "CESOP-DILIGENCIA",
        "System.Title": "PADRONIZAÇÃO E ATUALIZAÇÃO DAS STACKS DA APLICAÇÃO",
        "System.AreaPath": "CESOP-DILIGENCIA\\Sustentacao",
        "System.IterationPath": "CESOP-DILIGENCIA\\Sprint 18",
    }
    campos.update(sobrescritas)
    return {"id": 13959, "url": _URL, "fields": campos}


def _transporte(payload: object, status: int = 200) -> httpx.MockTransport:
    def responder(requisicao: httpx.Request) -> httpx.Response:
        assert requisicao.method == "GET"
        return httpx.Response(status, json=payload)

    return httpx.MockTransport(responder)


def _ler(payload: object, status: int = 200, tipo: str = "Demanda de Negócio"):
    return ler_demanda(
        "contoso",
        "CESOP-DILIGENCIA",
        "token-de-teste",
        13959,
        tipo,
        transport=_transporte(payload, status),
    )


def test_le_a_demanda_e_extrai_titulo_e_caminhos() -> None:
    demanda = _ler(_payload())
    assert demanda.id == 13959
    assert demanda.titulo == "PADRONIZAÇÃO E ATUALIZAÇÃO DAS STACKS DA APLICAÇÃO"
    assert demanda.area_path == "CESOP-DILIGENCIA\\Sustentacao"
    assert demanda.iteration_path == "CESOP-DILIGENCIA\\Sprint 18"
    assert demanda.url == _URL


def test_recusa_work_item_de_outro_tipo() -> None:
    with pytest.raises(ErroDestinoInvalido) as erro:
        _ler(_payload(**{"System.WorkItemType": "Epic"}))
    assert "Epic" in str(erro.value)
    assert "Demanda de Negócio" in str(erro.value)


def test_recusa_demanda_de_outro_projeto() -> None:
    with pytest.raises(ErroDestinoInvalido) as erro:
        _ler(_payload(**{"System.TeamProject": "OUTRO-PROJETO"}))
    assert "OUTRO-PROJETO" in str(erro.value)


@pytest.mark.parametrize("campo", ["System.AreaPath", "System.IterationPath", "System.Title"])
def test_recusa_demanda_sem_campo_necessario(campo: str) -> None:
    with pytest.raises(ErroDestinoInvalido) as erro:
        _ler(_payload(**{campo: ""}))
    assert campo in str(erro.value)


def test_recusa_work_item_inexistente() -> None:
    with pytest.raises(ErroDestinoInvalido) as erro:
        _ler({"message": "não encontrado"}, status=404)
    assert "13959" in str(erro.value)


def test_recusa_identificador_nao_positivo() -> None:
    with pytest.raises(ErroDestinoInvalido):
        ler_demanda(
            "contoso",
            "CESOP-DILIGENCIA",
            "token-de-teste",
            0,
            "Demanda de Negócio",
            transport=_transporte(_payload()),
        )


def test_nao_expoe_o_token_na_mensagem_de_erro() -> None:
    with pytest.raises(ErroDestinoInvalido) as erro:
        _ler({"message": "não encontrado"}, status=404)
    assert "token-de-teste" not in str(erro.value)
```

- [ ] **Step 2: Rodar e confirmar a falha**

```bash
cd /Volumes/DOCK/Projetos/pessoal/gerador-hu/publicar-backlog-demanda-azure-boards
uv run pytest tests/test_leitor_demanda.py -v
```

Esperado: FAIL com `ModuleNotFoundError: No module named
'publicar_backlog_demanda_azure_boards.leitor_demanda'`.

- [ ] **Step 3: Implementar o leitor**

```python
"""Lê a Demanda de Negócio que ancora a publicação, sem qualquer escrita.

Este módulo não usa ``ClienteAzureDevOps`` de propósito: o cliente é construído com uma
``ConfiguracaoPublicacao`` já completa, e os caminhos dessa configuração são justamente o
que a Demanda fornece. A leitura precisa acontecer antes de o destino existir.
"""

from __future__ import annotations

import base64
from typing import Any

import httpx

from publicar_backlog_demanda_azure_boards.cliente_azure_devops import (
    ErroDestinoInvalido,
    _verificar_status,
)
from publicar_backlog_demanda_azure_boards.modelos import Demanda

_VERSAO_API = "7.2-preview.3"
_CAMPOS_TEXTO = ("System.Title", "System.AreaPath", "System.IterationPath")


def ler_demanda(
    organizacao: str,
    projeto: str,
    token: str,
    id_demanda: int,
    tipo_esperado: str,
    *,
    transport: httpx.BaseTransport | None = None,
    timeout: float = 10.0,
) -> Demanda:
    """Busca a Demanda por `GET` e valida tipo, projeto e campos antes de derivar o destino."""
    if id_demanda <= 0:
        raise ErroDestinoInvalido(
            "O ID da Demanda de Negócio deve ser um inteiro positivo."
        )
    credencial = base64.b64encode(f":{token}".encode()).decode()
    url = (
        f"https://dev.azure.com/{organizacao}/{projeto}"
        f"/_apis/wit/workitems/{id_demanda}?$expand=Fields&api-version={_VERSAO_API}"
    )
    with httpx.Client(
        headers={"Authorization": f"Basic {credencial}"},
        timeout=httpx.Timeout(timeout),
        transport=transport,
    ) as cliente:
        resposta = cliente.get(url)
    try:
        _verificar_status(resposta)
    except Exception as erro:
        raise ErroDestinoInvalido(
            f"Não foi possível ler a Demanda de Negócio {id_demanda}."
        ) from erro

    payload = _objeto(resposta.json(), f"A resposta da Demanda {id_demanda} é inválida.")
    campos = _objeto(
        payload.get("fields"), f"A Demanda {id_demanda} não devolveu seus campos."
    )

    tipo = campos.get("System.WorkItemType")
    if tipo != tipo_esperado:
        raise ErroDestinoInvalido(
            f"O work item {id_demanda} é do tipo {tipo!r}; "
            f"esta skill publica apenas sob {tipo_esperado!r}."
        )

    team_project = campos.get("System.TeamProject")
    if team_project != projeto:
        raise ErroDestinoInvalido(
            f"A Demanda {id_demanda} pertence ao projeto {team_project!r}, "
            f"e não a {projeto!r}; o vínculo hierárquico não cruza projeto."
        )

    for campo in _CAMPOS_TEXTO:
        valor = campos.get(campo)
        if not isinstance(valor, str) or not valor.strip():
            raise ErroDestinoInvalido(
                f"A Demanda {id_demanda} não possui {campo}; não há de onde herdar o destino."
            )

    url_item = payload.get("url")
    if not isinstance(url_item, str) or not url_item.startswith("https://"):
        raise ErroDestinoInvalido(f"A Demanda {id_demanda} não devolveu uma URL utilizável.")

    return Demanda(
        id=id_demanda,
        titulo=str(campos["System.Title"]).strip(),
        area_path=str(campos["System.AreaPath"]).strip(),
        iteration_path=str(campos["System.IterationPath"]).strip(),
        url=url_item,
    )


def _objeto(valor: object, mensagem: str) -> dict[str, Any]:
    if not isinstance(valor, dict):
        raise ErroDestinoInvalido(mensagem)
    return valor
```

Se `_verificar_status` estiver privado a ponto de o `ruff` reclamar da importação, promover a função
a pública em `cliente_azure_devops.py` renomeando para `verificar_status` e atualizar as chamadas
internas. Não duplicar a lógica de status em dois módulos.

- [ ] **Step 4: Rodar e confirmar que passa**

```bash
cd /Volumes/DOCK/Projetos/pessoal/gerador-hu/publicar-backlog-demanda-azure-boards
uv run pytest tests/test_leitor_demanda.py -v
```

Esperado: PASS nos nove casos.

- [ ] **Step 5: Commit**

```bash
cd /Volumes/DOCK/Projetos/pessoal/gerador-hu
git add publicar-backlog-demanda-azure-boards
git commit -m "feat: le a Demanda de Negocio para derivar o destino"
```

---

### Task 8: A validação remota exercita o vínculo com a Demanda

Hoje `validar_operacao` valida sempre com pai nulo. O risco novo desta skill é justamente o processo
remoto aceitar (ou não) Épico como filho de Demanda de Negócio, e `--validar-apenas` precisa cobrir
isso antes de qualquer escrita.

**Files:**
- Modify: `src/.../cliente_azure_devops.py`
- Modify: `src/.../cli.py` (função `_verificar_preliminar`)
- Test: `tests/test_cliente_azure_devops.py`

**Interfaces:**
- Consumes: `ConfiguracaoPublicacao.demanda_id` da Task 5.
- Produces: `ClienteAzureDevOps.validar_operacao(operacao, id_pai: int | None = None) -> None` — a
  assinatura muda, e o `Protocol` `ClientePublicacao` em `cli.py` acompanha.

- [ ] **Step 1: Escrever os testes que falham**

Acrescentar a `tests/test_cliente_azure_devops.py`:

```python
def test_validar_operacao_envia_a_relacao_quando_ha_pai() -> None:
    capturado: list[list[dict[str, object]]] = []

    def responder(requisicao: httpx.Request) -> httpx.Response:
        assert "validateOnly=true" in str(requisicao.url)
        capturado.append(json.loads(requisicao.content))
        return httpx.Response(200, json={"id": 1, "url": "https://dev.azure.com/x/_apis/wit/workItems/1"})

    cliente = ClienteAzureDevOps(
        _configuracao_exemplo(),
        "token-de-teste",
        transport=httpx.MockTransport(responder),
    )
    cliente.validar_operacao(_operacao_epico(), id_pai=13959)

    relacoes = [op for op in capturado[0] if op["path"] == "/relations/-"]
    assert len(relacoes) == 1
    assert relacoes[0]["value"]["rel"] == "System.LinkTypes.Hierarchy-Reverse"
    assert str(relacoes[0]["value"]["url"]).endswith("/13959")


def test_validar_operacao_sem_pai_nao_envia_relacao() -> None:
    capturado: list[list[dict[str, object]]] = []

    def responder(requisicao: httpx.Request) -> httpx.Response:
        capturado.append(json.loads(requisicao.content))
        return httpx.Response(200, json={"id": 1, "url": "https://dev.azure.com/x/_apis/wit/workItems/1"})

    cliente = ClienteAzureDevOps(
        _configuracao_exemplo(),
        "token-de-teste",
        transport=httpx.MockTransport(responder),
    )
    cliente.validar_operacao(_operacao_epico())

    assert not [op for op in capturado[0] if op["path"] == "/relations/-"]
```

Reutilizar os auxiliares que o arquivo já tiver para construir configuração e operação; se não
houver, criar `_configuracao_exemplo()` devolvendo uma `ConfiguracaoPublicacao` com
`demanda_id=13959` e `_operacao_epico()` devolvendo uma `OperacaoCriacao` de `TipoItem.EPIC` com
`chave_pai=None`.

- [ ] **Step 2: Rodar e confirmar a falha**

```bash
cd /Volumes/DOCK/Projetos/pessoal/gerador-hu/publicar-backlog-demanda-azure-boards
uv run pytest tests/test_cliente_azure_devops.py -k validar_operacao -v
```

Esperado: FAIL com `TypeError: validar_operacao() got an unexpected keyword argument 'id_pai'`.

- [ ] **Step 3: Repassar o pai na validação**

```python
    def validar_operacao(self, operacao: OperacaoCriacao, id_pai: int | None = None) -> None:
        """Valida o JSON Patch no endpoint de criação, sem persistir o item.

        O ``id_pai`` é enviado para que a validação exercite também a relação hierárquica:
        é nela que mora o risco novo de o processo remoto recusar o Épico como filho da
        Demanda de Negócio.
        """
        self._enviar_criacao(operacao, validar=True, id_pai=id_pai)
```

- [ ] **Step 4: Ajustar a verificação preliminar da CLI**

```python
def _verificar_preliminar(
    cliente: ClientePublicacao,
    configuracao: ConfiguracaoPublicacao,
    operacoes: Sequence[OperacaoCriacao],
) -> None:
    cliente.verificar_destino(configuracao)
    for operacao in operacoes:
        id_pai = configuracao.demanda_id if operacao.chave_pai is None else None
        cliente.validar_operacao(operacao, id_pai=id_pai)
```

Um item sem `chave_pai` é sempre um Épico, cujo pai é a Demanda e já existe no Azure Boards. Features
e Histórias seguem validando sem pai, porque os seus ainda não foram criados.

Atualizar o `Protocol` no mesmo arquivo:

```python
    def validar_operacao(self, operacao: OperacaoCriacao, id_pai: int | None = None) -> None: ...
```

- [ ] **Step 4b: Provar que a verificação preliminar escolhe o pai certo**

Acrescentar a `tests/test_skill_integration.py`:

```python
def test_verificacao_preliminar_valida_epicos_contra_a_demanda() -> None:
    destino = ConfiguracaoPublicacao(
        organizacao="contoso",
        projeto="CESOP-DILIGENCIA",
        area_path="CESOP-DILIGENCIA\\Sustentacao",
        iteration_path="CESOP-DILIGENCIA\\Sprint 18",
        demanda_id=13959,
        mapeamento_tipos=MapeamentoTipos(),
    )
    plano = criar_plano(
        [
            ItemBacklog("1.0.0", TipoItem.EPIC, "Gestão", None, "d", ""),
            ItemBacklog("1.1.0", TipoItem.FEATURE, "Gestão", "1.0.0", "d", ""),
        ],
        destino,
        "2026-09-22",
    )

    validadas: list[tuple[str, int | None]] = []

    class _Cliente:
        configuracao = destino

        def verificar_destino(self, configuracao: ConfiguracaoPublicacao) -> object:
            return None

        def validar_operacao(
            self, operacao: OperacaoCriacao, id_pai: int | None = None
        ) -> None:
            validadas.append((operacao.chave, id_pai))

        def criar_item(
            self, operacao: OperacaoCriacao, id_pai: int | None = None
        ) -> object:  # pragma: no cover - não usado nesta verificação
            raise AssertionError("A verificação preliminar não pode criar itens.")

    _verificar_preliminar(_Cliente(), destino, plano.operacoes)

    assert dict(validadas) == {"1.0.0": 13959, "1.1.0": None}
```

Este é o teste que realiza o critério 3 da spec: `--validar-apenas` precisa exercitar o vínculo novo,
e não um Épico órfão.

- [ ] **Step 5: Rodar a suíte inteira**

```bash
cd /Volumes/DOCK/Projetos/pessoal/gerador-hu/publicar-backlog-demanda-azure-boards
uv run pytest
```

Esperado: PASS. Clientes falsos nos testes que definem `validar_operacao` sem `id_pai` precisam
receber o parâmetro novo.

- [ ] **Step 6: Commit**

```bash
cd /Volumes/DOCK/Projetos/pessoal/gerador-hu
git add publicar-backlog-demanda-azure-boards
git commit -m "feat: valida a relacao com a Demanda antes de qualquer escrita"
```

---

### Task 9: Os Épicos sobem como filhos da Demanda

**Files:**
- Modify: `src/.../executar_publicacao.py`
- Test: `publicar-backlog-demanda-azure-boards/tests/test_vinculo_demanda.py`

**Interfaces:**
- Consumes: `ConfiguracaoPublicacao.demanda_id` (Task 5); `executar_plano` inalterado na assinatura.
- Produces: nenhuma API nova.

- [ ] **Step 1: Escrever os testes que falham**

```python
"""Todo Épico publicado nasce filho da Demanda de Negócio informada."""

from dataclasses import dataclass
from pathlib import Path

from publicar_backlog_demanda_azure_boards.autorizacao import (
    ModalidadeAutorizacao,
    criar_autorizacao,
    criar_frase_confirmacao,
)
from publicar_backlog_demanda_azure_boards.executar_publicacao import executar_plano
from publicar_backlog_demanda_azure_boards.modelos import (
    ConfiguracaoPublicacao,
    ItemBacklog,
    MapeamentoTipos,
    OperacaoCriacao,
    TipoItem,
)
from publicar_backlog_demanda_azure_boards.planejar_publicacao import criar_plano

_DEMANDA = 13959


def _destino() -> ConfiguracaoPublicacao:
    return ConfiguracaoPublicacao(
        organizacao="contoso",
        projeto="CESOP-DILIGENCIA",
        area_path="CESOP-DILIGENCIA\\Sustentacao",
        iteration_path="CESOP-DILIGENCIA\\Sprint 18",
        demanda_id=_DEMANDA,
        mapeamento_tipos=MapeamentoTipos(),
    )


_ITENS = [
    ItemBacklog("1.0.0", TipoItem.EPIC, "Gestão do projeto", None, "d", ""),
    ItemBacklog("1.1.0", TipoItem.FEATURE, "Gestão do projeto", "1.0.0", "d", ""),
    ItemBacklog("1.1.1", TipoItem.HISTORIA_USUARIO, "Análise de stacks", "1.1.0", "d", ""),
    ItemBacklog("2.0.0", TipoItem.EPIC, "Padronização", None, "d", ""),
]


@dataclass
class _Criado:
    id: int
    url: str


class _ClienteFalso:
    def __init__(self, configuracao: ConfiguracaoPublicacao) -> None:
        self.configuracao = configuracao
        self.chamadas: list[tuple[str, int | None]] = []
        self._proximo = 13969

    def criar_item(self, operacao: OperacaoCriacao, id_pai: int | None = None) -> _Criado:
        self.chamadas.append((operacao.chave, id_pai))
        criado = _Criado(self._proximo, f"https://dev.azure.com/x/_apis/wit/workItems/{self._proximo}")
        self._proximo += 1
        return criado


def _publicar(tmp_path: Path) -> _ClienteFalso:
    destino = _destino()
    plano = criar_plano(_ITENS, destino, "2026-09-22")
    chaves = frozenset(operacao.chave for operacao in plano.operacoes)
    autorizacao = criar_autorizacao(
        plano,
        criar_frase_confirmacao(plano, chaves),
        chaves,
        modalidade=ModalidadeAutorizacao.INTEIRA,
    )
    cliente = _ClienteFalso(destino)
    executar_plano(plano, autorizacao, cliente, tmp_path / "manifesto.json")
    return cliente


def test_todo_epico_sobe_com_a_demanda_como_pai(tmp_path: Path) -> None:
    cliente = _publicar(tmp_path)
    pais = dict(cliente.chamadas)
    assert pais["1.0.0"] == _DEMANDA
    assert pais["2.0.0"] == _DEMANDA


def test_feature_e_historia_mantem_os_pais_do_backlog(tmp_path: Path) -> None:
    cliente = _publicar(tmp_path)
    pais = dict(cliente.chamadas)
    assert pais["1.1.0"] == 13969
    assert pais["1.1.1"] not in (None, _DEMANDA)


def test_nenhum_item_sobe_sem_pai(tmp_path: Path) -> None:
    cliente = _publicar(tmp_path)
    assert all(id_pai is not None for _, id_pai in cliente.chamadas)
```

- [ ] **Step 2: Rodar e confirmar a falha**

```bash
cd /Volumes/DOCK/Projetos/pessoal/gerador-hu/publicar-backlog-demanda-azure-boards
uv run pytest tests/test_vinculo_demanda.py -v
```

Esperado: FAIL, porque os Épicos hoje sobem com `id_pai=None`.

- [ ] **Step 3: Pendurar os Épicos na Demanda**

Em `executar_publicacao.py`, dentro do laço de `executar_plano`, substituir a resolução do pai:

```python
        id_pai = (
            registros[operacao.chave_pai].id
            if operacao.chave_pai is not None
            else cliente.configuracao.demanda_id
        )
```

Um item sem pai documental é um Épico, e o pai dele é a Demanda. Não existe mais item publicado sem
pai.

- [ ] **Step 4: Rodar e confirmar que passa**

```bash
cd /Volumes/DOCK/Projetos/pessoal/gerador-hu/publicar-backlog-demanda-azure-boards
uv run pytest tests/test_vinculo_demanda.py -v && uv run pytest
```

Esperado: PASS nos três testes novos e na suíte inteira.

- [ ] **Step 5: Commit**

```bash
cd /Volumes/DOCK/Projetos/pessoal/gerador-hu
git add publicar-backlog-demanda-azure-boards
git commit -m "feat: pendura os Epicos publicados na Demanda de Negocio"
```

---

### Task 10: O destino é herdado da Demanda

Retirar `Area Path` e `Iteration Path` da configuração manual e derivá-los da Demanda lida. Muda junto
a semântica de `--simulacao`, que deixa de ser offline.

**Files:**
- Modify: `src/.../configuracao.py`
- Modify: `src/.../cli.py`
- Modify: `.env.example`
- Test: `tests/test_configuracao_projeto.py`, `tests/test_skill_integration.py`

**Interfaces:**
- Consumes: `ler_demanda(...)` (Task 7); `Demanda` (Task 5).
- Produces:
  - `ConfiguracaoAzureDevOps.publicacao_para(demanda: Demanda) -> ConfiguracaoPublicacao`
    substitui a property `publicacao`.
  - `ConfiguracaoAzureDevOps` deixa de ter `area_path` e `iteration_path`.

- [ ] **Step 1: Escrever os testes que falham**

Acrescentar a `tests/test_configuracao_projeto.py`:

```python
def test_destino_herda_os_caminhos_da_demanda() -> None:
    configuracao = carregar_configuracao(
        argumentos={"organizacao": "contoso", "projeto": "CESOP-DILIGENCIA", "demanda_id": "13959"},
        caminho_env=Path("arquivo-inexistente.env"),
        ambiente={},
        exigir_token=False,
    )
    demanda = Demanda(
        id=13959,
        titulo="PADRONIZAÇÃO",
        area_path="CESOP-DILIGENCIA\\Sustentacao",
        iteration_path="CESOP-DILIGENCIA\\Sprint 18",
        url="https://dev.azure.com/contoso/_apis/wit/workItems/13959",
    )
    destino = configuracao.publicacao_para(demanda)
    assert destino.area_path == "CESOP-DILIGENCIA\\Sustentacao"
    assert destino.iteration_path == "CESOP-DILIGENCIA\\Sprint 18"
    assert destino.demanda_id == 13959


def test_configuracao_nao_aceita_mais_caminhos_manuais() -> None:
    assert "area_path" not in ConfiguracaoAzureDevOps.model_fields
    assert "iteration_path" not in ConfiguracaoAzureDevOps.model_fields


def test_a_cli_nao_oferece_mais_os_caminhos_manuais() -> None:
    ajuda = construir_parser().format_help()
    assert "--area-path" not in ajuda
    assert "--iteration-path" not in ajuda
    assert "--demanda" in ajuda
```

- [ ] **Step 2: Rodar e confirmar a falha**

```bash
cd /Volumes/DOCK/Projetos/pessoal/gerador-hu/publicar-backlog-demanda-azure-boards
uv run pytest tests/test_configuracao_projeto.py -v
```

Esperado: FAIL com `AttributeError: 'ConfiguracaoAzureDevOps' object has no attribute
'publicacao_para'`.

- [ ] **Step 3: Remover os caminhos manuais da configuração**

Em `configuracao.py`:

- apagar os campos `area_path` e `iteration_path` de `ConfiguracaoAzureDevOps` e retirá-los da lista
  do `field_validator`;
- apagar as chaves `"area_path"`, `"area_paths"` e `"iteration_path"` de `_CHAVES`;
- apagar a função `_obter_area_path` inteira e a sua chamada, junto do ramo de seleção entre múltiplos
  Area Paths;
- retirar `"iteration_path"` da tupla `campos` e do laço de perguntas obrigatórias;
- apagar os rótulos `"area_path"` e `"iteration_path"` de `_perguntar`;
- substituir a property `publicacao`:

```python
    def publicacao_para(self, demanda: Demanda) -> ConfiguracaoPublicacao:
        """Deriva o destino a partir da Demanda, que é a dona dos caminhos.

        `Area Path` e `Iteration Path` não são mais configuráveis por execução: publicar sob
        uma Demanda significa publicar onde ela está.
        """
        return ConfiguracaoPublicacao(
            organizacao=self.organizacao,
            projeto=self.projeto,
            area_path=_normalizar_caminho(self.projeto, demanda.area_path),
            iteration_path=_normalizar_caminho(self.projeto, demanda.iteration_path),
            demanda_id=self.demanda_id,
            mapeamento_tipos=MapeamentoTipos(
                epic=self.tipo_epic,
                feature=self.tipo_feature,
                historia_usuario=self.tipo_user_story,
                bug=self.tipo_bug,
            ),
        )
```

`_normalizar_caminho` permanece: ela garante o prefixo do projeto mesmo que o Azure devolva um caminho
já normalizado.

- [ ] **Step 4: Remover os argumentos da CLI e ler a Demanda**

Em `cli.py`, apagar `--area-path` e `--iteration-path` de `_adicionar_opcoes_configuracao` e retirar
`"area_path"` e `"iteration_path"` da tupla `nomes` de `_carregar_configuracao`.

Trocar a montagem do plano em `principal`:

```python
        configuracao = _carregar_configuracao(
            argumentos_parseados, cliente, entrada_real, saida_real
        )
        if cliente is not None:
            destino = cliente.configuracao
            demanda = None
        else:
            demanda = ler_demanda(
                configuracao.organizacao,
                configuracao.projeto,
                configuracao.obter_token(),
                configuracao.demanda_id,
                configuracao.tipo_demanda,
            )
            destino = configuracao.publicacao_para(demanda)
        plano = criar_plano(itens, destino, data_geracao)
```

O ramo `cliente is not None` cobre os testes e integrações que injetam um cliente com destino pronto;
ele não pode ler a Demanda porque não há token nesse fluxo.

`exige_token` em `_carregar_configuracao` passa a valer também para `planejar` e para a simulação,
porque os três precisam ler a Demanda:

```python
    exige_token = argumentos.comando in {"planejar", "publicar"} and cliente is None
```

Trocar a mensagem final da simulação, que hoje afirma algo que deixou de ser verdade:

```python
            _escrever(
                saida_real,
                "Simulação concluída: a Demanda foi lida; "
                "nenhuma autorização foi solicitada e nenhum item foi criado.\n",
            )
```

- [ ] **Step 4b: Provar que a simulação faz exatamente uma leitura e nenhuma escrita**

Acrescentar a `tests/test_skill_integration.py`:

```python
def test_simulacao_le_a_demanda_uma_vez_e_nao_escreve(tmp_path, monkeypatch) -> None:
    metodos: list[str] = []

    def responder(requisicao: httpx.Request) -> httpx.Response:
        metodos.append(requisicao.method)
        return httpx.Response(
            200,
            json={
                "id": 13959,
                "url": "https://dev.azure.com/contoso/_apis/wit/workItems/13959",
                "fields": {
                    "System.WorkItemType": "Demanda de Negócio",
                    "System.TeamProject": "CESOP-DILIGENCIA",
                    "System.Title": "PADRONIZAÇÃO",
                    "System.AreaPath": "CESOP-DILIGENCIA\\Sustentacao",
                    "System.IterationPath": "CESOP-DILIGENCIA\\Sprint 18",
                },
            },
        )

    transporte = httpx.MockTransport(responder)
    monkeypatch.setattr(
        "publicar_backlog_demanda_azure_boards.cli.ler_demanda",
        lambda *args, **kwargs: ler_demanda(*args, transport=transporte),
    )
    monkeypatch.setenv("AZURE_DEVOPS_ORGANIZACAO", "contoso")
    monkeypatch.setenv("AZURE_DEVOPS_PROJETO", "CESOP-DILIGENCIA")
    monkeypatch.setenv("AZURE_DEVOPS_DEMANDA", "13959")
    monkeypatch.setenv("AZURE_DEVOPS_TOKEN", "token-de-teste")

    codigo = principal(
        ["publicar", str(_backlog(tmp_path)), "--simulacao", "--env-file", "inexistente.env"],
        entrada=io.StringIO(""),
        saida=(saida := io.StringIO()),
    )

    assert codigo == 0
    assert metodos == ["GET"]
    assert "nenhuma autorização foi solicitada" in saida.getvalue()
```

Este é o teste que realiza o critério 2 da spec. Se `metodos` trouxer mais de uma entrada, a
simulação está lendo além do necessário; se trouxer um `POST`, está escrevendo.

- [ ] **Step 5: Atualizar o `.env.example`**

```dotenv
# Organização do Azure DevOps.
AZURE_DEVOPS_ORGANIZACAO=
# Projeto de destino no Azure DevOps.
AZURE_DEVOPS_PROJETO=
# ID da Demanda de Negócio que ancora o backlog; os Épicos sobem como filhos dela.
AZURE_DEVOPS_DEMANDA=
# Nome remoto do tipo da Demanda. Ajuste se o seu processo usar outro rótulo.
AZURE_DEVOPS_TIPO_DEMANDA=Demanda de Negócio
# Nome remoto do tipo documental User Story. Use Product Backlog Item em processos Scrum.
AZURE_DEVOPS_TIPO_USER_STORY=User Story
# Token pessoal; mantenha vazio neste arquivo e fora do controle de versão. A entrada interativa é sem eco.
AZURE_DEVOPS_TOKEN=
```

`AZURE_DEVOPS_AREA_PATH`, `AZURE_DEVOPS_AREA_PATHS` e `AZURE_DEVOPS_ITERATION_PATH` saem do arquivo:
os caminhos vêm da Demanda.

- [ ] **Step 6: Rodar a suíte inteira**

```bash
cd /Volumes/DOCK/Projetos/pessoal/gerador-hu/publicar-backlog-demanda-azure-boards
uv run pytest
```

Esperado: PASS. Testes herdados que passam `area_path`/`iteration_path` a `carregar_configuracao`
precisam parar de passar; testes que afirmam a seleção entre múltiplos Area Paths devem ser
**removidos**, porque o comportamento deixou de existir.

- [ ] **Step 7: Commit**

```bash
cd /Volumes/DOCK/Projetos/pessoal/gerador-hu
git add publicar-backlog-demanda-azure-boards
git commit -m "feat: herda Area Path e Iteration Path da Demanda"
```

---

### Task 11: O plano mostra a origem

**Files:**
- Modify: `src/.../cli.py` (`_apresentar_plano` e sua chamada)
- Test: `tests/test_skill_integration.py`

**Interfaces:**
- Consumes: `Demanda` (Task 5), o destino derivado (Task 10).
- Produces: `_apresentar_plano(plano, pendentes, total, registrados, caminho_manifesto, saida, demanda)`
  — um parâmetro a mais, `demanda: Demanda | None`.

- [ ] **Step 1: Escrever o teste que falha**

```python
def test_plano_apresenta_a_demanda_de_origem(capsys, backlog_exemplo, cliente_falso) -> None:
    codigo = principal(
        ["planejar", str(backlog_exemplo)],
        cliente=cliente_falso,
        entrada=io.StringIO(""),
        saida=(saida := io.StringIO()),
    )
    texto = saida.getvalue()
    assert codigo == 0
    assert "Demanda de Negócio: #13959" in texto
    assert "herdado da Demanda #13959" in texto
```

Ajustar as fixtures aos auxiliares já existentes no arquivo. O cliente falso precisa devolver uma
`ConfiguracaoPublicacao` com `demanda_id=13959`.

- [ ] **Step 2: Rodar e confirmar a falha**

```bash
cd /Volumes/DOCK/Projetos/pessoal/gerador-hu/publicar-backlog-demanda-azure-boards
uv run pytest tests/test_skill_integration.py -k demanda -v
```

Esperado: FAIL, porque o cabeçalho ainda não existe.

- [ ] **Step 3: Acrescentar o cabeçalho de origem**

```python
def _apresentar_plano(
    plano: PlanoPublicacao,
    pendentes: Sequence[OperacaoCriacao],
    total: int,
    registrados: int,
    caminho_manifesto: Path | None,
    saida: TextIO,
    demanda: Demanda | None = None,
) -> None:
    configuracao = plano.configuracao
    contagem = Counter(operacao.tipo_remoto for operacao in pendentes)
    _escrever(saida, "Plano de publicação\n")
    rotulo_demanda = f"#{configuracao.demanda_id}"
    if demanda is not None:
        rotulo_demanda = f"#{demanda.id} — {demanda.titulo}"
    _escrever(saida, f"Demanda de Negócio: {rotulo_demanda}\n")
    _escrever(saida, f"Organização: {configuracao.organizacao}\n")
    _escrever(saida, f"Projeto: {configuracao.projeto}\n")
    heranca = f" (herdado da Demanda #{configuracao.demanda_id})"
    _escrever(saida, f"Area Path: {configuracao.area_path}{heranca}\n")
    _escrever(saida, f"Iteration Path: {configuracao.iteration_path}{heranca}\n")
```

O restante da função permanece idêntico. Acrescentar também, logo depois de `Relações pai-filho`:

```python
    epicos = ", ".join(
        operacao.chave for operacao in pendentes if operacao.chave_pai is None
    )
    _escrever(
        saida,
        f"Épicos filhos da Demanda #{configuracao.demanda_id}: {epicos or 'nenhum'}\n",
    )
```

Acrescentar `Demanda` à importação de `modelos` no topo de `cli.py` — a Task 10 importou apenas
`ler_demanda`, e sem este import o parâmetro novo não tipa — e passar `demanda` na chamada dentro de
`principal`.

- [ ] **Step 4: Rodar a suíte inteira**

```bash
cd /Volumes/DOCK/Projetos/pessoal/gerador-hu/publicar-backlog-demanda-azure-boards
uv run pytest
```

Esperado: PASS.

- [ ] **Step 5: Commit**

```bash
cd /Volumes/DOCK/Projetos/pessoal/gerador-hu
git add publicar-backlog-demanda-azure-boards
git commit -m "feat: apresenta a Demanda de origem no plano de publicacao"
```

---

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

### Task 13: Fechamento e verificação

**Files:**
- Modify: `publicar-backlog-demanda-azure-boards/tests/test_integracao_final.py`

**Interfaces:**
- Consumes: tudo.
- Produces: nada.

- [ ] **Step 1: Escrever o teste de ponta a ponta**

Em `tests/test_integracao_final.py`, acrescentar um caso que percorre o caminho inteiro com transporte
falso: backlog com dois Épicos, leitura da Demanda, plano, frase, publicação e manifesto.

```python
def test_publicacao_completa_vincula_tudo_a_demanda(tmp_path) -> None:
    cliente = _ClienteFalso(_destino_com_demanda(13959))
    codigo = principal(
        ["publicar", str(_backlog(tmp_path)), "--manifesto", str(tmp_path / "m.json")],
        cliente=cliente,
        entrada=io.StringIO(f"1\n{_frase_esperada(tmp_path)}\n"),
        saida=(saida := io.StringIO()),
    )
    assert codigo == 0
    assert "DEMANDA 13959" in saida.getvalue()

    manifesto = json.loads((tmp_path / "m.json").read_text(encoding="utf-8"))
    assert manifesto["destino"]["demanda_id"] == 13959
    assert all(id_pai is not None for _, id_pai in cliente.chamadas)
    assert [id_pai for chave, id_pai in cliente.chamadas if chave.endswith(".0.0")] == [13959, 13959]
```

Reutilizar os auxiliares do arquivo para montar backlog, destino e frase; se `_frase_esperada` não
existir, derivá-la de `criar_frase_confirmacao` sobre o plano montado com os mesmos itens.

- [ ] **Step 2: Rodar a suíte inteira**

```bash
cd /Volumes/DOCK/Projetos/pessoal/gerador-hu/publicar-backlog-demanda-azure-boards
uv run pytest
```

Esperado: PASS em todos os arquivos, incluindo `test_sincronia_com_origem.py`.

- [ ] **Step 3: Rodar lint, tipos e SAST**

```bash
cd /Volumes/DOCK/Projetos/pessoal/gerador-hu/publicar-backlog-demanda-azure-boards
uv run ruff check .
uv run ruff format --check .
uv run mypy
uv run bandit -c pyproject.toml -r src
```

Esperado: zero achados. Corrigir o que aparecer; não silenciar com `# noqa` ou `# type: ignore` sem
justificativa escrita na mesma linha.

- [ ] **Step 4: Confirmar que a skill de origem não foi tocada**

```bash
cd /Volumes/DOCK/Projetos/pessoal/gerador-hu
git diff --stat main -- publicar-backlog-azure-boards
```

Esperado: saída vazia. Qualquer arquivo listado aqui é uma violação da restrição global e precisa ser
revertido.

- [ ] **Step 5: Rodar os hooks do repositório**

```bash
cd /Volumes/DOCK/Projetos/pessoal/gerador-hu
uv run pre-commit run --all-files
```

Esperado: todos os hooks passam ou apenas reformatam arquivos; nenhum achado novo de lint, mypy ou
bandit.

- [ ] **Step 6: Commit**

```bash
cd /Volumes/DOCK/Projetos/pessoal/gerador-hu
git add publicar-backlog-demanda-azure-boards
git commit -m "test: cobre o fluxo completo de publicacao vinculada"
```

- [ ] **Step 7: Publicação real, conduzida pelo usuário**

Este passo **não** é executado pelo agente. Entregar ao usuário o comando e esperar a decisão dele:

```bash
cd /Volumes/DOCK/Projetos/pessoal/gerador-hu/publicar-backlog-demanda-azure-boards
uv run python scripts/publicar_backlog_demanda.py publicar ../backlog.md --demanda 13959 --validar-apenas
```

Só depois de o usuário conferir a validação preliminar, e por decisão dele, rodar sem
`--validar-apenas`. A conferência final é visual no Azure Boards: a Demanda 13959 passa a listar os
Épicos como *Child*, com títulos `01`, `01.01` e `01.01.01` e os caminhos herdados.

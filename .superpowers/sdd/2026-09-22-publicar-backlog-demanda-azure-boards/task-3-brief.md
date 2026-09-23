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

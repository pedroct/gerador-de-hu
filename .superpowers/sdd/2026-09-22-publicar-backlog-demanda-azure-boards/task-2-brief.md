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

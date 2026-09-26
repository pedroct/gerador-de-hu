## Tarefa 8: checagem cruzada do `demanda_id`

**Arquivos:**
- Modificar: `publicar-backlog-demanda-azure-boards/src/publicar_backlog_demanda_azure_boards/interpretar_markdown.py`
- Modificar: `publicar-backlog-demanda-azure-boards/src/publicar_backlog_demanda_azure_boards/executar_publicacao.py`
- Testar: `publicar-backlog-demanda-azure-boards/tests/test_demanda_de_origem.py` (novo)
- Testar: `publicar-backlog-azure-boards/tests/test_interpretar_markdown.py` (não-regressão)

**Interfaces:**
- Consome: nada das tarefas anteriores.
- Produz: `extrair_demanda_origem(caminho: Path) -> int | None`, devolvendo `None` quando o backlog
  declara `Não se aplica`.

> Esta é a única tarefa **assimétrica**: a recusa vale só na publicadora de Demanda. A publicadora
> solta precisa continuar aceitando backlog com Demanda declarada, porque o backlog de débitos
> declara a Demanda e publica solto de propósito, pelo `Iteration Path`.

- [ ] **Passo 1: escrever os testes que falham**

Em `publicar-backlog-demanda-azure-boards/tests/test_demanda_de_origem.py`:

```python
from pathlib import Path

import pytest

from publicar_backlog_demanda_azure_boards.interpretar_markdown import (
    ErroContratoMarkdown,
    extrair_demanda_origem,
)

CABECALHO = (
    "# Backlog para Azure Boards\n\n## Metadados e cobertura\n"
    "- Data de geração: `2026-09-25`\n"
)


def test_le_o_id_da_demanda_de_origem(tmp_path: Path) -> None:
    caminho = tmp_path / "backlog.md"
    caminho.write_text(
        CABECALHO + "- Demanda de Negócio de origem: `#14125`\n", encoding="utf-8"
    )

    assert extrair_demanda_origem(caminho) == 14125


def test_devolve_none_quando_o_backlog_declara_nao_se_aplica(tmp_path: Path) -> None:
    caminho = tmp_path / "backlog.md"
    caminho.write_text(
        CABECALHO
        + "- Demanda de Negócio de origem: Não se aplica — a spec não nasceu de uma Demanda\n",
        encoding="utf-8",
    )

    assert extrair_demanda_origem(caminho) is None


def test_rejeita_metadado_ausente(tmp_path: Path) -> None:
    caminho = tmp_path / "backlog.md"
    caminho.write_text(CABECALHO, encoding="utf-8")

    with pytest.raises(ErroContratoMarkdown, match="Demanda de Negócio de origem"):
        extrair_demanda_origem(caminho)
```

Acrescente ao mesmo arquivo os testes da recusa:

```python
from publicar_backlog_demanda_azure_boards.executar_publicacao import conferir_demanda_de_origem


def backlog_com_demanda(tmp_path: Path, linha: str) -> Path:
    caminho = tmp_path / "backlog.md"
    caminho.write_text(CABECALHO + linha, encoding="utf-8")
    return caminho


def test_recusa_quando_o_id_informado_diverge_do_backlog(tmp_path: Path) -> None:
    caminho = backlog_com_demanda(tmp_path, "- Demanda de Negócio de origem: `#14125`\n")

    with pytest.raises(ValueError, match="#14125.*#99999"):
        conferir_demanda_de_origem(caminho, demanda_id=99999)


def test_recusa_backlog_que_nao_nasceu_de_demanda(tmp_path: Path) -> None:
    caminho = backlog_com_demanda(
        tmp_path,
        "- Demanda de Negócio de origem: Não se aplica — a spec não nasceu de uma Demanda\n",
    )

    with pytest.raises(ValueError, match="Não se aplica"):
        conferir_demanda_de_origem(caminho, demanda_id=14125)


def test_aceita_quando_o_id_confere(tmp_path: Path) -> None:
    caminho = backlog_com_demanda(tmp_path, "- Demanda de Negócio de origem: `#14125`\n")

    conferir_demanda_de_origem(caminho, demanda_id=14125)
```

Em `publicar-backlog-azure-boards/tests/test_interpretar_markdown.py`, o teste de não-regressão:

```python
def test_publicadora_solta_aceita_backlog_com_demanda_declarada(tmp_path: Path):
    """O backlog de débitos declara Demanda e publica solto de propósito.

    Se alguém "corrigir" a assimetria acrescentando a recusa aqui, o fluxo de débitos
    para de funcionar. Este teste existe para impedir essa correção.
    """
    caminho = tmp_path / "backlog.md"
    caminho.write_text(
        "# Backlog para Azure Boards\n\n## Metadados e cobertura\n"
        "- Data de geração: `2026-09-25`\n"
        "- Demanda de Negócio de origem: `#14125`\n\n"
        "## 1.0.0 [Epic] Épico\n\n### Description\nTexto\n",
        encoding="utf-8",
    )

    assert interpretar_backlog(caminho)[0].chave == "1.0.0"
```

- [ ] **Passo 2: rodar para confirmar que falham**

```bash
cd publicar-backlog-demanda-azure-boards && uv run pytest tests/test_demanda_de_origem.py -q
```

Esperado: FAIL com `ImportError: cannot import name 'extrair_demanda_origem'`.

- [ ] **Passo 3: implementar**

Em `interpretar_markdown.py` **só do pacote de Demanda**:

```python
_DEMANDA_ORIGEM_RE = re.compile(
    r"^- Demanda de Negócio de origem: (?P<valor>.+)$", re.MULTILINE
)
_DEMANDA_ID_RE = re.compile(r"^`#(\d+)`$")


def extrair_demanda_origem(caminho: Path) -> int | None:
    """Lê o ID da Demanda declarado nos Metadados; ``None`` quando o backlog não nasceu de uma."""
    texto = caminho.read_text(encoding="utf-8")
    correspondencia = _DEMANDA_ORIGEM_RE.search(texto)
    if correspondencia is None:
        raise ErroContratoMarkdown(
            "Metadados e cobertura não possui Demanda de Negócio de origem"
        )
    valor = correspondencia.group("valor").strip()
    if valor.startswith("Não se aplica"):
        return None
    id_declarado = _DEMANDA_ID_RE.match(valor)
    if id_declarado is None:
        raise ErroContratoMarkdown(
            f"Demanda de Negócio de origem inválida: {valor!r}; use `#<id>` ou 'Não se aplica'"
        )
    return int(id_declarado.group(1))
```

e a conferência, junto das demais recusas pré-escrita:

```python
def conferir_demanda_de_origem(caminho: Path, demanda_id: int) -> None:
    """Recusa publicar sob uma Demanda diferente da que o backlog declara.

    Sem flag de sobreposição de propósito: pendurar épicos na Demanda errada é caro de
    desfazer, e uma flag para forçar existiria para ser usada justamente sob a pressão
    em que o engano acontece. Republicar sob outra Demanda passa por corrigir o documento.
    """
    declarada = extrair_demanda_origem(caminho)
    if declarada is None:
        raise ValueError(
            "O backlog declara 'Não se aplica' em Demanda de Negócio de origem: ele não "
            "nasceu de uma Demanda, e esta não é a publicadora dele."
        )
    if declarada != demanda_id:
        raise ValueError(
            f"O backlog declara a Demanda #{declarada}, e a configuração informa "
            f"#{demanda_id}. Corrija o documento ou a configuração antes de publicar."
        )
```

Chame `conferir_demanda_de_origem` na verificação preliminar, antes de qualquer escrita e antes de
pedir autorização. **Não replique nada disso no pacote solto.**

- [ ] **Passo 4: rodar e confirmar que passam**

```bash
cd publicar-backlog-demanda-azure-boards && uv run pytest -q && uv run mypy src
cd ../publicar-backlog-azure-boards && uv run pytest -q && uv run mypy src
```

- [ ] **Passo 5: commitar**

```bash
git add publicar-backlog-demanda-azure-boards publicar-backlog-azure-boards
git commit -m "feat: recusa publicar sob Demanda diferente da declarada no backlog"
```

---

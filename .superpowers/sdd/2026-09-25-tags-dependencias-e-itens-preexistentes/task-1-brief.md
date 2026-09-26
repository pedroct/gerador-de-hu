## Tarefa 1: regras de formato do campo `Tags`

**Arquivos:**
- Modificar: `publicar-backlog-azure-boards/src/publicar_backlog_azure_boards/contrato_backlog.py`
- Modificar: `publicar-backlog-demanda-azure-boards/src/publicar_backlog_demanda_azure_boards/contrato_backlog.py`
- Testar: `publicar-backlog-azure-boards/tests/test_contrato_tags.py`
- Testar: `publicar-backlog-demanda-azure-boards/tests/test_contrato_tags.py`

**Interfaces:**
- Consome: nada de tarefas anteriores.
- Produz: `normalizar_tags(bruto: str) -> tuple[tuple[str, ...], list[str]]` em `contrato_backlog`,
  devolvendo as tags normalizadas e a lista de erros de formato (vazia quando válido). A Tarefa 2 a
  consome no parser tipado; a Tarefa 9 documenta as regras que ela implementa.

- [ ] **Passo 1: escrever os testes que falham**

Crie `publicar-backlog-azure-boards/tests/test_contrato_tags.py`:

```python
import pytest

from publicar_backlog_azure_boards.contrato_backlog import normalizar_tags


def test_seccao_ausente_nao_produz_tags_nem_erros() -> None:
    assert normalizar_tags("") == ((), [])


def test_separa_por_virgula_e_remove_espacos() -> None:
    tags, erros = normalizar_tags("debito-tecnico ,  dt-restricao")

    assert tags == ("debito-tecnico", "dt-restricao")
    assert erros == []


def test_deduplica_preservando_a_ordem() -> None:
    tags, erros = normalizar_tags("design-ux-ui, plataforma-web, design-ux-ui")

    assert tags == ("design-ux-ui", "plataforma-web")
    assert erros == []


def test_recusa_tag_vazia_entre_virgulas() -> None:
    tags, erros = normalizar_tags("debito-tecnico, , dt-restricao")

    assert tags == ()
    assert erros == ["a seção Tags possui uma tag vazia entre vírgulas"]


def test_recusa_ponto_e_virgula_dentro_da_tag() -> None:
    tags, erros = normalizar_tags("debito;tecnico")

    assert tags == ()
    assert erros == ["a tag 'debito;tecnico' contém ';', que o Azure Boards usa como separador"]


def test_recusa_tag_acima_do_limite_do_azure() -> None:
    longa = "x" * 401

    tags, erros = normalizar_tags(longa)

    assert tags == ()
    assert erros == [f"a tag '{longa}' passa de 400 caracteres, o limite do Azure Boards"]


def test_acumula_mais_de_um_erro_de_formato() -> None:
    _, erros = normalizar_tags("a;b, , c;d")

    assert len(erros) == 3
```

Copie o mesmo arquivo para `publicar-backlog-demanda-azure-boards/tests/test_contrato_tags.py`,
trocando o import para `publicar_backlog_demanda_azure_boards.contrato_backlog`.

- [ ] **Passo 2: rodar para confirmar que falham**

```bash
cd publicar-backlog-azure-boards && uv run pytest tests/test_contrato_tags.py -q
```

Esperado: FAIL com `ImportError: cannot import name 'normalizar_tags'`.

- [ ] **Passo 3: implementar**

Em `contrato_backlog.py` de **ambos** os pacotes, acrescente `"Tags"` a `SECTION_NAMES` e a função:

```python
TAGS = "Tags"
LIMITE_TAG = 400

SECTION_NAMES = {
    "Parent",
    "Título curto",
    "Description",
    "Acceptance Criteria",
    "Refinement Status",
    TAGS,
}


def normalizar_tags(bruto: str) -> tuple[tuple[str, ...], list[str]]:
    """Normaliza a seção ``Tags`` e devolve também os erros de formato encontrados.

    Uma seção ausente é legítima e devolve vazio sem erro; uma seção presente e vazia
    é erro de quem a valida, não desta função, porque só o chamador sabe distinguir
    "sem heading" de "heading sem conteúdo".
    """
    texto = bruto.strip()
    if not texto:
        return (), []

    erros: list[str] = []
    tags: list[str] = []
    for parte in texto.split(","):
        tag = parte.strip()
        if not tag:
            erros.append("a seção Tags possui uma tag vazia entre vírgulas")
            continue
        if ";" in tag:
            erros.append(f"a tag '{tag}' contém ';', que o Azure Boards usa como separador")
            continue
        if len(tag) > LIMITE_TAG:
            erros.append(f"a tag '{tag}' passa de {LIMITE_TAG} caracteres, o limite do Azure Boards")
            continue
        if tag not in tags:
            tags.append(tag)

    if erros:
        return (), erros
    return tuple(tags), []
```

- [ ] **Passo 4: rodar e confirmar que passam**

```bash
cd publicar-backlog-azure-boards && uv run pytest tests/test_contrato_tags.py -q && uv run ruff check . && uv run mypy src
cd ../publicar-backlog-demanda-azure-boards && uv run pytest tests/test_contrato_tags.py -q && uv run ruff check . && uv run mypy src
```

Esperado: PASS nos dois, sem achado de ruff nem de mypy.

- [ ] **Passo 5: commitar**

```bash
git add publicar-backlog-azure-boards/src/publicar_backlog_azure_boards/contrato_backlog.py \
        publicar-backlog-azure-boards/tests/test_contrato_tags.py \
        publicar-backlog-demanda-azure-boards/src/publicar_backlog_demanda_azure_boards/contrato_backlog.py \
        publicar-backlog-demanda-azure-boards/tests/test_contrato_tags.py
git commit -m "feat: regras de formato do campo Tags no contrato do backlog"
```

---

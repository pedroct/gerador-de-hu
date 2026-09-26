from publicar_backlog_demanda_azure_boards.contrato_backlog import (
    normalizar_tags,
    validate_backlog,
)


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


BACKLOG_COM_TAGS = """# Backlog para Azure Boards

## Metadados e cobertura
- Data de geração: `2026-09-25`

## 1.0.0 [Epic] Épico

### Description
Origem na spec: seção 1

### Tags
{tags}
"""


def test_validacao_aceita_tags_bem_formadas() -> None:
    erros = validate_backlog(BACKLOG_COM_TAGS.format(tags="debito-tecnico, dt-restricao"))

    assert not any("Tags" in erro for erro in erros)


def test_validacao_recusa_secao_tags_presente_e_vazia() -> None:
    erros = validate_backlog(BACKLOG_COM_TAGS.format(tags=""))

    assert any("1.0.0 possui a seção Tags presente e vazia" in erro for erro in erros)


def test_validacao_propaga_o_erro_de_formato_com_a_chave_do_item() -> None:
    erros = validate_backlog(BACKLOG_COM_TAGS.format(tags="debito;tecnico"))

    assert any(erro.startswith("1.0.0: a tag 'debito;tecnico' contém ';'") for erro in erros)

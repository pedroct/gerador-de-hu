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

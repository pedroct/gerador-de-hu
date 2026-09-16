from pathlib import Path

import pytest

from publicar_backlog_azure_boards.interpretar_markdown import (
    ErroContratoMarkdown,
    extrair_data_geracao,
    interpretar_backlog,
)


def test_interpreta_epic_feature_e_historia():
    itens = interpretar_backlog(Path("tests/fixtures/valid-backlog.md"))
    assert [(item.chave, item.tipo) for item in itens] == [
        ("1.0.0", "Epic"),
        ("1.1.0", "Feature"),
        ("1.1.1", "User Story"),
    ]
    assert itens[2].pai == "1.1.0"


def test_extrai_titulo_curto_quando_declarado():
    itens = interpretar_backlog(Path("tests/fixtures/valid-backlog.md"))
    assert itens[2].titulo_curto == "Reabertura no prazo"


def test_titulo_curto_fica_vazio_quando_nao_declarado():
    itens = interpretar_backlog(Path("tests/fixtures/valid-backlog.md"))
    assert itens[0].titulo_curto == ""


def test_extrai_data_geracao_dos_metadados():
    assert extrair_data_geracao(Path("tests/fixtures/valid-backlog.md")) == "2026-09-10"


def test_rejeita_backlog_sem_data_de_geracao(tmp_path: Path):
    caminho = tmp_path / "backlog.md"
    caminho.write_text(
        "# Backlog para Azure Boards\n\n## Metadados e cobertura\n- Spec de origem: `x`\n",
        encoding="utf-8",
    )
    with pytest.raises(ErroContratoMarkdown):
        extrair_data_geracao(caminho)


def test_rejeita_data_de_geracao_com_calendario_invalido(tmp_path: Path):
    caminho = tmp_path / "backlog.md"
    caminho.write_text(
        "# Backlog para Azure Boards\n\n## Metadados e cobertura\n"
        "- Data de geração: `2026-13-40`\n",
        encoding="utf-8",
    )
    with pytest.raises(ErroContratoMarkdown):
        extrair_data_geracao(caminho)


def test_evidencia_de_implementacao_nao_faz_parte_da_descricao():
    item = interpretar_backlog(Path("tests/fixtures/valid-backlog.md"))[-1]
    assert "Implementation Evidence" not in item.descricao


def test_card_e_conversation_sao_normalizados_para_heading_proeminente():
    """Nível 6 no documento fonte renderiza <h6>, menor que o texto em negrito ao redor."""
    item = interpretar_backlog(Path("tests/fixtures/valid-backlog.md"))[-1]
    assert "###### Card" not in item.descricao
    assert "###### Conversation" not in item.descricao
    assert "### Card" in item.descricao
    assert "### Conversation" in item.descricao


def test_ignora_heading_de_item_dentro_de_cerca_de_codigo(tmp_path: Path):
    caminho = tmp_path / "backlog.md"
    caminho.write_text(
        "## 1.0.0 [Epic] Épico\n### Description\n```markdown\n### 9.9.0 [Feature] Exemplo\n```\n",
        encoding="utf-8",
    )

    assert [item.chave for item in interpretar_backlog(caminho)] == ["1.0.0"]


def test_rejeita_pai_com_chave_incompativel(tmp_path: Path):
    caminho = tmp_path / "backlog.md"
    caminho.write_text(
        "## 1.0.0 [Epic] Primeiro épico\n"
        "### Description\nTexto.\n"
        "## 2.0.0 [Epic] Segundo épico\n"
        "### Description\nTexto.\n"
        "### 1.1.0 [Feature] Feature\n"
        "#### Parent\n`2.0.0`\n"
        "#### Description\nTexto.\n",
        encoding="utf-8",
    )

    with pytest.raises(ErroContratoMarkdown, match="1.1.0 possui pai incompatível: 2.0.0"):
        interpretar_backlog(caminho)


def test_rejeita_criterio_de_aceitacao_fora_de_bloco_gherkin(tmp_path: Path):
    caminho = tmp_path / "backlog.md"
    caminho.write_text(
        "## 1.0.0 [Epic] Épico\n### Description\nTexto.\n"
        "### 1.1.0 [Feature] Feature\n#### Parent\n`1.0.0`\n"
        "#### Description\nTexto.\n"
        "#### 1.1.1 [User Story] História\n##### Parent\n`1.1.0`\n"
        "##### Description\n###### Card\nTexto.\n###### Conversation\nTexto.\n"
        "##### Acceptance Criteria\nCritério narrativo inválido.\n",
        encoding="utf-8",
    )

    with pytest.raises(
        ErroContratoMarkdown,
        match="1.1.1 possui Acceptance Criteria fora de bloco gherkin",
    ):
        interpretar_backlog(caminho)


@pytest.mark.parametrize(
    ("texto", "mensagem"),
    [
        (
            "## 1.0.0 [Epic] Épico\n### Description\nTexto.\n"
            "### 1.1.0 [Feature] Feature\n#### Description\nTexto.\n",
            "1.1.0 não possui Parent",
        ),
        (
            "## 1.0.0 [Epic] Épico\n",
            "1.0.0 não possui Description",
        ),
        (
            "## 1.0.0 [Epic] Épico\n### Description\nTexto.\n### Título fora do contrato\n",
            "heading fora do contrato: ### Título fora do contrato",
        ),
    ],
)
def test_rejeita_contrato_invalido(tmp_path: Path, texto: str, mensagem: str):
    caminho = tmp_path / "backlog.md"
    caminho.write_text(texto, encoding="utf-8")

    with pytest.raises(ErroContratoMarkdown, match=mensagem):
        interpretar_backlog(caminho)

from pathlib import Path

import pytest

from publicar_backlog_azure_boards.interpretar_markdown import (
    ErroContratoMarkdown,
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


def test_evidencia_de_implementacao_nao_faz_parte_da_descricao():
    item = interpretar_backlog(Path("tests/fixtures/valid-backlog.md"))[-1]
    assert "Implementation Evidence" not in item.descricao


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

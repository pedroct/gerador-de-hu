from publicar_backlog_demanda_azure_boards.converter_para_html import (
    converter_criterios,
    converter_descricao,
)


def test_criterios_preservam_gherkin_em_bloco_pre() -> None:
    html = converter_criterios("```gherkin\nCenário: A\n```")

    assert "<pre" in html and "Cenário: A" in html


def test_descricao_converte_markdown_sem_interpretar_html_bruto() -> None:
    html = converter_descricao("## Título\n\n- primeiro\n- segundo\n\n<script>alert(1)</script>")

    assert "<h2>Título</h2>" in html
    assert "<li>primeiro</li>" in html
    assert "&lt;script&gt;" in html

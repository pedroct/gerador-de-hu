import sys
from pathlib import Path

import pytest

RAIZ_SKILL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ_SKILL / "scripts"))

from verificar_lacunas import extrair_lacunas, main, verificar  # noqa: E402

SPEC = """# Spec: Exemplo

## Lacunas e perguntas abertas

- **N1 · Negócio** — Hoje a data que o usuário vê não é a mesma que faz a diligência
  expirar. As duas devem virar uma só?
  <!-- evidência: MinhaDiligenciaDTO.java:76-78 vs DiligenciaService.java:269-270 -->
- **T1 · Técnico** — O prazo vigente deve ser persistido em `Diligencia.java:75` ou
  derivado na leitura?
"""


def test_extrai_identificador_audiencia_e_pergunta() -> None:
    lacunas = extrair_lacunas(SPEC)
    assert [lacuna.identificador for lacuna in lacunas] == ["N1", "T1"]
    assert [lacuna.audiencia for lacuna in lacunas] == ["Negócio", "Técnico"]
    assert "virar uma só?" in lacunas[0].pergunta


def test_evidencia_nao_entra_na_pergunta() -> None:
    """A evidência fica na spec, mas fora do corpo que vai para `negocio.md`."""
    lacunas = extrair_lacunas(SPEC)
    assert "MinhaDiligenciaDTO" not in lacunas[0].pergunta
    assert ".java" not in lacunas[0].pergunta


def test_spec_limpa_nao_gera_violacao() -> None:
    assert verificar(SPEC) == []


def test_lacuna_tecnica_pode_citar_codigo() -> None:
    """A regra de tradução vale só para `Negócio`; o dev precisa da citação."""
    tecnica = [lacuna for lacuna in extrair_lacunas(SPEC) if lacuna.audiencia == "Técnico"]
    assert len(tecnica) == 1 and ".java" in tecnica[0].pergunta
    assert verificar(SPEC) == []


def test_caminho_de_arquivo_em_pergunta_de_negocio_viola() -> None:
    texto = "- **N2 · Negócio** — O prazo sai de `DiligenciaService.java:269` ou da abertura?\n"
    violacoes = verificar(texto)
    assert len(violacoes) == 1
    assert violacoes[0].lacuna.identificador == "N2"
    assert violacoes[0].padrao == "caminho-de-arquivo"


def test_numero_de_linha_em_pergunta_de_negocio_viola() -> None:
    texto = "- **N3 · Negócio** — Quem vê o rótulo, conforme :140-145 do portal?\n"
    assert [v.padrao for v in verificar(texto)] == ["numero-de-linha"]


def test_chamada_de_metodo_em_pergunta_de_negocio_viola() -> None:
    texto = "- **N4 · Negócio** — A contagem usa LocalDateTime.plusDays() ou data civil?\n"
    assert [v.padrao for v in verificar(texto)] == ["chamada-de-metodo"]


def test_campo_do_azure_boards_em_pergunta_de_negocio_viola() -> None:
    """Vocabulário técnico que o PO não reconhece, ainda que não seja código-fonte."""
    texto = "- **N5 · Negócio** — O valor de Custom.DemandaValorEsperado está completo?\n"
    assert [v.padrao for v in verificar(texto)] == ["identificador-pontuado"]


def test_spec_sem_rotulos_de_audiencia_nao_gera_violacao() -> None:
    """Spec antiga não é violação: o verificador simplesmente não encontra lacunas rotuladas."""
    antiga = "## Lacunas e perguntas abertas\n\n- Qual data ancora o prazo (`X.java:12`)?\n"
    assert extrair_lacunas(antiga) == []
    assert verificar(antiga) == []


def test_cli_devolve_1_quando_ha_violacao(tmp_path: Path) -> None:
    spec = tmp_path / "spec.md"
    spec.write_text("- **N6 · Negócio** — O prazo sai de `X.java:12`?\n", encoding="utf-8")
    assert main([str(spec)]) == 1


def test_cli_devolve_0_quando_a_spec_esta_limpa(tmp_path: Path) -> None:
    spec = tmp_path / "spec.md"
    spec.write_text("- **N7 · Negócio** — O prazo sai da abertura?\n", encoding="utf-8")
    assert main([str(spec)]) == 0


def test_cli_devolve_2_para_arquivo_inexistente() -> None:
    """Arquivo ilegível é erro de uso, não violação: nem traceback, nem código 1."""
    assert main(["/caminho/que/nao/existe/spec.md"]) == 2


def test_hora_do_dia_em_pergunta_de_negocio_nao_viola() -> None:
    """Prazo e expiração são o domínio da skill: a hora de corte é pergunta de negócio legítima."""
    texto = "- **N8 · Negócio** — A diligência expira às 23:59 do último dia ou na virada?\n"
    assert verificar(texto) == []


def test_varias_horas_na_mesma_pergunta_de_negocio_nao_violam() -> None:
    texto = "- **N9 · Negócio** — O lembrete sai às 8:00 ou às 18:00?\n"
    assert verificar(texto) == []


def test_proporcao_em_pergunta_de_negocio_nao_viola() -> None:
    texto = "- **N10 · Negócio** — A proporção de 1:3 entre urgente e comum vale ainda?\n"
    assert verificar(texto) == []


def test_continuacao_sem_indentacao_entra_na_pergunta() -> None:
    """Continuação preguiçosa é Markdown válido: o que vaza nela tem de chegar ao gate."""
    texto = (
        "- **N11 · Negócio** — Uma pergunta que continua\n"
        "na linha seguinte sem indentação citando X.java:12?\n"
    )
    assert "sem indentação" in extrair_lacunas(texto)[0].pergunta
    assert [v.padrao for v in verificar(texto)] == ["caminho-de-arquivo"]


def test_item_seguinte_sem_indentacao_nao_e_continuacao() -> None:
    """A lacuna fecha no próximo item ou título; o vazamento do vizinho não migra para ela."""
    texto = (
        "- **N12 · Negócio** — Uma pergunta limpa sobre o prazo?\n"
        "- Item solto citando X.java:12\n"
        "## Outra seção\n"
    )
    lacunas = extrair_lacunas(texto)
    assert len(lacunas) == 1
    assert lacunas[0].pergunta == "Uma pergunta limpa sobre o prazo?"
    assert verificar(texto) == []


def test_cli_relata_quantas_lacunas_rotuladas_verificou(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Verde mudo não distingue spec limpa de formato que o extrator não reconheceu."""
    spec = tmp_path / "spec.md"
    spec.write_text(SPEC, encoding="utf-8")
    assert main([str(spec)]) == 0
    assert "2 lacunas rotuladas verificadas, nenhum vazamento." in capsys.readouterr().out


def test_cli_avisa_quando_a_secao_existe_e_nenhuma_lacuna_foi_reconhecida(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Deriva tipográfica no rótulo produzia saída idêntica à de uma spec limpa."""
    spec = tmp_path / "spec.md"
    spec.write_text(
        "## Lacunas e perguntas abertas\n\n- **N1 . Negócio** - Qual data ancora o prazo?\n",
        encoding="utf-8",
    )
    assert main([str(spec)]) == 0
    capturado = capsys.readouterr()
    assert "nenhuma lacuna rotulada foi reconhecida" in capturado.err
    assert "0 lacunas rotuladas verificadas, nenhum vazamento." in capturado.out


def test_spec_sem_a_secao_de_lacunas_nao_gera_aviso(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """O aviso é sobre a seção presente e vazia, não sobre qualquer arquivo sem lacunas."""
    spec = tmp_path / "spec.md"
    spec.write_text("# Spec: Exemplo\n\n## Escopo\nItem único.\n", encoding="utf-8")
    assert main([str(spec)]) == 0
    assert capsys.readouterr().err == ""


def test_marcador_de_bloco_fecha_a_lacuna_anterior() -> None:
    """Absorvido, o vazamento do vizinho sairia com o identificador da lacuna errada."""
    for vizinho in (
        "| Afirmação | X.java:12 |",
        "* Item solto citando X.java:12",
        "+ Item solto citando X.java:12",
        "1. Item solto citando X.java:12",
        "> Nota citando X.java:12",
        "---",
    ):
        texto = f"- **N13 · Negócio** — Uma pergunta limpa sobre o prazo?\n{vizinho}\n"
        lacunas = extrair_lacunas(texto)
        assert len(lacunas) == 1, vizinho
        assert lacunas[0].pergunta == "Uma pergunta limpa sobre o prazo?", vizinho
        assert verificar(texto) == [], vizinho

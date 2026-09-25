import sys
from pathlib import Path

RAIZ_SKILL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ_SKILL / "scripts"))

from verificar_lacunas import extrair_lacunas, verificar  # noqa: E402

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
    assert all(v.lacuna.audiencia != "Técnico" for v in verificar(SPEC))


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

## Tarefa 4: Verificador de linguagem das lacunas de negócio

Única parte do plano com lógica executável. Vem primeiro na fase porque é autocontida e a Tarefa 5 a referencia.

**Arquivos:**
- Criar: `redigir-spec-demanda-azure-boards/scripts/verificar_lacunas.py`
- Criar: `redigir-spec-demanda-azure-boards/tests/test_verificar_lacunas.py`
- Modificar: `pyproject.toml` (seção `[tool.coverage.run] source`, se ainda não cobrir `redigir-spec-demanda-azure-boards/scripts`)

**Interfaces:**
- Consome: nada.
- Produz:
  - `Lacuna(identificador: str, audiencia: str, pergunta: str, linha: int)` — dataclass congelada
  - `Violacao(lacuna: Lacuna, trecho: str, padrao: str)` — dataclass congelada
  - `extrair_lacunas(texto: str) -> list[Lacuna]`
  - `verificar(texto: str) -> list[Violacao]`
  - `main() -> int` — CLI, saída 1 com violações, 0 sem

- [ ] **Passo 1: Escrever os testes que falham**

Crie `redigir-spec-demanda-azure-boards/tests/test_verificar_lacunas.py`:

```python
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
    assert [l.identificador for l in lacunas] == ["N1", "T1"]
    assert [l.audiencia for l in lacunas] == ["Negócio", "Técnico"]
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
```

- [ ] **Passo 2: Rodar os testes e confirmar que falham**

```bash
uv run pytest redigir-spec-demanda-azure-boards/tests/test_verificar_lacunas.py -v
```

Esperado: `ModuleNotFoundError: No module named 'verificar_lacunas'`.

- [ ] **Passo 3: Escrever o verificador**

Crie `redigir-spec-demanda-azure-boards/scripts/verificar_lacunas.py`:

```python
"""Verifica se lacunas de negócio vazaram vocabulário técnico.

A regra de tradução exige que uma pergunta destinada à área de negócio não cite arquivo, classe,
método, campo, enum, número de linha ou variável. A evidência `caminho:linha` continua na spec, em
comentário, mas fora do corpo da pergunta.

Uso:
    uv run python redigir-spec-demanda-azure-boards/scripts/verificar_lacunas.py spec.md
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

CABECALHO = re.compile(
    r"^- \*\*(?P<id>[NT]\d+) · (?P<audiencia>Negócio|Técnico)\*\* — (?P<inicio>.*)$"
)
EVIDENCIA = re.compile(r"<!--.*?-->", re.DOTALL)

EXTENSOES = "java|ts|tsx|js|jsx|dart|py|kt|swift|cs|rb|go|php|vue|html|scss|css|sql|xml|ya?ml|json"
PADROES: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("caminho-de-arquivo", re.compile(rf"[\w/.\-]+\.({EXTENSOES})\b")),
    ("numero-de-linha", re.compile(r":\d+(?:-\d+)?\b")),
    ("chamada-de-metodo", re.compile(r"\b[A-Za-z_][\w.]*\.[a-z]\w*\s*\(")),
    ("identificador-pontuado", re.compile(r"\b[A-Z][A-Za-z0-9]*\.[A-Za-z][A-Za-z0-9]*\b")),
)


@dataclass(frozen=True)
class Lacuna:
    identificador: str
    audiencia: str
    pergunta: str
    linha: int


@dataclass(frozen=True)
class Violacao:
    lacuna: Lacuna
    trecho: str
    padrao: str


def extrair_lacunas(texto: str) -> list[Lacuna]:
    """Devolve as lacunas rotuladas. Uma spec sem rótulos devolve lista vazia, não erro."""
    lacunas: list[Lacuna] = []
    identificador = ""
    audiencia = ""
    linha_inicial = 0
    corpo: list[str] = []
    aberta = False

    def fechar() -> None:
        nonlocal aberta
        if not aberta:
            return
        pergunta = " ".join(EVIDENCIA.sub(" ", " ".join(corpo)).split())
        lacunas.append(Lacuna(identificador, audiencia, pergunta, linha_inicial))
        aberta = False

    for numero, linha in enumerate(texto.splitlines(), start=1):
        encontrado = CABECALHO.match(linha)
        if encontrado:
            fechar()
            identificador = encontrado.group("id")
            audiencia = encontrado.group("audiencia")
            linha_inicial = numero
            corpo = [encontrado.group("inicio")]
            aberta = True
        elif aberta and linha.startswith(("  ", "\t")):
            corpo.append(linha.strip())
        elif aberta:
            fechar()
    fechar()
    return lacunas


def verificar(texto: str) -> list[Violacao]:
    """Sinaliza vocabulário técnico dentro de perguntas de negócio."""
    violacoes: list[Violacao] = []
    for lacuna in extrair_lacunas(texto):
        if lacuna.audiencia != "Negócio":
            continue
        for nome, padrao in PADROES:
            achado = padrao.search(lacuna.pergunta)
            if achado:
                violacoes.append(Violacao(lacuna=lacuna, trecho=achado.group(0), padrao=nome))
                break
    return violacoes


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spec", help="caminho da spec, ou '-' para a entrada padrão")
    args = parser.parse_args()

    texto = sys.stdin.read() if args.spec == "-" else Path(args.spec).read_text("utf-8")
    violacoes = verificar(texto)
    if not violacoes:
        print("Nenhum vazamento de vocabulário técnico em lacunas de negócio.")
        return 0

    for violacao in violacoes:
        print(
            f"linha {violacao.lacuna.linha}: {violacao.lacuna.identificador} "
            f"({violacao.padrao}) — {violacao.trecho!r}",
            file=sys.stderr,
        )
    print(
        f"\n{len(violacoes)} lacuna(s) de negócio citam código. "
        "Reescreva a pergunta e mova a citação para o comentário de evidência.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Passo 4: Rodar os testes e confirmar que passam**

```bash
uv run pytest redigir-spec-demanda-azure-boards/tests/test_verificar_lacunas.py -v
```

Esperado: 9 PASS. Se `test_chamada_de_metodo_em_pergunta_de_negocio_viola` devolver `identificador-pontuado`, confirme que `chamada-de-metodo` vem antes na tupla `PADROES` — a ordem define qual padrão reporta.

- [ ] **Passo 5: Conferir a CLI na mão**

```bash
printf -- '- **N9 · Negócio** — O prazo sai de `X.java:12` ou da abertura?\n' \
  | uv run python redigir-spec-demanda-azure-boards/scripts/verificar_lacunas.py -
echo "codigo de saida: $?"
```

Esperado: mensagem em `stderr` citando `N9` e `caminho-de-arquivo`, código de saída 1.

- [ ] **Passo 6: Rodar lint e tipos**

```bash
uv run ruff check redigir-spec-demanda-azure-boards/scripts/verificar_lacunas.py
uv run ruff format --check redigir-spec-demanda-azure-boards/scripts/verificar_lacunas.py
uv run mypy --strict redigir-spec-demanda-azure-boards/scripts/verificar_lacunas.py
```

Esperado: `All checks passed!`, `1 file already formatted` e `Success: no issues found`. Este código
já foi validado contra os três — se algum acusar, foi a transcrição que divergiu, não o desenho.

- [ ] **Passo 7: Commit**

```bash
git add redigir-spec-demanda-azure-boards/scripts/verificar_lacunas.py \
        redigir-spec-demanda-azure-boards/tests/test_verificar_lacunas.py pyproject.toml
git commit -m "feat: verifica vazamento de vocabulario tecnico em lacuna de negocio

Unica parte do desenho com verificacao executavel, e justamente a que
falhou na reuniao que originou a mudanca. Spec sem rotulos nao e
violacao: o verificador simplesmente nao encontra lacunas rotuladas.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

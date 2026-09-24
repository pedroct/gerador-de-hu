"""Mede a priorização contra casos com nota esperada.

Notas são ordinais: além do acerto exato, reporta o acerto dentro de ±1 nível, que
é a tolerância que importa quando o resultado alimenta uma ordenação.

Uso: uv run python especificar-debitos-tecnicos/scripts/avaliar_priorizacao.py
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from cliente_jev import carregar_chave, decidir  # noqa: E402
from priorizacao import (  # noqa: E402
    PERGUNTAS,
    montar_state,
    priorizar,
    separar_em_faixas,
    sinalizar_inversoes,
)

CasoTeste = dict[str, Any]

CASOS: list[CasoTeste] = [
    {
        "nome": "comentario-mentiroso",
        "debito": (
            "Um comentário no topo do módulo de faturamento descreve um fluxo de aprovação que "
            "foi substituído há dois anos. O código atual está correto; só o comentário mente."
        ),
        "impacto": 1,
        "probabilidade": 1,
        "severidade": 1,
        "esforco": 1,
        "categoria": "Documentação",
        "tipo": "User Story",
    },
    {
        "nome": "query-duplicada-sem-teste",
        "debito": (
            "A camada de repositório repete a query de saldo em três serviços diferentes, cada "
            "um com um filtro de data ligeiramente distinto. Nenhuma delas tem teste. Quando o "
            "cálculo muda, é preciso lembrar de alterar os três."
        ),
        "impacto": 3,
        "probabilidade": 3,
        "severidade": 2,
        "esforco": 3,
        "categoria": "Código",
        "tipo": "User Story",
    },
    {
        "nome": "arredondamento-contra-contrato",
        "debito": (
            "O cálculo de juros arredonda para cima em todas as parcelas, mas o contrato assinado "
            "com o cliente especifica arredondamento bancário. Já houve duas reclamações formais "
            "e a contabilidade corrige na mão todo mês."
        ),
        "impacto": 4,
        "probabilidade": 5,
        "severidade": 4,
        "esforco": 2,
        "categoria": "Código",
        "tipo": "Bug",
    },
    {
        "nome": "framework-sem-suporte",
        "debito": (
            "A versão do framework web que sustenta o portal saiu de suporte há oito meses e não "
            "recebe mais correção de segurança. A atualização quebra a API de sessão, usada em "
            "praticamente todas as telas."
        ),
        "impacto": 4,
        "probabilidade": 3,
        "severidade": 5,
        "esforco": 5,
        "categoria": "Dependências",
        "tipo": "User Story",
    },
    {
        "nome": "sem-observabilidade",
        "debito": (
            "O serviço de integração com a Receita não emite log estruturado nem métrica. Quando "
            "ele falha, a equipe descobre pelo cliente e não consegue dizer qual chamada falhou "
            "sem reproduzir o caso em homologação."
        ),
        "impacto": 3,
        "probabilidade": 4,
        "severidade": 3,
        "esforco": 2,
        "categoria": "Infraestrutura",
        "tipo": "User Story",
    },
    {
        "nome": "dependencia-ciclica",
        "debito": (
            "Os módulos de cobrança e de cadastro importam um ao outro. Qualquer mudança em um "
            "recompila e re-testa o outro, e já impediu duas vezes extrair a cobrança para um "
            "serviço próprio, que está no plano do trimestre."
        ),
        "impacto": 4,
        "probabilidade": 2,
        "severidade": 2,
        "esforco": 4,
        "categoria": "Arquitetura",
        "tipo": "User Story",
    },
]

DIMENSOES = ("impacto", "probabilidade", "severidade", "esforco")


def main() -> int:
    chave = carregar_chave()
    exato = dentro_de_um = total = 0
    ok_categoria = ok_tipo = 0
    custo = 0.0
    resultados: list[dict[str, Any]] = []

    for caso in CASOS:
        resposta = decidir(montar_state(caso["debito"]), PERGUNTAS, chave)
        r = priorizar(resposta["answers"])
        custo += float(resposta.get("usage", {}).get("cost", 0.0))
        r["nome"] = caso["nome"]
        resultados.append(r)

        ok_categoria += r["categoria"] == caso["categoria"]
        ok_tipo += r["tipo_sugerido"] == caso["tipo"]

        print(f"\n{'=' * 78}")
        print(f"CASO: {caso['nome']}")
        print(f"  {'dim':<10}{'esperado':>9}{'obtido':>8}{'score':>8}{'conf.':>8}")
        for d in DIMENSOES:
            esperado, obtido = caso[d], r[d]
            total += 1
            exato += esperado == obtido
            dentro_de_um += abs(esperado - obtido) <= 1
            print(
                f"  {d:<10}{esperado:>9}{obtido:>8}"
                f"{r['scores_crus'][d]:>8.2f}{r['confiancas'][d]:>8.2f}"
            )
        cat = (
            "ok" if r["categoria"] == caso["categoria"] else f"ERRO (esperava {caso['categoria']})"
        )
        tip = "ok" if r["tipo_sugerido"] == caso["tipo"] else f"ERRO (esperava {caso['tipo']})"
        print(f"  categoria : {r['categoria']}  [{cat}]")
        print(f"  tipo      : {r['tipo_sugerido']}  [{tip}]")
        print(f"  prioridade: {r['prioridade']}")

    n = len(CASOS)
    print(f"\n{'=' * 78}")
    print(f"notas exatas     : {exato}/{total} ({exato / total:.0%})")
    print(f"notas dentro ±1  : {dentro_de_um}/{total} ({dentro_de_um / total:.0%})")
    print(f"categoria        : {ok_categoria}/{n}")
    print(f"tipo Bug/Story   : {ok_tipo}/{n}")
    print(f"custo            : US$ {custo:.6f}  |  por débito: US$ {custo / n:.6f}")

    faixas = separar_em_faixas(resultados)
    print(f"\n{'-' * 78}")
    print("FAIXA DE RESTRIÇÃO — severidade alta com probabilidade real; o esforço não adia:")
    for item in faixas["restricoes"] or []:
        print(
            f"  • {item['nome']:<34} I{item['impacto']} R{item['risco']} "
            f"E{item['esforco']}  (sev {item['severidade']}, prob {item['probabilidade']})"
        )
    if not faixas["restricoes"]:
        print("  (nenhum)")

    print("\nA CONFIRMAR — severidade julgada com confiança insuficiente para classificar:")
    for item in faixas["a_confirmar"] or []:
        print(
            f"  ? {item['nome']:<34} sev {item['severidade']} "
            f"(confiança {item['confiancas']['severidade']:.2f}) — a descrição não diz o "
            f"que acontece quando ocorre"
        )
    if not faixas["a_confirmar"]:
        print("  (nenhum)")

    print("\nCANDIDATOS — ordenados pela fórmula da skill:")
    for pos, item in enumerate(faixas["candidatos"], 1):
        print(
            f"  {pos}. {item['nome']:<34} prioridade {item['prioridade']:>3}  "
            f"(I{item['impacto']} R{item['risco']} E{item['esforco']})"
        )

    inversoes = sinalizar_inversoes(faixas["candidatos"])
    if inversoes:
        print("\ninversões de impacto entre candidatos (a fórmula é de eficiência):")
        for inv in inversoes:
            print(f"  - {inv['acima']['nome']} acima de {inv['abaixo']['nome']}: {inv['porque']}")

    return 0 if dentro_de_um == total and ok_tipo == n else 1


if __name__ == "__main__":
    raise SystemExit(main())

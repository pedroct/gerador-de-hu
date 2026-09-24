"""Retranslação BARS das âncoras de Impacto, Risco e Esforço.

O BARS (*Behaviorally Anchored Rating Scale*) prevê um passo de validação: examinadores
que não escreveram as âncoras reclassificam exemplos concretos, e só se mantêm as
âncoras em que a concordância é forte. Âncora que não atrai de volta o próprio exemplo
está ambígua ou se sobrepõe à vizinha.

Aqui o Jev faz o papel do examinador independente. Cada exemplar abaixo descreve um
débito real no nível que se pretende ancorar, com **redação diferente da âncora** — se
repetisse as palavras da âncora, o teste seria circular.

Uso: uv run python especificar-debitos-tecnicos/scripts/retranslacao.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from cliente_jev import carregar_chave, decidir  # noqa: E402
from priorizacao import PERGUNTAS, montar_state  # noqa: E402

EXEMPLARES: dict[str, list[str]] = {
    "impacto": [
        "O arquivo de estilos tem duas classes CSS com os nomes trocados entre si. Ninguém "
        "precisou mexer nelas desde que foram escritas, e as telas renderizam corretamente.",
        "As variáveis do cálculo de frete usam abreviações de uma sigla que a empresa aposentou. "
        "Quem mexe ali perde alguns minutos para se situar; fora isso, funciona.",
        "Qualquer alteração no fluxo de assinatura obriga a mexer em quatro classes que se "
        "referenciam. A equipe combinou de só tocar nessa área quando for inevitável.",
        "A rotina noturna de conciliação falhou três vezes neste trimestre e precisou ser "
        "reprocessada à mão. O projeto de fechamento automático está parado por causa dela.",
        "O endpoint de upload não valida tamanho de arquivo e já derrubou a API duas vezes em "
        "horário comercial. O portal do cliente foi prometido para este mês e depende dele.",
    ],
    "probabilidade": [
        "A função que formata CPF está duplicada em dois utilitários. As duas cópias estão "
        "corretas, o módulo não recebe commit há dois anos e nunca houve chamado relacionado.",
        "O parser de importação assume separador ponto-e-vírgula. Só quebraria se o fornecedor "
        "mudasse o layout, o que não aconteceu em seis anos e não consta do contrato deste ano.",
        "O módulo de relatórios carrega o resultado inteiro em memória. Hoje são quatro mil "
        "registros e a base cresce devagar, mas nada impede alguém pedir um recorte maior.",
        "O módulo de relatórios carrega tudo em memória e um cliente novo, que sozinho traz o "
        "dobro do volume atual, entra em produção em algum momento deste ano.",
        "O certificado do serviço de pagamento expira em duas semanas e a renovação é manual, "
        "sem alerta configurado.",
    ],
    "severidade": [
        "Quando acontece, o log grava uma mensagem com acento errado. Ninguém fora da equipe de "
        "desenvolvimento nota.",
        "Quando acontece, o relatório sai com a coluna de total em branco e alguém precisa "
        "gerá-lo de novo. Nada se perde.",
        "Quando acontece, a busca de produtos fica fora do ar por alguns minutos e os atendentes "
        "usam a listagem antiga enquanto isso.",
        "Quando acontece, os lançamentos entram duplicados no fechamento e a contabilidade "
        "precisa de um mutirão para identificar e estornar.",
        "Quando acontece, os dados cadastrais dos clientes ficam acessíveis sem autenticação, o "
        "que é violação da LGPD e obriga notificação à autoridade.",
    ],
    "esforco": [
        "Renomear uma constante mal escrita que aparece num único arquivo e já está coberta por "
        "teste.",
        "Extrair três funções repetidas dentro do mesmo serviço para um utilitário interno, sem "
        "alterar nenhuma assinatura pública.",
        "Introduzir uma camada de repositório entre o controlador e o banco, escrevendo testes "
        "novos para as consultas que passam a existir.",
        "Mudar o formato do campo de data na API pública que o aplicativo mobile consome, "
        "migrando os registros já gravados.",
        "Substituir o mecanismo de autenticação por um provedor externo, coordenando as equipes "
        "de web, mobile e infraestrutura.",
    ],
}

TOLERANCIA = 0.5  # distância máxima aceita entre o score e o nível pretendido


def main() -> int:
    chave = carregar_chave()
    total = aderentes = 0
    custo = 0.0
    problemas: list[str] = []

    for dimensao, exemplares in EXEMPLARES.items():
        print(f"\n{'=' * 78}\nDIMENSÃO: {dimensao}")
        print(f"  {'nível':<7}{'score':>8}{'desvio':>9}{'conf.':>8}  exemplar")
        for nivel, exemplar in enumerate(exemplares):
            resposta = decidir(montar_state(exemplar), PERGUNTAS, chave)
            answer = resposta["answers"][dimensao]
            custo += float(resposta.get("usage", {}).get("cost", 0.0))
            score = float(answer["score"])
            desvio = score - nivel
            total += 1
            ok = abs(desvio) <= TOLERANCIA
            aderentes += ok
            if not ok:
                problemas.append(
                    f"{dimensao} nível {nivel + 1}: exemplar caiu em {score + 1:.2f} "
                    f"(desvio {desvio:+.2f})"
                )
            marca = " " if ok else " <<"
            print(
                f"  {nivel + 1:<7}{score + 1:>8.2f}{desvio:>+9.2f}"
                f"{answer['confidence']:>8.2f}  {exemplar[:38]}…{marca}"
            )

    print(f"\n{'=' * 78}")
    print(
        f"âncoras que atraem o próprio exemplar (±{TOLERANCIA}): "
        f"{aderentes}/{total} ({aderentes / total:.0%})"
    )
    print(f"custo: US$ {custo:.6f}")
    if problemas:
        print("\nâncoras a revisar:")
        for p in problemas:
            print(f"  - {p}")
    return 0 if aderentes == total else 1


if __name__ == "__main__":
    raise SystemExit(main())

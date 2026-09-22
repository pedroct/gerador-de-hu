# Investigação de código a partir de uma Demanda no Azure Boards

Leia esta referência antes de investigar o código para redigir a Spec. O objetivo é descobrir
vocabulário, atores e comportamento atual com evidência verificável — não validar nem completar uma
decisão de negócio.

## Descoberta de repositórios

Como a skill roda a partir do diretório onde está instalada, trate esse diretório e seus repositórios
irmãos como universo de busca. Para cada repositório, registre se ele é relevante ao vocabulário,
entidades, telas ou endpoints da Demanda, incluindo o motivo dos descartados.

## Inspeção segura

1. Registre a raiz analisada e qualquer incerteza sobre qual repositório implementa o comportamento.
2. Faça somente leitura: use `rg`, incluindo `rg --files`, ou `find` para inventário; use `git status`
   para registrar o estado; leia código, testes e configuração apenas quando forem pertinentes. Escolha
   a busca menos abrangente que responda à pergunta.
3. Não execute aplicação. Não execute teste. Não execute build. Não execute migração. Também não
   execute scripts, servidores ou qualquer comando que altere arquivos, dependências, banco de dados,
   serviços ou configuração.
4. Investigue pontos de entrada, regras de domínio, atores e vocabulário somente quando forem ligados à
   Demanda. Um nome de arquivo, símbolo ou teste isolado não prova o comportamento completo.

Se nenhum repositório puder ser localizado ou lido com segurança, registre o limite e prossiga com a
Spec baseada apenas na Demanda; não preencha lacunas por plausibilidade.

## Categorias obrigatórias de conteúdo

Separe sempre os três tipos de informação:

- **Registrado na Demanda**: valor retornado pelo Azure Boards. Um campo da Demanda é evidência da
  síntese GEPRO, não prova de texto original da área solicitante. Não rotule esse valor como explícito
  ou inferido no pedido original.
- **Evidenciado pelo código**: cite cada evidência como `caminho:linha`, com caminho relativo à raiz
  analisada. Havendo mais de um repositório, prefixe pelo nome do repositório, por exemplo
  `gepro-api/src/demandas/servico.py:42`. Registre `Nenhuma evidência encontrada` quando a busca
  relevante terminar, ou `Evidência indisponível: <motivo>` quando não puder investigar. Nunca invente
  caminho ou linha.
- **Lacuna**: informação não confirmada pela Demanda nem pelo código; mantenha-a como pergunta aberta.

O código só descreve o estado atual. Ele não confirma intenção, valor, promessa da área ou decisão de
negócio. Propostas, hipóteses e achados sem relação com o escopo ficam fora da Spec.

## Divergências e confiança

Quando a Demanda e o código divergirem, registre as duas leituras em **Lacunas e perguntas abertas**,
sem escolher qual prevalece. A divergência é a informação disponível para decisão posterior.

Qualifique cada linha de evidência como `Alta`, `Média` ou `Baixa`. A confiança mede o quanto a
evidência sustenta a observação, mas não substitui a separação entre Registrado na Demanda,
Evidenciado pelo código e Lacuna.

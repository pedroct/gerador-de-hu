# Investigação de código a partir de um pedido de negócio

Leia esta referência antes de investigar o código para redigir a spec. O objetivo é descobrir
vocabulário, atores e comportamento atual com evidência verificável — não validar um requisito que
ainda não existe.

## Descoberta de repositórios

Como a skill roda a partir do diretório onde foi instalada, trate esse diretório e seus repositórios
irmãos como universo de busca. Para cada um, registre se é relevante ao vocabulário do pedido (nomes
de entidades, telas, endpoints citados ou implícitos) e o motivo — inclusive para os descartados.

## Inspeção segura

1. Registre a raiz analisada e qualquer incerteza sobre qual repositório implementa o comportamento
   descrito no pedido.
2. Faça somente leitura segura: inventário com `rg` (incluindo `rg --files`) ou `find`, estado do
   repositório com `git status`, leitura de arquivos de código e testes e leitura de arquivos de
   configuração. Use a ferramenta menos abrangente que responda à pergunta.
3. Não execute scripts, testes, builds, servidores, migrações ou a aplicação sem autorização explícita. Não altere arquivos, dependências, banco de dados, serviços nem configuração como parte da investigação.
4. Inspecione pontos de entrada, regras de domínio, atores e vocabulário somente quando forem
   relevantes ao pedido. O nome de um arquivo, símbolo ou teste isolado não prova o comportamento
   completo.

Se nenhum repositório puder ser localizado ou lido com segurança, registre o limite e prossiga com a
spec baseada apenas no pedido; não preencha lacunas com plausibilidade.

## Três categorias de conteúdo

Separe sempre:

- **Afirmado pelo pedido**: o que o texto original declara, citado ou parafraseado fielmente.
- **Evidenciado pelo código**: cite cada evidência como caminho relativo à raiz e linha inicial, por
  exemplo `src/diligencias/reopen_service.py:42`. Registre `Nenhuma evidência encontrada` quando a
  busca relevante estiver concluída, ou `Evidência indisponível: [motivo]` quando não foi possível
  investigar. Nunca invente caminho ou linha.
- **Lacuna**: o que não pôde ser confirmado nem pelo pedido nem pelo código; permanece como pergunta
  aberta.

Código existente não cria requisito nem confirma decisão de negócio; ele só descreve o estado atual.
Propostas, hipóteses e comportamentos encontrados sem relação com o pedido ficam fora da spec.

Quando o pedido e o código divergirem, registre as duas leituras em Lacunas e perguntas abertas, sem
escolher qual prevalece — a divergência em si é a informação relevante para quem for decidir depois.

## Confiança

Qualifique cada linha de evidência com `Alta`, `Média` ou `Baixa`. Confiança descreve o quanto a
evidência sustenta a observação; não substitui a distinção entre afirmado, evidenciado e lacuna.

## Handoff

Entregue a spec com as três categorias claramente identificadas. Quem for rodar
`generating-azure-boards-backlog-from-spec` sobre esse arquivo trata "Evidenciado pelo código" como
contexto Brownfield de estado atual, nunca como confirmação de valor ou decisão de negócio.

# Validação Brownfield de telas (web e mobile)

Leia esta referência somente quando houver código de front-end relevante para a plataforma em análise, ou
quando sua presença for ambígua. O objetivo é descrever a cobertura de tela atual com evidência
verificável, por plataforma, antes de decidir se a equipe de UX-UI precisa especificar algo novo.

## Inspeção segura

1. Registre a raiz analisada por plataforma, os limites de escopo e qualquer incerteza sobre qual
   repositório implementa o front-end web ou o app mobile do produto.
2. Faça somente leitura segura: inventário com `rg` (incluindo `rg --files`) ou `find`, estado do
   repositório com `git status`, leitura de arquivos de rotas/páginas/telas/componentes e de
   configuração. Use a ferramenta menos abrangente que responda à pergunta.
3. Não execute scripts, testes, builds, servidores, migrações, o aplicativo mobile nem o front-end web
   sem autorização explícita. Não altere arquivos, dependências nem configuração como parte da
   validação.
4. Inspecione rotas, páginas, telas, componentes e seus estados somente quando forem relevantes ao
   requisito inventariado da spec. O nome de um arquivo ou componente isolado não prova que o fluxo
   completo já está coberto.

Se o repositório de uma plataforma não puder ser localizado ou lido com segurança, mantenha o modo
Brownfield-UI para ela, registre o limite e classifique o que não pôde ser determinado como `Impossível
validar`; não preencha lacunas com plausibilidade.

## Regra de comparação

Compare o código somente com a necessidade de tela do requisito da spec. Código existente não confirma
valor, decisão de negócio nem regra de negócio — ele descreve apenas o estado atual da interface. Um
componente ou tela encontrados sem relação com o requisito não criam necessidade nem a descartam.

Para cada par (requisito, plataforma) com faceta de UI:

- procure evidência direta de uma tela ou fluxo equivalente ao que o requisito pede;
- cite cada evidência útil como caminho relativo à raiz e linha inicial, por exemplo
  `src/telas/Diligencia/ReaberturaScreen.tsx:18`;
- distinga tela/componente de produção de arquivos de teste ou storybook na síntese; um teste de
  interface existente pode aumentar confiança, mas não substitui evidência da tela implementada;
- uma tela existente que passa a mostrar **mais** do que mostrava (mais registros, de mais origens, de
  procedência diferente) é evidência de `Parcialmente implementado`, não de `Implementado`: a tela
  existe, mas o estado exigido pelo requisito ainda não foi desenhado;
- registre `Nenhuma evidência encontrada` quando a busca relevante estiver concluída, ou `Evidência
  indisponível: [motivo]` quando não foi possível validar. Nunca invente caminho ou linha.

Ausência de evidência não significa `Implementado`. Use exatamente um destes status por par
(requisito, plataforma):

| Status | Quando usar |
|---|---|
| `Implementado` | A tela ou o fluxo já cobre a capacidade e os estados exigidos pelo requisito no escopo analisado. |
| `Parcialmente implementado` | A tela existe, mas falta um estado, campo, etapa ou variação exigida pelo requisito. |
| `Não encontrado` | A inspeção relevante foi concluída e não encontrou tela ou fluxo para o requisito. |
| `Impossível validar` | A raiz, os arquivos ou a evidência necessários não estavam acessíveis, ou o escopo permaneceu ambíguo. |
| `Não aplicável` | O produto genuinamente não tem essa plataforma no seu escopo. |

Em Greenfield-UI (nenhum código de front-end acessível para a plataforma), classifique sempre como
`Não encontrado`, registrando a ausência de código como motivo; `Impossível validar` é reservado a uma
plataforma que existe mas não pôde ser inspecionada.

`Confiança` qualifica a conclusão (`Alta`, `Média` ou `Baixa`) e não substitui o status.

## Matriz obrigatória

Produza uma linha por par (requisito, plataforma) com faceta de UI.

| Requisito | Plataforma | Evidência `caminho:linha` | Status | Confiança |
|---|---|---|---|---|
| [requisito e origem na spec] | Web \| Mobile | [uma ou mais referências, nenhuma evidência ou motivo da indisponibilidade] | [status exato] | [Alta, Média ou Baixa] |

A matriz é insumo de análise; não decide sozinha o conteúdo do roteiro de tela nem substitui o Card da 3C
do item de design gerado depois pelo backlog.

## Evidência de padrão visual

O que a equipe de UX-UI aproveita de um produto existente é o **padrão**, não o componente. Ao procurar
referência de padrão para o item de design:

- prefira uma **tela equivalente em produção** — um cadastro administrativo existente é referência para
  um cadastro administrativo novo;
- descreva o que encontrou em linguagem de design: o que aparece na tela e em que ordem, onde ficam as
  ações, como o estado de cada registro é comunicado, onde criar e editar acontecem, como a confirmação
  de uma ação destrutiva é pedida, qual é o texto de lista vazia, e a partir de que largura o layout
  quebra ou rola;
- **distinga componente disponível de padrão adotado.** Um componente instalado, importado ou registrado
  no projeto e não usado por nenhuma tela **não é** referência de padrão: registre-o como disponível e
  diga explicitamente que não há precedente visual, porque isso muda o esforço de design;
- registre também a **ausência de precedente** para uma ação que o requisito pressupõe — por exemplo, um
  produto cujas telas administrativas só ativam e inativam, nunca excluem, quando o requisito fala em
  remover. Isso transforma uma ambiguidade do texto em pergunta objetiva;
- não conclua que um padrão cobre o requisito só porque a tela de referência existe: ela informa
  consistência visual, não cobertura funcional.

## Política de geração de item

- `Parcialmente implementado`, `Não encontrado` e `Impossível validar` geram um item de design candidato,
  um por plataforma.
- Necessidade de plataforma não confirmada — a spec não declara a plataforma e o produto não tem nenhum
  precedente daquele tipo de tela nela — não gera item: gera pergunta aberta registrada no item da
  plataforma que tem precedente.
- `Implementado` não gera item — a tela já cobre o requisito naquela plataforma.
- `Não aplicável` não gera item — a plataforma não existe no escopo do produto.

Compare o código somente com a necessidade de tela do requisito da spec: não transforme componente,
decisão técnica ou tela incidental encontrada no código, sem relação com o requisito, em necessidade de
especificação de tela.

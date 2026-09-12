# Design: redação de spec a partir de um pedido informal de negócio

## Contexto

As quatro skills existentes (`refining-user-stories-with-3w`, `refining-user-stories-with-3c`,
`refining-user-stories-with-gherkin`, `generating-azure-boards-backlog-from-spec`) partem de uma
**spec já escrita**. Na prática, a área de negócio frequentemente envia pedidos muito mais informais
— um e-mail ou ticket curto, sem tamanho conhecido de antemão, descrevendo um problema observado sem
detalhar atores, comportamento atual ou critérios de aceite.

Exemplo real que motivou este desenho (aplicação Diligência, SEFAZ-CE):

> P1 - Título: Cancelamento do pre-toaf duplicado
> O sistema está permitindo dois cancelamentos seguidos do mesmo pre-toaf quando o usuário trabalha em
> duas plataformas simultaneamente e esquece de atualizar a página. O sistema deveria emitir erro
> informando que o pre-toaf já está cancelado e, após o fechamento da mensagem, atualizar a página.

Esse texto não é uma spec: não nomeia o ator com precisão, não referencia telas/endpoints, e o
comportamento "atual" só pode ser confirmado lendo o código. As skills existentes já sabem *comparar*
uma spec com uma implementação (modo Brownfield de `generating-azure-boards-backlog-from-spec`), mas
nenhuma delas sabe *descobrir* o requisito quando ele ainda não foi articulado.

Este design cobre uma quinta skill que preenche essa lacuna, sem alterar nenhuma das quatro existentes.

## Objetivos

1. Criar a skill `drafting-a-spec-from-business-request`.
2. Aceitar um pedido de negócio informal, de tamanho desconhecido (e-mail, ticket, trecho de chat),
   como entrada única — nunca fatiada em múltiplos itens.
3. Investigar, em modo somente leitura, o código-fonte presente no(s) repositório(s) irmão(s) de onde a
   skill está instalada, para descobrir vocabulário, atores, comportamento atual e pontos de entrada
   relevantes ao pedido.
4. Produzir um documento de spec em Markdown, salvo em arquivo, compatível com a entrada que
   `generating-azure-boards-backlog-from-spec` já aceita hoje.
5. Preservar a distinção entre o que o pedido afirma, o que o código evidencia e o que continua sendo
   lacuna — sem fabricar ator, regra ou critério de aceite em nenhum dos dois lados.

## Fora de escopo

- Alterar `refining-user-stories-with-3w`, `refining-user-stories-with-3c`,
  `refining-user-stories-with-gherkin` ou `generating-azure-boards-backlog-from-spec`.
- Decompor um pedido com múltiplos itens em specs separadas; todo pedido é tratado como escopo único.
- Encadear automaticamente a geração do backlog após redigir a spec.
- Executar a aplicação, testes, build, migrações ou qualquer script como parte da investigação.
- Exigir que o usuário informe o caminho do repositório: a skill descobre os repositórios a partir de
  onde está instalada.
- Definir Area Path, Iteration Path, Story Points, prioridade, responsável ou datas.

## Contexto de instalação

A skill é instalada dentro do diretório da própria aplicação-alvo, não neste repositório de skills.
Quando essa aplicação é composta por múltiplos repositórios irmãos (caso do Diligência: `diligencia-api`,
`diligencia-front`, `diligencia-mobile`, lado a lado num workspace comum), a skill enxerga todos eles a
partir do seu diretório de instalação. Não há parâmetro de caminho: "a raiz analisada" é o próprio local
onde a skill roda, generalizando o conceito de "raiz analisada" já usado em
`references/brownfield-validation.md` da quarta skill.

## Workflow

1. **Ler o pedido por completo.** Tratar o texto inteiro como uma única unidade de trabalho, mesmo que
   pareça pequeno ou incompleto. Nunca dividir em múltiplos itens.
2. **Descobrir repositórios candidatos.** Listar os diretórios de projeto presentes junto à instalação
   da skill (ex.: irmãos com `pom.xml`, `package.json`, `pubspec.yaml` ou marcadores equivalentes de
   projeto). Registrar, para cada um, se foi considerado relevante ao vocabulário do pedido (nomes de
   entidades, telas, endpoints citados ou implícitos) e por quê — inclusive os descartados.
3. **Investigar somente leitura nos repositórios relevantes**, seguindo as mesmas regras de inspeção
   segura já estabelecidas em `brownfield-validation.md`: `rg`/`rg --files`/`find` para localizar,
   `git status` para estado do repositório, leitura de código/testes/config; nunca executar scripts,
   testes, build, servidores, migrações ou a aplicação sem autorização explícita; nunca alterar nada.
4. **Separar três categorias de conteúdo** ao longo de toda a spec:
   - o que o pedido de negócio afirma (citação ou paráfrase fiel);
   - o que o código evidencia, com `caminho:linha` (mesmo formato de evidência da quarta skill);
   - o que permanece como lacuna ou pergunta em aberto — nunca preenchida por plausibilidade.
   Código existente não cria requisito nem confirma decisão de negócio; ele só descreve o estado atual,
   exatamente como já vale para o modo Brownfield da quarta skill.
5. **Redigir a spec** no template fixo descrito abaixo.
6. **Salvar em arquivo** (`docs/specs/AAAA-MM-DD-<titulo-curto>.md` na aplicação-alvo, ajustável à
   convenção local do projeto onde a skill for instalada) **e parar.** Não invocar
   `generating-azure-boards-backlog-from-spec` nem nenhuma outra skill. Informar ao usuário o caminho do
   arquivo e um resumo das lacunas/perguntas encontradas, para que ele avalie o tamanho real do pedido
   antes de decidir os próximos passos.

## Template da spec gerada

```markdown
# Spec: <título curto>

## Fonte do pedido
Texto original (citado ou anexado) e canal de origem (e-mail, ticket, etc.), sem edição de conteúdo.

## Escopo
Tratado como item único; nenhuma decomposição foi aplicada.

## Repositórios considerados
| Repositório | Relevante? | Motivo |
|---|---|---|
| [nome] | Sim/Não | [justificativa] |

## Problema relatado
Síntese fiel do que o pedido descreve, sem inferências.

## Comportamento atual (evidência no código)
| Afirmação/observação | Evidência `caminho:linha` | Confiança |
|---|---|---|
| ... | ... | Alta/Média/Baixa |

Usar `Nenhuma evidência encontrada` ou `Evidência indisponível: [motivo]` quando aplicável — nunca
inventar caminho ou linha.

## Comportamento esperado
- Afirmado explicitamente pelo pedido: ...
- Inferido (marcado como inferência, não fato confirmado): ...

## Atores e vocabulário identificados no código
Lista de atores, entidades e termos de domínio encontrados, com evidência.

## Lacunas e perguntas abertas
Tudo que não pôde ser confirmado nem pelo pedido nem pelo código.
```

Esse template não inclui Épico/Feature/História, `Description` nem `Acceptance Criteria`: essas
estruturas continuam sendo responsabilidade exclusiva de `generating-azure-boards-backlog-from-spec` e
da 3C, quando o usuário decidir rodar esse fluxo sobre o arquivo gerado.

## Arquitetura de skills

```text
drafting-a-spec-from-business-request   (nova, independente)
        |
        | (arquivo de spec, uso manual pelo usuário)
        v
generating-azure-boards-backlog-from-spec   (inalterada)
  -> refining-user-stories-with-3c            (inalterada)
       -> refining-user-stories-with-3w       (inalterada)
       -> refining-user-stories-with-gherkin  (inalterada)
```

A nova skill não é chamada por nenhuma das quatro existentes, e não chama nenhuma delas. A ligação entre
as duas metades do fluxo é o arquivo Markdown que o usuário revisa e decide usar — não uma chamada
automática.

## Arquivos previstos

```text
drafting-a-spec-from-business-request/
├── SKILL.md
├── agents/openai.yaml
└── references/business-request-investigation.md
```

Nenhum arquivo das quatro skills existentes é criado, removido ou modificado.

## Tratamento de lacunas e conflitos

- Pedido de negócio é evidência de intenção, não uma decisão confirmada de todos os detalhes; ausência
  de ator, regra ou critério permanece como lacuna explícita, nunca preenchida por plausibilidade.
- Código existente não substitui nem contradiz o pedido de negócio; quando os dois divergem, registrar
  ambas as leituras na seção de Lacunas e perguntas abertas.
- Se nenhum repositório relevante for encontrado, registrar essa ausência e prosseguir com uma spec
  baseada somente no pedido (comportamento equivalente ao modo Greenfield da quarta skill), sem travar
  a entrega do documento.

## Estratégia de testes

1. Teste estático (seguindo o padrão de `test_skill_integration.py`): garantir que
   `drafting-a-spec-from-business-request/SKILL.md` não invoca nenhuma das quatro skills existentes por
   nome, e que nenhuma das quatro skills existentes referencia a nova skill — mantendo o grafo acíclico
   e a nova skill como predecessora isolada.
2. `quick_validate.py` executado sobre o novo diretório de skill, no mesmo laço já usado para as outras
   quatro no README.
3. Cenário manual de aceite: aplicar a skill ao exemplo real do pre-toaf duplicado contra o repositório
   Diligência e revisar se a spec resultante separa corretamente afirmação do pedido, evidência de
   código e lacunas, sem fabricar critério de aceite.

Como a skill não introduz script determinístico próprio (não há um `validate_*.py` equivalente ao da
quarta skill), a qualidade da investigação e da redação fica sujeita a self-review da spec gerada e à
revisão humana do arquivo, não a um gate automatizado.

## Atualização (2026-09-12) — sugestão explícita de `interviewing-request-gaps` ao final do fluxo

Além da referência condicional já registrada em `interviewing-request-gaps-design.md` (usar essa skill,
se instalada, para fechar lacunas antes de salvar), o passo final do Fluxo agora também informa
explicitamente ao usuário — quando a spec salva ainda tiver itens em `## Lacunas e perguntas abertas` —
que o próximo passo manual é rodar `interviewing-request-gaps` (quando instalada), antes de a spec
seguir para `generating-azure-boards-backlog-from-spec`. É o mesmo padrão de sugestão de próximo passo
usado por `superpowers:brainstorming` ao final de um design aprovado, e não uma invocação automática:
esta skill continua parando após salvar o arquivo, sem encadear nenhuma outra skill além da exceção já
prevista no passo anterior.

## Critérios de conclusão

- A nova skill existe, com `SKILL.md`, `agents/openai.yaml` e a referência de investigação.
- Nenhuma das quatro skills existentes foi alterada.
- O teste estático de isolamento do grafo acíclico passa.
- `quick_validate.py` passa para o novo diretório.
- O template de spec gerado distingue claramente pedido, evidência de código e lacunas, e não inclui
  Épico/Feature/História nem Acceptance Criteria.
- Aplicado ao exemplo do pre-toaf duplicado, o documento produzido é utilizável como entrada de
  `generating-azure-boards-backlog-from-spec` sem exigir reescrita manual da estrutura.

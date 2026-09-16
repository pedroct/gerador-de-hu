# Especificação de endurecimento do publicador de backlog no Azure Boards

## Contexto

A implementação prevista em `2026-09-15-publicar-backlog-azure-boards.md` foi concluída em
`634dbbb`, mas a revisão final identificou quatro falhas de integração que impedem o merge seguro:

- o cliente recebido pelo executor pode apontar para um destino diferente do plano autorizado;
- o estado interno `_confirmada` pode ser injetado por construção direta de `Autorizacao`;
- algumas respostas REST ambíguas não preservam a necessidade de reconciliação manual;
- a validação estrutural depende de um arquivo externo ao pacote instalado.

O `pip-audit` também reportou vulnerabilidades transitivas de desenvolvimento. Elas precisam de
triagem rastreável, mas não devem ser ocultadas por exclusões silenciosas.

## Objetivo

Tornar o publicador seguro para merge e operação local, garantindo que nenhuma chamada de criação
ocorra fora do plano explicitamente confirmado e que qualquer resultado incerto exija reconciliação
manual antes de nova escrita.

## Fora de escopo

- Publicação real em um projeto Azure DevOps de produção.
- Idempotência inventada no Azure DevOps ou reconciliação automática por heurística.
- Exclusão, rollback ou atualização automática de work items.
- Migração para FastAPI, banco de dados ou interface web.
- Supressão indiscriminada de vulnerabilidades do `pip-audit`.
- Alteração do contrato Markdown produzido pela skill geradora.

## Restrições globais

- Conteúdo criado em português brasileiro.
- REST continua sendo o único caminho de escrita; MCP permanece opcional e somente para inspeção.
- Não usar `--yes`, confirmação implícita, `bypassRules=true` ou publicação por existência de manifesto.
- Testes padrão nunca criam work items reais.
- O token nunca aparece em logs, mensagens, exceções, planos ou manifesto.
- Timeout de uma criação não deve ser repetido automaticamente sem mecanismo de idempotência comprovado.

## Decisões de arquitetura

### Autorização vinculada ao plano

`Autorizacao` será criada somente por uma fábrica que receba o plano e a confirmação digitada.
O estado de confirmação não será aceito como argumento público da dataclass. O objeto deverá
carregar uma impressão imutável da autorização contendo, no mínimo:

- hash do plano;
- quantidade autorizada;
- modalidade (`INTEIRO` ou `LOTES`);
- conjunto de chaves autorizadas;
- identidade completa do destino: organização, projeto, Area Path, Iteration Path e mapeamento
  de tipos remotos;
- resumo criptográfico do conteúdo das operações autorizadas.

O executor deverá validar a autorização contra o plano recebido e contra a configuração do cliente
antes da primeira chamada de criação. Manifesto vazio não é exceção a essa validação. Divergência
encerra a execução sem chamadas de escrita.

Na modalidade por lotes, uma autorização só poderá percorrer o conjunto de chaves daquele lote.
Cada lote exigirá uma nova autorização.

### Reconciliação de resultado incerto

Falha de rede após o envio, timeout, resposta 2xx incompleta ou resposta com URL inválida serão
classificados como `ErroCriacaoAmbigua`. O executor deverá:

1. preservar um registro de reconciliação local antes ou durante a tentativa, sem marcá-lo como criado;
2. impedir nova criação para aquela chave enquanto o registro estiver pendente;
3. informar o item e o destino sem expor o token;
4. exigir ação manual explícita para limpar ou resolver o estado;
5. nunca tentar descobrir ou atualizar automaticamente um work item.

Erros determinísticos de autenticação, permissão, destino, tipo ou payload inválido continuam sendo
falhas permanentes e não devem ser convertidos em sucesso.

### Validação estrutural isolável

O validador do contrato Markdown será transformado em dependência empacotável do publicador ou sua
lógica será extraída para um módulo compartilhado incluído no wheel. A execução instalada não poderá
depender de `../gerar-backlog-azure-boards` existir no filesystem.

O comportamento deverá manter as regras do validador existente, incluindo origem, `Refinement Status`,
Card, Conversation, hierarquia, campos obrigatórios e headings válidos. A CLI deve chamar essa
validação antes de criar plano, autorização ou cliente de escrita.

### Destino e cliente

O cliente deve receber a mesma `ConfiguracaoPublicacao` usada para gerar o plano, ou rejeitar
explicitamente qualquer configuração diferente. A URL de criação continuará usando
`/workitems/$<tipo-remoto>` e os caminhos de classificação serão comparados usando a representação
oficial retornada pela API, distinguindo nome, caminho completo, URL e tipo de nó.

## Fluxo esperado

```text
Markdown
  → validador empacotado
  → interpretação
  → plano completo e hash
  → manifesto validado
  → cliente com destino idêntico ao plano
  → verificação somente leitura
  → resumo e confirmação exata
  → validação final da autorização
  → criação do lote autorizado
  → manifesto ou reconciliação pendente
```

Simulação deve executar somente validação e planejamento local, sem token e sem cliente HTTP.
`--validar-apenas` pode criar o cliente e fazer leituras remotas, mas nunca solicita autorização nem
faz POST de criação.

## Segurança de credenciais

Variáveis de ambiente e arquivo `.env` continuam aceitos. Quando o token for solicitado, a entrada
deve usar mecanismo sem eco, como `getpass`, e a exceção de fallback deve ser tratada sem imprimir o
valor. Testes devem substituir o prompt por uma função injetável, sem capturar ou persistir segredo.

## Dependências e auditoria

O relatório de `pip-audit` deverá registrar cada identificador, pacote afetado, caminho transitivo,
se afeta produção ou somente desenvolvimento, versão corretiva disponível e decisão tomada. Cada
vulnerabilidade deverá ser corrigida, removida por atualização compatível ou aceita temporariamente
com justificativa e responsável. O comando não poderá ser mascarado por `|| true`.

## Testes de aceitação

### Autorização e destino

- Construção direta não consegue definir autorização confirmada.
- Plano com quantidade, destino, mapeamento ou conteúdo diferente é rejeitado.
- Cliente configurado para outro projeto é rejeitado mesmo com manifesto vazio.
- Lote só cria chaves pertencentes ao lote autorizado.
- Confirmação ausente, parcial, com newline interno ou incorreta gera zero POST.

### REST e reconciliação

- Criação usa `/workitems/$Epic` ou o tipo remoto configurado.
- Respostas 2xx sem ID, URL, URL HTTPS válida ou com URL malformada geram reconciliação pendente.
- Timeout após envio não provoca segunda tentativa automática.
- Estado pendente bloqueia nova criação até resolução manual.
- `401`, `403`, `404`, `409` e erros transitórios mantêm os tipos de erro documentados.

### Empacotamento e CLI

- Instalação normal do wheel consegue validar um backlog sem acessar diretórios irmãos.
- O entry point instalado executa a CLI real.
- Simulação funciona sem token e sem chamadas HTTP.
- Validação estrutural rejeita fixture inválida antes do planejamento.
- Testes padrão permanecem totalmente simulados.

### Qualidade

- `pytest`, `ruff check`, `ruff format --check`, `mypy`, `bandit` e `semgrep` passam.
- `pip-audit` passa ou possui relatório de exceções individualizadas e aprovado.
- Nenhum token aparece em saída, logs, exceções, manifesto ou arquivos versionados.

## Critério de conclusão

A spec será considerada implementada quando todos os testes de aceitação passarem, o pacote instalado
for isolável, a revisão final não encontrar escrita fora da autorização e o `pip-audit` tiver resultado
passante ou exceções individualmente justificadas e registradas.

## Relação com o plano anterior

Esta especificação é uma correção subsequente e não reabre silenciosamente as oito tarefas originais.
Ela deve ter um plano próprio, com tarefas de implementação, revisão por tarefa e uma nova revisão
ampla antes de qualquer merge ou publicação.

# Publicador de backlog vinculado a uma Demanda de Negócio

Executor Python isolável para validar, planejar e publicar um backlog Markdown no Azure Boards
**pendurado em uma Demanda de Negócio que já existe**, informada por ID. Publicar é uma operação de
escrita: a ferramenta exige uma autorização textual exata para o plano apresentado e não oferece
confirmação implícita.

O resultado no board é este:

```text
Demanda de Negócio #13959
└─ [Epic]        01 Gestão do projeto
   └─ [Feature]  01.01 Gestão do projeto
      └─ [Story] 01.01.01 Análise de padrões de stacks
```

A Demanda em si **nunca é escrita**: o vínculo nasce do lado do Épico, via
`System.LinkTypes.Hierarchy-Reverse`, no mesmo POST que cria o Épico.

## Pré-requisitos

- Python 3.12 ou superior;
- [`uv`](https://docs.astral.sh/uv/);
- uma credencial do Azure DevOps fornecida pelo ambiente ou por um mecanismo seguro local.

No diretório `publicar-backlog-demanda-azure-boards`, instale/resolva o ambiente com:

```bash
uv lock
```

Segredos não devem ser versionados. Copie `.env.example` para `.env` apenas localmente e preencha
os valores necessários.

O token solicitado interativamente é lido sem eco; nunca o informe em argumentos, arquivos
versionados, planos, manifestos, logs ou mensagens de erro.

## Configuração por execução

A precedência é: argumentos da CLI, arquivo TOML passado por `--config`, arquivo `.env` passado por
`--env-file` e perguntas interativas. Quando não estiver configurado, o token é solicitado sem eco
no terminal. Ele não aparece no plano, no manifesto, em logs ou em mensagens de erro.

```dotenv
AZURE_DEVOPS_ORGANIZACAO=organizacao
AZURE_DEVOPS_PROJETO=Projeto
AZURE_DEVOPS_DEMANDA=13959
AZURE_DEVOPS_TIPO_DEMANDA=Demanda de Negócio
AZURE_DEVOPS_TIPO_USER_STORY=User Story
AZURE_DEVOPS_TOKEN=
```

**Não existe configuração de `Area Path` nem de `Iteration Path`.** Os dois são herdados da Demanda:
publicar sob uma Demanda significa publicar onde ela está. Caminhos relativos devolvidos pela API
continuam sendo normalizados com o nome do projeto antes do plano e da validação remota, e ambos
aparecem no plano marcados como herdados, validados remotamente antes da autorização.

O ID da Demanda participa do hash do plano, da frase de autorização e do manifesto. Uma frase
emitida para uma Demanda não autoriza publicar sob outra, e um manifesto de uma Demanda não retoma
sob outra.

Em projetos Scrum, mapeie o tipo documental sem alterar o backlog:

```dotenv
AZURE_DEVOPS_TIPO_USER_STORY=Product Backlog Item
```

O mapeamento remoto aparece no plano, integra o payload e também participa do hash autorizado.

## Fluxo operacional

Valide primeiro o contrato Markdown. O publicador embarca sua própria cópia das regras do contrato
estrutural, no módulo `contrato_backlog.py`; a CLI executa essa cópia antes do interpretador e do
planejamento, sem depender de `gerar-backlog-azure-boards` em tempo de execução. Essa cópia precisa
ser ressincronizada manualmente se as regras da skill geradora
(`gerar-backlog-azure-boards/scripts/validate_backlog.py`) mudarem — não há sincronização
automática:

```bash
uv run python scripts/publicar_backlog_demanda.py validar backlog.md
```

Para revisar o plano sem chamadas remotas:

```bash
uv run python scripts/publicar_backlog_demanda.py planejar backlog.md --demanda 13959
```

O plano apresenta a Demanda de origem, organização, projeto, `Area Path`, `Iteration Path`,
mapeamento de tipos, quantidades, tipos, ordem
`Epic → Feature → User Story/Bug`, relações pai-filho, manifesto e hash. O hash vincula a
confirmação ao backlog, ao destino e aos tipos remotos. A autorização também registra a quantidade,
o conteúdo executável e o conjunto pendente ou a faixa do lote; qualquer divergência é recusada
novamente pelo executor antes da escrita.

Antes de solicitar autorização, `publicar` faz a verificação preliminar somente leitura: credencial,
destino, tipos, campos, relação hierárquica, Area Path, Iteration Path e consistência do manifesto.
Os Épicos são validados com a Demanda como pai, para que `--validar-apenas` exercite o vínculo em
vez de conferir um Épico órfão. Use:

```bash
uv run python scripts/publicar_backlog_demanda.py publicar backlog.md --demanda 13959 \
  --manifesto manifesto-publicacao.json
```

A confirmação pode autorizar o backlog inteiro ou lotes. Para lotes, cada tamanho e cada conjunto
são reapresentados e exigem uma frase própria. A frase deve ser digitada exatamente, por exemplo:

```text
AUTORIZAR PUBLICAÇÃO 12 ITENS DEMANDA 13959 Projeto Projeto Projeto\\Sprint 18 7F3A
AUTORIZAR LOTE 2 4 ITENS DEMANDA 13959 Projeto Projeto Projeto\\Sprint 18 B91C
```

A comparação é exata, inclusive maiúsculas e minúsculas. Uma confirmação incorreta permite até 3
tentativas na mesma execução antes de cancelar, com um aviso a cada erro; confirmação ausente
(entrada encerrada) cancela imediatamente. Confirmação ausente, vaga, incorreta ou ligada a outro
hash resulta em zero chamadas de criação. Não existe opção `--yes`, variável de ambiente de
confirmação nem autorização concedida pela existência do manifesto.

## Modos sem publicação

`--simulacao` interpreta, valida localmente, lê a Demanda, monta e mostra o plano, sem pedir
autorização e sem criar work item algum. `--validar-apenas` executa a verificação remota das
operações usando `validateOnly=true`, sem solicitar autorização e sem criar work items.

**A simulação deixou de ser offline e exige token.** Como `Area Path` e `Iteration Path` vêm da
Demanda, não há como montar o plano — nem o hash — sem ler o work item. O que ela preserva é o
resto: exatamente um `GET`, nenhuma escrita e nenhuma autorização solicitada. O comando `validar`
continua totalmente local e sem token, para quem só quer conferir o documento.

`--validar-apenas` pode fazer somente as consultas remotas necessárias para verificar destino,
tipos, campos, relações e caminhos; a validação das operações usa `validateOnly=true` e não envia
POST persistente.

## Manifesto, falha parcial e retomada

O manifesto é apenas um registro de correlação e prevenção de duplicidade; ele nunca concede
autorização. Na retomada, seus registros são comparados primeiro com o backlog completo; só depois
os itens já publicados são removidos do conjunto pendente. Antes de cada POST, o manifesto recebe
atomicamente um marcador de criação em andamento. Depois do sucesso, esse marcador é substituído
pela chave documental, ID, tipo, URL, título, hash e destino.

Se uma criação falhar de forma definitiva, os itens já registrados são preservados e a execução
para sem rollback, exclusão ou atualização automática. Timeout, erro de rede, resposta transitória
ou resposta de criação sem identidade são ambíguos: o POST nunca é repetido e o marcador bloqueia
qualquer nova escrita. Confira manualmente o Azure Boards e reconcilie o manifesto antes de tentar
novamente. Uma retomada exige nova autorização; divergência de hash, destino, tipo ou título também
interrompe o fluxo para revisão manual.

reconciliação manual é obrigatória após qualquer criação ambígua: compare a chave documental, o
título, o tipo, o destino e o ID no Azure Boards com o marcador do manifesto. Só depois de corrigir
o manifesto e obter nova autorização vinculada ao plano a retomada pode continuar.

Uma reconciliação pendente (`resolucao: "pendente"`) só pode ser encerrada com um dos dois estados
terminais abaixo — não existe um estado genérico `"resolvida"`. Cada um exige uma consistência
específica com `manifesto.itens`, e `validar_manifesto` rejeita o manifesto (sem criar nada) quando
essa consistência não é respeitada:

- `resolvida_criada`: use quando a conferência no Azure Boards confirmou que o item **existe**. A
  chave precisa estar presente em `manifesto.itens` com o `id`, `tipo`, `título` e `url` reais do
  item encontrado; se a chave estiver ausente de `itens`, a validação falha.
- `resolvida_nao_criada`: use quando a conferência confirmou que o item **não existe** no Azure
  Boards. A chave precisa continuar ausente de `manifesto.itens`; se a chave estiver presente em
  `itens`, a validação falha.

Marcar `resolvida_criada` sem também adicionar a chave a `itens` (ou vice-versa) deixaria a próxima
execução livre para recriar um item já existente ou esconder um item nunca criado; por isso o
operador deve sempre atualizar `itens` e `resolucao` juntos antes de retomar a publicação.

## REST e MCP

A publicação usa obrigatoriamente a REST API do Azure DevOps. Isso mantém a ordem hierárquica, o
hash, a autorização por lote, o manifesto, as tentativas limitadas para leituras e o tratamento
determinístico de falhas.

O MCP do Azure DevOps é opcional e pode apoiar inspeção interativa de tipos, campos e caminhos. Sua
ausência não impede a CLI, e ele não substitui a REST API nem autoriza publicações.

## Títulos publicados

Os títulos seguem a numeração hierárquica praticada no board, sem prefixo de data:

| Tipo | Chave documental | Título publicado |
|---|---|---|
| Epic | `1.0.0` | `01 Gestão do projeto` |
| Feature | `1.1.0` | `01.01 Gestão do projeto` |
| User Story / Bug | `1.1.1` | `01.01.01 Análise de padrões de stacks` |

A data de geração sai do título, mas continua sendo lida do Markdown, exibida no plano e incluída no
hash: é ela que distingue duas gerações do mesmo backlog e impede que uma autorização antiga valha
para um documento regerado.

Não existe nível Task: a hierarquia publicada vai de Épico a História ou Bug.

## Desenvolvimento e verificações

```bash
uv run pytest -q
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv run bandit -r src
uv run pip-audit
```

Os testes padrão usam respostas e clientes simulados; não criam work items reais. O arquivo
`Implementation Evidence` do backlog não é enviado ao Azure Boards.

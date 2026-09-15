# Publicador de backlog no Azure Boards

Executor Python isolável para validar, planejar e publicar um backlog Markdown no Azure Boards.
Publicar é uma operação de escrita: a ferramenta exige uma autorização textual exata para o plano
apresentado e não oferece confirmação implícita.

## Pré-requisitos

- Python 3.12 ou superior;
- [`uv`](https://docs.astral.sh/uv/);
- uma credencial do Azure DevOps fornecida pelo ambiente ou por um mecanismo seguro local.

No diretório `publicar-backlog-azure-boards`, instale/resolva o ambiente com:

```bash
uv lock
```

Segredos não devem ser versionados. Copie `.env.example` para `.env` apenas localmente e preencha
os valores necessários.

## Configuração por execução

A precedência é: argumentos da CLI, arquivo TOML passado por `--config`, arquivo `.env` passado por
`--env-file` e perguntas interativas. O token é lido como segredo e não aparece no plano, no
manifesto, em logs ou em mensagens de erro.

```dotenv
AZURE_DEVOPS_ORGANIZACAO=organizacao
AZURE_DEVOPS_PROJETO=Projeto
AZURE_DEVOPS_AREA_PATHS=Sustentacao,Projeto
AZURE_DEVOPS_AREA_PATH=Projeto
AZURE_DEVOPS_ITERATION_PATH=Projeto\\Sprint 2026\\Sprint 18
AZURE_DEVOPS_TOKEN=
```

O projeto disponibiliza os Area Paths `Sustentacao` e `Projeto`. Se `AZURE_DEVOPS_AREA_PATH` ou
`--area-path` não for informado quando houver mais de uma opção, a ferramenta exige uma seleção
explícita; ela nunca escolhe silenciosamente. O `Iteration Path` muda por sprint e precisa ser
informado em cada execução, por `--iteration-path`, `.env` atualizado ou pergunta interativa.
Ambos os caminhos são mostrados no plano e validados remotamente antes da autorização.

## Fluxo operacional

Valide primeiro o contrato Markdown:

```bash
uv run python scripts/publicar_backlog.py validar backlog.md
```

Para revisar o plano sem chamadas remotas:

```bash
uv run python scripts/publicar_backlog.py planejar backlog.md \
  --area-path Projeto \
  --iteration-path 'Projeto\\Sprint 2026\\Sprint 18'
```

O plano apresenta organização, projeto, `Area Path`, `Iteration Path`, quantidades, tipos, ordem
`Epic → Feature → User Story/Bug`, relações pai-filho, manifesto e hash. O hash vincula a
confirmação ao backlog e ao destino; mudar qualquer um deles exige um novo plano e uma nova
autorização.

Antes de solicitar autorização, `publicar` faz a verificação preliminar somente leitura: credencial,
destino, tipos, campos, relação hierárquica, Area Path, Iteration Path e consistência do manifesto.
Use:

```bash
uv run python scripts/publicar_backlog.py publicar backlog.md \
  --manifesto manifesto-publicacao.json
```

A confirmação pode autorizar o backlog inteiro ou lotes. Para lotes, cada tamanho e cada conjunto
são reapresentados e exigem uma frase própria. A frase deve ser digitada exatamente, por exemplo:

```text
AUTORIZAR PUBLICAÇÃO 12 ITENS Projeto Projeto Projeto\\Sprint 2026\\Sprint 18 7F3A
AUTORIZAR LOTE 2 4 ITENS Projeto Projeto Projeto\\Sprint 2026\\Sprint 18 B91C
```

Confirmação ausente, vaga, incorreta ou ligada a outro hash resulta em zero chamadas de criação.
Não existe opção `--yes`, variável de ambiente de confirmação nem autorização concedida pela
existência do manifesto.

## Modos sem publicação

`--simulacao` interpreta, valida localmente, monta e mostra o plano sem chamadas HTTP e sem pedir
autorização. `--validar-apenas` executa a verificação remota das operações usando
`validateOnly=true`, sem solicitar autorização e sem criar work items.

## Manifesto, falha parcial e retomada

O manifesto é apenas um registro de correlação e prevenção de duplicidade; ele nunca concede
autorização. Depois de cada criação bem-sucedida, o arquivo é gravado atomicamente com a chave
documental, ID, tipo, URL, título, hash e destino.

Se uma criação falhar, os itens já registrados são preservados e a execução para sem rollback,
exclusão ou atualização automática. Para retomar, corrija a causa, mantenha o backlog e o destino
compatíveis, execute novamente e forneça uma nova autorização. Itens registrados e validados são
ignorados; divergência de hash, destino, tipo ou título interrompe a execução para revisão manual.

## REST e MCP

A publicação usa obrigatoriamente a REST API do Azure DevOps. Isso mantém a ordem hierárquica, o
hash, a autorização por lote, o manifesto, as tentativas limitadas para leituras e o tratamento
determinístico de falhas.

O MCP do Azure DevOps é opcional e pode apoiar inspeção interativa de tipos, campos e caminhos. Sua
ausência não impede a CLI, e ele não substitui a REST API nem autoriza publicações.

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

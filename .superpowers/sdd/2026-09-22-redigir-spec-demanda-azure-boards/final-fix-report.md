# Relatório da fix wave final

## Status

Concluída, sem consulta ao Azure Boards, sem uso do ID fornecido pelo usuário e sem expansão de
escopo. O leitor continua restrito a operações `GET`, e o conteúdo criado permanece em português
brasileiro.

## Correções

- `principal()` agora comunica a categoria pública do erro e, no erro de contrato, o nome exato do
  campo remoto ausente, inclusive campos `Custom...`. A mensagem interna da exceção, detalhes da
  resposta externa e token não são repassados à saída da CLI.
- Lista vazia em campo customizado opcional é mapeada para `None`, que a saída JSON serializa como
  `null`. Inteiros, listas não vazias e demais tipos não textuais continuam rejeitados.
- A matriz de configuração cobre a precedência argumento, tabela `[azure_devops]` no TOML, `.env` e
  ambiente.
- O teste estático verifica a ordem da investigação, os gatilhos das skills especializadas e o
  tratamento de lacunas.
- O README usa `pytest` em todos os comandos de validação das skills.

## Verificações

- Testes focados: `38 passed`.
- Suíte completa: `137 passed`.
- `quick_validate.py`: `Skill is valid!`.
- `git diff --check`: passou.
- `ruff` nos arquivos alterados: passou.

## Preocupações conhecidas

`uv run ruff check .` ainda reporta cinco achados preexistentes em testes de outras skills; eles estão
fora do escopo desta wave e não foram alterados. Não foi feita validação de integração contra um Azure
Boards real, conforme solicitado.

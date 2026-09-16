# Relatório — Task 2: Fechar reconciliação de resultados incertos

## Resultado

A reconciliação de criações ambíguas agora é persistível e bloqueia novas escritas até uma
resolução manual explícita. O cliente classifica URL malformada, resposta 2xx sem identidade,
falha de transporte após o envio e resposta bem-sucedida inválida como `ErroCriacaoAmbigua`, sem
repetir o POST.

O marcador é gravado atomicamente antes da criação e contém chave, destino completo, tipo
documental, tipo remoto, título, hash do plano, timestamp UTC, motivo e resolução `pendente`. O
manifesto expõe o mapa `reconciliacoes` e mantém compatibilidade de leitura com o campo singular
`reconciliacao_pendente` usado pelo formato anterior. A presença de qualquer reconciliação pendente
levanta `ErroReconciliacaoPendente` antes de uma nova criação; essa exceção também é compatível
com `ReconciliacaoManualNecessaria`.

## Ciclos RED/GREEN

### Baseline

Comando:

```text
cd publicar-backlog-azure-boards && uv run pytest tests/test_cliente_azure_devops.py tests/test_manifesto.py tests/test_executar_publicacao.py -q
```

Saída:

```text
38 passed in 0.11s
```

O baseline já continha parte da proteção de reconciliação, mas ainda não cobria URL malformada nem
o contrato rico do novo mapa.

### RED

Foram adicionadas regressões para URL malformada, round-trip do contexto completo, exposição do
mapa novo e bloqueio com a exceção específica. A primeira execução falhou na coleta porque
`ErroReconciliacaoPendente` ainda não existia no manifesto:

```text
2 errors during collection
ImportError: cannot import name 'ErroReconciliacaoPendente'
```

Com a exceção disponível, a regressão da URL também reproduzia o problema de `urlparse` deixar
escapar `ValueError` antes da classificação como ambiguidade.

### GREEN

Após implementar o modelo, a persistência compatível, a captura de exceções e o marcador completo:

```text
cd publicar-backlog-azure-boards && uv run pytest tests/test_cliente_azure_devops.py tests/test_manifesto.py tests/test_executar_publicacao.py -q
43 passed in 0.11s
```

## Arquivos alterados

- `publicar-backlog-azure-boards/src/publicar_backlog_azure_boards/modelos.py`: adiciona o modelo
  imutável `ReconciliacaoPendente` com contexto operacional e estado de resolução.
- `publicar-backlog-azure-boards/src/publicar_backlog_azure_boards/manifesto.py`: serializa e
  converte reconciliações completas, normaliza o mapa novo com o campo legado e bloqueia estados
  pendentes com erro específico.
- `publicar-backlog-azure-boards/src/publicar_backlog_azure_boards/cliente_azure_devops.py`:
  captura `ValueError`/`UnicodeError` na validação de identidade e URL, mantendo POST sem retry.
- `publicar-backlog-azure-boards/src/publicar_backlog_azure_boards/executar_publicacao.py`: grava
  marcador completo antes do POST e remove somente a chave confirmada após persistir o sucesso.
- `publicar-backlog-azure-boards/tests/test_cliente_azure_devops.py`: regressão para URL HTTPS
  malformada e garantia de uma única chamada.
- `publicar-backlog-azure-boards/tests/test_manifesto.py`: cobertura de round-trip, metadados,
  compatibilidade legada e formato da exceção.
- `publicar-backlog-azure-boards/tests/test_executar_publicacao.py`: cobertura de marcador
  completo e bloqueio sem novas criações.

## Verificações finais

```text
uv run pytest -q
91 passed in 0.20s

uv run ruff check .
All checks passed!

uv run ruff format --check .
22 files already formatted

uv run mypy src
Success: no issues found in 12 source files

uv run bandit -r src
No issues identified.

git diff --check
saída vazia; sem erros de espaço em branco
```

## Autorrevisão

- Confirmei que o marcador é persistido antes de qualquer chamada de criação e que a gravação usa
  o caminho atômico já existente.
- Confirmei que respostas 2xx sem identidade, URL não HTTPS, URL malformada e falhas de transporte
  não geram registro de item criado.
- Confirmei que POST continua com uma única tentativa; somente leituras GET usam retry.
- Confirmei que estado pendente impede qualquer nova criação antes de consultar ou alterar itens.
- Confirmei que o manifesto não serializa token e que o teste de round-trip não encontra `token` no
  JSON persistido.
- Mantive compatibilidade com o campo singular legado e não alterei o diretório não rastreado
  preexistente `graphify-out/`.
- Não despachei subagentes nem revisores, conforme solicitado.

## Preocupações

Não há bloqueadores conhecidos. A resolução não foi automatizada de propósito: o estado pendente
deve ser conferido no Azure Boards e limpo por uma operação manual explícita fora do fluxo de
publicação. O formato continua aceitando registros legados com metadados ausentes para permitir
leitura e migração segura; marcadores criados pelo executor sempre recebem o contexto completo.

## Adendo — fix round 1

### Achados tratados

- `EstadoReconciliacao` agora limita a resolução a `pendente` e `resolvida`. O modelo rejeita
  valores desconhecidos, impedindo que typos sejam interpretados como resolução e liberem POST.
  O fluxo automático só grava `pendente`; `resolvida` continua sendo uma decisão manual explícita.
- Entradas do mapa novo `reconciliacoes` exigem destino interno completo e falham quando `destino`
  está ausente ou é `null`. A compatibilidade sem destino ficou restrita ao campo legado
  `reconciliacao_pendente`, claramente identificado.

### RED

Comando:

```text
cd publicar-backlog-azure-boards && uv run pytest tests/test_manifesto.py tests/test_executar_publicacao.py -q
```

Saída:

```text
3 failed, 16 passed in 0.13s
```

As falhas cobriram o estado desconhecido e os dois formatos de destino ausente/nulo no mapa novo.

### GREEN e verificação

Teste focado solicitado:

```text
cd publicar-backlog-azure-boards && uv run pytest tests/test_cliente_azure_devops.py tests/test_manifesto.py tests/test_executar_publicacao.py -q
47 passed in 0.12s
```

Suíte completa:

```text
uv run pytest -q
95 passed in 0.27s
```

Verificações adicionais após o fix:

```text
uv run ruff check .
All checks passed!

uv run ruff format --check .
22 files already formatted

uv run mypy src
Success: no issues found in 12 source files

uv run bandit -r src
No issues identified.

git diff --check
saída vazia; sem erros de espaço em branco
```

## Re-revisão — correção da Task 2

Escopo limitado aos três critérios solicitados. Não executei testes, não alterei código e não
despachei agentes.

### 1. Estados desconhecidos não liberam POST — ADDRESSED

- `modelos.py:101-109`: `ReconciliacaoPendente.__post_init__` rejeita qualquer resolução fora de
  `pendente` e `resolvida`.
- `manifesto.py:78-82` e `manifesto.py:134-143`: o manifesto só considera `pendente` como
  liberador de bloqueio; `executar_publicacao.py:73-74` chama essa validação antes do loop que faz
  o POST em `executar_publicacao.py:111`.

Assim, um estado desconhecido não chega ao caminho de criação.

### 2. Reconciliação nova exige destino — NOT ADDRESSED

- `manifesto.py:58-68` só rejeita entradas sem destino quando
  `reconciliacao_pendente is None`. Uma construção direta com uma entrada nova em
  `reconciliacoes` sem destino e um campo legado singular preenchido contorna essa validação.
- A leitura JSON do mapa novo está protegida em `manifesto.py:298-305` e `manifesto.py:336-344`,
  mas a invariável não é garantida no modelo `Manifesto` para todos os estados em memória.

### 3. Não há nova quebra — NOT ADDRESSED

- `manifesto.py:87-88` normaliza uma reconciliação legada `resolvida` para
  `reconciliacao_pendente = None`.
- Depois, `manifesto.py:174-177` exclui do mapa qualquer reconciliação sem destino. Portanto, ao
  gravar um manifesto legado já resolvido (sem destino), a entrada é perdida; antes desta correção,
  o mapa era serializado sem esse filtro (`reconciliacoes` era emitido integralmente).

Esse é um novo risco de perda de estado de formato legado, ainda que reconciliações legadas
pendentes continuem preservadas pelo campo singular.

## Adendo — correção da re-revisão

### Achados tratados

- A validação de `Manifesto` agora exige destino completo para toda entrada fornecida no mapa novo
  `reconciliacoes`, mesmo quando o manifesto também contém o campo legado singular.
- O campo legado singular é preservado exatamente quando contém uma reconciliação `resolvida`;
  somente um alias ausente é preenchido a partir de uma pendência do mapa. Assim, registros legados
  resolvidos sem destino continuam presentes no round-trip e não são convertidos em pendentes.

### RED

Comando:

```text
cd publicar-backlog-azure-boards && uv run pytest tests/test_manifesto.py tests/test_executar_publicacao.py -q
```

Saída:

```text
2 failed, 19 passed in 0.14s
```

As falhas reproduziram a aceitação indevida de uma entrada nova sem destino junto de um registro
legado e a perda de uma reconciliação legada resolvida durante o round-trip.

### GREEN

Teste focado solicitado:

```text
cd publicar-backlog-azure-boards && uv run pytest tests/test_cliente_azure_devops.py tests/test_manifesto.py tests/test_executar_publicacao.py -q
```

Saída:

```text
49 passed in 0.10s
```

# Plano: suporte Greenfield e Brownfield

## Objetivo

Permitir que as skills gerem backlog a partir de uma spec sem código (Greenfield) ou validem a spec contra um projeto existente antes de gerar o backlog (Brownfield).

## Progresso

- [x] Baseline registrado em `brownfield-baseline.md`.
- [x] Testes estáticos adicionados e observados em RED.
- [x] Contratos Greenfield/Brownfield e integração 3W/3C/Gherkin implementados.
- [x] README atualizado com fluxos e classificações.
- [x] Verificações finais e relatório.

## Tarefas

1. [Concluído] Registrar baseline Brownfield sem as novas instruções.
2. [Concluído] Atualizar a skill de backlog com detecção de modo, inventário de código, matriz requisito × evidência e regras de escopo.
3. [Concluído] Atualizar 3W/3C/Gherkin para consumir evidências do código sem transformar implementação em requisito.
4. [Concluído] Adicionar testes estáticos e casos de validação para os dois modos.
5. [Concluído] Atualizar README e referências, validar as quatro skills e executar a suíte.

## Critérios de aceitação

- Greenfield não exige código-fonte.
- Brownfield inspeciona código antes do refinamento.
- Cada requisito Brownfield recebe status e caminho/linha quando houver evidência.
- Divergências não são corrigidas nem tratadas como requisito confirmado automaticamente.
- O backlog registra evidências sem misturar código em Acceptance Criteria.
- Nenhum work item Azure é criado ou alterado.

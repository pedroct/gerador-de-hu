## Tarefa 2b: `Tags` do plano até o payload do Azure Boards

Segunda metade da Tarefa 2 do plano. A Tarefa 2a já lê a seção `Tags` em `ItemBacklog.tags`. Você
propaga para a operação de criação, torna o hash assimétrico e envia `System.Tags`.

**Arquivos:**
- Modificar: `modelos.py`, `planejar_publicacao.py` e `cliente_azure_devops.py` em **ambos** os pacotes
- Testar: `tests/test_planejar_publicacao.py` e `tests/test_cliente_azure_devops.py` em ambos

**Interfaces:**
- Consome: `ItemBacklog.tags: tuple[str, ...]` da Tarefa 2a.
- Produz: `OperacaoCriacao.tags: tuple[str, ...] = ()` e o helper `_conteudo_do_item(item)` em
  `planejar_publicacao.py`. As Tarefas 4 e 7 acrescentam suas próprias chaves a esse helper, pelo
  mesmo critério de "só quando preenchido".

- [ ] **Passo 1: capturar o hash de hoje, ANTES de qualquer mudança**

Este é o passo mais importante da tarefa. O literal capturado é o que garante que todo manifesto de
publicação parcial já gravado continue retomando.

```bash
cd publicar-backlog-azure-boards && uv run python -c "
from publicar_backlog_azure_boards.modelos import ConfiguracaoPublicacao, ItemBacklog, TipoItem
from publicar_backlog_azure_boards.planejar_publicacao import criar_plano
configuracao = ConfiguracaoPublicacao('organizacao', 'projeto', 'projeto', 'projeto\\\\Sprint 18')
itens = [
    ItemBacklog('1.1.1', TipoItem.HISTORIA_USUARIO, 'História', '1.1.0', 'Descrição', ''),
    ItemBacklog('1.1.0', TipoItem.FEATURE, 'Feature', '1.0.0', 'Descrição', ''),
    ItemBacklog('1.0.0', TipoItem.EPIC, 'Épico', None, 'Descrição', ''),
]
print(criar_plano(itens, configuracao, '2026-09-16').hash_plano)
"
```

Repita dentro de `publicar-backlog-demanda-azure-boards`, trocando o nome do pacote no import.
**Confirme o valor de cada pacote em vez de supor que são iguais.** Anote os dois no relatório.

- [ ] **Passo 2: escrever os testes que falham**

Em `tests/test_planejar_publicacao.py`, com o literal capturado no topo do arquivo:

```python
# Hash produzido pela versão anterior aos campos novos. Ele existe para que um backlog
# sem tags, sem dependências e sem ID declarado continue gerando o mesmo plano — é o que
# permite a toda publicação parcial já gravada retomar. Se este teste falhar, a assimetria
# do hash foi quebrada; não atualize o literal para "consertar".
HASH_ANTES_DOS_CAMPOS_NOVOS = "<cole aqui a saída do Passo 1 deste pacote>"


def test_hash_nao_muda_para_backlog_sem_tags() -> None:
    plano = criar_plano(ITENS, CONFIGURACAO, DATA_GERACAO)

    assert plano.hash_plano == HASH_ANTES_DOS_CAMPOS_NOVOS


def test_operacao_propaga_tags_do_item() -> None:
    itens = [replace(ITENS[0], tags=("debito-tecnico",)), ITENS[1], ITENS[2]]

    plano = criar_plano(itens, CONFIGURACAO, DATA_GERACAO)

    assert plano.operacoes[-1].tags == ("debito-tecnico",)


def test_hash_muda_quando_ha_tags() -> None:
    com_tags = [replace(ITENS[0], tags=("debito-tecnico",)), ITENS[1], ITENS[2]]

    assert (
        criar_plano(com_tags, CONFIGURACAO, DATA_GERACAO).hash_plano
        != criar_plano(ITENS, CONFIGURACAO, DATA_GERACAO).hash_plano
    )
```

Em `tests/test_cliente_azure_devops.py` (acrescente `import json` e
`from dataclasses import replace` ao topo se ainda não estiverem lá):

```python
def test_criacao_envia_tags_unidas_por_ponto_e_virgula() -> None:
    cliente_azure, chamadas = cliente(
        [resposta(200, {"id": 7, "url": "https://dev.azure.com/item/7"})]
    )
    operacao = replace(OPERACAO, tags=("debito-tecnico", "dt-restricao"))

    cliente_azure.criar_item(operacao)

    patch = json.loads(chamadas[0].content)
    campos = {entrada["path"]: entrada["value"] for entrada in patch if "fields" in entrada["path"]}
    assert campos["/fields/System.Tags"] == "debito-tecnico; dt-restricao"


def test_criacao_omite_system_tags_quando_nao_ha_tags() -> None:
    cliente_azure, chamadas = cliente(
        [resposta(200, {"id": 7, "url": "https://dev.azure.com/item/7"})]
    )

    cliente_azure.criar_item(OPERACAO)

    patch = json.loads(chamadas[0].content)
    assert all("System.Tags" not in entrada["path"] for entrada in patch)
```

Replique tudo no pacote de Demanda, trocando só o import.

- [ ] **Passo 3: rodar para confirmar que falham**

```bash
cd publicar-backlog-azure-boards && uv run pytest tests/test_planejar_publicacao.py tests/test_cliente_azure_devops.py -q
```

Esperado: FAIL com `TypeError: OperacaoCriacao.__init__() got an unexpected keyword argument 'tags'`.
`test_hash_nao_muda_para_backlog_sem_tags` deve **passar** desde já — ele é a linha de base.

- [ ] **Passo 4: implementar**

Em `modelos.py`, o campo vai para o fim do dataclass, com default:

```python
@dataclass(frozen=True)
class OperacaoCriacao:
    """Representa uma criação planejada, sem executar qualquer escrita."""

    chave: str
    tipo: TipoItem
    titulo: str
    descricao: str
    criterios_aceitacao: str
    chave_pai: str | None
    tipo_remoto: str
    tags: tuple[str, ...] = ()
```

Em `planejar_publicacao.py`, propague em `_criar_operacao` (`tags=item.tags`) e extraia o conteúdo
serializado do item para um helper, incluindo a chave só quando houver:

```python
def _conteudo_do_item(item: ItemBacklog) -> dict[str, object]:
    conteudo: dict[str, object] = {
        "chave": item.chave,
        "tipo": item.tipo,
        "titulo": item.titulo,
        "titulo_curto": item.titulo_curto,
        "pai": item.pai,
        "descricao": item.descricao,
        "criterios_aceitacao": item.criterios_aceitacao,
    }
    # A chave só entra quando preenchida: um backlog sem campos novos precisa produzir
    # o hash anterior, ou todo manifesto de publicação parcial deixa de retomar. Não
    # "simplifique" incluindo sempre.
    if item.tags:
        conteudo["tags"] = list(item.tags)
    return conteudo
```

e use `_conteudo_do_item(item) for item in itens` dentro de `_calcular_hash`, preservando as demais
chaves do dicionário serializado (`configuracao`, `data_geracao`) exatamente como estão.

Em `cliente_azure_devops.py`, dentro de `_enviar_criacao`, depois da montagem de `patch`:

```python
        if operacao.tags:
            patch.append(
                {"op": "add", "path": "/fields/System.Tags", "value": "; ".join(operacao.tags)}
            )
```

- [ ] **Passo 5: rodar a suíte inteira dos dois pacotes**

```bash
cd publicar-backlog-azure-boards && uv run pytest -q && uv run ruff check . && uv run ruff format --check . && uv run mypy src
cd ../publicar-backlog-demanda-azure-boards && uv run pytest -q && uv run ruff check . && uv run ruff format --check . && uv run mypy src
```

**Se `test_hash_nao_muda_para_backlog_sem_tags` falhar, PARE e reporte BLOCKED.** Significa que a
assimetria do hash foi quebrada e a retomada de manifestos existentes deixou de funcionar. Não
atualize o literal para fazer passar.

- [ ] **Passo 6: commitar**

```bash
git add publicar-backlog-azure-boards publicar-backlog-demanda-azure-boards
git commit -m "feat: publica System.Tags a partir da secao Tags do backlog"
```

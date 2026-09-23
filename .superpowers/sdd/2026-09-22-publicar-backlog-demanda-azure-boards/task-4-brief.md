### Task 4: O plano passa a usar o título hierárquico

**Files:**
- Modify: `publicar-backlog-demanda-azure-boards/src/publicar_backlog_demanda_azure_boards/planejar_publicacao.py`
- Test: `publicar-backlog-demanda-azure-boards/tests/test_planejar_publicacao.py`

**Interfaces:**
- Consumes: `montar_titulo(item)` da Task 3.
- Produces: `criar_plano(itens, configuracao, data_geracao)` com assinatura inalterada; muda apenas o
  conteúdo de `OperacaoCriacao.titulo`. `data_geracao` continua entrando no hash.

- [ ] **Step 1: Escrever o teste que falha**

Acrescentar a `tests/test_planejar_publicacao.py`:

```python
def test_titulo_usa_numeracao_hierarquica_sem_data(configuracao_exemplo) -> None:
    itens = [
        ItemBacklog(
            chave="1.0.0",
            tipo=TipoItem.EPIC,
            titulo="Gestão do projeto",
            pai=None,
            descricao="",
            criterios_aceitacao="",
        ),
        ItemBacklog(
            chave="1.1.1",
            tipo=TipoItem.HISTORIA_USUARIO,
            titulo="Análise de padrões de stacks",
            pai="1.1.0",
            descricao="",
            criterios_aceitacao="",
        ),
    ]
    plano = criar_plano(itens, configuracao_exemplo, "2026-09-22")
    titulos = {operacao.chave: operacao.titulo for operacao in plano.operacoes}
    assert titulos["1.0.0"] == "01 Gestão do projeto"
    assert titulos["1.1.1"] == "01.01.01 Análise de padrões de stacks"
    assert all("2026-09-22" not in titulo for titulo in titulos.values())


def test_data_de_geracao_continua_no_hash(configuracao_exemplo) -> None:
    itens = [
        ItemBacklog(
            chave="1.0.0",
            tipo=TipoItem.EPIC,
            titulo="Gestão do projeto",
            pai=None,
            descricao="",
            criterios_aceitacao="",
        )
    ]
    primeiro = criar_plano(itens, configuracao_exemplo, "2026-09-22")
    segundo = criar_plano(itens, configuracao_exemplo, "2026-09-23")
    assert primeiro.hash_plano != segundo.hash_plano
```

Onde `configuracao_exemplo` é a fixture de `ConfiguracaoPublicacao` já usada pelo arquivo. Se ela não
existir com esse nome, reutilizar a construção local que os testes existentes já fazem.

- [ ] **Step 2: Rodar e confirmar a falha**

```bash
cd /Volumes/DOCK/Projetos/pessoal/gerador-hu/publicar-backlog-demanda-azure-boards
uv run pytest tests/test_planejar_publicacao.py -v
```

Esperado: FAIL em `test_titulo_usa_numeracao_hierarquica_sem_data`, com o título recebido começando
por `2026-09-22`. Os testes herdados que afirmam o título datado também falham — eles serão corrigidos
no passo seguinte, porque afirmam o comportamento antigo.

- [ ] **Step 3: Trocar a montagem do título**

Em `planejar_publicacao.py`, acrescentar a importação e substituir a linha do título:

```python
from publicar_backlog_demanda_azure_boards.titulo_hierarquico import montar_titulo
```

```python
def _criar_operacao(
    item: ItemBacklog, configuracao: ConfiguracaoPublicacao, data_geracao: str
) -> OperacaoCriacao:
    return OperacaoCriacao(
        chave=item.chave,
        tipo=item.tipo,
        titulo=montar_titulo(item),
        descricao=converter_descricao(item.descricao),
        criterios_aceitacao=converter_criterios(item.criterios_aceitacao),
        chave_pai=item.pai,
        tipo_remoto=configuracao.mapeamento_tipos.nome_remoto(item.tipo),
    )
```

`data_geracao` deixa de ser usado por `_criar_operacao`, mas **permanece** no parâmetro de
`criar_plano` e dentro de `_calcular_hash`. Trocar a assinatura para
`_criar_operacao(item, configuracao)` e ajustar a chamada.

- [ ] **Step 4: Corrigir os testes herdados que afirmam o título datado**

```bash
cd /Volumes/DOCK/Projetos/pessoal/gerador-hu/publicar-backlog-demanda-azure-boards
grep -rn '2026-\|data_geracao' tests/*.py | grep -i titulo
```

Em cada afirmação encontrada, trocar o título esperado `"<data> <chave> <texto>"` pelo hierárquico
`"<numeração> <texto>"`. Não remover a afirmação: ela continua provando qual título é enviado.

- [ ] **Step 5: Rodar a suíte inteira**

```bash
cd /Volumes/DOCK/Projetos/pessoal/gerador-hu/publicar-backlog-demanda-azure-boards
uv run pytest
```

Esperado: PASS em tudo.

- [ ] **Step 6: Commit**

```bash
cd /Volumes/DOCK/Projetos/pessoal/gerador-hu
git add publicar-backlog-demanda-azure-boards
git commit -m "feat: publica titulos com numeracao hierarquica"
```

---

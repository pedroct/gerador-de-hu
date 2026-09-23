### Task 9: Os Épicos sobem como filhos da Demanda

**Files:**
- Modify: `src/.../executar_publicacao.py`
- Test: `publicar-backlog-demanda-azure-boards/tests/test_vinculo_demanda.py`

**Interfaces:**
- Consumes: `ConfiguracaoPublicacao.demanda_id` (Task 5); `executar_plano` inalterado na assinatura.
- Produces: nenhuma API nova.

- [ ] **Step 1: Escrever os testes que falham**

```python
"""Todo Épico publicado nasce filho da Demanda de Negócio informada."""

from dataclasses import dataclass
from pathlib import Path

from publicar_backlog_demanda_azure_boards.autorizacao import (
    ModalidadeAutorizacao,
    criar_autorizacao,
    criar_frase_confirmacao,
)
from publicar_backlog_demanda_azure_boards.executar_publicacao import executar_plano
from publicar_backlog_demanda_azure_boards.modelos import (
    ConfiguracaoPublicacao,
    ItemBacklog,
    MapeamentoTipos,
    OperacaoCriacao,
    TipoItem,
)
from publicar_backlog_demanda_azure_boards.planejar_publicacao import criar_plano

_DEMANDA = 13959


def _destino() -> ConfiguracaoPublicacao:
    return ConfiguracaoPublicacao(
        organizacao="contoso",
        projeto="CESOP-DILIGENCIA",
        area_path="CESOP-DILIGENCIA\\Sustentacao",
        iteration_path="CESOP-DILIGENCIA\\Sprint 18",
        demanda_id=_DEMANDA,
        mapeamento_tipos=MapeamentoTipos(),
    )


_ITENS = [
    ItemBacklog("1.0.0", TipoItem.EPIC, "Gestão do projeto", None, "d", ""),
    ItemBacklog("1.1.0", TipoItem.FEATURE, "Gestão do projeto", "1.0.0", "d", ""),
    ItemBacklog("1.1.1", TipoItem.HISTORIA_USUARIO, "Análise de stacks", "1.1.0", "d", ""),
    ItemBacklog("2.0.0", TipoItem.EPIC, "Padronização", None, "d", ""),
]


@dataclass
class _Criado:
    id: int
    url: str


class _ClienteFalso:
    def __init__(self, configuracao: ConfiguracaoPublicacao) -> None:
        self.configuracao = configuracao
        self.chamadas: list[tuple[str, int | None]] = []
        self._proximo = 13969

    def criar_item(self, operacao: OperacaoCriacao, id_pai: int | None = None) -> _Criado:
        self.chamadas.append((operacao.chave, id_pai))
        criado = _Criado(self._proximo, f"https://dev.azure.com/x/_apis/wit/workItems/{self._proximo}")
        self._proximo += 1
        return criado


def _publicar(tmp_path: Path) -> _ClienteFalso:
    destino = _destino()
    plano = criar_plano(_ITENS, destino, "2026-09-22")
    chaves = frozenset(operacao.chave for operacao in plano.operacoes)
    autorizacao = criar_autorizacao(
        plano,
        criar_frase_confirmacao(plano, chaves),
        chaves,
        modalidade=ModalidadeAutorizacao.INTEIRA,
    )
    cliente = _ClienteFalso(destino)
    executar_plano(plano, autorizacao, cliente, tmp_path / "manifesto.json")
    return cliente


def test_todo_epico_sobe_com_a_demanda_como_pai(tmp_path: Path) -> None:
    cliente = _publicar(tmp_path)
    pais = dict(cliente.chamadas)
    assert pais["1.0.0"] == _DEMANDA
    assert pais["2.0.0"] == _DEMANDA


def test_feature_e_historia_mantem_os_pais_do_backlog(tmp_path: Path) -> None:
    cliente = _publicar(tmp_path)
    pais = dict(cliente.chamadas)
    assert pais["1.1.0"] == 13969
    assert pais["1.1.1"] not in (None, _DEMANDA)


def test_nenhum_item_sobe_sem_pai(tmp_path: Path) -> None:
    cliente = _publicar(tmp_path)
    assert all(id_pai is not None for _, id_pai in cliente.chamadas)
```

- [ ] **Step 2: Rodar e confirmar a falha**

```bash
cd /Volumes/DOCK/Projetos/pessoal/gerador-hu/publicar-backlog-demanda-azure-boards
uv run pytest tests/test_vinculo_demanda.py -v
```

Esperado: FAIL, porque os Épicos hoje sobem com `id_pai=None`.

- [ ] **Step 3: Pendurar os Épicos na Demanda**

Em `executar_publicacao.py`, dentro do laço de `executar_plano`, substituir a resolução do pai:

```python
        id_pai = (
            registros[operacao.chave_pai].id
            if operacao.chave_pai is not None
            else cliente.configuracao.demanda_id
        )
```

Um item sem pai documental é um Épico, e o pai dele é a Demanda. Não existe mais item publicado sem
pai.

- [ ] **Step 4: Rodar e confirmar que passa**

```bash
cd /Volumes/DOCK/Projetos/pessoal/gerador-hu/publicar-backlog-demanda-azure-boards
uv run pytest tests/test_vinculo_demanda.py -v && uv run pytest
```

Esperado: PASS nos três testes novos e na suíte inteira.

- [ ] **Step 5: Commit**

```bash
cd /Volumes/DOCK/Projetos/pessoal/gerador-hu
git add publicar-backlog-demanda-azure-boards
git commit -m "feat: pendura os Epicos publicados na Demanda de Negocio"
```

---

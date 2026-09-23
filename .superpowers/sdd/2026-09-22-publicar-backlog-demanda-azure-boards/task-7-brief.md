### Task 7: Leitor da Demanda

**Files:**
- Create: `publicar-backlog-demanda-azure-boards/src/publicar_backlog_demanda_azure_boards/leitor_demanda.py`
- Test: `publicar-backlog-demanda-azure-boards/tests/test_leitor_demanda.py`

**Interfaces:**
- Consumes: `Demanda` da Task 5; as classes de erro de `cliente_azure_devops.py`.
- Produces:
  ```python
  def ler_demanda(
      organizacao: str,
      projeto: str,
      token: str,
      id_demanda: int,
      tipo_esperado: str,
      *,
      transport: httpx.BaseTransport | None = None,
      timeout: float = 10.0,
  ) -> Demanda: ...
  ```
  Consumida pela Task 10.

- [ ] **Step 1: Escrever os testes que falham**

```python
"""Leitura somente leitura da Demanda de Negócio que ancora a publicação."""

import httpx
import pytest

from publicar_backlog_demanda_azure_boards.cliente_azure_devops import ErroDestinoInvalido
from publicar_backlog_demanda_azure_boards.leitor_demanda import ler_demanda

_URL = "https://dev.azure.com/contoso/CESOP-DILIGENCIA/_apis/wit/workItems/13959"


def _payload(**sobrescritas: object) -> dict[str, object]:
    campos: dict[str, object] = {
        "System.WorkItemType": "Demanda de Negócio",
        "System.TeamProject": "CESOP-DILIGENCIA",
        "System.Title": "PADRONIZAÇÃO E ATUALIZAÇÃO DAS STACKS DA APLICAÇÃO",
        "System.AreaPath": "CESOP-DILIGENCIA\\Sustentacao",
        "System.IterationPath": "CESOP-DILIGENCIA\\Sprint 18",
    }
    campos.update(sobrescritas)
    return {"id": 13959, "url": _URL, "fields": campos}


def _transporte(payload: object, status: int = 200) -> httpx.MockTransport:
    def responder(requisicao: httpx.Request) -> httpx.Response:
        assert requisicao.method == "GET"
        return httpx.Response(status, json=payload)

    return httpx.MockTransport(responder)


def _ler(payload: object, status: int = 200, tipo: str = "Demanda de Negócio"):
    return ler_demanda(
        "contoso",
        "CESOP-DILIGENCIA",
        "token-de-teste",
        13959,
        tipo,
        transport=_transporte(payload, status),
    )


def test_le_a_demanda_e_extrai_titulo_e_caminhos() -> None:
    demanda = _ler(_payload())
    assert demanda.id == 13959
    assert demanda.titulo == "PADRONIZAÇÃO E ATUALIZAÇÃO DAS STACKS DA APLICAÇÃO"
    assert demanda.area_path == "CESOP-DILIGENCIA\\Sustentacao"
    assert demanda.iteration_path == "CESOP-DILIGENCIA\\Sprint 18"
    assert demanda.url == _URL


def test_recusa_work_item_de_outro_tipo() -> None:
    with pytest.raises(ErroDestinoInvalido) as erro:
        _ler(_payload(**{"System.WorkItemType": "Epic"}))
    assert "Epic" in str(erro.value)
    assert "Demanda de Negócio" in str(erro.value)


def test_recusa_demanda_de_outro_projeto() -> None:
    with pytest.raises(ErroDestinoInvalido) as erro:
        _ler(_payload(**{"System.TeamProject": "OUTRO-PROJETO"}))
    assert "OUTRO-PROJETO" in str(erro.value)


@pytest.mark.parametrize("campo", ["System.AreaPath", "System.IterationPath", "System.Title"])
def test_recusa_demanda_sem_campo_necessario(campo: str) -> None:
    with pytest.raises(ErroDestinoInvalido) as erro:
        _ler(_payload(**{campo: ""}))
    assert campo in str(erro.value)


def test_recusa_work_item_inexistente() -> None:
    with pytest.raises(ErroDestinoInvalido) as erro:
        _ler({"message": "não encontrado"}, status=404)
    assert "13959" in str(erro.value)


def test_recusa_identificador_nao_positivo() -> None:
    with pytest.raises(ErroDestinoInvalido):
        ler_demanda(
            "contoso",
            "CESOP-DILIGENCIA",
            "token-de-teste",
            0,
            "Demanda de Negócio",
            transport=_transporte(_payload()),
        )


def test_nao_expoe_o_token_na_mensagem_de_erro() -> None:
    with pytest.raises(ErroDestinoInvalido) as erro:
        _ler({"message": "não encontrado"}, status=404)
    assert "token-de-teste" not in str(erro.value)
```

- [ ] **Step 2: Rodar e confirmar a falha**

```bash
cd /Volumes/DOCK/Projetos/pessoal/gerador-hu/publicar-backlog-demanda-azure-boards
uv run pytest tests/test_leitor_demanda.py -v
```

Esperado: FAIL com `ModuleNotFoundError: No module named
'publicar_backlog_demanda_azure_boards.leitor_demanda'`.

- [ ] **Step 3: Implementar o leitor**

```python
"""Lê a Demanda de Negócio que ancora a publicação, sem qualquer escrita.

Este módulo não usa ``ClienteAzureDevOps`` de propósito: o cliente é construído com uma
``ConfiguracaoPublicacao`` já completa, e os caminhos dessa configuração são justamente o
que a Demanda fornece. A leitura precisa acontecer antes de o destino existir.
"""

from __future__ import annotations

import base64
from typing import Any

import httpx

from publicar_backlog_demanda_azure_boards.cliente_azure_devops import (
    ErroDestinoInvalido,
    _verificar_status,
)
from publicar_backlog_demanda_azure_boards.modelos import Demanda

_VERSAO_API = "7.2-preview.3"
_CAMPOS_TEXTO = ("System.Title", "System.AreaPath", "System.IterationPath")


def ler_demanda(
    organizacao: str,
    projeto: str,
    token: str,
    id_demanda: int,
    tipo_esperado: str,
    *,
    transport: httpx.BaseTransport | None = None,
    timeout: float = 10.0,
) -> Demanda:
    """Busca a Demanda por `GET` e valida tipo, projeto e campos antes de derivar o destino."""
    if id_demanda <= 0:
        raise ErroDestinoInvalido(
            "O ID da Demanda de Negócio deve ser um inteiro positivo."
        )
    credencial = base64.b64encode(f":{token}".encode()).decode()
    url = (
        f"https://dev.azure.com/{organizacao}/{projeto}"
        f"/_apis/wit/workitems/{id_demanda}?$expand=Fields&api-version={_VERSAO_API}"
    )
    with httpx.Client(
        headers={"Authorization": f"Basic {credencial}"},
        timeout=httpx.Timeout(timeout),
        transport=transport,
    ) as cliente:
        resposta = cliente.get(url)
    try:
        _verificar_status(resposta)
    except Exception as erro:
        raise ErroDestinoInvalido(
            f"Não foi possível ler a Demanda de Negócio {id_demanda}."
        ) from erro

    payload = _objeto(resposta.json(), f"A resposta da Demanda {id_demanda} é inválida.")
    campos = _objeto(
        payload.get("fields"), f"A Demanda {id_demanda} não devolveu seus campos."
    )

    tipo = campos.get("System.WorkItemType")
    if tipo != tipo_esperado:
        raise ErroDestinoInvalido(
            f"O work item {id_demanda} é do tipo {tipo!r}; "
            f"esta skill publica apenas sob {tipo_esperado!r}."
        )

    team_project = campos.get("System.TeamProject")
    if team_project != projeto:
        raise ErroDestinoInvalido(
            f"A Demanda {id_demanda} pertence ao projeto {team_project!r}, "
            f"e não a {projeto!r}; o vínculo hierárquico não cruza projeto."
        )

    for campo in _CAMPOS_TEXTO:
        valor = campos.get(campo)
        if not isinstance(valor, str) or not valor.strip():
            raise ErroDestinoInvalido(
                f"A Demanda {id_demanda} não possui {campo}; não há de onde herdar o destino."
            )

    url_item = payload.get("url")
    if not isinstance(url_item, str) or not url_item.startswith("https://"):
        raise ErroDestinoInvalido(f"A Demanda {id_demanda} não devolveu uma URL utilizável.")

    return Demanda(
        id=id_demanda,
        titulo=str(campos["System.Title"]).strip(),
        area_path=str(campos["System.AreaPath"]).strip(),
        iteration_path=str(campos["System.IterationPath"]).strip(),
        url=url_item,
    )


def _objeto(valor: object, mensagem: str) -> dict[str, Any]:
    if not isinstance(valor, dict):
        raise ErroDestinoInvalido(mensagem)
    return valor
```

Se `_verificar_status` estiver privado a ponto de o `ruff` reclamar da importação, promover a função
a pública em `cliente_azure_devops.py` renomeando para `verificar_status` e atualizar as chamadas
internas. Não duplicar a lógica de status em dois módulos.

- [ ] **Step 4: Rodar e confirmar que passa**

```bash
cd /Volumes/DOCK/Projetos/pessoal/gerador-hu/publicar-backlog-demanda-azure-boards
uv run pytest tests/test_leitor_demanda.py -v
```

Esperado: PASS nos nove casos.

- [ ] **Step 5: Commit**

```bash
cd /Volumes/DOCK/Projetos/pessoal/gerador-hu
git add publicar-backlog-demanda-azure-boards
git commit -m "feat: le a Demanda de Negocio para derivar o destino"
```

---

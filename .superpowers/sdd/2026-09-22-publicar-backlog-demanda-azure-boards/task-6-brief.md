### Task 6: Provar que a autorização não atravessa Demandas

Tarefa de teste. Ela existe porque é a garantia central do desenho: uma confirmação emitida para uma
Demanda não pode publicar sob outra.

**Files:**
- Create: `publicar-backlog-demanda-azure-boards/tests/test_autorizacao_vinculada_a_demanda.py`

**Interfaces:**
- Consumes: `ConfiguracaoPublicacao.demanda_id`, `criar_plano`, `criar_autorizacao`,
  `criar_frase_confirmacao`, `validar_manifesto`, `Manifesto` — todos da Task 5.
- Produces: nada consumido por tarefas seguintes.

- [ ] **Step 1: Escrever os testes**

```python
"""A autorização e o manifesto ficam presos à Demanda para a qual foram emitidos."""

import pytest

from publicar_backlog_demanda_azure_boards.autorizacao import (
    ModalidadeAutorizacao,
    criar_autorizacao,
    criar_frase_confirmacao,
)
from publicar_backlog_demanda_azure_boards.manifesto import Manifesto, validar_manifesto
from publicar_backlog_demanda_azure_boards.modelos import (
    ConfiguracaoPublicacao,
    ItemBacklog,
    MapeamentoTipos,
    RegistroManifesto,
    TipoItem,
)
from publicar_backlog_demanda_azure_boards.planejar_publicacao import criar_plano

_ITENS = [
    ItemBacklog(
        chave="1.0.0",
        tipo=TipoItem.EPIC,
        titulo="Gestão do projeto",
        pai=None,
        descricao="Contexto.",
        criterios_aceitacao="",
    )
]


def _destino(demanda_id: int) -> ConfiguracaoPublicacao:
    return ConfiguracaoPublicacao(
        organizacao="contoso",
        projeto="CESOP-DILIGENCIA",
        area_path="CESOP-DILIGENCIA\\Sustentacao",
        iteration_path="CESOP-DILIGENCIA\\Sprint 18",
        demanda_id=demanda_id,
        mapeamento_tipos=MapeamentoTipos(),
    )


def _plano(demanda_id: int):
    return criar_plano(_ITENS, _destino(demanda_id), "2026-09-22")


def test_trocar_a_demanda_muda_o_hash_do_plano() -> None:
    assert _plano(13959).hash_plano != _plano(13970).hash_plano


def test_a_frase_nomeia_a_demanda() -> None:
    frase = criar_frase_confirmacao(_plano(13959), ("1.0.0",))
    assert "DEMANDA 13959" in frase


def test_frase_de_uma_demanda_nao_autoriza_outra() -> None:
    frase_original = criar_frase_confirmacao(_plano(13959), ("1.0.0",))
    with pytest.raises(PermissionError):
        criar_autorizacao(
            _plano(13970),
            frase_original,
            frozenset({"1.0.0"}),
            modalidade=ModalidadeAutorizacao.INTEIRA,
        )


def test_autorizacao_valida_nao_vale_para_outro_destino() -> None:
    plano = _plano(13959)
    autorizacao = criar_autorizacao(
        plano,
        criar_frase_confirmacao(plano, ("1.0.0",)),
        frozenset({"1.0.0"}),
        modalidade=ModalidadeAutorizacao.INTEIRA,
    )
    assert autorizacao.valida_para(plano, _destino(13959))
    assert not autorizacao.valida_para(plano, _destino(13970))


def test_manifesto_de_uma_demanda_nao_retoma_sob_outra() -> None:
    plano_original = _plano(13959)
    manifesto = Manifesto(
        hash_plano=plano_original.hash_plano,
        configuracao=_destino(13959),
        itens={"1.0.0": RegistroManifesto(id=13969, tipo=TipoItem.EPIC, url="https://exemplo")},
        titulos={"1.0.0": plano_original.operacoes[0].titulo},
    )
    with pytest.raises(ValueError):
        validar_manifesto(manifesto, _plano(13970), _destino(13970))
```

- [ ] **Step 2: Rodar e confirmar que passam**

```bash
cd /Volumes/DOCK/Projetos/pessoal/gerador-hu/publicar-backlog-demanda-azure-boards
uv run pytest tests/test_autorizacao_vinculada_a_demanda.py -v
```

Esperado: PASS nos cinco testes. Se algum falhar, a Task 5 deixou `demanda_id` fora de um dos pontos
de vinculação — hash, impressão de destino, frase ou manifesto. Corrigir lá, não aqui.

- [ ] **Step 3: Commit**

```bash
cd /Volumes/DOCK/Projetos/pessoal/gerador-hu
git add publicar-backlog-demanda-azure-boards/tests/test_autorizacao_vinculada_a_demanda.py
git commit -m "test: prova que a autorizacao nao atravessa Demandas"
```

---

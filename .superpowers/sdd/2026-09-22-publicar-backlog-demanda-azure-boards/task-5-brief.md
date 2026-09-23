### Task 5: A Demanda entra no destino

Mudança atômica: `demanda_id` passa a fazer parte da identidade do destino e, por consequência, do
hash do plano, da impressão de autorização, da frase de confirmação e do manifesto. Tudo que constrói
ou serializa `ConfiguracaoPublicacao` precisa acompanhar na mesma tarefa, ou a suíte não fecha.

**Files:**
- Modify: `src/.../modelos.py`
- Modify: `src/.../autorizacao.py`
- Modify: `src/.../manifesto.py`
- Modify: `src/.../configuracao.py`
- Modify: `src/.../cli.py`
- Test: `tests/test_manifesto.py`, `tests/test_autorizacao.py`, `tests/test_configuracao_projeto.py`

**Interfaces:**
- Consumes: nada das tarefas anteriores.
- Produces:
  - `Demanda(id: int, titulo: str, area_path: str, iteration_path: str, url: str)` — dataclass
    congelada em `modelos.py`, consumida pela Task 7 e pela Task 10.
  - `ConfiguracaoPublicacao(..., demanda_id: int)` — campo obrigatório, sem valor padrão.
  - `ConfiguracaoAzureDevOps(..., demanda_id: int, tipo_demanda: str = "Demanda de Negócio")`.
  - Argumentos de CLI `--demanda` e `--tipo-demanda`.

- [ ] **Step 1: Escrever os testes que falham**

Criar `tests/test_demanda_no_destino.py`:

```python
"""O ID da Demanda faz parte da identidade do destino publicado."""

import pytest

from publicar_backlog_demanda_azure_boards.autorizacao import imprimir_destino
from publicar_backlog_demanda_azure_boards.modelos import (
    ConfiguracaoPublicacao,
    Demanda,
    MapeamentoTipos,
)


def _destino(demanda_id: int) -> ConfiguracaoPublicacao:
    return ConfiguracaoPublicacao(
        organizacao="contoso",
        projeto="CESOP-DILIGENCIA",
        area_path="CESOP-DILIGENCIA\\Sustentacao",
        iteration_path="CESOP-DILIGENCIA\\Sprint 18",
        demanda_id=demanda_id,
        mapeamento_tipos=MapeamentoTipos(),
    )


def test_demanda_id_e_obrigatorio_no_destino() -> None:
    with pytest.raises(TypeError):
        ConfiguracaoPublicacao(  # type: ignore[call-arg]
            organizacao="contoso",
            projeto="CESOP-DILIGENCIA",
            area_path="CESOP-DILIGENCIA\\Sustentacao",
            iteration_path="CESOP-DILIGENCIA\\Sprint 18",
        )


def test_destinos_com_demandas_diferentes_tem_impressoes_diferentes() -> None:
    assert imprimir_destino(_destino(13959)) != imprimir_destino(_destino(13970))


def test_demanda_carrega_titulo_e_caminhos_para_derivar_o_destino() -> None:
    demanda = Demanda(
        id=13959,
        titulo="PADRONIZAÇÃO E ATUALIZAÇÃO DAS STACKS DA APLICAÇÃO",
        area_path="CESOP-DILIGENCIA\\Sustentacao",
        iteration_path="CESOP-DILIGENCIA\\Sprint 18",
        url="https://dev.azure.com/contoso/_apis/wit/workItems/13959",
    )
    assert demanda.id == 13959
    assert demanda.area_path.endswith("Sustentacao")
```

- [ ] **Step 2: Rodar e confirmar a falha**

```bash
cd /Volumes/DOCK/Projetos/pessoal/gerador-hu/publicar-backlog-demanda-azure-boards
uv run pytest tests/test_demanda_no_destino.py -v
```

Esperado: FAIL com `ImportError: cannot import name 'Demanda'`.

- [ ] **Step 3: Acrescentar `Demanda` e `demanda_id` em `modelos.py`**

```python
@dataclass(frozen=True)
class Demanda:
    """Demanda de Negócio lida do Azure Boards, usada para derivar e exibir o destino.

    ``titulo`` e ``url`` existem apenas para apresentação no plano. Eles ficam de fora de
    hash, impressão de destino e manifesto de propósito: uma edição cosmética do título no
    Azure Boards invalidaria um manifesto válido e bloquearia uma retomada legítima.
    """

    id: int
    titulo: str
    area_path: str
    iteration_path: str
    url: str
```

Em `ConfiguracaoPublicacao`, acrescentar `demanda_id: int` **antes** de `mapeamento_tipos`, para que
continue sendo o único campo com valor padrão:

```python
@dataclass(frozen=True)
class ConfiguracaoPublicacao:
    """Representa o destino já validado para uma publicação vinculada a uma Demanda."""

    organizacao: str
    projeto: str
    area_path: str
    iteration_path: str
    demanda_id: int
    mapeamento_tipos: MapeamentoTipos = field(default_factory=MapeamentoTipos)
```

Em `assinatura_plano`, acrescentar a chave ao dicionário `configuracao`:

```python
        "configuracao": {
            "organizacao": configuracao.organizacao,
            "projeto": configuracao.projeto,
            "area_path": configuracao.area_path,
            "iteration_path": configuracao.iteration_path,
            "demanda_id": configuracao.demanda_id,
            "mapeamento_tipos": configuracao.mapeamento_tipos.como_dict(),
        },
```

- [ ] **Step 4: Incluir `demanda_id` no hash do plano**

Em `planejar_publicacao.py`, dentro de `_calcular_hash`, acrescentar a mesma chave ao dicionário
`configuracao`. Sem isso, o hash não distinguiria duas Demandas, que é exatamente o risco que esta
tarefa fecha.

```python
        "configuracao": {
            "organizacao": configuracao.organizacao,
            "projeto": configuracao.projeto,
            "area_path": configuracao.area_path,
            "iteration_path": configuracao.iteration_path,
            "demanda_id": configuracao.demanda_id,
            "mapeamento_tipos": configuracao.mapeamento_tipos.como_dict(),
        },
```

- [ ] **Step 5: Incluir `demanda_id` na impressão e na frase, em `autorizacao.py`**

```python
def imprimir_destino(configuracao: ConfiguracaoPublicacao) -> str:
    """Resume criptograficamente todos os campos que identificam o destino remoto."""
    conteudo = {
        "organizacao": configuracao.organizacao,
        "projeto": configuracao.projeto,
        "area_path": configuracao.area_path,
        "iteration_path": configuracao.iteration_path,
        "demanda_id": configuracao.demanda_id,
        "mapeamento_tipos": configuracao.mapeamento_tipos.como_dict(),
    }
    return _resumir(conteudo)
```

```python
def criar_frase_confirmacao(
    plano: PlanoPublicacao,
    chaves_autorizadas: Collection[str],
    numero_lote: int | None = None,
) -> str:
    """Gera a frase que vincula quantidade, Demanda, destino e código do plano completo."""
    configuracao = plano.configuracao
    inicio = "AUTORIZAR PUBLICAÇÃO" if numero_lote is None else f"AUTORIZAR LOTE {numero_lote}"
    return (
        f"{inicio} {len(chaves_autorizadas)} ITENS "
        f"DEMANDA {configuracao.demanda_id} {configuracao.projeto} "
        f"{configuracao.area_path} {configuracao.iteration_path} "
        f"{plano.hash_plano[:4].upper()}"
    )
```

- [ ] **Step 6: Persistir `demanda_id` no manifesto**

Em `manifesto.py`, `_serializar_configuracao`:

```python
def _serializar_configuracao(configuracao: ConfiguracaoPublicacao) -> dict[str, object]:
    return {
        "organizacao": configuracao.organizacao,
        "projeto": configuracao.projeto,
        "area_path": configuracao.area_path,
        "iteration_path": configuracao.iteration_path,
        "demanda_id": configuracao.demanda_id,
        "mapeamento_tipos": configuracao.mapeamento_tipos.como_dict(),
    }
```

E em `_configuracao`, exigir o campo em vez de assumir um padrão — um manifesto sem Demanda é um
manifesto de outro formato, e aceitar zero silenciosamente liberaria escrita sob a Demanda errada:

```python
def _configuracao(destino: dict[str, object]) -> ConfiguracaoPublicacao:
    campos = ("organizacao", "projeto", "area_path", "iteration_path")
    valores = [destino.get(campo) for campo in campos]
    if not all(isinstance(valor, str) and valor for valor in valores):
        raise ValueError("O destino do manifesto é inválido.")
    demanda_id = destino.get("demanda_id")
    if not isinstance(demanda_id, int) or isinstance(demanda_id, bool) or demanda_id <= 0:
        raise ValueError("O destino do manifesto não identifica a Demanda de Negócio.")
    mapeamento_dados = destino.get("mapeamento_tipos", {})
    if not isinstance(mapeamento_dados, dict):
        raise ValueError("O mapeamento de tipos do manifesto é inválido.")
    mapeamento = MapeamentoTipos(
        epic=_tipo_remoto(mapeamento_dados, "Epic", "Epic"),
        feature=_tipo_remoto(mapeamento_dados, "Feature", "Feature"),
        historia_usuario=_tipo_remoto(mapeamento_dados, "User Story", "User Story"),
        bug=_tipo_remoto(mapeamento_dados, "Bug", "Bug"),
    )
    organizacao, projeto, area_path, iteration_path = (cast(str, valor) for valor in valores)
    return ConfiguracaoPublicacao(
        organizacao=organizacao,
        projeto=projeto,
        area_path=area_path,
        iteration_path=iteration_path,
        demanda_id=demanda_id,
        mapeamento_tipos=mapeamento,
    )
```

- [ ] **Step 7: Carregar o ID pela configuração**

Em `configuracao.py`, acrescentar os campos a `ConfiguracaoAzureDevOps`:

```python
    demanda_id: int
    tipo_demanda: str = "Demanda de Negócio"
```

```python
    @field_validator("demanda_id")
    @classmethod
    def validar_demanda(cls, valor: int) -> int:
        """Rejeita um identificador de Demanda que não possa endereçar um work item."""
        if valor <= 0:
            raise ValueError("deve ser um inteiro positivo")
        return valor
```

Acrescentar `"tipo_demanda"` à lista do `field_validator` de texto obrigatório, incluir
`demanda_id` na construção de `ConfiguracaoPublicacao` dentro da property `publicacao`, e registrar
as chaves:

```python
_CHAVES = {
    ...
    "demanda_id": "AZURE_DEVOPS_DEMANDA",
    "tipo_demanda": "AZURE_DEVOPS_TIPO_DEMANDA",
}
```

Em `carregar_configuracao`, acrescentar `"demanda_id"` e `"tipo_demanda"` à tupla `campos`, aplicar o
padrão `"Demanda de Negócio"` a `tipo_demanda` junto dos demais tipos, e converter o ID:

```python
    bruto = valores["demanda_id"]
    if bruto is None:
        bruto = _perguntar("demanda_id", entrada_interativa, saida_interativa)
    try:
        demanda_id = int(str(bruto).strip().lstrip("#"))
    except ValueError as erro:
        raise ErroConfiguracao(
            "O ID da Demanda de Negócio deve ser um número inteiro."
        ) from erro
```

Acrescentar o rótulo ao dicionário de `_perguntar`:

```python
        "demanda_id": "ID da Demanda de Negócio",
```

E passar os dois campos na construção final, junto dos que já existem:

```python
        return ConfiguracaoAzureDevOps(
            organizacao=_exigir_valor(valores["organizacao"], "Organização do Azure DevOps"),
            projeto=_exigir_valor(valores["projeto"], "Projeto do Azure DevOps"),
            area_path=_exigir_valor(valores["area_path"], "Area Path"),
            iteration_path=_exigir_valor(valores["iteration_path"], "Iteration Path"),
            demanda_id=demanda_id,
            tipo_demanda=_exigir_valor(valores["tipo_demanda"], "Tipo remoto da Demanda"),
            token=(...),  # inalterado
            tipo_epic=_exigir_valor(valores["tipo_epic"], "Tipo remoto de Epic"),
            tipo_feature=_exigir_valor(valores["tipo_feature"], "Tipo remoto de Feature"),
            tipo_user_story=_exigir_valor(valores["tipo_user_story"], "Tipo remoto de User Story"),
            tipo_bug=_exigir_valor(valores["tipo_bug"], "Tipo remoto de Bug"),
        )
```

`area_path` e `iteration_path` continuam aqui nesta tarefa; a Task 10 é que os remove.

- [ ] **Step 8: Expor `--demanda` e `--tipo-demanda` na CLI**

Em `cli.py`, dentro de `_adicionar_opcoes_configuracao`:

```python
    parser.add_argument("--demanda", dest="demanda_id")
    parser.add_argument("--tipo-demanda")
```

E acrescentar `"demanda_id"` e `"tipo_demanda"` à tupla `nomes` de `_carregar_configuracao`.

- [ ] **Step 9: Corrigir a suíte herdada**

```bash
cd /Volumes/DOCK/Projetos/pessoal/gerador-hu/publicar-backlog-demanda-azure-boards
uv run pytest
```

Toda construção de `ConfiguracaoPublicacao` nos testes passa a exigir `demanda_id=13959` (ou outro
inteiro positivo). Toda afirmação sobre a frase de confirmação passa a incluir `DEMANDA <id>`. Todo
manifesto de fixture ganha `"demanda_id"` no objeto `destino`. Corrigir uma a uma até a suíte fechar.

- [ ] **Step 10: Commit**

```bash
cd /Volumes/DOCK/Projetos/pessoal/gerador-hu
git add publicar-backlog-demanda-azure-boards
git commit -m "feat: vincula o destino da publicacao a uma Demanda de Negocio"
```

---

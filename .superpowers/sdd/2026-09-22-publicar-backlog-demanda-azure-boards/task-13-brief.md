### Task 13: Fechamento e verificação

**Files:**
- Modify: `publicar-backlog-demanda-azure-boards/tests/test_integracao_final.py`

**Interfaces:**
- Consumes: tudo.
- Produces: nada.

- [ ] **Step 1: Escrever o teste de ponta a ponta**

Em `tests/test_integracao_final.py`, acrescentar um caso que percorre o caminho inteiro com transporte
falso: backlog com dois Épicos, leitura da Demanda, plano, frase, publicação e manifesto.

```python
def test_publicacao_completa_vincula_tudo_a_demanda(tmp_path) -> None:
    cliente = _ClienteFalso(_destino_com_demanda(13959))
    codigo = principal(
        ["publicar", str(_backlog(tmp_path)), "--manifesto", str(tmp_path / "m.json")],
        cliente=cliente,
        entrada=io.StringIO(f"1\n{_frase_esperada(tmp_path)}\n"),
        saida=(saida := io.StringIO()),
    )
    assert codigo == 0
    assert "DEMANDA 13959" in saida.getvalue()

    manifesto = json.loads((tmp_path / "m.json").read_text(encoding="utf-8"))
    assert manifesto["destino"]["demanda_id"] == 13959
    assert all(id_pai is not None for _, id_pai in cliente.chamadas)
    assert [id_pai for chave, id_pai in cliente.chamadas if chave.endswith(".0.0")] == [13959, 13959]
```

Reutilizar os auxiliares do arquivo para montar backlog, destino e frase; se `_frase_esperada` não
existir, derivá-la de `criar_frase_confirmacao` sobre o plano montado com os mesmos itens.

- [ ] **Step 2: Rodar a suíte inteira**

```bash
cd /Volumes/DOCK/Projetos/pessoal/gerador-hu/publicar-backlog-demanda-azure-boards
uv run pytest
```

Esperado: PASS em todos os arquivos, incluindo `test_sincronia_com_origem.py`.

- [ ] **Step 3: Rodar lint, tipos e SAST**

```bash
cd /Volumes/DOCK/Projetos/pessoal/gerador-hu/publicar-backlog-demanda-azure-boards
uv run ruff check .
uv run ruff format --check .
uv run mypy
uv run bandit -c pyproject.toml -r src
```

Esperado: zero achados. Corrigir o que aparecer; não silenciar com `# noqa` ou `# type: ignore` sem
justificativa escrita na mesma linha.

- [ ] **Step 4: Confirmar que a skill de origem não foi tocada**

```bash
cd /Volumes/DOCK/Projetos/pessoal/gerador-hu
git diff --stat main -- publicar-backlog-azure-boards
```

Esperado: saída vazia. Qualquer arquivo listado aqui é uma violação da restrição global e precisa ser
revertido.

- [ ] **Step 5: Rodar os hooks do repositório**

```bash
cd /Volumes/DOCK/Projetos/pessoal/gerador-hu
uv run pre-commit run --all-files
```

Esperado: todos os hooks passam ou apenas reformatam arquivos; nenhum achado novo de lint, mypy ou
bandit.

- [ ] **Step 6: Commit**

```bash
cd /Volumes/DOCK/Projetos/pessoal/gerador-hu
git add publicar-backlog-demanda-azure-boards
git commit -m "test: cobre o fluxo completo de publicacao vinculada"
```

- [ ] **Step 7: Publicação real, conduzida pelo usuário**

Este passo **não** é executado pelo agente. Entregar ao usuário o comando e esperar a decisão dele:

```bash
cd /Volumes/DOCK/Projetos/pessoal/gerador-hu/publicar-backlog-demanda-azure-boards
uv run python scripts/publicar_backlog_demanda.py publicar ../backlog.md --demanda 13959 --validar-apenas
```

Só depois de o usuário conferir a validação preliminar, e por decisão dele, rodar sem
`--validar-apenas`. A conferência final é visual no Azure Boards: a Demanda 13959 passa a listar os
Épicos como *Child*, com títulos `01`, `01.01` e `01.01.01` e os caminhos herdados.

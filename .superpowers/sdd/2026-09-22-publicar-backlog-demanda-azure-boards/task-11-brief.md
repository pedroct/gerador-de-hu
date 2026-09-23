### Task 11: O plano mostra a origem

**Files:**
- Modify: `src/.../cli.py` (`_apresentar_plano` e sua chamada)
- Test: `tests/test_skill_integration.py`

**Interfaces:**
- Consumes: `Demanda` (Task 5), o destino derivado (Task 10).
- Produces: `_apresentar_plano(plano, pendentes, total, registrados, caminho_manifesto, saida, demanda)`
  — um parâmetro a mais, `demanda: Demanda | None`.

- [ ] **Step 1: Escrever o teste que falha**

```python
def test_plano_apresenta_a_demanda_de_origem(capsys, backlog_exemplo, cliente_falso) -> None:
    codigo = principal(
        ["planejar", str(backlog_exemplo)],
        cliente=cliente_falso,
        entrada=io.StringIO(""),
        saida=(saida := io.StringIO()),
    )
    texto = saida.getvalue()
    assert codigo == 0
    assert "Demanda de Negócio: #13959" in texto
    assert "herdado da Demanda #13959" in texto
```

Ajustar as fixtures aos auxiliares já existentes no arquivo. O cliente falso precisa devolver uma
`ConfiguracaoPublicacao` com `demanda_id=13959`.

- [ ] **Step 2: Rodar e confirmar a falha**

```bash
cd /Volumes/DOCK/Projetos/pessoal/gerador-hu/publicar-backlog-demanda-azure-boards
uv run pytest tests/test_skill_integration.py -k demanda -v
```

Esperado: FAIL, porque o cabeçalho ainda não existe.

- [ ] **Step 3: Acrescentar o cabeçalho de origem**

```python
def _apresentar_plano(
    plano: PlanoPublicacao,
    pendentes: Sequence[OperacaoCriacao],
    total: int,
    registrados: int,
    caminho_manifesto: Path | None,
    saida: TextIO,
    demanda: Demanda | None = None,
) -> None:
    configuracao = plano.configuracao
    contagem = Counter(operacao.tipo_remoto for operacao in pendentes)
    _escrever(saida, "Plano de publicação\n")
    rotulo_demanda = f"#{configuracao.demanda_id}"
    if demanda is not None:
        rotulo_demanda = f"#{demanda.id} — {demanda.titulo}"
    _escrever(saida, f"Demanda de Negócio: {rotulo_demanda}\n")
    _escrever(saida, f"Organização: {configuracao.organizacao}\n")
    _escrever(saida, f"Projeto: {configuracao.projeto}\n")
    heranca = f" (herdado da Demanda #{configuracao.demanda_id})"
    _escrever(saida, f"Area Path: {configuracao.area_path}{heranca}\n")
    _escrever(saida, f"Iteration Path: {configuracao.iteration_path}{heranca}\n")
```

O restante da função permanece idêntico. Acrescentar também, logo depois de `Relações pai-filho`:

```python
    epicos = ", ".join(
        operacao.chave for operacao in pendentes if operacao.chave_pai is None
    )
    _escrever(
        saida,
        f"Épicos filhos da Demanda #{configuracao.demanda_id}: {epicos or 'nenhum'}\n",
    )
```

Acrescentar `Demanda` à importação de `modelos` no topo de `cli.py` — a Task 10 importou apenas
`ler_demanda`, e sem este import o parâmetro novo não tipa — e passar `demanda` na chamada dentro de
`principal`.

- [ ] **Step 4: Rodar a suíte inteira**

```bash
cd /Volumes/DOCK/Projetos/pessoal/gerador-hu/publicar-backlog-demanda-azure-boards
uv run pytest
```

Esperado: PASS.

- [ ] **Step 5: Commit**

```bash
cd /Volumes/DOCK/Projetos/pessoal/gerador-hu
git add publicar-backlog-demanda-azure-boards
git commit -m "feat: apresenta a Demanda de origem no plano de publicacao"
```

---

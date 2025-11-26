from __future__ import annotations
import concurrent.futures as futures
from pathlib import Path
import os, shutil, subprocess, sys
import typer
from rich.console import Console
from rich.progress import Progress
from .handlers import route_file
from .utils import discover_inputs

app = typer.Typer(help="Converte arquivos em PDF rapidamente")
console = Console()

# Função movida para o nível superior e ajustada para receber argumentos adicionais

def work(item, timeout, optimize, lo_listener):
    src, dst = item
    try:
        route_file(src, dst, timeout=timeout, optimize=optimize, lo_listener=lo_listener)
        return (src, dst, True, "")
    except Exception as e:
        return (src, dst, False, str(e))

# Função auxiliar para encapsular os argumentos necessários para o ProcessPoolExecutor

def work_with_args(item_and_args):
    item, timeout, optimize, lo_listener = item_and_args
    return work(item, timeout, optimize, lo_listener)

@app.command()
def main(
    paths: list[str] = typer.Argument(..., help="Arquivos, pastas ou globs"),
    outdir: Path | None = typer.Option(None, help="Diretório de saída (se não informado, usa pasta do arquivo de origem)"),
    jobs: int = typer.Option(0, help="Nº de processos (0 = núcleos)"),
    timeout: int = typer.Option(60, help="Timeout por arquivo (s)"),
    optimize: str | None = typer.Option(None, help="Perfil Ghostscript"),
    lo_listener: bool = typer.Option(False, help="Usa listener do LibreOffice"),
    overwrite: bool = typer.Option(False, help="Sobrescreve PDFs existentes"),
    dry_run: bool = typer.Option(False, help="Apenas lista conversões"),
    verbose: bool = typer.Option(False, "--verbose", "-v"),
):
    files = discover_inputs(paths)
    if not files:
        typer.secho("Nenhum arquivo encontrado.", fg=typer.colors.RED)
        raise typer.Exit(code=2)

    max_workers = os.cpu_count() if jobs in (0, None) else jobs
    tasks = []
    skipped = []
    # Se outdir foi fornecido explicitamente, garanta que exista
    if outdir is not None:
        outdir.mkdir(parents=True, exist_ok=True)
    for src in files:
        srcp = Path(src)

        if outdir is not None:
            dst = outdir / (srcp.stem + ".pdf")
        else:
            dst = srcp.with_suffix(".pdf")

        # Garantir que o diretório de destino exista somente quando necessário
        if dst.exists() and not overwrite:
            skipped.append((src, str(dst)))
            # Aviso imediato ao usuário com boas práticas de UX
            typer.secho(f"Ignorado: '{srcp.name}' - já existe em '{dst.parent}'", fg=typer.colors.YELLOW)
            typer.secho("Dica: use --overwrite para substituir ou --outdir para escolher outro diretório.", fg=typer.colors.CYAN)
            continue
        tasks.append((src, str(dst)))

    if dry_run:
        for src, dst in tasks:
            typer.echo(f"DRY-RUN: {src} -> {dst}")
        raise typer.Exit(0)

    with Progress() as progress:
        t = progress.add_task("Convertendo...", total=len(tasks))

        with futures.ProcessPoolExecutor(max_workers=max_workers) as ex:
            args = [(task, timeout, optimize, lo_listener) for task in tasks]
            for ok in ex.map(work_with_args, args):
                progress.update(t, advance=1)

    # Relatório simples
    # Verifica existência final dos arquivos de saída conforme caminhos alvo calculados
    success = [x for x in tasks if Path(x[1]).exists()]
    failed = [x for x in tasks if not Path(x[1]).exists()]
    console.print(f"Sucesso: {len(success)} | Falhas: {len(failed)}")
    if skipped:
        console.print(f"Ignorados ({len(skipped)}) por já existirem; use --overwrite para forçar:")
        for s, d in skipped:
            console.print(f"  - {s} -> {d}")

if __name__ == "__main__":
    app()


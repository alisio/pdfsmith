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
    outdir: Path = typer.Option(Path("./out"), help="Diretório de saída"),
    jobs: int = typer.Option(0, help="Nº de processos (0 = núcleos)"),
    timeout: int = typer.Option(60, help="Timeout por arquivo (s)"),
    optimize: str | None = typer.Option(None, help="Perfil Ghostscript"),
    lo_listener: bool = typer.Option(False, help="Usa listener do LibreOffice"),
    overwrite: bool = typer.Option(False, help="Sobrescreve PDFs existentes"),
    dry_run: bool = typer.Option(False, help="Apenas lista conversões"),
    verbose: bool = typer.Option(False, "--verbose", "-v"),
):
    outdir.mkdir(parents=True, exist_ok=True)
    files = discover_inputs(paths)
    if not files:
        typer.secho("Nenhum arquivo encontrado.", fg=typer.colors.RED)
        raise typer.Exit(code=2)

    max_workers = os.cpu_count() if jobs in (0, None) else jobs
    tasks = []
    for src in files:
        dst = outdir / (Path(src).stem + ".pdf")
        if dst.exists() and not overwrite:
            continue
        tasks.append((src, dst))

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
    success = [x for x in tasks if Path(outdir / (Path(x[0]).stem + ".pdf")).exists()]
    failed = [x for x in tasks if not Path(outdir / (Path(x[0]).stem + ".pdf")).exists()]
    console.print(f"Sucesso: {len(success)} | Falhas: {len(failed)}")

if __name__ == "__main__":
    app()

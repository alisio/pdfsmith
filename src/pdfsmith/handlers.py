from __future__ import annotations
from pathlib import Path
from tempfile import TemporaryDirectory
import subprocess, shutil
from markdown_it import MarkdownIt

EXT_MD = {".md", ".markdown", ".txt"}
EXT_OFFICE = {".docx", ".doc", ".pptx", ".xlsx", ".odt", ".odp", ".ods"}

class CmdErr(RuntimeError):
    pass

def run(cmd, timeout=None):
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if r.returncode != 0:
        raise CmdErr(f"cmd failed: {' '.join(cmd)}\n{r.stderr}")
    return r

def detect(cmds):
    for c in cmds:
        p = shutil.which(c)
        if p:
            return p
    return None

CHROME_CANDIDATES = [
    "chrome", "google-chrome", "google-chrome-stable", "chromium", "chromium-browser",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
]

WKHTML = detect(["wkhtmltopdf"])
CHROME = detect(CHROME_CANDIDATES)
SOFFICE = detect(["soffice", "libreoffice"])
GS = detect(["gs", "gswin64c"])

def md_to_pdf(src: Path, dst: Path, timeout: int):
    text = Path(src).read_text(encoding="utf-8")
    
    # Se for Markdown, converter para HTML; se for TXT puro, apenas escapar HTML
    if src.suffix.lower() in {".md", ".markdown"}:
        content_html = MarkdownIt().render(text)
    else:
        # Para TXT puro, escapar HTML e preservar quebras de linha
        import html
        content_html = f"<pre>{html.escape(text)}</pre>"
    
    # Criar HTML com charset UTF-8 explícito
    html_document = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        pre {{ white-space: pre-wrap; word-wrap: break-word; font-family: monospace; }}
    </style>
</head>
<body>
{content_html}
</body>
</html>"""
    
    with TemporaryDirectory() as tmp:
        in_html = Path(tmp)/"in.html"
        in_html.write_text(html_document, encoding="utf-8")
        if WKHTML:
            run([WKHTML, "--quiet", str(in_html), str(dst)], timeout=timeout)
        elif CHROME:
            run([CHROME, "--headless", "--disable-gpu", f"--print-to-pdf={dst}", in_html.as_uri()], timeout=timeout)
        else:
            raise CmdErr("Nenhum motor HTML->PDF encontrado (wkhtmltopdf ou Chrome/Chromium)")

def office_to_pdf(src: Path, outdir: Path, timeout: int, lo_listener: bool):
    if not SOFFICE:
        raise CmdErr("LibreOffice (soffice) não encontrado")
    cmd = [SOFFICE, "--headless", "--nologo", "--nofirststartwizard",
           "--convert-to", "pdf", "--outdir", str(outdir), str(src)]
    run(cmd, timeout=timeout)

def pdf_passthrough(src: Path, dst: Path, timeout: int, optimize: str | None):
    if optimize and GS:
        cmd = [GS, "-sDEVICE=pdfwrite", f"-dPDFSETTINGS=/{optimize}",
               "-dNOPAUSE", "-dBATCH", "-dQUIET", f"-sOutputFile={dst}", str(src)]
        run(cmd, timeout=timeout)
    else:
        shutil.copyfile(src, dst)

def route_file(src: str, dst: str, timeout: int, optimize: str | None, lo_listener: bool):
    s, d = Path(src), Path(dst)
    ext = s.suffix.lower()
    if ext in EXT_MD:
        md_to_pdf(s, d, timeout)
    elif ext in EXT_OFFICE:
        d.parent.mkdir(parents=True, exist_ok=True)
        office_to_pdf(s, d.parent, timeout, lo_listener)
    elif ext == ".pdf":
        pdf_passthrough(s, d, timeout, optimize)
    else:
        # Tenta via LibreOffice
        d.parent.mkdir(parents=True, exist_ok=True)
        office_to_pdf(s, d.parent, timeout, lo_listener)

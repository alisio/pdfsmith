# pdfsmith

## Descrição

O `pdfsmith` é uma ferramenta de linha de comando (CLI) rápida e eficiente para converter vários formatos de arquivo em PDF. Ele suporta uma ampla gama de formatos, incluindo arquivos de texto, Markdown, documentos do Office, e muito mais.

## Requisitos

- **macOS** (12+) ou **Linux** (Ubuntu 20.04+/Debian-based)
- Python 3.10+
- Dependências nativas:
  - LibreOffice
  - Ghostscript
  - wkhtmltopdf (ou Google Chrome/Chromium como fallback)

## Instalação

### macOS

```bash
# Instale as dependências nativas
brew install --cask libreoffice ghostscript
brew install --cask wkhtmltopdf || brew install --cask google-chrome

# Configure o ambiente Python
python3 -m venv .venv && source .venv/bin/activate
pip install --upgrade pip
pip install .
```

### Linux

```bash
# Instale as dependências nativas
sudo apt update
sudo apt install -y libreoffice ghostscript wkhtmltopdf
sudo snap install chromium  # ou: sudo apt install chromium-browser

# Configure o ambiente Python
python3 -m venv .venv && source .venv/bin/activate
pip install --upgrade pip
pip install .
```

## Uso

### Comandos básicos

```bash
# Converter um único arquivo
pdfsmith docs/apresentacao.pptx --outdir ./pdfs

# Converter um lote com 8 processos e otimização leve
pdfsmith documentos/**/* --jobs 8 --optimize screen

# Apenas simular conversões
pdfsmith src/**/*.docx --dry-run -v
```

### Opções disponíveis

- `--outdir <dir>`: Diretório de saída (padrão: `./out`)
- `--jobs <N>`: Número de processos paralelos (padrão: núcleos da CPU)
- `--timeout <seg>`: Tempo limite por arquivo (padrão: 60 segundos)
- `--optimize [screen|ebook|printer|prepress|default]`: Otimização de PDF
- `--lo-listener`: Usa um listener persistente do LibreOffice
- `--overwrite`: Sobrescreve PDFs existentes
- `--dry-run`: Apenas lista as conversões sem executá-las
- `--verbose`: Exibe mais detalhes durante a execução

## Testes

Para executar os testes:

```bash
pytest tests/
```

## Contribuição

Contribuições são bem-vindas! Sinta-se à vontade para abrir issues ou enviar PRs.

## Licença

Este projeto está licenciado sob a licença MIT.

## Runtime dependencies
- fdb
- pg8000

## How to install:
`py -m pip install fdb pg8000`

## How to generate .exe:
`py -m pip install pyinstaller`
`cd output`
`py -m PyInstaller --onefile --windowed --name="ImportadorSistemaDatha" ../src/main.py`

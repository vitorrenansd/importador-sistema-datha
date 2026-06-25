## Runtime dependencies
- fdb
- pg8000

## How to install:
`py -m pip install fdb pg8000`

## How to generate .exe:
1. `py -m pip install pyinstaller`
2. `cd output`
3. `py -m PyInstaller --onefile --windowed --name="ImportadorSistemaDatha" ../src/main.py`

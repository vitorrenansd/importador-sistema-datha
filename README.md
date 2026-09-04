## Runtime dependencies
- firebirdsql
- passlib
- pg8000

`firebirdsql` e um driver puro Python: fala o wire protocol direto com o
servidor Firebird, sem depender da `fbclient.dll` instalada na maquina.
Isso permite rodar contra Firebird 2.1 (o `fdb` exige client 2.5+, e falha
com `function 'fb_shutdown_callback' not found`).

`passlib` e dependencia opcional do `firebirdsql`, exigida pelo Legacy_Auth
- o modo de autenticacao do Firebird 2.1. Sem ele a conexao falha com
`No module named 'passlib'`. Precisa estar instalado no ambiente que gera
o .exe, senao o PyInstaller nao o empacota.

## How to install:
`py -m pip install firebirdsql passlib pg8000`

## How to generate .exe:
1. `py -m pip install pyinstaller`
2. `cd output`
3. `py -m PyInstaller --clean --onefile --windowed --name="ImportadorSistemaDatha" ../src/main.py`

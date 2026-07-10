"""Ponto de entrada da aplicação desktop.

Este arquivo mantém o arranque do sistema simples:
1. garante a existência das pastas do projeto;
2. inicializa o banco de dados;
3. cria a interface;
4. entrega o controle ao loop gráfico do Tkinter.
"""

from config import ensure_project_dirs
from database import Database
from interface.app import MultiplicaApp


def main() -> None:
    """Executa a sequência mínima de inicialização antes de abrir a janela."""
    ensure_project_dirs()
    database = Database()
    database.initialize()
    app = MultiplicaApp(database)
    app.mainloop()


if __name__ == "__main__":
    main()

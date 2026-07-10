from pathlib import Path
import re
import unicodedata


APP_NAME = "Multiplica Evidências"
APP_VERSION = "2,015"
APP_VERSION_TAG = "v2.015"
BASE_DIR = Path(__file__).resolve().parent
INTERFACE_DIR = BASE_DIR / "interface"
MODELOS_DIR = BASE_DIR / "modelos"
DATA_DIR = BASE_DIR / "data"
DOCS_DIR = BASE_DIR / "docs"
EVIDENCIAS_DIR = BASE_DIR / "evidencias"
ACOMPANHAMENTOS_DIR = BASE_DIR / "acompanhamentos"
SOCIALIZACOES_DIR = BASE_DIR / "socializacoes"
SAIDAS_DIR = BASE_DIR / "saidas"
BACKUP_DIR = SAIDAS_DIR / "backups"
DB_PATH = DATA_DIR / "multiplica.db"
MODEL_DOCX_PATH = MODELOS_DIR / "evidencias.docx"
GUIA_RAPIDO_PATH = DOCS_DIR / "guia_rapido.md"
MANUAL_USUARIO_PATH = DOCS_DIR / "manual_usuario.md"
MANUAL_EDITORIAL_PATH = DOCS_DIR / "manual_usuario_editorial.md"
AJUDA_RESUMIDA_PATH = DOCS_DIR / "ajuda_resumida.md"


def ensure_project_dirs() -> None:
    for path in (
        DATA_DIR,
        DOCS_DIR,
        EVIDENCIAS_DIR,
        ACOMPANHAMENTOS_DIR,
        SOCIALIZACOES_DIR,
        SAIDAS_DIR,
        BACKUP_DIR,
        MODELOS_DIR,
    ):
        path.mkdir(parents=True, exist_ok=True)


def slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value or "")
    ascii_only = normalized.encode("ascii", "ignore").decode("ascii")
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", ascii_only.strip())
    return cleaned.strip("._") or "item"

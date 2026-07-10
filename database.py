"""Camada de persistência da aplicação baseada em SQLite.

Toda leitura e gravação de dados passa por este módulo. A interface não fala
diretamente com SQL: ela pede operações para a classe `Database`, que centraliza
esquema, normalização e consultas.
"""

from datetime import datetime
import re
import shutil
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional

from config import (
    BACKUP_DIR,
    DB_PATH,
    EVIDENCIAS_DIR,
    slugify,
)
from models import MONTH_NAMES_PT, ProfessorDefaults


class Database:
    """Encapsula acesso ao banco e regras de persistência do projeto."""

    def __init__(self, db_path: Path = DB_PATH) -> None:
        """Permite trocar o caminho do banco em cenários de teste ou manutenção."""
        self.db_path = Path(db_path)

    def connect(self) -> sqlite3.Connection:
        """Abre conexão configurada para retornar linhas nomeadas (`sqlite3.Row`)."""
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def initialize(self) -> None:
        """Cria a estrutura do banco e aplica ajustes de compatibilidade."""
        with self.connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS app_config (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS month_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ref_month INTEGER NOT NULL,
                    ref_year INTEGER NOT NULL,
                    ref_label TEXT NOT NULL,
                    teacher_name TEXT NOT NULL DEFAULT '',
                    theme TEXT NOT NULL DEFAULT '',
                    institutional_email TEXT NOT NULL DEFAULT '',
                    diretoria_ure TEXT NOT NULL DEFAULT '',
                    pec_responsavel TEXT NOT NULL DEFAULT '',
                    weekly_rate_cents INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(ref_month, ref_year)
                );

                CREATE TABLE IF NOT EXISTS turmas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    codigo TEXT NOT NULL UNIQUE,
                    dia_semana TEXT NOT NULL DEFAULT '',
                    horario TEXT NOT NULL DEFAULT '',
                    componente TEXT NOT NULL DEFAULT '',
                    situacao TEXT NOT NULL DEFAULT 'ativa',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS encontros (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    month_id INTEGER NOT NULL,
                    turma_id INTEGER NOT NULL,
                    data_encontro TEXT NOT NULL,
                    pauta_numero INTEGER NOT NULL,
                    hora_inicio TEXT NOT NULL DEFAULT '',
                    hora_fim TEXT NOT NULL DEFAULT '',
                    participantes INTEGER,
                    duracao TEXT NOT NULL DEFAULT '',
                    observacao TEXT NOT NULL DEFAULT '',
                    situacao TEXT NOT NULL DEFAULT 'realizado',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(month_id, turma_id, data_encontro, pauta_numero),
                    FOREIGN KEY(month_id) REFERENCES month_records(id) ON DELETE CASCADE,
                    FOREIGN KEY(turma_id) REFERENCES turmas(id)
                );

                CREATE TABLE IF NOT EXISTS evidencias (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    encontro_id INTEGER NOT NULL,
                    arquivo_original TEXT NOT NULL DEFAULT '',
                    arquivo_copiado TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(encontro_id) REFERENCES encontros(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS cursistas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL,
                    turma_id INTEGER,
                    email_institucional TEXT NOT NULL DEFAULT '',
                    email_pessoal TEXT NOT NULL DEFAULT '',
                    telefone_whatsapp TEXT NOT NULL DEFAULT '',
                    status_busca_ativa TEXT NOT NULL DEFAULT 'nao_iniciado',
                    observacao_geral TEXT NOT NULL DEFAULT '',
                    ativo INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(turma_id) REFERENCES turmas(id)
                );

                CREATE TABLE IF NOT EXISTS acompanhamentos_cursistas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cursista_id INTEGER NOT NULL,
                    turma_id INTEGER,
                    encontro_id INTEGER,
                    categoria TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'aberto',
                    prioridade TEXT NOT NULL DEFAULT 'normal',
                    resumo TEXT NOT NULL,
                    descricao TEXT NOT NULL DEFAULT '',
                    encaminhar_pec INTEGER NOT NULL DEFAULT 0,
                    data_abertura TEXT NOT NULL,
                    data_resolucao TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(cursista_id) REFERENCES cursistas(id) ON DELETE CASCADE,
                    FOREIGN KEY(turma_id) REFERENCES turmas(id),
                    FOREIGN KEY(encontro_id) REFERENCES encontros(id)
                );

                CREATE TABLE IF NOT EXISTS socializacoes_cursistas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cursista_id INTEGER NOT NULL,
                    turma_id INTEGER,
                    mes_referencia INTEGER NOT NULL,
                    ano_referencia INTEGER NOT NULL,
                    status_envio TEXT NOT NULL DEFAULT 'nao_enviada',
                    data_envio TEXT NOT NULL DEFAULT '',
                    observacao_pedagogica TEXT NOT NULL DEFAULT '',
                    necessita_apoio INTEGER NOT NULL DEFAULT 0,
                    destaque_potencial INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(cursista_id, mes_referencia, ano_referencia),
                    FOREIGN KEY(cursista_id) REFERENCES cursistas(id) ON DELETE CASCADE,
                    FOREIGN KEY(turma_id) REFERENCES turmas(id)
                );

                CREATE TABLE IF NOT EXISTS acompanhamento_movimentacoes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    acompanhamento_id INTEGER NOT NULL,
                    data_movimentacao TEXT NOT NULL,
                    descricao TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(acompanhamento_id) REFERENCES acompanhamentos_cursistas(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS acompanhamento_anexos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    acompanhamento_id INTEGER NOT NULL,
                    arquivo_original TEXT NOT NULL DEFAULT '',
                    arquivo_copiado TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(acompanhamento_id) REFERENCES acompanhamentos_cursistas(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS socializacao_movimentacoes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    socializacao_id INTEGER NOT NULL,
                    data_movimentacao TEXT NOT NULL,
                    descricao TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(socializacao_id) REFERENCES socializacoes_cursistas(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS socializacao_anexos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    socializacao_id INTEGER NOT NULL,
                    arquivo_original TEXT NOT NULL DEFAULT '',
                    arquivo_copiado TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(socializacao_id) REFERENCES socializacoes_cursistas(id) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_cursistas_nome
                ON cursistas(nome);

                CREATE INDEX IF NOT EXISTS idx_cursistas_turma_ativo
                ON cursistas(turma_id, ativo);

                CREATE INDEX IF NOT EXISTS idx_acompanhamentos_status_categoria
                ON acompanhamentos_cursistas(status, categoria);

                CREATE INDEX IF NOT EXISTS idx_acompanhamentos_cursista_data
                ON acompanhamentos_cursistas(cursista_id, data_abertura);

                CREATE INDEX IF NOT EXISTS idx_socializacoes_periodo_status
                ON socializacoes_cursistas(ano_referencia, mes_referencia, status_envio);

                CREATE INDEX IF NOT EXISTS idx_acompanhamento_movimentacoes_data
                ON acompanhamento_movimentacoes(acompanhamento_id, data_movimentacao);

                CREATE INDEX IF NOT EXISTS idx_socializacao_movimentacoes_data
                ON socializacao_movimentacoes(socializacao_id, data_movimentacao);
                """
            )
            self._ensure_column(
                connection,
                "month_records",
                "weekly_rate_cents",
                "INTEGER NOT NULL DEFAULT 0",
            )
        self.reconcile_data_by_encounter_date()

    def _ensure_column(
        self,
        connection: sqlite3.Connection,
        table_name: str,
        column_name: str,
        column_sql: str,
    ) -> None:
        columns = connection.execute(f"PRAGMA table_info({table_name})").fetchall()
        if any(str(column["name"]) == column_name for column in columns):
            return
        connection.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_sql}")

    def _parse_currency_to_cents(self, value: object) -> int:
        if value is None:
            return 0
        if isinstance(value, int):
            return max(value, 0)
        if isinstance(value, float):
            return max(int(round(value * 100)), 0)

        normalized = str(value).strip()
        if not normalized:
            return 0

        normalized = normalized.replace("R$", "").replace(" ", "")
        if "," in normalized and "." in normalized:
            if normalized.rfind(",") > normalized.rfind("."):
                normalized = normalized.replace(".", "").replace(",", ".")
            else:
                normalized = normalized.replace(",", "")
        elif "," in normalized:
            normalized = normalized.replace(".", "").replace(",", ".")
        amount = float(normalized)
        return max(int(round(amount * 100)), 0)

    def _save_cursista_on_connection(
        self,
        connection: sqlite3.Connection,
        data: Dict[str, object],
        cursista_id: Optional[int] = None,
    ) -> int:
        payload = (
            str(data.get("nome", "") or "").strip(),
            data.get("turma_id"),
            str(data.get("email_institucional", "") or "").strip(),
            str(data.get("email_pessoal", "") or "").strip(),
            str(data.get("telefone_whatsapp", "") or "").strip(),
            str(data.get("status_busca_ativa", "nao_iniciado") or "nao_iniciado").strip(),
            str(data.get("observacao_geral", "") or "").strip(),
            1 if bool(data.get("ativo", True)) else 0,
        )
        if cursista_id:
            connection.execute(
                """
                UPDATE cursistas
                SET nome = ?,
                    turma_id = ?,
                    email_institucional = ?,
                    email_pessoal = ?,
                    telefone_whatsapp = ?,
                    status_busca_ativa = ?,
                    observacao_geral = ?,
                    ativo = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                payload + (cursista_id,),
            )
            return cursista_id

        cursor = connection.execute(
            """
            INSERT INTO cursistas(
                nome,
                turma_id,
                email_institucional,
                email_pessoal,
                telefone_whatsapp,
                status_busca_ativa,
                observacao_geral,
                ativo
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            payload,
        )
        return int(cursor.lastrowid)

    def normalize_import_cursista_nome(self, value: object) -> str:
        normalized = " ".join(str(value or "").strip().split())
        if " - " in normalized:
            normalized = normalized.split(" - ", 1)[0].strip()
        return normalized

    def extract_import_turma_codigo(self, value: object) -> str:
        normalized = " ".join(str(value or "").strip().split())
        if not normalized:
            return ""
        if normalized.isdigit():
            return normalized

        without_period = re.sub(r"^\[[^\]]+\]\s*-\s*", "", normalized.upper())
        weekday_pattern = r"(SEG|TER|QUA|QUI|SEX|SAB|DOM)"
        structured_match = re.search(
            rf"(?:^|[A-Z]{{2,}}-)(\d{{3,6}})-{weekday_pattern}-\d{{1,2}}:\d{{2}}$",
            without_period,
        )
        if structured_match:
            return str(structured_match.group(1))

        fallback_match = re.search(rf"-(\d{{3,6}})-{weekday_pattern}\b", without_period)
        if fallback_match:
            return str(fallback_match.group(1))

        return ""

    def _parse_import_bool(self, value: object) -> Optional[bool]:
        if value is None:
            return None
        if isinstance(value, bool):
            return value

        normalized = str(value).strip().lower()
        if not normalized:
            return None
        if normalized in {"1", "sim", "s", "true", "ativo", "ativa"}:
            return True
        if normalized in {"0", "nao", "não", "n", "false", "inativo", "inativa"}:
            return False
        return None

    def _normalize_import_status_busca(self, value: object) -> str:
        normalized = str(value or "").strip().lower()
        if not normalized:
            return "nao_iniciado"
        if normalized in {
            "nao_iniciado",
            "em_contato",
            "aguardando_retorno",
            "localizado",
            "encerrado",
        }:
            return normalized
        return "nao_iniciado"

    def reconcile_data_by_encounter_date(self) -> int:
        """Corrige vínculos de mês usando a data real dos encontros.

        Essa rotina protege o histórico quando a regra de competência evolui.
        Em vez de confiar apenas no `month_id` antigo, ela compara a data do
        encontro e move o registro para o mês coerente, se necessário.
        """
        defaults = self.get_defaults()
        fixes_applied = 0

        with self.connect() as connection:
            encontros = connection.execute(
                """
                SELECT
                    encontros.id,
                    encontros.month_id,
                    encontros.turma_id,
                    encontros.data_encontro,
                    encontros.pauta_numero,
                    turmas.codigo AS turma_codigo,
                    month_records.ref_month,
                    month_records.ref_year
                FROM encontros
                JOIN turmas ON turmas.id = encontros.turma_id
                JOIN month_records ON month_records.id = encontros.month_id
                ORDER BY encontros.id
                """
            ).fetchall()

            for encontro in encontros:
                encounter_date = datetime.strptime(encontro["data_encontro"], "%Y-%m-%d")
                target_month_id = int(encontro["month_id"])
                target_month = connection.execute(
                    """
                    SELECT id
                    FROM month_records
                    WHERE ref_month = ? AND ref_year = ?
                    """,
                    (encounter_date.month, encounter_date.year),
                ).fetchone()

                if target_month:
                    target_month_id = int(target_month["id"])
                else:
                    cursor = connection.execute(
                        """
                        INSERT INTO month_records(
                            ref_month,
                            ref_year,
                            ref_label,
                            teacher_name,
                            theme,
                            institutional_email,
                            diretoria_ure,
                            pec_responsavel,
                            weekly_rate_cents
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            encounter_date.month,
                            encounter_date.year,
                            self._month_label(encounter_date.month, encounter_date.year),
                            defaults["nome"],
                            defaults["tema"],
                            defaults["email_institucional"],
                            defaults["diretoria_ure"],
                            defaults["pec_responsavel"],
                            self._parse_currency_to_cents(defaults.get("valor_formacao_semanal", "")),
                        ),
                    )
                    target_month_id = int(cursor.lastrowid)

                if (
                    int(encontro["ref_month"]) != encounter_date.month
                    or int(encontro["ref_year"]) != encounter_date.year
                ):
                    connection.execute(
                        "UPDATE encontros SET month_id = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                        (target_month_id, int(encontro["id"])),
                    )
                    fixes_applied += 1

                evidencias = connection.execute(
                    """
                    SELECT id, arquivo_copiado
                    FROM evidencias
                    WHERE encontro_id = ?
                    ORDER BY id
                    """,
                    (int(encontro["id"]),),
                ).fetchall()

                target_dir = (
                    EVIDENCIAS_DIR
                    / f"{encounter_date.year}-{encounter_date.month:02d}"
                    / slugify(str(encontro["turma_codigo"]))
                    / f"pauta_{int(encontro['pauta_numero']):02d}"
                )
                target_dir.mkdir(parents=True, exist_ok=True)

                for index, evidencia in enumerate(evidencias, start=1):
                    current_path = Path(str(evidencia["arquivo_copiado"]))
                    extension = current_path.suffix or ".png"
                    target_path = target_dir / f"{encontro['data_encontro']}_{index:02d}{extension}"
                    if current_path == target_path:
                        continue

                    if current_path.exists():
                        if target_path.exists() and current_path.resolve() != target_path.resolve():
                            target_path.unlink()
                        shutil.move(str(current_path), str(target_path))

                    connection.execute(
                        """
                        UPDATE evidencias
                        SET arquivo_copiado = ?
                        WHERE id = ?
                        """,
                        (str(target_path), int(evidencia["id"])),
                    )

        return fixes_applied

    def _month_label(self, ref_month: int, ref_year: int) -> str:
        nome_mes = MONTH_NAMES_PT.get(ref_month, str(ref_month))
        return f"{ref_month:02d}/{ref_year} - {nome_mes}"

    def get_defaults(self) -> Dict[str, str]:
        keys = [
            "nome",
            "tema",
            "email_institucional",
            "diretoria_ure",
            "pec_responsavel",
            "valor_formacao_semanal",
        ]
        defaults = {key: "" for key in keys}
        with self.connect() as connection:
            rows = connection.execute(
                "SELECT key, value FROM app_config WHERE key IN (?, ?, ?, ?, ?, ?)",
                keys,
            ).fetchall()
        for row in rows:
            defaults[row["key"]] = row["value"]
        return defaults

    def save_defaults(self, data: Dict[str, str]) -> None:
        with self.connect() as connection:
            for key, value in data.items():
                connection.execute(
                    """
                    INSERT INTO app_config(key, value)
                    VALUES(?, ?)
                    ON CONFLICT(key) DO UPDATE SET value = excluded.value
                    """,
                    (key, value or ""),
                )

    def get_app_config_value(self, key: str, default: str = "") -> str:
        with self.connect() as connection:
            row = connection.execute(
                "SELECT value FROM app_config WHERE key = ?",
                (key,),
            ).fetchone()
        if not row:
            return default
        return str(row["value"])

    def set_app_config_value(self, key: str, value: str) -> None:
        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO app_config(key, value)
                VALUES(?, ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value
                """,
                (key, value),
            )

    def list_months(self) -> List[sqlite3.Row]:
        with self.connect() as connection:
            return connection.execute(
                """
                SELECT id, ref_month, ref_year, ref_label
                FROM month_records
                ORDER BY ref_year DESC, ref_month DESC
                """
            ).fetchall()

    def get_month(self, month_id: int) -> Optional[sqlite3.Row]:
        with self.connect() as connection:
            return connection.execute(
                "SELECT * FROM month_records WHERE id = ?",
                (month_id,),
            ).fetchone()

    def get_month_by_reference(self, ref_month: int, ref_year: int) -> Optional[sqlite3.Row]:
        with self.connect() as connection:
            return connection.execute(
                """
                SELECT *
                FROM month_records
                WHERE ref_month = ? AND ref_year = ?
                """,
                (ref_month, ref_year),
            ).fetchone()

    def get_or_create_month(self, ref_month: int, ref_year: int) -> int:
        defaults = self.get_defaults()
        label = self._month_label(ref_month, ref_year)
        with self.connect() as connection:
            existing = connection.execute(
                """
                SELECT id FROM month_records
                WHERE ref_month = ? AND ref_year = ?
                """,
                (ref_month, ref_year),
            ).fetchone()
            if existing:
                return int(existing["id"])

            cursor = connection.execute(
                """
                INSERT INTO month_records(
                    ref_month,
                    ref_year,
                    ref_label,
                    teacher_name,
                    theme,
                    institutional_email,
                    diretoria_ure,
                    pec_responsavel,
                    weekly_rate_cents
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    ref_month,
                    ref_year,
                    label,
                    defaults["nome"],
                    defaults["tema"],
                    defaults["email_institucional"],
                    defaults["diretoria_ure"],
                    defaults["pec_responsavel"],
                    self._parse_currency_to_cents(defaults.get("valor_formacao_semanal", "")),
                ),
            )
            return int(cursor.lastrowid)

    def save_month(self, month_id: int, data: Dict[str, str], update_weekly_rate: bool = True) -> None:
        month = self.get_month(month_id)
        if not month:
            raise ValueError("Mês de referência não encontrado.")

        with self.connect() as connection:
            if update_weekly_rate:
                connection.execute(
                    """
                    UPDATE month_records
                    SET teacher_name = ?,
                        theme = ?,
                        institutional_email = ?,
                        diretoria_ure = ?,
                        pec_responsavel = ?,
                        weekly_rate_cents = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (
                        data.get("nome", ""),
                        data.get("tema", ""),
                        data.get("email_institucional", ""),
                        data.get("diretoria_ure", ""),
                        data.get("pec_responsavel", ""),
                        self._parse_currency_to_cents(data.get("valor_formacao_semanal", "")),
                        month_id,
                    ),
                )
            else:
                connection.execute(
                    """
                    UPDATE month_records
                    SET teacher_name = ?,
                        theme = ?,
                        institutional_email = ?,
                        diretoria_ure = ?,
                        pec_responsavel = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (
                        data.get("nome", ""),
                        data.get("tema", ""),
                        data.get("email_institucional", ""),
                        data.get("diretoria_ure", ""),
                        data.get("pec_responsavel", ""),
                        month_id,
                    ),
                )

    def list_turmas(self, include_inactive: bool = True) -> List[sqlite3.Row]:
        query = """
            SELECT *
            FROM turmas
        """
        params: tuple = ()
        if not include_inactive:
            query += " WHERE situacao = ?"
            params = ("ativa",)
        query += " ORDER BY codigo"
        with self.connect() as connection:
            return connection.execute(query, params).fetchall()

    def get_turma(self, turma_id: int) -> Optional[sqlite3.Row]:
        with self.connect() as connection:
            return connection.execute(
                "SELECT * FROM turmas WHERE id = ?",
                (turma_id,),
            ).fetchone()

    def get_turma_by_codigo(self, codigo: str) -> Optional[sqlite3.Row]:
        normalized = str(codigo or "").strip()
        if not normalized:
            return None
        with self.connect() as connection:
            return connection.execute(
                "SELECT * FROM turmas WHERE codigo = ?",
                (normalized,),
            ).fetchone()

    def save_turma(self, data: Dict[str, str], turma_id: Optional[int] = None) -> int:
        payload = (
            data.get("codigo", "").strip(),
            data.get("dia_semana", "").strip(),
            data.get("horario", "").strip(),
            data.get("componente", "").strip(),
            data.get("situacao", "ativa").strip() or "ativa",
        )
        with self.connect() as connection:
            if turma_id:
                connection.execute(
                    """
                    UPDATE turmas
                    SET codigo = ?,
                        dia_semana = ?,
                        horario = ?,
                        componente = ?,
                        situacao = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    payload + (turma_id,),
                )
                return turma_id

            cursor = connection.execute(
                """
                INSERT INTO turmas(codigo, dia_semana, horario, componente, situacao)
                VALUES (?, ?, ?, ?, ?)
                """,
                payload,
            )
            return int(cursor.lastrowid)

    def list_cursistas(
        self,
        include_inactive: bool = True,
        turma_id: Optional[int] = None,
        search: str = "",
        status_busca_ativa: str = "",
    ) -> List[sqlite3.Row]:
        query = """
            SELECT
                cursistas.*,
                turmas.codigo AS turma_codigo
            FROM cursistas
            LEFT JOIN turmas ON turmas.id = cursistas.turma_id
            WHERE 1 = 1
        """
        params: list[object] = []
        if not include_inactive:
            query += " AND cursistas.ativo = 1"
        if turma_id:
            query += " AND cursistas.turma_id = ?"
            params.append(turma_id)
        if status_busca_ativa:
            query += " AND cursistas.status_busca_ativa = ?"
            params.append(status_busca_ativa)
        if search.strip():
            query += " AND LOWER(cursistas.nome) LIKE ?"
            params.append(f"%{search.strip().lower()}%")
        query += " ORDER BY LOWER(cursistas.nome), cursistas.id"

        with self.connect() as connection:
            return connection.execute(query, tuple(params)).fetchall()

    def get_cursista(self, cursista_id: int) -> Optional[sqlite3.Row]:
        with self.connect() as connection:
            return connection.execute(
                """
                SELECT
                    cursistas.*,
                    turmas.codigo AS turma_codigo
                FROM cursistas
                LEFT JOIN turmas ON turmas.id = cursistas.turma_id
                WHERE cursistas.id = ?
                """,
                (cursista_id,),
            ).fetchone()

    def save_cursista(self, data: Dict[str, object], cursista_id: Optional[int] = None) -> int:
        with self.connect() as connection:
            return self._save_cursista_on_connection(connection, data, cursista_id)

    def find_cursistas_by_nome_turma(
        self,
        nome: str,
        turma_id: int,
        include_inactive: bool = True,
    ) -> List[sqlite3.Row]:
        query = """
            SELECT
                cursistas.*,
                turmas.codigo AS turma_codigo
            FROM cursistas
            LEFT JOIN turmas ON turmas.id = cursistas.turma_id
            WHERE LOWER(TRIM(cursistas.nome)) = ?
              AND cursistas.turma_id = ?
        """
        params: list[object] = [nome.strip().lower(), turma_id]
        if not include_inactive:
            query += " AND cursistas.ativo = 1"
        query += " ORDER BY cursistas.ativo DESC, cursistas.id"
        with self.connect() as connection:
            return connection.execute(query, tuple(params)).fetchall()

    def preview_cursista_import(self, rows: List[Dict[str, object]]) -> Dict[str, object]:
        preview_rows: list[dict[str, object]] = []
        totals = {"novo": 0, "atualizar": 0, "conflito": 0, "ignorado": 0}
        seen_keys: dict[tuple[str, str], int] = {}

        with self.connect() as connection:
            for index, raw_row in enumerate(rows, start=1):
                source_row = index
                if raw_row.get("source_row") is not None:
                    try:
                        source_row = int(raw_row.get("source_row"))
                    except (TypeError, ValueError):
                        source_row = index

                nome = self.normalize_import_cursista_nome(raw_row.get("nome", ""))
                raw_turma = raw_row.get("turma_codigo", raw_row.get("turma", ""))
                turma_codigo = self.extract_import_turma_codigo(raw_turma)
                email = str(
                    raw_row.get("email_pessoal", raw_row.get("email", "")) or ""
                ).strip()
                telefone = str(
                    raw_row.get("telefone_whatsapp", raw_row.get("telefone", "")) or ""
                ).strip()
                observacao = str(raw_row.get("observacao_geral", "") or "").strip()
                status_busca_raw = str(raw_row.get("status_busca_ativa", "") or "").strip()
                status_busca = self._normalize_import_status_busca(status_busca_raw)
                ativo_value = self._parse_import_bool(raw_row.get("ativo"))

                preview_row: dict[str, object] = {
                    "source_row": source_row,
                    "nome": nome,
                    "turma_codigo": turma_codigo,
                    "email_pessoal": email,
                    "telefone_whatsapp": telefone,
                    "observacao_geral": observacao,
                    "status_busca_ativa": status_busca,
                    "status_busca_informado": bool(status_busca_raw),
                    "ativo": True if ativo_value is None else ativo_value,
                    "ativo_informado": ativo_value is not None,
                    "status": "ignorado",
                    "motivo": "",
                    "turma_id": None,
                    "cursista_id": None,
                }

                if not any([nome, turma_codigo, email, telefone, observacao]):
                    preview_row["motivo"] = "linha_vazia"
                    preview_rows.append(preview_row)
                    totals["ignorado"] += 1
                    continue

                if not nome:
                    preview_row["status"] = "conflito"
                    preview_row["motivo"] = "nome_nao_identificado"
                    preview_rows.append(preview_row)
                    totals["conflito"] += 1
                    continue

                if not turma_codigo:
                    preview_row["status"] = "conflito"
                    preview_row["motivo"] = "turma_nao_identificada"
                    preview_rows.append(preview_row)
                    totals["conflito"] += 1
                    continue

                duplicate_key = (nome.lower(), turma_codigo)
                if duplicate_key in seen_keys:
                    preview_row["status"] = "conflito"
                    preview_row["motivo"] = f"duplicada_na_planilha_linha_{seen_keys[duplicate_key]}"
                    preview_rows.append(preview_row)
                    totals["conflito"] += 1
                    continue
                seen_keys[duplicate_key] = source_row

                turma_row = connection.execute(
                    "SELECT * FROM turmas WHERE codigo = ?",
                    (turma_codigo,),
                ).fetchone()
                if not turma_row:
                    preview_row["status"] = "conflito"
                    preview_row["motivo"] = "turma_nao_cadastrada"
                    preview_rows.append(preview_row)
                    totals["conflito"] += 1
                    continue

                turma_id = int(turma_row["id"])
                preview_row["turma_id"] = turma_id

                matched_rows = connection.execute(
                    """
                    SELECT
                        cursistas.*,
                        turmas.codigo AS turma_codigo
                    FROM cursistas
                    LEFT JOIN turmas ON turmas.id = cursistas.turma_id
                    WHERE LOWER(TRIM(cursistas.nome)) = ?
                      AND cursistas.turma_id = ?
                    ORDER BY cursistas.ativo DESC, cursistas.id
                    """,
                    (nome.lower(), turma_id),
                ).fetchall()
                if len(matched_rows) > 1:
                    preview_row["status"] = "conflito"
                    preview_row["motivo"] = "mais_de_um_cursista_mesmo_nome_turma"
                    preview_rows.append(preview_row)
                    totals["conflito"] += 1
                    continue

                if matched_rows:
                    preview_row["status"] = "atualizar"
                    preview_row["cursista_id"] = int(matched_rows[0]["id"])
                    preview_rows.append(preview_row)
                    totals["atualizar"] += 1
                    continue

                if email:
                    email_match = connection.execute(
                        """
                        SELECT id
                        FROM cursistas
                        WHERE LOWER(TRIM(email_pessoal)) = ?
                        ORDER BY ativo DESC, id
                        """,
                        (email.lower(),),
                    ).fetchall()
                    if email_match:
                        preview_row["status"] = "conflito"
                        preview_row["motivo"] = "email_ja_cadastrado"
                        preview_rows.append(preview_row)
                        totals["conflito"] += 1
                        continue

                preview_row["status"] = "novo"
                preview_rows.append(preview_row)
                totals["novo"] += 1

        return {
            "rows": preview_rows,
            "totals": totals,
            "processavel": totals["novo"] + totals["atualizar"],
        }

    def apply_cursista_import(self, rows: List[Dict[str, object]]) -> Dict[str, object]:
        preview = self.preview_cursista_import(rows)
        applied_rows: list[dict[str, object]] = []
        inserted = 0
        updated = 0

        with self.connect() as connection:
            for item in preview["rows"]:
                status = str(item.get("status") or "")
                if status not in {"novo", "atualizar"}:
                    applied_rows.append(item)
                    continue

                payload = {
                    "nome": item["nome"],
                    "turma_id": item["turma_id"],
                    "email_institucional": "",
                    "email_pessoal": item["email_pessoal"],
                    "telefone_whatsapp": item["telefone_whatsapp"],
                    "status_busca_ativa": item["status_busca_ativa"],
                    "observacao_geral": item["observacao_geral"],
                    "ativo": item["ativo"],
                }

                if status == "atualizar":
                    existing = connection.execute(
                        "SELECT * FROM cursistas WHERE id = ?",
                        (item["cursista_id"],),
                    ).fetchone()
                    if not existing:
                        updated_item = dict(item)
                        updated_item["status"] = "conflito"
                        updated_item["motivo"] = "cursista_nao_encontrado_na_aplicacao"
                        applied_rows.append(updated_item)
                        continue

                    payload["email_institucional"] = str(existing["email_institucional"] or "")
                    payload["email_pessoal"] = (
                        str(item["email_pessoal"] or "").strip()
                        or str(existing["email_pessoal"] or "").strip()
                    )
                    payload["telefone_whatsapp"] = (
                        str(item["telefone_whatsapp"] or "").strip()
                        or str(existing["telefone_whatsapp"] or "").strip()
                    )
                    payload["observacao_geral"] = (
                        str(item["observacao_geral"] or "").strip()
                        or str(existing["observacao_geral"] or "").strip()
                    )
                    if bool(item.get("status_busca_informado")):
                        payload["status_busca_ativa"] = str(
                            item["status_busca_ativa"] or "nao_iniciado"
                        ).strip()
                    else:
                        payload["status_busca_ativa"] = str(
                            existing["status_busca_ativa"] or "nao_iniciado"
                        ).strip()
                    if not bool(item.get("ativo_informado")):
                        payload["ativo"] = bool(existing["ativo"])

                saved_id = self._save_cursista_on_connection(
                    connection,
                    payload,
                    int(item["cursista_id"]) if item.get("cursista_id") else None,
                )
                updated_item = dict(item)
                updated_item["cursista_id"] = saved_id
                updated_item["aplicado"] = True
                applied_rows.append(updated_item)
                if status == "novo":
                    inserted += 1
                else:
                    updated += 1

        return {
            "rows": applied_rows,
            "totals": preview["totals"],
            "processavel": preview["processavel"],
            "inseridos": inserted,
            "atualizados": updated,
        }

    def deactivate_cursista(self, cursista_id: int) -> None:
        with self.connect() as connection:
            connection.execute(
                """
                UPDATE cursistas
                SET ativo = 0,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (cursista_id,),
            )

    def list_encontros_for_turma(
        self,
        turma_id: int,
        month_id: Optional[int] = None,
    ) -> List[sqlite3.Row]:
        query = """
            SELECT
                encontros.id,
                encontros.month_id,
                encontros.turma_id,
                encontros.data_encontro,
                encontros.pauta_numero,
                turmas.codigo AS turma_codigo
            FROM encontros
            JOIN turmas ON turmas.id = encontros.turma_id
            WHERE encontros.turma_id = ?
        """
        params: list[object] = [turma_id]
        if month_id:
            query += " AND encontros.month_id = ?"
            params.append(month_id)
        query += " ORDER BY encontros.data_encontro DESC, encontros.pauta_numero DESC"

        with self.connect() as connection:
            return connection.execute(query, tuple(params)).fetchall()

    def list_acompanhamentos(
        self,
        status_filter: str = "",
        turma_id: Optional[int] = None,
        categoria: str = "",
        search: str = "",
        attachment_filter: str = "",
        movement_filter: str = "",
    ) -> List[sqlite3.Row]:
        query = """
            SELECT
                acompanhamentos_cursistas.*,
                cursistas.nome AS cursista_nome,
                turmas.codigo AS turma_codigo,
                encontros.data_encontro AS encontro_data,
                encontros.pauta_numero AS encontro_pauta,
                (SELECT COUNT(*) FROM acompanhamento_anexos WHERE acompanhamento_id = acompanhamentos_cursistas.id) AS total_anexos,
                (SELECT COUNT(*) FROM acompanhamento_movimentacoes WHERE acompanhamento_id = acompanhamentos_cursistas.id) AS total_movimentacoes
            FROM acompanhamentos_cursistas
            JOIN cursistas ON cursistas.id = acompanhamentos_cursistas.cursista_id
            LEFT JOIN turmas ON turmas.id = acompanhamentos_cursistas.turma_id
            LEFT JOIN encontros ON encontros.id = acompanhamentos_cursistas.encontro_id
            WHERE 1 = 1
        """
        params: list[object] = []
        if status_filter:
            if status_filter == "abertas":
                query += " AND acompanhamentos_cursistas.status NOT IN ('resolvido', 'arquivado')"
            else:
                query += " AND acompanhamentos_cursistas.status = ?"
                params.append(status_filter)
        if turma_id:
            query += " AND acompanhamentos_cursistas.turma_id = ?"
            params.append(turma_id)
        if categoria:
            query += " AND acompanhamentos_cursistas.categoria = ?"
            params.append(categoria)
        if search.strip():
            query += " AND (LOWER(cursistas.nome) LIKE ? OR LOWER(acompanhamentos_cursistas.resumo) LIKE ?)"
            like_value = f"%{search.strip().lower()}%"
            params.extend([like_value, like_value])
        if attachment_filter == "com_anexos":
            query += " AND EXISTS (SELECT 1 FROM acompanhamento_anexos aa WHERE aa.acompanhamento_id = acompanhamentos_cursistas.id)"
        elif attachment_filter == "sem_anexos":
            query += " AND NOT EXISTS (SELECT 1 FROM acompanhamento_anexos aa WHERE aa.acompanhamento_id = acompanhamentos_cursistas.id)"
        if movement_filter == "com_movimentacoes":
            query += " AND EXISTS (SELECT 1 FROM acompanhamento_movimentacoes am WHERE am.acompanhamento_id = acompanhamentos_cursistas.id)"
        elif movement_filter == "sem_movimentacoes":
            query += " AND NOT EXISTS (SELECT 1 FROM acompanhamento_movimentacoes am WHERE am.acompanhamento_id = acompanhamentos_cursistas.id)"
        query += " ORDER BY acompanhamentos_cursistas.data_abertura DESC, acompanhamentos_cursistas.id DESC"

        with self.connect() as connection:
            return connection.execute(query, tuple(params)).fetchall()

    def get_acompanhamento(self, acompanhamento_id: int) -> Optional[sqlite3.Row]:
        with self.connect() as connection:
            return connection.execute(
                """
                SELECT
                    acompanhamentos_cursistas.*,
                    cursistas.nome AS cursista_nome,
                    turmas.codigo AS turma_codigo
                FROM acompanhamentos_cursistas
                JOIN cursistas ON cursistas.id = acompanhamentos_cursistas.cursista_id
                LEFT JOIN turmas ON turmas.id = acompanhamentos_cursistas.turma_id
                WHERE acompanhamentos_cursistas.id = ?
                """,
                (acompanhamento_id,),
            ).fetchone()

    def save_acompanhamento(
        self,
        data: Dict[str, object],
        acompanhamento_id: Optional[int] = None,
    ) -> int:
        """Insere ou atualiza uma ocorrência do módulo de acompanhamento."""
        payload = (
            data["cursista_id"],
            data.get("turma_id"),
            data.get("encontro_id"),
            str(data.get("categoria", "") or "").strip(),
            str(data.get("status", "aberto") or "aberto").strip(),
            str(data.get("prioridade", "normal") or "normal").strip(),
            str(data.get("resumo", "") or "").strip(),
            str(data.get("descricao", "") or "").strip(),
            1 if bool(data.get("encaminhar_pec", False)) else 0,
            str(data.get("data_abertura", "") or "").strip(),
            str(data.get("data_resolucao", "") or "").strip(),
        )
        with self.connect() as connection:
            if acompanhamento_id:
                connection.execute(
                    """
                    UPDATE acompanhamentos_cursistas
                    SET cursista_id = ?,
                        turma_id = ?,
                        encontro_id = ?,
                        categoria = ?,
                        status = ?,
                        prioridade = ?,
                        resumo = ?,
                        descricao = ?,
                        encaminhar_pec = ?,
                        data_abertura = ?,
                        data_resolucao = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    payload + (acompanhamento_id,),
                )
                return acompanhamento_id

            cursor = connection.execute(
                """
                INSERT INTO acompanhamentos_cursistas(
                    cursista_id,
                    turma_id,
                    encontro_id,
                    categoria,
                    status,
                    prioridade,
                    resumo,
                    descricao,
                    encaminhar_pec,
                    data_abertura,
                    data_resolucao
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                payload,
            )
            return int(cursor.lastrowid)

    def list_acompanhamento_movimentacoes(self, acompanhamento_id: int) -> List[sqlite3.Row]:
        with self.connect() as connection:
            return connection.execute(
                """
                SELECT *
                FROM acompanhamento_movimentacoes
                WHERE acompanhamento_id = ?
                ORDER BY data_movimentacao DESC, id DESC
                """,
                (acompanhamento_id,),
            ).fetchall()

    def add_acompanhamento_movimentacao(
        self,
        acompanhamento_id: int,
        data_movimentacao: str,
        descricao: str,
    ) -> int:
        with self.connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO acompanhamento_movimentacoes(
                    acompanhamento_id,
                    data_movimentacao,
                    descricao
                )
                VALUES (?, ?, ?)
                """,
                (acompanhamento_id, data_movimentacao, descricao.strip()),
            )
            return int(cursor.lastrowid)

    def delete_acompanhamento_movimentacao(self, movimentacao_id: int) -> None:
        with self.connect() as connection:
            connection.execute(
                "DELETE FROM acompanhamento_movimentacoes WHERE id = ?",
                (movimentacao_id,),
            )

    def list_acompanhamento_anexos(self, acompanhamento_id: int) -> List[sqlite3.Row]:
        with self.connect() as connection:
            return connection.execute(
                """
                SELECT *
                FROM acompanhamento_anexos
                WHERE acompanhamento_id = ?
                ORDER BY id
                """,
                (acompanhamento_id,),
            ).fetchall()

    def add_acompanhamento_anexo(
        self,
        acompanhamento_id: int,
        arquivo_original: str,
        arquivo_copiado: str,
    ) -> int:
        with self.connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO acompanhamento_anexos(
                    acompanhamento_id,
                    arquivo_original,
                    arquivo_copiado
                )
                VALUES (?, ?, ?)
                """,
                (acompanhamento_id, arquivo_original, arquivo_copiado),
            )
            return int(cursor.lastrowid)

    def delete_acompanhamento_anexo(self, anexo_id: int) -> Optional[str]:
        with self.connect() as connection:
            row = connection.execute(
                "SELECT arquivo_copiado FROM acompanhamento_anexos WHERE id = ?",
                (anexo_id,),
            ).fetchone()
            if not row:
                return None
            connection.execute("DELETE FROM acompanhamento_anexos WHERE id = ?", (anexo_id,))
            return str(row["arquivo_copiado"])

    def list_socializacoes(
        self,
        ref_month: int,
        ref_year: int,
        turma_id: Optional[int] = None,
        status_envio: str = "",
        search: str = "",
        attachment_filter: str = "",
        movement_filter: str = "",
    ) -> List[sqlite3.Row]:
        """Lista a visão mensal de socializações por cursista.

        O `LEFT JOIN` é intencional: ele permite mostrar quem já tem ficha no
        período e também quem ainda não enviou socialização naquele mês.
        """
        query = """
            SELECT
                socializacoes_cursistas.id AS socializacao_id,
                cursistas.id AS cursista_id,
                cursistas.nome AS cursista_nome,
                cursistas.ativo AS cursista_ativo,
                cursistas.status_busca_ativa,
                turmas.codigo AS turma_codigo,
                cursistas.turma_id AS turma_id,
                COALESCE(socializacoes_cursistas.status_envio, 'nao_enviada') AS status_envio,
                COALESCE(socializacoes_cursistas.data_envio, '') AS data_envio,
                COALESCE(socializacoes_cursistas.observacao_pedagogica, '') AS observacao_pedagogica,
                COALESCE(socializacoes_cursistas.necessita_apoio, 0) AS necessita_apoio,
                COALESCE(socializacoes_cursistas.destaque_potencial, 0) AS destaque_potencial,
                CASE
                    WHEN socializacoes_cursistas.id IS NULL THEN 0
                    ELSE (SELECT COUNT(*) FROM socializacao_anexos WHERE socializacao_id = socializacoes_cursistas.id)
                END AS total_anexos,
                CASE
                    WHEN socializacoes_cursistas.id IS NULL THEN 0
                    ELSE (SELECT COUNT(*) FROM socializacao_movimentacoes WHERE socializacao_id = socializacoes_cursistas.id)
                END AS total_movimentacoes,
                ? AS mes_referencia,
                ? AS ano_referencia
            FROM cursistas
            LEFT JOIN turmas ON turmas.id = cursistas.turma_id
            LEFT JOIN socializacoes_cursistas
                ON socializacoes_cursistas.cursista_id = cursistas.id
                AND socializacoes_cursistas.mes_referencia = ?
                AND socializacoes_cursistas.ano_referencia = ?
            WHERE cursistas.ativo = 1
        """
        params: list[object] = [ref_month, ref_year, ref_month, ref_year]
        if turma_id:
            query += " AND cursistas.turma_id = ?"
            params.append(turma_id)
        if status_envio:
            query += " AND COALESCE(socializacoes_cursistas.status_envio, 'nao_enviada') = ?"
            params.append(status_envio)
        if search.strip():
            query += " AND LOWER(cursistas.nome) LIKE ?"
            params.append(f"%{search.strip().lower()}%")
        if attachment_filter == "com_anexos":
            query += " AND socializacoes_cursistas.id IS NOT NULL AND EXISTS (SELECT 1 FROM socializacao_anexos sa WHERE sa.socializacao_id = socializacoes_cursistas.id)"
        elif attachment_filter == "sem_anexos":
            query += " AND (socializacoes_cursistas.id IS NULL OR NOT EXISTS (SELECT 1 FROM socializacao_anexos sa WHERE sa.socializacao_id = socializacoes_cursistas.id))"
        if movement_filter == "com_movimentacoes":
            query += " AND socializacoes_cursistas.id IS NOT NULL AND EXISTS (SELECT 1 FROM socializacao_movimentacoes sm WHERE sm.socializacao_id = socializacoes_cursistas.id)"
        elif movement_filter == "sem_movimentacoes":
            query += " AND (socializacoes_cursistas.id IS NULL OR NOT EXISTS (SELECT 1 FROM socializacao_movimentacoes sm WHERE sm.socializacao_id = socializacoes_cursistas.id))"
        query += " ORDER BY LOWER(cursistas.nome), cursistas.id"

        with self.connect() as connection:
            return connection.execute(query, tuple(params)).fetchall()

    def get_socializacao(self, socializacao_id: int) -> Optional[sqlite3.Row]:
        with self.connect() as connection:
            return connection.execute(
                """
                SELECT
                    socializacoes_cursistas.*,
                    cursistas.nome AS cursista_nome,
                    turmas.codigo AS turma_codigo
                FROM socializacoes_cursistas
                JOIN cursistas ON cursistas.id = socializacoes_cursistas.cursista_id
                LEFT JOIN turmas ON turmas.id = socializacoes_cursistas.turma_id
                WHERE socializacoes_cursistas.id = ?
                """,
                (socializacao_id,),
            ).fetchone()

    def save_socializacao(
        self,
        data: Dict[str, object],
        socializacao_id: Optional[int] = None,
    ) -> int:
        """Insere ou atualiza a ficha mensal de socialização de um cursista."""
        payload = (
            data["cursista_id"],
            data.get("turma_id"),
            int(data["mes_referencia"]),
            int(data["ano_referencia"]),
            str(data.get("status_envio", "nao_enviada") or "nao_enviada").strip(),
            str(data.get("data_envio", "") or "").strip(),
            str(data.get("observacao_pedagogica", "") or "").strip(),
            1 if bool(data.get("necessita_apoio", False)) else 0,
            1 if bool(data.get("destaque_potencial", False)) else 0,
        )
        with self.connect() as connection:
            if socializacao_id:
                connection.execute(
                    """
                    UPDATE socializacoes_cursistas
                    SET cursista_id = ?,
                        turma_id = ?,
                        mes_referencia = ?,
                        ano_referencia = ?,
                        status_envio = ?,
                        data_envio = ?,
                        observacao_pedagogica = ?,
                        necessita_apoio = ?,
                        destaque_potencial = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    payload + (socializacao_id,),
                )
                return socializacao_id

            cursor = connection.execute(
                """
                INSERT INTO socializacoes_cursistas(
                    cursista_id,
                    turma_id,
                    mes_referencia,
                    ano_referencia,
                    status_envio,
                    data_envio,
                    observacao_pedagogica,
                    necessita_apoio,
                    destaque_potencial
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(cursista_id, mes_referencia, ano_referencia)
                DO UPDATE SET
                    turma_id = excluded.turma_id,
                    status_envio = excluded.status_envio,
                    data_envio = excluded.data_envio,
                    observacao_pedagogica = excluded.observacao_pedagogica,
                    necessita_apoio = excluded.necessita_apoio,
                    destaque_potencial = excluded.destaque_potencial,
                    updated_at = CURRENT_TIMESTAMP
                """,
                payload,
            )
            row = connection.execute(
                """
                SELECT id
                FROM socializacoes_cursistas
                WHERE cursista_id = ?
                  AND mes_referencia = ?
                  AND ano_referencia = ?
                """,
                (payload[0], payload[2], payload[3]),
            ).fetchone()
            if not row:
                raise ValueError("Não foi possível salvar a socialização.")
            return int(row["id"])

    def upsert_socializacao_mensal(self, data: Dict[str, object]) -> int:
        return self.save_socializacao(data)

    def list_socializacao_movimentacoes(self, socializacao_id: int) -> List[sqlite3.Row]:
        with self.connect() as connection:
            return connection.execute(
                """
                SELECT *
                FROM socializacao_movimentacoes
                WHERE socializacao_id = ?
                ORDER BY data_movimentacao DESC, id DESC
                """,
                (socializacao_id,),
            ).fetchall()

    def add_socializacao_movimentacao(
        self,
        socializacao_id: int,
        data_movimentacao: str,
        descricao: str,
    ) -> int:
        with self.connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO socializacao_movimentacoes(
                    socializacao_id,
                    data_movimentacao,
                    descricao
                )
                VALUES (?, ?, ?)
                """,
                (socializacao_id, data_movimentacao, descricao.strip()),
            )
            return int(cursor.lastrowid)

    def delete_socializacao_movimentacao(self, movimentacao_id: int) -> None:
        with self.connect() as connection:
            connection.execute(
                "DELETE FROM socializacao_movimentacoes WHERE id = ?",
                (movimentacao_id,),
            )

    def list_socializacao_anexos(self, socializacao_id: int) -> List[sqlite3.Row]:
        with self.connect() as connection:
            return connection.execute(
                """
                SELECT *
                FROM socializacao_anexos
                WHERE socializacao_id = ?
                ORDER BY id
                """,
                (socializacao_id,),
            ).fetchall()

    def add_socializacao_anexo(
        self,
        socializacao_id: int,
        arquivo_original: str,
        arquivo_copiado: str,
    ) -> int:
        with self.connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO socializacao_anexos(
                    socializacao_id,
                    arquivo_original,
                    arquivo_copiado
                )
                VALUES (?, ?, ?)
                """,
                (socializacao_id, arquivo_original, arquivo_copiado),
            )
            return int(cursor.lastrowid)

    def delete_socializacao_anexo(self, anexo_id: int) -> Optional[str]:
        with self.connect() as connection:
            row = connection.execute(
                "SELECT arquivo_copiado FROM socializacao_anexos WHERE id = ?",
                (anexo_id,),
            ).fetchone()
            if not row:
                return None
            connection.execute("DELETE FROM socializacao_anexos WHERE id = ?", (anexo_id,))
            return str(row["arquivo_copiado"])

    def get_busca_ativa_pendentes(self) -> int:
        with self.connect() as connection:
            row = connection.execute(
                """
                SELECT COUNT(*) AS total
                FROM cursistas
                WHERE ativo = 1
                  AND status_busca_ativa NOT IN ('localizado', 'encerrado')
                """
            ).fetchone()
        return int(row["total"] or 0) if row else 0

    def get_socializacao_resumo(self, ref_month: int, ref_year: int) -> Dict[str, int]:
        with self.connect() as connection:
            row = connection.execute(
                """
                SELECT
                    COUNT(*) AS total_cursistas,
                    SUM(CASE WHEN COALESCE(s.status_envio, 'nao_enviada') = 'nao_enviada' THEN 1 ELSE 0 END) AS nao_enviada,
                    SUM(CASE WHEN COALESCE(s.status_envio, 'nao_enviada') = 'enviada' THEN 1 ELSE 0 END) AS enviada,
                    SUM(CASE WHEN COALESCE(s.necessita_apoio, 0) = 1 THEN 1 ELSE 0 END) AS necessita_apoio,
                    SUM(CASE WHEN COALESCE(s.destaque_potencial, 0) = 1 THEN 1 ELSE 0 END) AS destaque
                FROM cursistas c
                LEFT JOIN socializacoes_cursistas s
                    ON s.cursista_id = c.id
                    AND s.mes_referencia = ?
                    AND s.ano_referencia = ?
                WHERE c.ativo = 1
                """,
                (ref_month, ref_year),
            ).fetchone()
        if not row:
            return {
                "total_cursistas": 0,
                "nao_enviada": 0,
                "enviada": 0,
                "necessita_apoio": 0,
                "destaque": 0,
            }
        return {
            "total_cursistas": int(row["total_cursistas"] or 0),
            "nao_enviada": int(row["nao_enviada"] or 0),
            "enviada": int(row["enviada"] or 0),
            "necessita_apoio": int(row["necessita_apoio"] or 0),
            "destaque": int(row["destaque"] or 0),
        }

    def get_cursistas_dashboard_counts(
        self,
        ref_month: Optional[int] = None,
        ref_year: Optional[int] = None,
    ) -> Dict[str, int]:
        reference = datetime.today()
        month = ref_month or reference.month
        year = ref_year or reference.year

        with self.connect() as connection:
            total_row = connection.execute(
                "SELECT COUNT(*) AS total FROM cursistas WHERE ativo = 1"
            ).fetchone()
            acompanhamento_row = connection.execute(
                """
                SELECT COUNT(*) AS total
                FROM acompanhamentos_cursistas
                WHERE status NOT IN ('resolvido', 'arquivado')
                """
            ).fetchone()

        socializacao = self.get_socializacao_resumo(month, year)
        return {
            "cursistas_ativos": int(total_row["total"] or 0) if total_row else 0,
            "busca_ativa_pendente": self.get_busca_ativa_pendentes(),
            "acompanhamentos_abertos": int(acompanhamento_row["total"] or 0)
            if acompanhamento_row
            else 0,
            "socializacoes_nao_enviadas": socializacao["nao_enviada"],
            "socializacoes_destaque": socializacao["destaque"],
        }

    def list_encontros(self, month_id: int) -> List[sqlite3.Row]:
        with self.connect() as connection:
            return connection.execute(
                """
                SELECT
                    encontros.*,
                    turmas.codigo AS turma_codigo,
                    month_records.weekly_rate_cents AS weekly_rate_cents,
                    (SELECT COUNT(*) FROM evidencias WHERE encontro_id = encontros.id) AS total_imagens
                FROM encontros
                JOIN turmas ON turmas.id = encontros.turma_id
                JOIN month_records ON month_records.id = encontros.month_id
                WHERE encontros.month_id = ?
                ORDER BY encontros.data_encontro, encontros.pauta_numero, turmas.codigo
                """,
                (month_id,),
            ).fetchall()

    def get_encontro(self, encontro_id: int) -> Optional[sqlite3.Row]:
        with self.connect() as connection:
            return connection.execute(
                """
                SELECT encontros.*, turmas.codigo AS turma_codigo
                FROM encontros
                JOIN turmas ON turmas.id = encontros.turma_id
                WHERE encontros.id = ?
                """,
                (encontro_id,),
            ).fetchone()

    def save_encontro(self, data: Dict[str, object], encontro_id: Optional[int] = None) -> int:
        """Insere ou atualiza um encontro pedagógico."""
        payload = (
            data["month_id"],
            data["turma_id"],
            data["data_encontro"],
            data["pauta_numero"],
            data.get("hora_inicio", "") or "",
            data.get("hora_fim", "") or "",
            data.get("participantes"),
            data.get("duracao", "") or "",
            data.get("observacao", "") or "",
            data.get("situacao", "realizado") or "realizado",
        )
        with self.connect() as connection:
            if encontro_id:
                connection.execute(
                    """
                    UPDATE encontros
                    SET month_id = ?,
                        turma_id = ?,
                        data_encontro = ?,
                        pauta_numero = ?,
                        hora_inicio = ?,
                        hora_fim = ?,
                        participantes = ?,
                        duracao = ?,
                        observacao = ?,
                        situacao = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    payload + (encontro_id,),
                )
                return encontro_id

            cursor = connection.execute(
                """
                INSERT INTO encontros(
                    month_id,
                    turma_id,
                    data_encontro,
                    pauta_numero,
                    hora_inicio,
                    hora_fim,
                    participantes,
                    duracao,
                    observacao,
                    situacao
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                payload,
            )
            return int(cursor.lastrowid)

    def add_evidence(self, encontro_id: int, arquivo_original: str, arquivo_copiado: str) -> int:
        with self.connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO evidencias(encontro_id, arquivo_original, arquivo_copiado)
                VALUES (?, ?, ?)
                """,
                (encontro_id, arquivo_original, arquivo_copiado),
            )
            return int(cursor.lastrowid)

    def list_evidences(self, encontro_id: int) -> List[sqlite3.Row]:
        with self.connect() as connection:
            return connection.execute(
                """
                SELECT *
                FROM evidencias
                WHERE encontro_id = ?
                ORDER BY id
                """,
                (encontro_id,),
            ).fetchall()

    def delete_evidence(self, evidence_id: int) -> Optional[str]:
        with self.connect() as connection:
            row = connection.execute(
                "SELECT arquivo_copiado FROM evidencias WHERE id = ?",
                (evidence_id,),
            ).fetchone()
            if not row:
                return None
            connection.execute("DELETE FROM evidencias WHERE id = ?", (evidence_id,))
            return row["arquivo_copiado"]

    def get_month_bundle(self, month_id: int) -> Dict[str, object]:
        """Agrupa em um único pacote os dados usados pelos relatórios do mês."""
        month = self.get_month(month_id)
        if not month:
            raise ValueError("Mês não encontrado.")

        encontros = []
        for encontro in self.list_encontros(month_id):
            encontro_dict = dict(encontro)
            encontro_dict["evidencias"] = [
                dict(item) for item in self.list_evidences(int(encontro["id"]))
            ]
            encontros.append(encontro_dict)

        turmas_no_mes = []
        seen = set()
        for encontro in encontros:
            codigo = encontro["turma_codigo"]
            if codigo not in seen:
                turmas_no_mes.append(codigo)
                seen.add(codigo)

        if not turmas_no_mes:
            turmas_no_mes = [row["codigo"] for row in self.list_turmas(include_inactive=False)]

        return {
            "month": dict(month),
            "encontros": encontros,
            "turmas": turmas_no_mes,
            "checklist": self.get_checklist(month_id),
        }

    def get_checklist(self, month_id: int) -> Dict[str, object]:
        """Resume pendências do mês para conferência antes da emissão final."""
        encontros = [dict(row) for row in self.list_encontros(month_id)]

        issues = []
        turmas = sorted({item["turma_codigo"] for item in encontros})
        pautas = sorted({item["pauta_numero"] for item in encontros})

        sem_imagem = []
        sem_observacao = []
        sem_horario = []
        sem_participantes = []
        counts_by_turma: Dict[str, int] = {}
        counts_by_pauta: Dict[int, int] = {}
        counts_by_status: Dict[str, int] = {}

        for encontro in encontros:
            counts_by_turma[encontro["turma_codigo"]] = (
                counts_by_turma.get(encontro["turma_codigo"], 0) + 1
            )
            counts_by_pauta[encontro["pauta_numero"]] = (
                counts_by_pauta.get(encontro["pauta_numero"], 0) + 1
            )
            counts_by_status[encontro["situacao"]] = (
                counts_by_status.get(encontro["situacao"], 0) + 1
            )

            descriptor = (
                f"{encontro['data_encontro']} | Pauta {encontro['pauta_numero']} | "
                f"{encontro['turma_codigo']}"
            )
            if int(encontro["total_imagens"] or 0) == 0:
                sem_imagem.append(descriptor)
            if not (encontro["observacao"] or "").strip():
                sem_observacao.append(descriptor)
            if not (encontro["hora_inicio"] or "").strip() or not (encontro["hora_fim"] or "").strip():
                sem_horario.append(descriptor)
            if encontro["participantes"] is None:
                sem_participantes.append(descriptor)

        if sem_imagem:
            issues.append("Existem encontros sem imagem anexada.")
        if sem_observacao:
            issues.append("Existem encontros sem observação.")
        if sem_horario:
            issues.append("Existem encontros sem horário completo.")
        if sem_participantes:
            issues.append("Existem encontros sem participantes informados.")

        realizados = counts_by_status.get("realizado", 0) + counts_by_status.get("sem cursistas", 0)
        month = self.get_month(month_id)
        weekly_rate_cents = int(month["weekly_rate_cents"] or 0) if month else 0
        total_monthly_cents = realizados * weekly_rate_cents

        return {
            "total_registrados": len(encontros),
            "total_realizados": realizados,
            "valor_formacao_semanal_centavos": weekly_rate_cents,
            "valor_total_mensal_centavos": total_monthly_cents,
            "turmas": turmas,
            "pautas": pautas,
            "sem_imagem": sem_imagem,
            "sem_observacao": sem_observacao,
            "sem_horario": sem_horario,
            "sem_participantes": sem_participantes,
            "por_turma": counts_by_turma,
            "por_pauta": counts_by_pauta,
            "por_status": counts_by_status,
            "issues": issues,
        }

    def backup_database(self, destination_dir: Path = BACKUP_DIR) -> Path:
        destination_dir.mkdir(parents=True, exist_ok=True)
        backup_path = destination_dir / "multiplica_backup.db"
        counter = 1
        while backup_path.exists():
            backup_path = destination_dir / f"multiplica_backup_{counter}.db"
            counter += 1
        shutil.copy2(self.db_path, backup_path)
        return backup_path

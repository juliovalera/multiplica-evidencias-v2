from datetime import datetime
import shutil
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional

from config import BACKUP_DIR, DB_PATH, EVIDENCIAS_DIR, slugify
from models import MONTH_NAMES_PT, ProfessorDefaults


class Database:
    def __init__(self, db_path: Path = DB_PATH) -> None:
        self.db_path = Path(db_path)

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def initialize(self) -> None:
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

    def reconcile_data_by_encounter_date(self) -> int:
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

    def save_month(self, month_id: int, data: Dict[str, str]) -> None:
        month = self.get_month(month_id)
        if not month:
            raise ValueError("Mês de referência não encontrado.")

        with self.connect() as connection:
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

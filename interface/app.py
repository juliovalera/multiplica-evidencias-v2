from __future__ import annotations

import calendar
from datetime import date, datetime, timedelta
from pathlib import Path
import os
import shutil
import sqlite3
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from config import APP_NAME, APP_VERSION, BACKUP_DIR, EVIDENCIAS_DIR, SAIDAS_DIR, slugify
from database import Database
from models import AUTO_OBSERVATIONS, STATUS_OPTIONS, TURMA_STATUS_OPTIONS, WEEKDAY_OPTIONS
from relatorio import export_pdf, generate_docx, generate_financial_statement_docx


class DatePickerDialog(tk.Toplevel):
    WEEKDAY_LABELS = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sab", "Dom"]
    MONTH_LABELS = [
        "Janeiro",
        "Fevereiro",
        "Março",
        "Abril",
        "Maio",
        "Junho",
        "Julho",
        "Agosto",
        "Setembro",
        "Outubro",
        "Novembro",
        "Dezembro",
    ]

    def __init__(
        self,
        master: tk.Misc,
        initial_date: datetime,
        on_select,
        preferred_weekday: int | None = None,
        holiday_resolver=None,
    ) -> None:
        super().__init__(master)
        self.title("Selecionar data")
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()

        self.on_select = on_select
        self.current_year = initial_date.year
        self.current_month = initial_date.month
        self.selected_day = initial_date.day
        self.preferred_weekday = preferred_weekday
        self.holiday_resolver = holiday_resolver or (lambda _year: {})

        self._build_layout()
        self._render_days()

        self.bind("<Escape>", lambda _event: self.destroy())
        self.protocol("WM_DELETE_WINDOW", self.destroy)

    def _build_layout(self) -> None:
        container = ttk.Frame(self, padding=12)
        container.pack(fill="both", expand=True)

        header = ttk.Frame(container)
        header.pack(fill="x", pady=(0, 8))

        ttk.Button(header, text="<", width=3, command=lambda: self._change_month(-1)).pack(
            side="left"
        )
        self.month_title_var = tk.StringVar()
        ttk.Label(
            header,
            textvariable=self.month_title_var,
            anchor="center",
            font=("Segoe UI", 10, "bold"),
        ).pack(side="left", expand=True, padx=8)
        ttk.Button(header, text=">", width=3, command=lambda: self._change_month(1)).pack(
            side="right"
        )

        week_header = ttk.Frame(container)
        week_header.pack(fill="x")
        for index, label in enumerate(self.WEEKDAY_LABELS):
            ttk.Label(week_header, text=label, anchor="center", width=5).grid(
                row=0, column=index, padx=1, pady=(0, 2)
            )

        self.days_frame = ttk.Frame(container)
        self.days_frame.pack(fill="both", expand=True)

        footer = ttk.Frame(container)
        footer.pack(fill="x", pady=(10, 0))
        self.holiday_summary_var = tk.StringVar(value="")
        ttk.Label(
            footer,
            textvariable=self.holiday_summary_var,
            justify="left",
            wraplength=280,
        ).pack(side="left", padx=(0, 12))
        ttk.Button(footer, text="Hoje", command=self._select_today).pack(side="left")
        ttk.Button(footer, text="Cancelar", command=self.destroy).pack(side="right")

        legend = ttk.Frame(container)
        legend.pack(fill="x", pady=(8, 0))
        self._add_legend_item(legend, "#dbeafe", "#1d4ed8", "Dia padrão da turma")
        self._add_legend_item(legend, "#fecaca", "#7f1d1d", "Feriado nacional")
        self._add_legend_item(legend, "#c084fc", "#ffffff", "Dia da turma e feriado")

    def _add_legend_item(self, parent: ttk.Frame, bg: str, fg: str, text: str) -> None:
        item = ttk.Frame(parent)
        item.pack(side="left", padx=(0, 10))
        tk.Label(item, text="  ", bg=bg, fg=fg, relief="solid", borderwidth=1).pack(side="left")
        ttk.Label(item, text=text).pack(side="left", padx=(4, 0))

    def _change_month(self, delta: int) -> None:
        new_month = self.current_month + delta
        new_year = self.current_year
        if new_month == 0:
            new_month = 12
            new_year -= 1
        elif new_month == 13:
            new_month = 1
            new_year += 1
        self.current_month = new_month
        self.current_year = new_year
        self._render_days()

    def _render_days(self) -> None:
        for widget in self.days_frame.winfo_children():
            widget.destroy()

        self.month_title_var.set(
            f"{self.MONTH_LABELS[self.current_month - 1]} de {self.current_year}"
        )

        month_days = calendar.Calendar(firstweekday=0).monthdayscalendar(
            self.current_year, self.current_month
        )
        holiday_map = self.holiday_resolver(self.current_year)
        holiday_lines = []
        for row_index, week in enumerate(month_days):
            for column_index, day in enumerate(week):
                if day == 0:
                    ttk.Label(self.days_frame, text="", width=5).grid(
                        row=row_index, column=column_index, padx=1, pady=1
                    )
                    continue

                current_date = date(self.current_year, self.current_month, day)
                is_holiday = current_date in holiday_map
                is_preferred_weekday = self.preferred_weekday == column_index
                if is_holiday:
                    holiday_lines.append(f"{day:02d}/{self.current_month:02d} - {holiday_map[current_date]}")

                bg = "#f3f4f6"
                fg = "#111827"
                if is_holiday and is_preferred_weekday:
                    bg = "#a855f7"
                    fg = "#ffffff"
                elif is_holiday:
                    bg = "#fecaca"
                    fg = "#7f1d1d"
                elif is_preferred_weekday:
                    bg = "#dbeafe"
                    fg = "#1d4ed8"

                relief = "raised"
                borderwidth = 1
                if (
                    self.current_year == datetime.today().year
                    and self.current_month == datetime.today().month
                    and day == datetime.today().day
                ):
                    relief = "solid"
                    borderwidth = 2

                button = tk.Button(
                    self.days_frame,
                    text=str(day),
                    width=5,
                    bg=bg,
                    fg=fg,
                    activebackground=bg,
                    activeforeground=fg,
                    relief=relief,
                    borderwidth=borderwidth,
                    command=lambda selected_day=day: self._select_day(selected_day),
                )
                button.grid(row=row_index, column=column_index, padx=1, pady=1)

        self.holiday_summary_var.set(
            "Feriados no mês:\n" + "\n".join(holiday_lines) if holiday_lines else "Sem feriados nacionais neste mês."
        )

    def _select_day(self, day: int) -> None:
        selected_date = datetime(self.current_year, self.current_month, day)
        self.on_select(selected_date.strftime("%d/%m/%Y"))
        self.destroy()

    def _select_today(self) -> None:
        today = datetime.today()
        self.on_select(today.strftime("%d/%m/%Y"))
        self.destroy()


class MultiplicaApp(tk.Tk):
    TURMA_WEEKDAY_TO_INDEX = {
        "SEG": 0,
        "TER": 1,
        "QUA": 2,
        "QUI": 3,
        "SEX": 4,
        "SAB": 5,
        "DOM": 6,
    }
    TERMS_VERSION = "2026-07-06"
    TERMS_CONFIG_KEY = "terms_accepted_version"
    TERMS_ACCEPTED_AT_KEY = "terms_accepted_at"

    def __init__(self, database: Database) -> None:
        super().__init__()
        self.database = database
        self.title(APP_NAME)
        self.geometry("1280x780")
        self.minsize(1080, 680)

        self.current_month_id: int | None = None
        self.selected_turma_id: int | None = None
        self.selected_encontro_id: int | None = None
        self.selected_evidence_id: int | None = None
        self.preview_photo = None
        self.preview_image_path: Path | None = None
        self.report_generation_in_progress = False

        self.month_label_to_id: dict[str, int] = {}
        self.turma_label_to_id: dict[str, int] = {}
        self.auto_observacao_names = list(AUTO_OBSERVATIONS.keys())
        self._formatting_locks: set[str] = set()
        self._formatted_entries: dict[str, tuple[tk.Entry, object]] = {}
        self._tree_column_configs: dict[ttk.Treeview, dict[str, object]] = {}

        self._build_variables()
        self._setup_auto_formatters()
        self._configure_styles()
        self._build_layout()
        self._load_initial_state()
        self.after(150, self.ensure_terms_acceptance)

    def _build_variables(self) -> None:
        today = datetime.today()

        self.current_month_label_var = tk.StringVar()

        self.nome_var = tk.StringVar()
        self.tema_var = tk.StringVar()
        self.email_var = tk.StringVar()
        self.diretoria_var = tk.StringVar()
        self.pec_var = tk.StringVar()
        self.valor_formacao_semanal_var = tk.StringVar()

        self.turma_codigo_var = tk.StringVar()
        self.turma_dia_var = tk.StringVar(value=WEEKDAY_OPTIONS[0])
        self.turma_horario_var = tk.StringVar()
        self.turma_componente_var = tk.StringVar()
        self.turma_situacao_var = tk.StringVar(value=TURMA_STATUS_OPTIONS[0])

        self.encontro_data_var = tk.StringVar()
        self.encontro_pauta_var = tk.StringVar()
        self.encontro_turma_var = tk.StringVar()
        self.encontro_inicio_var = tk.StringVar()
        self.encontro_fim_var = tk.StringVar()
        self.encontro_participantes_var = tk.StringVar()
        self.encontro_duracao_var = tk.StringVar()
        self.encontro_status_var = tk.StringVar(value=STATUS_OPTIONS[0])
        self.auto_observacao_var = tk.StringVar(value=self.auto_observacao_names[0])

        self.status_bar_var = tk.StringVar(
            value="Tudo permanece local: banco SQLite, imagens e relatórios."
        )

    def _setup_auto_formatters(self) -> None:
        self._formatted_entries = {}

    def _configure_styles(self) -> None:
        self.style = ttk.Style(self)
        try:
            if self.style.theme_use() != "clam":
                self.style.theme_use("clam")
        except tk.TclError:
            pass

        self.style.configure(
            "Multiplica.TNotebook",
            background="#dfe4ea",
            borderwidth=2,
            relief="solid",
            tabmargins=(4, 4, 4, 0),
        )
        self.style.configure(
            "Multiplica.TNotebook.Tab",
            padding=(12, 6, 12, 6),
            font=("Segoe UI", 9, "bold"),
            background="#e8edf3",
            foreground="#243447",
            borderwidth=1,
            relief="solid",
            lightcolor="#9aa9b8",
            darkcolor="#748394",
        )
        self.style.map(
            "Multiplica.TNotebook.Tab",
            background=[
                ("selected", "#ffffff"),
                ("active", "#f8fbff"),
            ],
            foreground=[
                ("selected", "#0f4c81"),
                ("active", "#12385f"),
            ],
            lightcolor=[
                ("selected", "#0f4c81"),
                ("active", "#4f83b8"),
            ],
            darkcolor=[
                ("selected", "#0f4c81"),
                ("active", "#4f83b8"),
            ],
            expand=[("selected", (1, 1, 1, 0))],
        )

    def _register_formatted_entry(self, entry: tk.Entry, formatter) -> None:
        widget_name = str(entry)
        self._formatted_entries[widget_name] = (entry, formatter)
        entry.bind("<KeyRelease>", self._handle_formatted_entry_keyrelease, add="+")

    def _handle_formatted_entry_keyrelease(self, event) -> None:
        entry = event.widget
        widget_name = str(entry)
        if widget_name not in self._formatted_entries or widget_name in self._formatting_locks:
            return

        formatter = self._formatted_entries[widget_name][1]
        current_value = entry.get()
        cursor_index = entry.index(tk.INSERT)
        digits_before_cursor = sum(1 for char in current_value[:cursor_index] if char.isdigit())
        formatted_value = formatter(current_value)
        if formatted_value == current_value:
            return

        new_cursor_index = self._find_cursor_position_from_digits(formatted_value, digits_before_cursor)

        self._formatting_locks.add(widget_name)
        try:
            entry.delete(0, tk.END)
            entry.insert(0, formatted_value)
            entry.icursor(new_cursor_index)
        finally:
            self._formatting_locks.discard(widget_name)

    def _find_cursor_position_from_digits(self, formatted_value: str, digits_before_cursor: int) -> int:
        if digits_before_cursor <= 0:
            return 0

        counted_digits = 0
        for index, char in enumerate(formatted_value):
            if char.isdigit():
                counted_digits += 1
                if counted_digits >= digits_before_cursor:
                    return index + 1
        return len(formatted_value)

    def _register_treeview_autofit(
        self,
        tree: ttk.Treeview,
        columns: tuple[str, ...],
        weights: dict[str, int],
        min_widths: dict[str, int],
    ) -> None:
        self._tree_column_configs[tree] = {
            "columns": columns,
            "weights": weights,
            "min_widths": min_widths,
        }
        tree.bind("<Configure>", lambda _event, current_tree=tree: self._autofit_treeview_columns(current_tree), add="+")
        self.after(50, lambda current_tree=tree: self._autofit_treeview_columns(current_tree))

    def _autofit_treeview_columns(self, tree: ttk.Treeview) -> None:
        config = self._tree_column_configs.get(tree)
        if not config:
            return

        columns = config["columns"]
        weights = config["weights"]
        min_widths = config["min_widths"]

        total_width = max(tree.winfo_width() - 6, 200)
        total_weight = sum(weights[column] for column in columns)
        assigned_width = 0

        for index, column in enumerate(columns):
            if index == len(columns) - 1:
                width = max(total_width - assigned_width, min_widths[column])
            else:
                width = max(int(total_width * weights[column] / total_weight), min_widths[column])
                assigned_width += width
            tree.column(column, width=width, stretch=True)

    def _format_time_live(self, value: str) -> str:
        digits = "".join(char for char in value if char.isdigit())[:4]
        if len(digits) <= 2:
            return digits
        return f"{digits[:2]}:{digits[2:]}"

    def _format_date_live(self, value: str) -> str:
        digits = "".join(char for char in value if char.isdigit())[:8]
        if len(digits) <= 2:
            return digits
        if len(digits) <= 4:
            return f"{digits[:2]}/{digits[2:]}"
        return f"{digits[:2]}/{digits[2:4]}/{digits[4:]}"

    def _parse_currency_to_cents(self, value: str) -> int:
        normalized = value.strip().replace("R$", "").replace(" ", "")
        if "," in normalized and "." in normalized:
            if normalized.rfind(",") > normalized.rfind("."):
                normalized = normalized.replace(".", "").replace(",", ".")
            else:
                normalized = normalized.replace(",", "")
        elif "," in normalized:
            normalized = normalized.replace(".", "").replace(",", ".")
        if not normalized:
            return 0
        amount = float(normalized)
        return max(int(round(amount * 100)), 0)

    def _format_currency_from_cents(self, cents: int) -> str:
        value = max(cents, 0) / 100
        formatted = f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return f"R$ {formatted}"

    def _normalize_currency_field(self, _event=None) -> bool:
        raw_value = self.valor_formacao_semanal_var.get().strip()
        if not raw_value:
            return True
        try:
            cents = self._parse_currency_to_cents(raw_value)
        except ValueError:
            messagebox.showwarning(
                "Valor inválido",
                "Informe o valor da formação semanal em formato numérico, por exemplo: 150,00",
            )
            return False
        self.valor_formacao_semanal_var.set(self._format_currency_from_cents(cents))
        return True

    def _resolve_display_date(self, value: str) -> datetime:
        cleaned = value.strip()
        if not cleaned:
            if self.current_month_id:
                month_row = self.database.get_month(self.current_month_id)
                if month_row:
                    return datetime(int(month_row["ref_year"]), int(month_row["ref_month"]), 1)
            return datetime.today()

        for date_format in ("%d/%m/%Y", "%Y-%m-%d"):
            try:
                return datetime.strptime(cleaned, date_format)
            except ValueError:
                continue
        return datetime.today()

    def open_encontro_calendar(self) -> None:
        initial_date = self._resolve_display_date(self.encontro_data_var.get())
        preferred_weekday = self._get_selected_turma_weekday_index()
        picker = DatePickerDialog(
            self,
            initial_date,
            self.encontro_data_var.set,
            preferred_weekday=preferred_weekday,
            holiday_resolver=self._get_brazil_national_holidays,
        )
        picker.focus_set()

    def _get_selected_turma_row(self) -> sqlite3.Row | None:
        turma_label = self.encontro_turma_var.get().strip()
        turma_id = self.turma_label_to_id.get(turma_label)
        if not turma_id:
            return None
        return self.database.get_turma(turma_id)

    def _get_selected_turma_weekday_index(self) -> int | None:
        turma = self._get_selected_turma_row()
        if not turma:
            return None
        return self.TURMA_WEEKDAY_TO_INDEX.get((turma["dia_semana"] or "").strip().upper())

    def _calculate_easter_sunday(self, year: int) -> date:
        a = year % 19
        b = year // 100
        c = year % 100
        d = b // 4
        e = b % 4
        f = (b + 8) // 25
        g = (b - f + 1) // 3
        h = (19 * a + b - d - g + 15) % 30
        i = c // 4
        k = c % 4
        l = (32 + 2 * e + 2 * i - h - k) % 7
        m = (a + 11 * h + 22 * l) // 451
        month = (h + l - 7 * m + 114) // 31
        day = ((h + l - 7 * m + 114) % 31) + 1
        return date(year, month, day)

    def _get_brazil_national_holidays(self, year: int) -> dict[date, str]:
        easter = self._calculate_easter_sunday(year)
        good_friday = easter - timedelta(days=2)
        return {
            date(year, 1, 1): "Confraternização Universal",
            good_friday: "Paixão de Cristo",
            date(year, 4, 21): "Tiradentes",
            date(year, 5, 1): "Dia do Trabalhador",
            date(year, 9, 7): "Independência do Brasil",
            date(year, 10, 12): "Nossa Senhora Aparecida",
            date(year, 11, 2): "Finados",
            date(year, 11, 15): "Proclamação da República",
            date(year, 11, 20): "Consciência Negra",
            date(year, 12, 25): "Natal",
        }

    def _build_layout(self) -> None:
        self._build_top_bar()

        self.notebook = ttk.Notebook(self, style="Multiplica.TNotebook")
        self.notebook.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.home_tab = ttk.Frame(self.notebook, padding=10)
        self.professor_tab = ttk.Frame(self.notebook, padding=10)
        self.turmas_tab = ttk.Frame(self.notebook, padding=10)
        self.encontros_tab = ttk.Frame(self.notebook, padding=10)
        self.checklist_tab = ttk.Frame(self.notebook, padding=10)

        self.notebook.add(self.home_tab, text="Início")
        self.notebook.add(self.professor_tab, text="Professor Multiplicador")
        self.notebook.add(self.turmas_tab, text="Turmas")
        self.notebook.add(self.encontros_tab, text="Encontros")
        self.notebook.add(self.checklist_tab, text="Checklist e relatório")

        self._build_home_tab()
        self._build_professor_tab()
        self._build_turmas_tab()
        self._build_encontros_tab()
        self._build_checklist_tab()

        status_bar = ttk.Label(
            self,
            textvariable=self.status_bar_var,
            anchor="w",
            padding=(8, 6),
        )
        status_bar.pack(fill="x", side="bottom")

    def _build_top_bar(self) -> None:
        frame = ttk.Frame(self, padding=(8, 8, 8, 4))
        frame.pack(fill="x")

        ttk.Label(frame, text="Meses com encontros").grid(row=0, column=0, sticky="w")
        self.month_combo = ttk.Combobox(
            frame,
            textvariable=self.current_month_label_var,
            state="readonly",
            width=24,
        )
        self.month_combo.grid(row=1, column=0, sticky="w", padx=(0, 12))
        self.month_combo.bind("<<ComboboxSelected>>", self._on_month_selected)

        ttk.Button(frame, text="Abrir saídas", command=self.open_output_folder).grid(
            row=1, column=1, padx=6
        )
        ttk.Button(frame, text="Abrir pasta das evidências", command=self.open_evidence_folder).grid(
            row=1, column=2, padx=6
        )
        ttk.Button(frame, text="Backup do banco", command=self.backup_database).grid(
            row=1, column=3, padx=6
        )
        ttk.Button(frame, text="Sobre o projeto", command=self.show_about_dialog).grid(
            row=1, column=4, padx=6
        )

        frame.columnconfigure(5, weight=1)

    def _build_home_tab(self) -> None:
        title = ttk.Label(
            self.home_tab,
            text="Multiplica Evidências",
            font=("Segoe UI", 16, "bold"),
        )
        title.pack(anchor="w")

        body = (
            "Aplicação local e independente para apoiar o professor multiplicador "
            "na organização de encontros, evidências e documentos mensais."
        )
        ttk.Label(self.home_tab, text=body, wraplength=860, justify="left").pack(
            anchor="w", pady=(8, 12)
        )
        ttk.Label(
            self.home_tab,
            text=f"Versão atual: {APP_VERSION}",
            justify="left",
        ).pack(anchor="w", pady=(0, 8))
        tk.Label(
            self.home_tab,
            text=(
                "AVISO IMPORTANTE: ESTE PROJETO É INDEPENDENTE E NÃO OFICIAL.\n"
                "A menção ao Programa Multiplica é apenas descritiva e não representa\n"
                "homologação, licenciamento de marca ou vínculo institucional automático."
            ),
            font=("Segoe UI", 10, "bold"),
            fg="#8b1e1e",
            bg=self.home_tab.cget("background"),
            justify="left",
        ).pack(anchor="w", pady=(0, 8))
        ttk.Label(
            self.home_tab,
            text=(
                "Aviso: no primeiro uso, o sistema solicita o aceite dos termos de uso "
                "antes da utilização."
            ),
            justify="left",
        ).pack(anchor="w", pady=(0, 12))

        quick = ttk.LabelFrame(self.home_tab, text="Fluxo sugerido", padding=10)
        quick.pack(fill="x", pady=(0, 10))
        ttk.Label(
            quick,
            text=(
                "1. Salve os dados do professor.\n"
                "2. Cadastre as turmas.\n"
                "3. Registre cada encontro e anexe os prints.\n"
                "4. O mês é criado automaticamente pela data do encontro.\n"
                "5. Selecione um mês existente para revisar o checklist e gerar o relatório."
            ),
            justify="left",
        ).pack(anchor="w")

        actions = ttk.LabelFrame(self.home_tab, text="Ações rápidas", padding=10)
        actions.pack(fill="x")
        buttons = [
            ("Cadastrar professor", 1),
            ("Cadastrar turma", 2),
            ("Registrar encontro", 3),
            ("Checklist mensal", 4),
            ("Sobre o projeto", None),
        ]
        for column, (label, tab_index) in enumerate(buttons):
            ttk.Button(
                actions,
                text=label,
                command=(
                    self.show_about_dialog
                    if tab_index is None
                    else lambda index=tab_index: self.notebook.select(index)
                ),
            ).grid(row=0, column=column, padx=(0, 8), pady=2, sticky="w")

    def _build_professor_tab(self) -> None:
        frame = ttk.LabelFrame(self.professor_tab, text="Dados do professor multiplicador", padding=10)
        frame.pack(fill="x", anchor="n")

        labels = [
            ("Nome", self.nome_var),
            ("Tema", self.tema_var),
            ("E-mail institucional", self.email_var),
            ("Diretoria / URE", self.diretoria_var),
            ("PEC responsável", self.pec_var),
            ("Valor por formação semanal (R$)", self.valor_formacao_semanal_var),
        ]
        for row, (label, variable) in enumerate(labels):
            ttk.Label(frame, text=label).grid(row=row, column=0, sticky="w", pady=4)
            entry = ttk.Entry(frame, textvariable=variable, width=68)
            entry.grid(row=row, column=1, sticky="ew", pady=4, padx=(12, 0))
            if variable is self.valor_formacao_semanal_var:
                entry.bind("<FocusOut>", self._normalize_currency_field, add="+")

        frame.columnconfigure(1, weight=1)

        button_row = ttk.Frame(self.professor_tab, padding=(0, 10, 0, 0))
        button_row.pack(fill="x")
        ttk.Button(button_row, text="Salvar dados do professor", command=self.save_current_month).pack(
            side="left"
        )
        ttk.Button(
            button_row,
            text="Salvar como padrão",
            command=self.save_defaults,
        ).pack(side="left", padx=(10, 0))
        ttk.Button(
            button_row,
            text="Usar padrão salvo",
            command=self.apply_defaults_to_form,
        ).pack(side="left", padx=(10, 0))

    def _build_turmas_tab(self) -> None:
        top = ttk.Frame(self.turmas_tab)
        top.pack(fill="both", expand=True)

        form = ttk.LabelFrame(top, text="Cadastro de turma", padding=10)
        form.pack(fill="x", anchor="n")

        fields = [
            ("Código da turma", self.turma_codigo_var, 44),
            ("Dia da semana", self.turma_dia_var, 12),
            ("Horário", self.turma_horario_var, 10),
            ("Tema / componente", self.turma_componente_var, 24),
            ("Situação", self.turma_situacao_var, 12),
        ]

        ttk.Label(form, text=fields[0][0]).grid(row=0, column=0, sticky="w", pady=4)
        ttk.Entry(form, textvariable=fields[0][1], width=fields[0][2]).grid(
            row=0, column=1, sticky="ew", pady=4, padx=(12, 16)
        )

        ttk.Label(form, text=fields[1][0]).grid(row=0, column=2, sticky="w", pady=4)
        ttk.Combobox(
            form,
            values=WEEKDAY_OPTIONS,
            textvariable=fields[1][1],
            state="readonly",
            width=10,
        ).grid(row=0, column=3, sticky="w", pady=4, padx=(12, 16))

        ttk.Label(form, text=fields[2][0]).grid(row=0, column=4, sticky="w", pady=4)
        turma_horario_entry = ttk.Entry(form, textvariable=fields[2][1], width=fields[2][2])
        turma_horario_entry.grid(row=0, column=5, sticky="w", pady=4, padx=(12, 16))
        self._register_formatted_entry(turma_horario_entry, self._format_time_live)

        ttk.Label(form, text=fields[3][0]).grid(row=1, column=0, sticky="w", pady=4)
        ttk.Entry(form, textvariable=fields[3][1], width=fields[3][2]).grid(
            row=1, column=1, columnspan=3, sticky="ew", pady=4, padx=(12, 16)
        )

        ttk.Label(form, text=fields[4][0]).grid(row=1, column=4, sticky="w", pady=4)
        ttk.Combobox(
            form,
            values=TURMA_STATUS_OPTIONS,
            textvariable=fields[4][1],
            state="readonly",
            width=10,
        ).grid(row=1, column=5, sticky="w", pady=4, padx=(12, 0))

        buttons = ttk.Frame(form)
        buttons.grid(row=2, column=0, columnspan=6, sticky="w", pady=(8, 0))
        ttk.Button(buttons, text="Salvar turma", command=self.save_turma).pack(side="left")
        ttk.Button(buttons, text="Nova turma", command=self.clear_turma_form).pack(
            side="left", padx=(10, 0)
        )
        ttk.Button(
            buttons,
            text="Carregar selecionada",
            command=self.load_selected_turma,
        ).pack(side="left", padx=(10, 0))
        ttk.Button(
            buttons,
            text="Alternar situação",
            command=self.toggle_selected_turma_status,
        ).pack(side="left", padx=(10, 0))

        tree_frame = ttk.LabelFrame(top, text="Turmas cadastradas", padding=8)
        tree_frame.pack(fill="both", expand=True, pady=(10, 0))

        columns = ("codigo", "dia", "horario", "componente", "situacao")
        self.turma_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=10)
        headers = {
            "codigo": "Código",
            "dia": "Dia",
            "horario": "Horário",
            "componente": "Componente",
            "situacao": "Situação",
        }
        min_widths = {
            "codigo": 150,
            "dia": 70,
            "horario": 80,
            "componente": 150,
            "situacao": 90,
        }
        weights = {
            "codigo": 34,
            "dia": 10,
            "horario": 12,
            "componente": 28,
            "situacao": 16,
        }
        for column in columns:
            self.turma_tree.heading(column, text=headers[column])
            self.turma_tree.column(column, width=min_widths[column], anchor="w", stretch=True)
        self.turma_tree.pack(side="left", fill="both", expand=True)
        self.turma_tree.bind("<Double-1>", lambda _event: self.load_selected_turma())
        self._register_treeview_autofit(self.turma_tree, columns, weights, min_widths)

        tree_scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.turma_tree.yview)
        tree_scroll.pack(side="right", fill="y")
        self.turma_tree.configure(yscrollcommand=tree_scroll.set)

    def _build_encontros_tab(self) -> None:
        paned = ttk.Panedwindow(self.encontros_tab, orient="horizontal")
        paned.pack(fill="both", expand=True)

        left = ttk.Frame(paned, padding=(0, 0, 8, 0))
        right = ttk.Frame(paned)
        paned.add(left, weight=2)
        paned.add(right, weight=2)

        form = ttk.LabelFrame(left, text="Registro de encontro", padding=10)
        form.pack(fill="x", anchor="n")

        ttk.Label(form, text="Turma").grid(row=0, column=0, sticky="w", pady=4)
        self.encontro_turma_combo = ttk.Combobox(
            form,
            textvariable=self.encontro_turma_var,
            state="readonly",
            width=40,
        )
        self.encontro_turma_combo.grid(
            row=0, column=1, columnspan=4, sticky="ew", pady=4, padx=(12, 0)
        )
        self.encontro_turma_combo.bind("<<ComboboxSelected>>", self._on_encontro_turma_selected)

        ttk.Label(form, text="Data (dd/mm/aaaa ou aaaa-mm-dd)").grid(
            row=1, column=0, sticky="w", pady=4
        )
        encontro_data_entry = ttk.Entry(form, textvariable=self.encontro_data_var, width=16)
        encontro_data_entry.grid(row=1, column=1, sticky="w", padx=(12, 8), pady=4)
        self._register_formatted_entry(encontro_data_entry, self._format_date_live)
        ttk.Button(form, text="Calendário", command=self.open_encontro_calendar).grid(
            row=1, column=2, sticky="w", pady=4, padx=(0, 16)
        )
        ttk.Label(form, text="Número da pauta").grid(row=1, column=3, sticky="w", pady=4)
        ttk.Entry(form, textvariable=self.encontro_pauta_var, width=8).grid(
            row=1, column=4, sticky="w", padx=(12, 0), pady=4
        )

        ttk.Label(form, text="Início").grid(row=2, column=0, sticky="w", pady=4)
        encontro_inicio_entry = ttk.Entry(form, textvariable=self.encontro_inicio_var, width=10)
        encontro_inicio_entry.grid(row=2, column=1, sticky="w", padx=(12, 16), pady=4)
        self._register_formatted_entry(encontro_inicio_entry, self._format_time_live)
        ttk.Label(form, text="Término").grid(row=2, column=3, sticky="w", pady=4)
        encontro_fim_entry = ttk.Entry(form, textvariable=self.encontro_fim_var, width=10)
        encontro_fim_entry.grid(row=2, column=4, sticky="w", padx=(12, 0), pady=4)
        self._register_formatted_entry(encontro_fim_entry, self._format_time_live)

        ttk.Label(form, text="Participantes").grid(row=3, column=0, sticky="w", pady=4)
        ttk.Entry(form, textvariable=self.encontro_participantes_var, width=10).grid(
            row=3, column=1, sticky="w", padx=(12, 16), pady=4
        )
        ttk.Label(form, text="Duração").grid(row=3, column=3, sticky="w", pady=4)
        ttk.Entry(form, textvariable=self.encontro_duracao_var, width=10).grid(
            row=3, column=4, sticky="w", padx=(12, 0), pady=4
        )

        ttk.Label(form, text="Situação").grid(row=4, column=0, sticky="w", pady=4)
        ttk.Combobox(
            form,
            values=STATUS_OPTIONS,
            textvariable=self.encontro_status_var,
            state="readonly",
            width=16,
        ).grid(row=4, column=1, sticky="w", padx=(12, 16), pady=4)

        ttk.Label(form, text="Texto automático").grid(row=4, column=3, sticky="w", pady=4)
        ttk.Combobox(
            form,
            values=self.auto_observacao_names,
            textvariable=self.auto_observacao_var,
            state="readonly",
            width=24,
        ).grid(row=4, column=4, sticky="w", padx=(12, 0), pady=4)

        ttk.Button(form, text="Aplicar texto", command=self.apply_auto_observation).grid(
            row=5, column=4, sticky="e", pady=(6, 8)
        )

        ttk.Label(form, text="Observação").grid(row=5, column=0, sticky="nw", pady=(10, 4))
        self.observacao_text = tk.Text(form, width=62, height=5, wrap="word")
        self.observacao_text.grid(row=6, column=0, columnspan=5, sticky="ew", pady=(0, 8))

        action_row = ttk.Frame(form)
        action_row.grid(row=7, column=0, columnspan=5, sticky="w")
        ttk.Button(action_row, text="Salvar encontro", command=self.save_encontro).pack(side="left")
        ttk.Button(action_row, text="Inserir encontro", command=self.clear_encontro_form).pack(
            side="left", padx=(10, 0)
        )
        ttk.Button(
            action_row,
            text="Carregar selecionado",
            command=self.load_selected_encontro,
        ).pack(side="left", padx=(10, 0))

        form.columnconfigure(1, weight=1)
        form.columnconfigure(4, weight=1)

        evidence_frame = ttk.LabelFrame(left, text="Evidências do encontro", padding=10)
        evidence_frame.pack(fill="both", expand=True, pady=(10, 0))

        evidence_list_frame = ttk.Frame(evidence_frame)
        evidence_list_frame.pack(fill="both", expand=True)

        self.evidence_listbox = tk.Listbox(evidence_list_frame, height=9)
        self.evidence_listbox.pack(side="left", fill="both", expand=True)
        self.evidence_listbox.bind("<<ListboxSelect>>", self._on_evidence_selected)

        evidence_scroll_y = ttk.Scrollbar(
            evidence_list_frame, orient="vertical", command=self.evidence_listbox.yview
        )
        evidence_scroll_y.pack(side="right", fill="y")
        self.evidence_listbox.configure(yscrollcommand=evidence_scroll_y.set)

        evidence_buttons = ttk.Frame(evidence_frame)
        evidence_buttons.pack(fill="x", pady=(10, 0))
        ttk.Button(evidence_buttons, text="Colar print", command=self.paste_image_from_clipboard).pack(
            side="left"
        )
        ttk.Button(evidence_buttons, text="Adicionar imagem", command=self.add_image_file).pack(
            side="left", padx=(10, 0)
        )
        ttk.Button(
            evidence_buttons,
            text="Visualizar imagem",
            command=self.open_selected_evidence,
        ).pack(side="left", padx=(10, 0))
        ttk.Button(evidence_buttons, text="Remover imagem", command=self.remove_selected_evidence).pack(
            side="left", padx=(10, 0)
        )

        right_paned = ttk.Panedwindow(right, orient="vertical")
        right_paned.pack(fill="both", expand=True)

        encontro_list_frame = ttk.LabelFrame(right_paned, text="Encontros do mês", padding=8)
        preview_frame = ttk.LabelFrame(right_paned, text="Pré-visualização da evidência", padding=8)
        right_paned.add(encontro_list_frame, weight=1)
        right_paned.add(preview_frame, weight=1)

        columns = ("data", "pauta", "turma", "status", "participantes", "imagens")
        self.encontro_tree = ttk.Treeview(
            encontro_list_frame,
            columns=columns,
            show="headings",
            height=15,
        )
        headers = {
            "data": "Data",
            "pauta": "Pauta",
            "turma": "Turma",
            "status": "Situação",
            "participantes": "Participantes",
            "imagens": "Imagens",
        }
        min_widths = {
            "data": 80,
            "pauta": 70,
            "turma": 115,
            "status": 100,
            "participantes": 88,
            "imagens": 68,
        }
        weights = {
            "data": 12,
            "pauta": 10,
            "turma": 28,
            "status": 20,
            "participantes": 16,
            "imagens": 14,
        }
        for column in columns:
            self.encontro_tree.heading(column, text=headers[column])
            self.encontro_tree.column(column, width=min_widths[column], anchor="w", stretch=True)
        self.encontro_tree.pack(side="left", fill="both", expand=True)
        self.encontro_tree.bind("<Double-1>", lambda _event: self.load_selected_encontro())
        self._register_treeview_autofit(self.encontro_tree, columns, weights, min_widths)

        encontro_scroll = ttk.Scrollbar(
            encontro_list_frame, orient="vertical", command=self.encontro_tree.yview
        )
        encontro_scroll.pack(side="right", fill="y")
        encontro_scroll_x = ttk.Scrollbar(
            encontro_list_frame, orient="horizontal", command=self.encontro_tree.xview
        )
        encontro_scroll_x.pack(side="bottom", fill="x")
        self.encontro_tree.configure(
            yscrollcommand=encontro_scroll.set,
            xscrollcommand=encontro_scroll_x.set,
        )

        self.preview_title_var = tk.StringVar(value="Selecione uma evidência à esquerda.")
        ttk.Label(preview_frame, textvariable=self.preview_title_var).pack(anchor="w", pady=(0, 8))

        self.preview_canvas = tk.Canvas(preview_frame, background="#f3f4f6", highlightthickness=0)
        self.preview_canvas.pack(fill="both", expand=True)
        self.preview_canvas.bind("<Configure>", lambda _event: self._render_preview_image())

    def _build_checklist_tab(self) -> None:
        summary = ttk.LabelFrame(self.checklist_tab, text="Conferência mensal", padding=10)
        summary.pack(fill="x")

        self.checklist_labels: dict[str, ttk.Label] = {}
        rows = [
            ("total_registrados", "Total registrados"),
            ("total_realizados", "Total realizados"),
            ("valor_formacao_semanal", "Valor formação semanal"),
            ("valor_total_mensal", "Valor total mensal"),
            ("turmas", "Turmas"),
            ("pautas", "Pautas"),
            ("sem_imagem", "Sem imagem"),
            ("sem_observacao", "Sem observação"),
            ("sem_horario", "Sem horário"),
            ("sem_participantes", "Sem participantes"),
        ]
        for row, (key, label_text) in enumerate(rows):
            ttk.Label(summary, text=label_text).grid(
                row=row, column=0, sticky="w", pady=2
            )
            label = ttk.Label(summary, text="-")
            label.grid(row=row, column=1, sticky="w", padx=(12, 0), pady=2)
            self.checklist_labels[key] = label

        detail_frame = ttk.LabelFrame(
            self.checklist_tab,
            text="Pendências e detalhes",
            padding=10,
        )
        detail_frame.pack(fill="both", expand=True, pady=(10, 0))

        self.checklist_listbox = tk.Listbox(detail_frame, height=14)
        self.checklist_listbox.pack(fill="both", expand=True)

        action_row = ttk.Frame(self.checklist_tab, padding=(0, 10, 0, 0))
        action_row.pack(fill="x")
        self.refresh_checklist_button = ttk.Button(
            action_row, text="Atualizar checklist", command=self.refresh_checklist
        )
        self.refresh_checklist_button.pack(
            side="left"
        )
        self.generate_docx_button = ttk.Button(
            action_row, text="Gerar relatório DOCX", command=self.generate_docx_report
        )
        self.generate_docx_button.pack(side="left", padx=(10, 0))
        self.generate_pdf_button = ttk.Button(
            action_row, text="Gerar relatório PDF", command=self.generate_pdf_report
        )
        self.generate_pdf_button.pack(side="left", padx=(10, 0))
        self.generate_financial_button = ttk.Button(
            action_row,
            text="Gerar extrato financeiro",
            command=self.generate_financial_report,
        )
        self.generate_financial_button.pack(side="left", padx=(10, 0))
        self.open_evidence_button = ttk.Button(
            action_row,
            text="Abrir pasta das evidências",
            command=self.open_evidence_folder,
        )
        self.open_evidence_button.pack(side="left", padx=(10, 0))
        self.open_output_button = ttk.Button(
            action_row, text="Abrir pasta de saída", command=self.open_output_folder
        )
        self.open_output_button.pack(side="left", padx=(10, 0))

        self.report_progress_var = tk.StringVar(value="")
        self.report_progress = ttk.Progressbar(
            self.checklist_tab, mode="indeterminate", length=260
        )
        self.report_progress.pack(anchor="w", pady=(10, 0))
        self.report_progress.pack_forget()
        self.report_progress_label = ttk.Label(
            self.checklist_tab, textvariable=self.report_progress_var
        )
        self.report_progress_label.pack(anchor="w", pady=(6, 0))

    def _load_initial_state(self) -> None:
        self.apply_defaults_to_form()
        self.refresh_month_selector()
        self.refresh_turma_tree()
        self.refresh_encontro_tree()
        self.refresh_checklist()

        if self.month_label_to_id:
            first_label = next(iter(self.month_label_to_id))
            self.current_month_label_var.set(first_label)
            self.load_month(self.month_label_to_id[first_label])
        else:
            self.current_month_id = None
            self.current_month_label_var.set("")
            self.status_bar_var.set(
                "Nenhum mês com encontros ainda. O primeiro mês será criado ao salvar um encontro."
            )

    def refresh_month_selector(self, select_month_id: int | None = None) -> None:
        rows = self.database.list_months()
        self.month_label_to_id = {row["ref_label"]: int(row["id"]) for row in rows}
        labels = list(self.month_label_to_id.keys())
        self.month_combo["values"] = labels

        if select_month_id is not None:
            for label, month_id in self.month_label_to_id.items():
                if month_id == select_month_id:
                    self.current_month_label_var.set(label)
                    return

        if labels and not self.current_month_label_var.get():
            self.current_month_label_var.set(labels[0])

    def _on_month_selected(self, _event=None) -> None:
        label = self.current_month_label_var.get()
        month_id = self.month_label_to_id.get(label)
        if month_id:
            self.load_month(month_id)

    def load_month(self, month_id: int) -> None:
        row = self.database.get_month(month_id)
        if not row:
            return

        self.current_month_id = month_id
        self.nome_var.set(row["teacher_name"])
        self.tema_var.set(row["theme"])
        self.email_var.set(row["institutional_email"])
        self.diretoria_var.set(row["diretoria_ure"])
        self.pec_var.set(row["pec_responsavel"])
        self.valor_formacao_semanal_var.set(self._format_currency_from_cents(int(row["weekly_rate_cents"] or 0)))
        self.status_bar_var.set(
            f"Mês ativo: {row['ref_label']} | Dados mantidos apenas localmente."
        )

        self.clear_encontro_form()
        self.refresh_turma_tree()
        self.refresh_encontro_tree()
        self.refresh_checklist()

    def collect_professor_data(self) -> dict[str, str]:
        return {
            "nome": self.nome_var.get().strip(),
            "tema": self.tema_var.get().strip(),
            "email_institucional": self.email_var.get().strip(),
            "diretoria_ure": self.diretoria_var.get().strip(),
            "pec_responsavel": self.pec_var.get().strip(),
            "valor_formacao_semanal": self.valor_formacao_semanal_var.get().strip(),
        }

    def save_current_month(self) -> None:
        if not self.current_month_id:
            messagebox.showwarning("Mês não selecionado", "Crie ou selecione um mês primeiro.")
            return
        if not self._normalize_currency_field():
            return
        self.database.save_month(self.current_month_id, self.collect_professor_data())
        self.status_bar_var.set("Dados do mês atualizados.")
        messagebox.showinfo("Dados salvos", "Os dados do professor foram salvos no mês ativo.")

    def save_defaults(self) -> None:
        if not self._normalize_currency_field():
            return
        self.database.save_defaults(self.collect_professor_data())
        self.status_bar_var.set("Padrão do professor atualizado.")
        messagebox.showinfo("Padrão salvo", "Os dados foram gravados como padrão para próximos meses.")

    def apply_defaults_to_form(self) -> None:
        defaults = self.database.get_defaults()
        self.nome_var.set(defaults.get("nome", ""))
        self.tema_var.set(defaults.get("tema", ""))
        self.email_var.set(defaults.get("email_institucional", ""))
        self.diretoria_var.set(defaults.get("diretoria_ure", ""))
        self.pec_var.set(defaults.get("pec_responsavel", ""))
        self.valor_formacao_semanal_var.set(defaults.get("valor_formacao_semanal", ""))

    def clear_turma_form(self) -> None:
        self.selected_turma_id = None
        self.turma_codigo_var.set("")
        self.turma_dia_var.set(WEEKDAY_OPTIONS[0])
        self.turma_horario_var.set("")
        self.turma_componente_var.set("")
        self.turma_situacao_var.set(TURMA_STATUS_OPTIONS[0])

    def save_turma(self) -> None:
        codigo = self.turma_codigo_var.get().strip()
        if not codigo:
            messagebox.showwarning("Turma incompleta", "Informe o código da turma.")
            return

        payload = {
            "codigo": codigo,
            "dia_semana": self.turma_dia_var.get().strip(),
            "horario": self.turma_horario_var.get().strip(),
            "componente": self.turma_componente_var.get().strip(),
            "situacao": self.turma_situacao_var.get().strip() or TURMA_STATUS_OPTIONS[0],
        }

        try:
            self.selected_turma_id = self.database.save_turma(payload, self.selected_turma_id)
        except sqlite3.IntegrityError:
            messagebox.showerror("Turma duplicada", "Já existe uma turma com esse código.")
            return

        self.refresh_turma_tree(select_id=self.selected_turma_id)
        self.refresh_encontro_tree()
        self.status_bar_var.set("Turma atualizada no banco local.")
        messagebox.showinfo("Turma salva", "Cadastro de turma salvo com sucesso.")

    def refresh_turma_tree(self, select_id: int | None = None) -> None:
        rows = self.database.list_turmas(include_inactive=True)
        for item in self.turma_tree.get_children():
            self.turma_tree.delete(item)

        active_labels = []
        self.turma_label_to_id = {}
        for row in rows:
            turma_id = int(row["id"])
            values = (
                row["codigo"],
                row["dia_semana"],
                row["horario"],
                row["componente"],
                row["situacao"],
            )
            self.turma_tree.insert("", "end", iid=str(turma_id), values=values)
            if row["situacao"] == "ativa":
                active_labels.append(row["codigo"])
                self.turma_label_to_id[row["codigo"]] = turma_id
            elif row["codigo"] not in self.turma_label_to_id:
                self.turma_label_to_id[row["codigo"]] = turma_id

        self.encontro_turma_combo["values"] = active_labels or list(self.turma_label_to_id.keys())

        if select_id is not None and str(select_id) in self.turma_tree.get_children():
            self.turma_tree.selection_set(str(select_id))
            self.turma_tree.focus(str(select_id))

    def load_selected_turma(self) -> None:
        selection = self.turma_tree.selection()
        if not selection:
            messagebox.showwarning("Selecione uma turma", "Escolha uma turma na lista.")
            return

        turma_id = int(selection[0])
        row = self.database.get_turma(turma_id)
        if not row:
            return

        self.selected_turma_id = turma_id
        self.turma_codigo_var.set(row["codigo"])
        self.turma_dia_var.set(row["dia_semana"])
        self.turma_horario_var.set(row["horario"])
        self.turma_componente_var.set(row["componente"])
        self.turma_situacao_var.set(row["situacao"])

    def toggle_selected_turma_status(self) -> None:
        selection = self.turma_tree.selection()
        if not selection:
            messagebox.showwarning("Selecione uma turma", "Escolha uma turma para alterar a situação.")
            return

        turma_id = int(selection[0])
        row = self.database.get_turma(turma_id)
        if not row:
            return

        new_status = "inativa" if row["situacao"] == "ativa" else "ativa"
        payload = {
            "codigo": row["codigo"],
            "dia_semana": row["dia_semana"],
            "horario": row["horario"],
            "componente": row["componente"],
            "situacao": new_status,
        }
        self.database.save_turma(payload, turma_id)
        self.refresh_turma_tree(select_id=turma_id)
        self.status_bar_var.set(f"Situação da turma alterada para {new_status}.")

    def clear_encontro_form(self) -> None:
        self.selected_encontro_id = None
        self.selected_evidence_id = None
        self.encontro_data_var.set("")
        self.encontro_pauta_var.set("")
        self.encontro_turma_var.set("")
        self.encontro_inicio_var.set("")
        self.encontro_fim_var.set("")
        self.encontro_participantes_var.set("")
        self.encontro_duracao_var.set("")
        self.encontro_status_var.set(STATUS_OPTIONS[0])
        self.observacao_text.delete("1.0", "end")
        self.evidence_listbox.delete(0, "end")
        self._clear_preview("Selecione uma evidência à esquerda.")

    def apply_auto_observation(self) -> None:
        selected = self.auto_observacao_var.get()
        text = AUTO_OBSERVATIONS.get(selected)
        if not text:
            return
        self.observacao_text.delete("1.0", "end")
        self.observacao_text.insert("1.0", text)

    def _parse_date(self, raw_value: str) -> str:
        text = raw_value.strip()
        if not text:
            raise ValueError("Não permitir encontro sem data.")

        for date_format in ("%d/%m/%Y", "%Y-%m-%d"):
            try:
                return datetime.strptime(text, date_format).strftime("%Y-%m-%d")
            except ValueError:
                continue
        raise ValueError("Use a data no formato dd/mm/aaaa ou aaaa-mm-dd.")

    def _normalize_time(self, raw_value: str) -> str:
        text = raw_value.strip()
        if not text:
            return ""
        try:
            return datetime.strptime(text, "%H:%M").strftime("%H:%M")
        except ValueError as error:
            raise ValueError("Os horários precisam usar o formato HH:MM.") from error

    def _get_or_create_month_from_iso_date(self, iso_date: str) -> int:
        encounter_date = datetime.strptime(iso_date, "%Y-%m-%d")
        month_id = self.database.get_or_create_month(encounter_date.month, encounter_date.year)
        if not self._normalize_currency_field():
            raise ValueError("Informe um valor válido para a formação semanal.")
        self.database.save_month(month_id, self.collect_professor_data())
        return month_id

    def _collect_encontro_payload(self) -> dict[str, object]:
        turma_label = self.encontro_turma_var.get().strip()
        turma_id = self.turma_label_to_id.get(turma_label)
        if not turma_id:
            raise ValueError("Não permitir encontro sem turma.")

        pauta_text = self.encontro_pauta_var.get().strip()
        if not pauta_text:
            raise ValueError("Não permitir encontro sem número de pauta.")

        try:
            pauta_numero = int(pauta_text)
        except ValueError as error:
            raise ValueError("O número da pauta precisa ser numérico.") from error

        participantes_text = self.encontro_participantes_var.get().strip()
        participantes = None
        if participantes_text:
            try:
                participantes = int(participantes_text)
            except ValueError as error:
                raise ValueError("Participantes precisa ser um numero inteiro.") from error

        data_encontro = self._parse_date(self.encontro_data_var.get())
        month_id = self._get_or_create_month_from_iso_date(data_encontro)

        return {
            "month_id": month_id,
            "turma_id": turma_id,
            "data_encontro": data_encontro,
            "pauta_numero": pauta_numero,
            "hora_inicio": self._normalize_time(self.encontro_inicio_var.get()),
            "hora_fim": self._normalize_time(self.encontro_fim_var.get()),
            "participantes": participantes,
            "duracao": self.encontro_duracao_var.get().strip(),
            "observacao": self.observacao_text.get("1.0", "end").strip(),
            "situacao": self.encontro_status_var.get().strip() or STATUS_OPTIONS[0],
        }

    def save_encontro(self, show_message: bool = True) -> int | None:
        try:
            payload = self._collect_encontro_payload()
        except ValueError as error:
            messagebox.showwarning("Encontro incompleto", str(error))
            return None

        try:
            self.selected_encontro_id = self.database.save_encontro(payload, self.selected_encontro_id)
        except sqlite3.IntegrityError:
            messagebox.showerror(
                "Encontro duplicado",
                "Já existe encontro com a mesma data, turma e pauta neste mês.",
            )
            return None

        target_month_id = int(payload["month_id"])
        self.refresh_month_selector(select_month_id=target_month_id)
        self.load_month(target_month_id)
        encontro_id = self.selected_encontro_id
        if encontro_id:
            self.load_encontro_into_form(encontro_id)

        if show_message:
            messagebox.showinfo("Encontro salvo", "Registro do encontro salvo com sucesso.")
        self.status_bar_var.set("Encontro salvo no banco local e vinculado ao mês da data.")
        return encontro_id

    def refresh_encontro_tree(self, select_id: int | None = None) -> None:
        for item in self.encontro_tree.get_children():
            self.encontro_tree.delete(item)

        if not self.current_month_id:
            return

        rows = self.database.list_encontros(self.current_month_id)
        for row in rows:
            self.encontro_tree.insert(
                "",
                "end",
                iid=str(int(row["id"])),
                values=(
                    self._format_date_for_display(row["data_encontro"]),
                    row["pauta_numero"],
                    row["turma_codigo"],
                    row["situacao"],
                    row["participantes"] if row["participantes"] is not None else "",
                    row["total_imagens"],
                ),
            )

        if select_id is not None and str(select_id) in self.encontro_tree.get_children():
            self.encontro_tree.selection_set(str(select_id))
            self.encontro_tree.focus(str(select_id))

    def load_selected_encontro(self) -> None:
        selection = self.encontro_tree.selection()
        if not selection:
            messagebox.showwarning("Selecione um encontro", "Escolha um encontro na lista.")
            return
        self.load_encontro_into_form(int(selection[0]))

    def load_encontro_into_form(self, encontro_id: int) -> None:
        row = self.database.get_encontro(encontro_id)
        if not row:
            return

        self.selected_encontro_id = encontro_id
        self.encontro_data_var.set(self._format_date_for_display(row["data_encontro"], full_year=True))
        self.encontro_pauta_var.set(str(row["pauta_numero"]))
        self.encontro_turma_var.set(row["turma_codigo"])
        self.encontro_inicio_var.set(row["hora_inicio"])
        self.encontro_fim_var.set(row["hora_fim"])
        self.encontro_participantes_var.set(
            "" if row["participantes"] is None else str(row["participantes"])
        )
        self.encontro_duracao_var.set(row["duracao"])
        self.encontro_status_var.set(row["situacao"])
        self.observacao_text.delete("1.0", "end")
        self.observacao_text.insert("1.0", row["observacao"])
        self.refresh_evidence_list()

    def _format_date_for_display(self, iso_date: str, full_year: bool = False) -> str:
        fmt = "%d/%m/%Y" if full_year else "%d/%m"
        return datetime.strptime(iso_date, "%Y-%m-%d").strftime(fmt)

    def _calculate_end_time(self, start_time: str) -> str:
        normalized_start = self._normalize_time(start_time)
        start_dt = datetime.strptime(normalized_start, "%H:%M")
        end_dt = start_dt + timedelta(minutes=90)
        return end_dt.strftime("%H:%M")

    def _fill_schedule_from_selected_turma(self) -> None:
        turma_label = self.encontro_turma_var.get().strip()
        turma_id = self.turma_label_to_id.get(turma_label)
        if not turma_id:
            return

        turma = self.database.get_turma(turma_id)
        if not turma:
            return

        horario_inicio = (turma["horario"] or "").strip()
        if not horario_inicio:
            self.encontro_inicio_var.set("")
            self.encontro_fim_var.set("")
            self.encontro_duracao_var.set("")
            return

        try:
            horario_inicio = self._normalize_time(horario_inicio)
            horario_fim = self._calculate_end_time(horario_inicio)
        except ValueError:
            self.status_bar_var.set(
                "A turma selecionada tem horário inválido. Ajuste o cadastro da turma."
            )
            return

        self.encontro_inicio_var.set(horario_inicio)
        self.encontro_fim_var.set(horario_fim)
        self.encontro_duracao_var.set("1h30")

    def _on_encontro_turma_selected(self, _event=None) -> None:
        self._fill_schedule_from_selected_turma()

    def ensure_encontro_saved(self) -> int | None:
        if self.selected_encontro_id:
            return self.selected_encontro_id
        return self.save_encontro(show_message=False)

    def _build_evidence_directory(self, encontro_row: sqlite3.Row) -> Path:
        month = self.database.get_month(int(encontro_row["month_id"]))
        if not month:
            raise ValueError("Mês do encontro não encontrado.")

        month_folder = f"{month['ref_year']}-{int(month['ref_month']):02d}"
        turma_folder = slugify(str(encontro_row["turma_codigo"]))
        pauta_folder = f"pauta_{int(encontro_row['pauta_numero']):02d}"
        target = EVIDENCIAS_DIR / month_folder / turma_folder / pauta_folder
        target.mkdir(parents=True, exist_ok=True)
        return target

    def _next_evidence_path(self, encontro_row: sqlite3.Row, extension: str) -> Path:
        folder = self._build_evidence_directory(encontro_row)
        data = str(encontro_row["data_encontro"])
        counter = 1
        while True:
            candidate = folder / f"{data}_{counter:02d}{extension}"
            if not candidate.exists():
                return candidate
            counter += 1

    def refresh_evidence_list(self) -> None:
        self.selected_evidence_id = None
        self.evidence_listbox.delete(0, "end")
        if not self.selected_encontro_id:
            self._clear_preview("Selecione uma evidência à esquerda.")
            return

        evidences = self.database.list_evidences(self.selected_encontro_id)
        for item in evidences:
            label = f"{item['id']} - {Path(item['arquivo_copiado']).name}"
            self.evidence_listbox.insert("end", label)

        if evidences:
            self.evidence_listbox.selection_set(0)
            self._on_evidence_selected()
        else:
            self._clear_preview("Nenhuma evidência anexada para este encontro.")

    def _clear_preview(self, message: str) -> None:
        self.preview_photo = None
        self.preview_image_path = None
        self.preview_title_var.set(message)
        self.preview_canvas.delete("all")

    def _on_evidence_selected(self, _event=None) -> None:
        evidence = self._get_selected_evidence_row()
        if not evidence:
            self._clear_preview("Selecione uma evidência à esquerda.")
            return

        image_path = Path(evidence["arquivo_copiado"])
        self.preview_image_path = image_path
        self.preview_title_var.set(image_path.name)
        self._render_preview_image()

    def _render_preview_image(self) -> None:
        image_path = getattr(self, "preview_image_path", None)
        if not image_path:
            return

        canvas_width = max(self.preview_canvas.winfo_width(), 320)
        canvas_height = max(self.preview_canvas.winfo_height(), 220)
        self.preview_canvas.delete("all")

        try:
            from PIL import Image, ImageTk
        except ImportError:
            self.preview_canvas.create_text(
                canvas_width / 2,
                canvas_height / 2,
                text="Instale Pillow para ver a pré-visualização.\n\npip install Pillow",
                justify="center",
            )
            return

        try:
            image = Image.open(image_path)
        except Exception as error:
            self.preview_canvas.create_text(
                canvas_width / 2,
                canvas_height / 2,
                text=f"Não foi possível abrir a imagem.\n\n{error}",
                justify="center",
            )
            return

        image.thumbnail((canvas_width - 16, canvas_height - 16))
        self.preview_photo = ImageTk.PhotoImage(image)
        self.preview_canvas.create_image(
            canvas_width / 2,
            canvas_height / 2,
            image=self.preview_photo,
            anchor="center",
        )

    def _get_selected_evidence_row(self) -> sqlite3.Row | None:
        if not self.selected_encontro_id:
            return None
        selection = self.evidence_listbox.curselection()
        if not selection:
            return None
        index = selection[0]
        evidences = self.database.list_evidences(self.selected_encontro_id)
        if index >= len(evidences):
            return None
        return evidences[index]

    def add_image_file(self) -> None:
        encontro_id = self.ensure_encontro_saved()
        if not encontro_id:
            return

        file_paths = filedialog.askopenfilenames(
            title="Selecione imagens",
            filetypes=[("Imagens", "*.png *.jpg *.jpeg *.bmp *.gif *.webp")],
        )
        if not file_paths:
            return

        encontro_row = self.database.get_encontro(encontro_id)
        if not encontro_row:
            return

        saved = 0
        for source in file_paths:
            source_path = Path(source)
            extension = source_path.suffix.lower() or ".png"
            target = self._next_evidence_path(encontro_row, extension)
            shutil.copy2(source_path, target)
            self.database.add_evidence(encontro_id, str(source_path), str(target))
            saved += 1

        self.refresh_evidence_list()
        self.refresh_encontro_tree(select_id=encontro_id)
        self.refresh_checklist()
        self.status_bar_var.set(f"{saved} imagem(ns) anexada(s) ao encontro.")

    def paste_image_from_clipboard(self) -> None:
        encontro_id = self.ensure_encontro_saved()
        if not encontro_id:
            return

        encontro_row = self.database.get_encontro(encontro_id)
        if not encontro_row:
            return

        try:
            from PIL import ImageGrab
        except ImportError:
            messagebox.showerror(
                "Dependência ausente",
                "O recurso de colar print precisa da biblioteca Pillow.\n\n"
                "Instale com:\n"
                "pip install Pillow",
            )
            return

        try:
            clipboard_data = ImageGrab.grabclipboard()
        except Exception as error:
            messagebox.showerror("Área de transferência", f"Não foi possível acessar o clipboard: {error}")
            return

        if clipboard_data is None:
            messagebox.showwarning("Clipboard vazio", "Não há imagem copiada no momento.")
            return

        saved = 0
        if isinstance(clipboard_data, list):
            for item in clipboard_data:
                path = Path(item)
                if path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp"}:
                    continue
                target = self._next_evidence_path(encontro_row, path.suffix.lower())
                shutil.copy2(path, target)
                self.database.add_evidence(encontro_id, str(path), str(target))
                saved += 1
        else:
            target = self._next_evidence_path(encontro_row, ".png")
            clipboard_data.save(target, format="PNG")
            self.database.add_evidence(encontro_id, "clipboard", str(target))
            saved = 1

        if saved == 0:
            messagebox.showwarning(
                "Clipboard sem imagem válida",
                "O conteúdo copiado não contém imagem ou arquivo de imagem suportado.",
            )
            return

        self.refresh_evidence_list()
        self.refresh_encontro_tree(select_id=encontro_id)
        self.refresh_checklist()
        self.status_bar_var.set("Imagem colada e salva localmente.")

    def open_selected_evidence(self) -> None:
        row = self._get_selected_evidence_row()
        if not row:
            messagebox.showwarning("Selecione uma imagem", "Escolha uma evidência na lista.")
            return
        self._open_path(Path(row["arquivo_copiado"]))

    def remove_selected_evidence(self) -> None:
        row = self._get_selected_evidence_row()
        if not row:
            messagebox.showwarning("Selecione uma imagem", "Escolha uma evidência para remover.")
            return

        if not messagebox.askyesno("Remover imagem", "Deseja remover a evidência selecionada"):
            return

        removed_path = self.database.delete_evidence(int(row["id"]))
        if removed_path:
            try:
                Path(removed_path).unlink(missing_ok=True)
            except TypeError:
                path = Path(removed_path)
                if path.exists():
                    path.unlink()

        self.refresh_evidence_list()
        if self.selected_encontro_id:
            self.refresh_encontro_tree(select_id=self.selected_encontro_id)
        self.refresh_checklist()
        self.status_bar_var.set("Evidência removida.")

    def refresh_checklist(self) -> None:
        checklist = self.database.get_checklist(self.current_month_id) if self.current_month_id else None
        if not checklist:
            for label in self.checklist_labels.values():
                label.configure(text="-")
            self.checklist_listbox.delete(0, "end")
            return

        self.checklist_labels["total_registrados"].configure(text=str(checklist["total_registrados"]))
        self.checklist_labels["total_realizados"].configure(text=str(checklist["total_realizados"]))
        self.checklist_labels["valor_formacao_semanal"].configure(
            text=self._format_currency_from_cents(int(checklist["valor_formacao_semanal_centavos"]))
        )
        self.checklist_labels["valor_total_mensal"].configure(
            text=self._format_currency_from_cents(int(checklist["valor_total_mensal_centavos"]))
        )
        self.checklist_labels["turmas"].configure(
            text=", ".join(checklist["turmas"]) if checklist["turmas"] else "-"
        )
        self.checklist_labels["pautas"].configure(
            text=", ".join(str(item) for item in checklist["pautas"]) if checklist["pautas"] else "-"
        )
        self.checklist_labels["sem_imagem"].configure(text=str(len(checklist["sem_imagem"])))
        self.checklist_labels["sem_observacao"].configure(text=str(len(checklist["sem_observacao"])))
        self.checklist_labels["sem_horario"].configure(text=str(len(checklist["sem_horario"])))
        self.checklist_labels["sem_participantes"].configure(
            text=str(len(checklist["sem_participantes"]))
        )

        self.checklist_listbox.delete(0, "end")
        issues = checklist["issues"] or ["Nenhuma pendência crítica encontrada."]
        for issue in issues:
            self.checklist_listbox.insert("end", issue)

        detail_groups = [
            ("Por turma", checklist["por_turma"]),
            ("Por pauta", checklist["por_pauta"]),
            ("Por situação", checklist["por_status"]),
        ]
        for title, values in detail_groups:
            self.checklist_listbox.insert("end", "")
            self.checklist_listbox.insert("end", title)
            for key, value in values.items():
                self.checklist_listbox.insert("end", f"  {key}: {value}")

        missing_groups = [
            ("Encontros sem imagem", checklist["sem_imagem"]),
            ("Encontros sem observação", checklist["sem_observacao"]),
            ("Encontros sem horário", checklist["sem_horario"]),
            ("Encontros sem participantes", checklist["sem_participantes"]),
        ]
        for title, items in missing_groups:
            if not items:
                continue
            self.checklist_listbox.insert("end", "")
            self.checklist_listbox.insert("end", title)
            for item in items:
                self.checklist_listbox.insert("end", f"  {item}")

    def _generate_bundle(self) -> dict[str, object] | None:
        if not self.current_month_id:
            messagebox.showwarning("Mês não selecionado", "Crie ou selecione um mês primeiro.")
            return None

        if not self._normalize_currency_field():
            return None
        self.database.save_month(self.current_month_id, self.collect_professor_data())
        return self.database.get_month_bundle(self.current_month_id)

    def _set_report_generation_state(self, in_progress: bool, message: str = "") -> None:
        self.report_generation_in_progress = in_progress
        button_state = "disabled" if in_progress else "normal"
        self.generate_docx_button.configure(state=button_state)
        self.generate_pdf_button.configure(state=button_state)
        self.generate_financial_button.configure(state=button_state)
        self.refresh_checklist_button.configure(state=button_state)
        self.open_evidence_button.configure(state=button_state)
        self.open_output_button.configure(state=button_state)

        if in_progress:
            self.report_progress_var.set(message)
            self.report_progress.pack(anchor="w", pady=(10, 0))
            self.report_progress.start(12)
        else:
            self.report_progress.stop()
            self.report_progress.pack_forget()
            self.report_progress_var.set(message)

    def _start_report_generation(self, report_type: str) -> None:
        if self.report_generation_in_progress:
            messagebox.showinfo(
                "Processando relatório",
                "Já existe uma geração de relatório em andamento. Aguarde a conclusão.",
            )
            return

        bundle = self._generate_bundle()
        if not bundle:
            return

        progress_messages = {
            "docx": "Gerando relatório DOCX...",
            "pdf": "Gerando relatório PDF...",
            "financial": "Gerando extrato financeiro...",
        }
        progress_message = progress_messages.get(report_type, "Processando arquivo...")
        self._set_report_generation_state(True, progress_message)
        self.status_bar_var.set(progress_message)

        worker = threading.Thread(
            target=self._run_report_generation_task,
            args=(report_type, bundle),
            daemon=True,
        )
        worker.start()

    def _run_report_generation_task(self, report_type: str, bundle: dict[str, object]) -> None:
        try:
            if report_type == "financial":
                output_path = generate_financial_statement_docx(
                    month_data=bundle["month"],
                    encontros=bundle["encontros"],
                    output_dir=SAIDAS_DIR,
                )
            else:
                docx_path = generate_docx(
                    month_data=bundle["month"],
                    encontros=bundle["encontros"],
                    turmas=bundle["turmas"],
                    total_realizados=bundle["checklist"]["total_realizados"],
                    output_dir=SAIDAS_DIR,
                )
                output_path = docx_path
            if report_type == "pdf":
                output_path = export_pdf(docx_path)
        except Exception as error:
            self.after(0, lambda err=error, kind=report_type: self._finish_report_generation_error(kind, err))
            return

        self.after(0, lambda path=output_path, kind=report_type: self._finish_report_generation_success(kind, path))

    def _finish_report_generation_success(self, report_type: str, output_path: Path) -> None:
        self._set_report_generation_state(False, "")
        if report_type == "pdf":
            self.status_bar_var.set(f"Relatório PDF gerado em {output_path.name}.")
            messagebox.showinfo(
                "PDF pronto",
                "Relatório gerado com sucesso.\n\n"
                f"Arquivo:\n{output_path}\n\n"
                "Você pode encontrá-lo na pasta 'saídas' do programa.\n"
                "Se preferir, clique no botão 'Abrir saídas' para acessar a pasta.",
            )
        elif report_type == "financial":
            self.status_bar_var.set(f"Extrato financeiro gerado em {output_path.name}.")
            messagebox.showinfo(
                "Extrato financeiro pronto",
                "Extrato gerado com sucesso.\n\n"
                f"Arquivo:\n{output_path}\n\n"
                "Você pode encontrá-lo na pasta 'saídas' do programa.\n"
                "Se preferir, clique no botão 'Abrir saídas' para acessar a pasta.",
            )
        else:
            self.status_bar_var.set(f"Relatório DOCX gerado em {output_path.name}.")
            messagebox.showinfo(
                "Relatório pronto",
                "Relatório gerado com sucesso.\n\n"
                f"Arquivo:\n{output_path}\n\n"
                "Você pode encontrá-lo na pasta 'saídas' do programa.\n"
                "Se preferir, clique no botão 'Abrir saídas' para acessar a pasta.",
            )

    def _finish_report_generation_error(self, report_type: str, error: Exception) -> None:
        self._set_report_generation_state(False, "")
        if report_type == "pdf":
            messagebox.showerror(
                "PDF indisponível",
                "Não foi possível exportar para PDF.\n\n"
                f"Detalhe: {error}\n\n"
                "Instale o LibreOffice ou use o Microsoft Word com pywin32.",
            )
            self.status_bar_var.set("Falha ao gerar relatório PDF.")
        elif report_type == "financial":
            messagebox.showerror("Falha ao gerar extrato", str(error))
            self.status_bar_var.set("Falha ao gerar extrato financeiro.")
        else:
            messagebox.showerror("Falha ao gerar DOCX", str(error))
            self.status_bar_var.set("Falha ao gerar relatório DOCX.")

    def generate_docx_report(self) -> None:
        self._start_report_generation("docx")

    def generate_pdf_report(self) -> None:
        self._start_report_generation("pdf")

    def generate_financial_report(self) -> None:
        self._start_report_generation("financial")

    def show_about_dialog(self) -> None:
        dialog = tk.Toplevel(self)
        dialog.title("Sobre o projeto")
        dialog.geometry("760x560")
        dialog.minsize(640, 440)
        dialog.resizable(False, False)
        dialog.transient(self)

        container = ttk.Frame(dialog, padding=16)
        container.pack(fill="both", expand=True)

        ttk.Label(
            container,
            text="Multiplica Evidências",
            font=("Segoe UI", 16, "bold"),
        ).pack(anchor="w")
        ttk.Label(
            container,
            text=f"Versão {APP_VERSION}",
            font=("Segoe UI", 10, "bold"),
        ).pack(anchor="w", pady=(2, 2))
        ttk.Label(
            container,
            text="Júlio César Valera • Professor de Matemática, Programação e Robótica",
            font=("Segoe UI", 10, "italic"),
        ).pack(anchor="w", pady=(4, 14))
        ttk.Label(
            container,
            text=(
                "Contato: julio@projetos.tec.br • "
                "juliovalera@professor.educacao.sp.gov.br"
            ),
            font=("Segoe UI", 9),
        ).pack(anchor="w", pady=(0, 10))
        ttk.Label(
            container,
            text=self._get_terms_acceptance_summary(),
            font=("Segoe UI", 9),
        ).pack(anchor="w", pady=(0, 10))
        tk.Label(
            container,
            text=(
                "AVISO IMPORTANTE: PROJETO INDEPENDENTE E NÃO OFICIAL.\n"
                "Uso descritivo do nome Programa Multiplica, sem homologação\n"
                "ou vínculo institucional automático."
            ),
            font=("Segoe UI", 10, "bold"),
            fg="#8b1e1e",
            bg=container.cget("background"),
            justify="left",
        ).pack(anchor="w", pady=(0, 10))

        text_frame = ttk.Frame(container)
        text_frame.pack(fill="both", expand=True)

        scrollbar = ttk.Scrollbar(text_frame, orient="vertical")
        scrollbar.pack(side="right", fill="y")

        text_widget = tk.Text(
            text_frame,
            wrap="word",
            font=("Segoe UI", 10),
            padx=12,
            pady=12,
            yscrollcommand=scrollbar.set,
            relief="solid",
            borderwidth=1,
            background="#fcfcfd",
        )
        text_widget.pack(fill="both", expand=True)
        scrollbar.config(command=text_widget.yview)

        text_widget.insert("1.0", self._get_about_text())
        text_widget.config(state="disabled")

        button_row = ttk.Frame(container)
        button_row.pack(fill="x", pady=(12, 0))
        ttk.Button(
            button_row,
            text="Copiar e-mails",
            command=self.copy_about_contacts,
        ).pack(side="left")
        ttk.Button(
            button_row,
            text="Ler termos novamente",
            command=self.open_terms_review_dialog,
        ).pack(side="left", padx=(10, 0))
        ttk.Button(button_row, text="Fechar", command=dialog.destroy).pack(side="right")

        dialog.bind("<Escape>", lambda _event: dialog.destroy())
        dialog.focus_set()

    def copy_about_contacts(self) -> None:
        contacts = "julio@projetos.tec.br; juliovalera@professor.educacao.sp.gov.br"
        self.clipboard_clear()
        self.clipboard_append(contacts)
        self.update_idletasks()
        messagebox.showinfo(
            "Contatos copiados",
            "Os e-mails de contato foram copiados para a área de transferência.",
        )

    def ensure_terms_acceptance(self) -> None:
        accepted_version = self.database.get_app_config_value(self.TERMS_CONFIG_KEY)
        if accepted_version == self.TERMS_VERSION:
            return
        self.show_terms_dialog(require_acceptance=True)

    def open_terms_review_dialog(self) -> None:
        self.show_terms_dialog(require_acceptance=False)

    def show_terms_dialog(self, require_acceptance: bool = True) -> None:
        dialog = tk.Toplevel(self)
        dialog.title("Termos de uso")
        dialog.geometry("820x620")
        dialog.minsize(720, 520)
        dialog.transient(self)
        if require_acceptance:
            dialog.grab_set()

        container = ttk.Frame(dialog, padding=16)
        container.pack(fill="both", expand=True)

        ttk.Label(
            container,
            text="Termos de uso e aviso importante",
            font=("Segoe UI", 15, "bold"),
        ).pack(anchor="w")
        ttk.Label(
            container,
            text="Leia com atenção antes de utilizar o sistema.",
            font=("Segoe UI", 10),
        ).pack(anchor="w", pady=(6, 12))
        tk.Label(
            container,
            text=(
                "AVISO IMPORTANTE: ESTE SOFTWARE É INDEPENDENTE E NÃO OFICIAL.\n"
                "A referência ao Programa Multiplica tem caráter apenas descritivo."
            ),
            font=("Segoe UI", 10, "bold"),
            fg="#8b1e1e",
            bg=container.cget("background"),
            justify="left",
        ).pack(anchor="w", pady=(0, 12))

        text_frame = ttk.Frame(container)
        text_frame.pack(fill="both", expand=True)

        text_scroll = ttk.Scrollbar(text_frame, orient="vertical")
        text_scroll.pack(side="right", fill="y")

        text_widget = tk.Text(
            text_frame,
            wrap="word",
            font=("Segoe UI", 10),
            padx=12,
            pady=12,
            yscrollcommand=text_scroll.set,
            relief="solid",
            borderwidth=1,
            background="#fcfcfd",
        )
        text_widget.pack(fill="both", expand=True)
        text_scroll.config(command=text_widget.yview)
        text_widget.insert("1.0", self._get_terms_text())
        text_widget.config(state="disabled")

        button_row = ttk.Frame(container)
        button_row.pack(fill="x", pady=(14, 0))

        if require_acceptance:
            self.terms_accept_var = tk.BooleanVar(value=False)
            ttk.Checkbutton(
                container,
                text=(
                    "Li e compreendi os termos de uso. Reconheço que devo conferir os dados "
                    "antes de qualquer uso oficial."
                ),
                variable=self.terms_accept_var,
                command=self._update_terms_accept_button_state,
            ).pack(anchor="w", pady=(12, 0))

            ttk.Label(
                container,
                text=(
                    "Sem esse aceite o programa será fechado. O aceite fica salvo apenas neste computador."
                ),
                justify="left",
            ).pack(anchor="w", pady=(8, 0))

            ttk.Button(button_row, text="Sair", command=lambda: self._decline_terms(dialog)).pack(
                side="left"
            )
            self.accept_terms_button = ttk.Button(
                button_row,
                text="Aceito os termos",
                command=lambda: self._accept_terms(dialog),
                state="disabled",
            )
            self.accept_terms_button.pack(side="right")
            dialog.protocol("WM_DELETE_WINDOW", lambda: self._decline_terms(dialog))
            dialog.bind("<Escape>", lambda _event: self._decline_terms(dialog))
        else:
            ttk.Label(
                button_row,
                text=self._get_terms_acceptance_summary(),
                justify="left",
            ).pack(side="left")
            ttk.Button(button_row, text="Fechar", command=dialog.destroy).pack(side="right")
            dialog.protocol("WM_DELETE_WINDOW", dialog.destroy)
            dialog.bind("<Escape>", lambda _event: dialog.destroy())

        dialog.focus_force()

    def _update_terms_accept_button_state(self) -> None:
        if hasattr(self, "accept_terms_button"):
            state = "normal" if self.terms_accept_var.get() else "disabled"
            self.accept_terms_button.configure(state=state)

    def _accept_terms(self, dialog: tk.Toplevel) -> None:
        accepted_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.database.set_app_config_value(self.TERMS_CONFIG_KEY, self.TERMS_VERSION)
        self.database.set_app_config_value(self.TERMS_ACCEPTED_AT_KEY, accepted_at)
        self.status_bar_var.set("Termos de uso aceitos neste computador.")
        dialog.destroy()

    def _decline_terms(self, dialog: tk.Toplevel) -> None:
        dialog.destroy()
        self.after(50, self.destroy)

    def _get_terms_acceptance_summary(self) -> str:
        accepted_at = self.database.get_app_config_value(self.TERMS_ACCEPTED_AT_KEY)
        if not accepted_at:
            return "Aceite dos termos: ainda não registrado neste computador."
        try:
            accepted_dt = datetime.strptime(accepted_at, "%Y-%m-%d %H:%M:%S")
            accepted_label = accepted_dt.strftime("%d/%m/%Y às %H:%M")
        except ValueError:
            accepted_label = accepted_at
        return f"Aceite dos termos registrado neste computador em: {accepted_label}"

    def _get_terms_text(self) -> str:
        return (
            "Este projeto tem finalidade pedagógica, organizacional e de apoio técnico, tendo sido "
            "desenvolvido para auxiliar o registro local de encontros, evidências e relatórios no "
            "contexto de atuação do professor multiplicador.\n\n"
            "A menção ao Programa Multiplica neste software tem caráter exclusivamente descritivo, "
            "sem representar oficialidade, homologação, licenciamento de marca ou vínculo "
            "institucional automático.\n\n"
            "O sistema não substitui a conferência humana nem a validação institucional das informações, "
            "documentos, datas, imagens, horários, participantes e relatórios gerados. Antes de qualquer "
            "envio, protocolo ou uso oficial, o usuário deve revisar cuidadosamente todo o conteúdo.\n\n"
            "Os dados permanecem armazenados localmente neste computador, incluindo banco SQLite, imagens "
            "e arquivos gerados, sem envio automático para serviços externos pelo sistema.\n\n"
            "Por se tratar de um projeto em desenvolvimento contínuo, o autor não garante adequação integral "
            "a normas, rotinas, exigências administrativas específicas ou funcionamento livre de falhas em "
            "todos os ambientes de uso. O sistema deve ser utilizado com prudência, bom senso e conferência "
            "final, especialmente em contextos institucionais.\n\n"
            "O aceite destes termos registra ciência e concordância com essas condições de uso. Em situações "
            "específicas, recomenda-se também observar as normas institucionais aplicáveis e, quando necessário, "
            "a orientação jurídica pertinente.\n\n"
            "Sugestões, críticas construtivas e contribuições são bem-vindas.\n\n"
            "Contato para diálogo e colaboração:\n"
            "• julio@projetos.tec.br\n"
            "• juliovalera@professor.educacao.sp.gov.br"
        )

    def _get_about_text(self) -> str:
        return (
            "Este projeto foi concebido com finalidade pedagógica, organizacional e de apoio técnico, "
            "buscando auxiliar o registro local de encontros, evidências e relatórios no contexto do "
            "trabalho do professor multiplicador. "
            "A referência ao Programa Multiplica é utilizada apenas para indicar esse contexto de uso, "
            "sem afirmar caráter oficial do software.\n\n"
            "Sua motivação nasce de uma necessidade concreta da rotina docente: organizar informações com mais "
            "clareza, menos retrabalho e maior autonomia no uso dos próprios dados.\n\n"
            "Ao reunir essas informações em um único ambiente local, o sistema procura valorizar o tempo "
            "pedagógico do professor multiplicador. Em vez de dispersar registros em pastas, anotações e "
            "documentos manuais, a proposta é oferecer um fluxo mais consistente, preservando a memória do "
            "trabalho realizado e facilitando a conferência mensal das evidências.\n\n"
            "A linguagem Python foi escolhida por reunir legibilidade, estabilidade, facilidade de manutenção "
            "e ótima integração com documentos, imagens e banco de dados local. Além disso, Python ocupa hoje "
            "um papel relevante na educação tecnológica, no ensino de programação e no desenvolvimento de "
            "materiais digitais conectados a problemas reais do cotidiano.\n\n"
            "Vivemos uma realidade em que materiais digitais, registros eletrônicos e produção documental fazem "
            "parte da vida escolar e profissional. Saber organizar dados com responsabilidade, preservar "
            "evidências e transformar informações em relatórios úteis é uma competência cada vez mais relevante. "
            "Este projeto se insere justamente nesse contexto: usar a tecnologia como instrumento de organização, "
            "autoria e apoio ao trabalho humano.\n\n"
            "Multiplica Evidências permanece em desenvolvimento contínuo. Por isso, o sistema não substitui a "
            "conferência humana nem a validação institucional das informações, documentos e relatórios gerados. "
            "Antes de qualquer envio, protocolo ou uso oficial, recomenda-se revisão cuidadosa de todo o conteúdo.\n\n"
            "Por se tratar de um projeto em evolução, não há garantia de adequação integral a todas as rotinas, "
            "normas ou exigências administrativas específicas, nem de funcionamento livre de falhas em todos os "
            "ambientes. O uso deve ocorrer com prudência, bom senso e conferência final, especialmente em contextos "
            "institucionais.\n\n"
            "Sugestões, críticas construtivas, observações de melhoria e contribuições de uso são bem-vindas. "
            "Este projeto também se fortalece pelo diálogo com outros educadores e usuários interessados em "
            "aperfeiçoar ferramentas digitais voltadas à organização pedagógica.\n\n"
            "Contato para diálogo e colaboração:\n"
            "• julio@projetos.tec.br\n"
            "• juliovalera@professor.educacao.sp.gov.br"
        )

    def open_output_folder(self) -> None:
        self._open_path(SAIDAS_DIR)

    def open_evidence_folder(self) -> None:
        self._open_path(EVIDENCIAS_DIR)

    def backup_database(self) -> None:
        backup_path = self.database.backup_database(BACKUP_DIR)
        self.status_bar_var.set(f"Backup criado: {backup_path.name}")
        messagebox.showinfo("Backup concluído", f"Arquivo salvo em:\n{backup_path}")

    def _open_path(self, path: Path) -> None:
        try:
            if os.name == "nt":
                os.startfile(path)  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                subprocess.run(["open", str(path)], check=False)
            else:
                subprocess.run(["xdg-open", str(path)], check=False)
        except Exception as error:
            messagebox.showerror("Abrir arquivo", f"Não foi possível abrir:\n{path}\n\n{error}")

from dataclasses import dataclass, field
from typing import List, Optional


STATUS_OPTIONS = [
    "realizado",
    "sem cursistas",
    "cancelado",
    "remarcado",
    "outro",
]

TURMA_STATUS_OPTIONS = ["ativa", "inativa"]

BUSCA_ATIVA_STATUS_OPTIONS = [
    "nao_iniciado",
    "em_contato",
    "aguardando_retorno",
    "localizado",
    "encerrado",
]

ACOMPANHAMENTO_CATEGORIAS = [
    "curso_errado",
    "turma_errada",
    "consta_em_outra_turma",
    "nao_aparece_na_lista",
    "acesso",
    "teams",
    "inscricao",
    "busca_ativa",
    "duvida_pedagogica",
    "outro",
]

ACOMPANHAMENTO_STATUS_OPTIONS = [
    "aberto",
    "em_acompanhamento",
    "aguardando_retorno",
    "encaminhado_pec",
    "resolvido",
    "arquivado",
]

PRIORIDADE_OPTIONS = ["baixa", "normal", "alta"]

SOCIALIZACAO_STATUS_OPTIONS = [
    "nao_enviada",
    "enviada",
    "em_analise",
    "devolutiva_registrada",
    "destaque",
]

WEEKDAY_OPTIONS = [
    "",
    "SEG",
    "TER",
    "QUA",
    "QUI",
    "SEX",
    "SAB",
    "DOM",
]

MONTH_NAMES_PT = {
    1: "janeiro",
    2: "fevereiro",
    3: "março",
    4: "abril",
    5: "maio",
    6: "junho",
    7: "julho",
    8: "agosto",
    9: "setembro",
    10: "outubro",
    11: "novembro",
    12: "dezembro",
}

AUTO_OBSERVATIONS = {
    "Encontro realizado": (
        "Encontro realizado normalmente, com participação registrada no ambiente Teams."
    ),
    "Sem cursistas": (
        "Não houve cursistas presentes nesta turma, embora o professor tenha permanecido "
        "disponível durante todo o horário do encontro."
    ),
    "Evidência complementar": (
        "Evidência referente à participação, chat, gravação ou recapitulação do encontro."
    ),
}


@dataclass
class ProfessorDefaults:
    nome: str = ""
    tema: str = ""
    email_institucional: str = ""
    diretoria_ure: str = ""
    pec_responsavel: str = ""


@dataclass
class MonthRecord:
    ref_month: int
    ref_year: int
    nome: str = ""
    tema: str = ""
    email_institucional: str = ""
    diretoria_ure: str = ""
    pec_responsavel: str = ""
    id: Optional[int] = None


@dataclass
class TurmaRecord:
    codigo: str
    dia_semana: str = ""
    horario: str = ""
    componente: str = ""
    situacao: str = "ativa"
    id: Optional[int] = None


@dataclass
class EvidenceRecord:
    arquivo_copiado: str
    arquivo_original: str = ""
    id: Optional[int] = None


@dataclass
class EncontroRecord:
    month_id: int
    turma_id: int
    data_encontro: str
    pauta_numero: int
    hora_inicio: str = ""
    hora_fim: str = ""
    participantes: Optional[int] = None
    duracao: str = ""
    observacao: str = ""
    situacao: str = "realizado"
    id: Optional[int] = None
    evidencias: List[EvidenceRecord] = field(default_factory=list)

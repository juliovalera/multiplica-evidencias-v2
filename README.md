<div align="center">

# Multiplica Evidências

Aplicação desktop em Python para registrar encontros do Programa Multiplica, armazenar evidências localmente e gerar documentos mensais de apoio pedagógico e administrativo.

**Versão atual:** `1,023` • **Primeira publicação pública:** `1.000` • **Licença:** `MIT`

</div>

---

## Visão geral

O projeto foi criado para reduzir retrabalho no registro mensal de encontros do professor multiplicador. A aplicação centraliza professor, turmas, encontros, evidências, checklist e geração de arquivos em um fluxo local, simples e sem dependência de internet.

## Principais recursos

- Cadastro local do professor multiplicador.
- Reaproveitamento de dados padrão entre meses.
- Cadastro de turmas com código, dia da semana, horário, componente e situação.
- Registro de encontros com pauta, data, turma, participantes, observação e situação.
- Preenchimento automático de início, término e duração com base no horário da turma.
- Colagem direta de prints da área de transferência.
- Anexação de imagens salvas no computador.
- Organização das evidências por mês, turma e pauta.
- Pré-visualização da evidência dentro da interface.
- Checklist mensal com alertas de pendências.
- Relatório de evidências em `DOCX`.
- Exportação opcional para `PDF`.
- Extrato financeiro mensal em documento separado.
- Backup local do banco de dados.

---

## Estrutura do projeto

```text
multiplica_evidencias/
├─ main.py
├─ config.py
├─ database.py
├─ models.py
├─ relatorio.py
├─ interface/
│  └─ app.py
├─ modelos/
├─ data/
├─ evidencias/
├─ saidas/
├─ requirements.txt
└─ README.md
```

### Arquivos principais

- `main.py` — ponto de entrada da aplicação.
- `config.py` — nome do app, versão, caminhos e utilitários.
- `database.py` — banco SQLite, persistência, checklist e agregações.
- `models.py` — listas padrão e textos automáticos.
- `relatorio.py` — geração do relatório de evidências, extrato financeiro e exportação PDF.
- `interface/app.py` — interface Tkinter.

---

## Requisitos

- Python `3.11` ou superior
- Windows recomendado para colagem de imagens e integração com Word/LibreOffice
- `Pillow` para imagens
- `python-docx` para gerar `DOCX`
- `LibreOffice` **ou** `Microsoft Word + pywin32` para exportação em `PDF`

---

## Instalação

### 1. Criar ambiente virtual

```powershell
python -m venv .venv
```

### 2. Ativar ambiente virtual

```powershell
.venv\Scripts\Activate.ps1
```

### 3. Instalar dependências

```powershell
pip install -r requirements.txt
```

---

## Como executar

```powershell
python main.py
```

---

## Fluxo de uso recomendado

1. Abrir a aplicação.
2. Aceitar os termos de uso no primeiro acesso.
3. Preencher os dados na aba `Professor Multiplicador`.
4. Cadastrar as turmas na aba `Turmas`.
5. Registrar os encontros na aba `Encontros`.
6. Colar ou anexar as evidências.
7. Revisar a aba `Checklist e relatório`.
8. Gerar o relatório de evidências em `DOCX` ou `PDF`.
9. Gerar o extrato financeiro quando necessário.

---

## Relatórios gerados

### Relatório de evidências

Inclui:

- identificação do professor;
- tema;
- lista de turmas do mês;
- encontros organizados por pauta e data;
- observações do encontro;
- imagens das evidências;
- tabela-resumo final com data, turma e pauta;
- total de encontros realizados no mês.

### Extrato financeiro

Inclui:

- identificação do professor;
- valor por formação semanal;
- encontros considerados para pagamento;
- valor total mensal estimado;
- tabela de lançamentos do mês.

---

## Modelo DOCX

- Se desejar manter uma referência visual própria, coloque o arquivo em `modelos/evidencias.docx`.
- O sistema gera os documentos com `python-docx`.
- O modelo visual não é versionado no repositório público para evitar exposição de documentos pessoais.

---

## Privacidade e uso local

- Todos os dados permanecem no computador local.
- Não há envio automático para internet.
- Não há uso de API externa.
- Não há upload automático de imagens, banco ou relatórios.

---

## Versionamento

O projeto adota um versionamento incremental a partir da publicação pública inicial no GitHub.

- `1.000` → publicação pública inicial
- `1,023` → versão atual, consolidando **23 implementações e correções** desde a primeira publicação

> Convenção adotada neste projeto: a parte fracionária representa o acumulado de implementações/correções relevantes publicadas após a base `1.000`.

---

## Histórico de versões

### Versão 1.023 — pacote acumulado de 23 implementações e correções

1. Criação automática do mês a partir da data do encontro.
2. Reaproveitamento de dados padrão do professor multiplicador.
3. Cadastro do valor por formação semanal em reais.
4. Cálculo do valor total mensal estimado no checklist.
5. Preenchimento automático do horário do encontro com base na turma.
6. Cálculo automático de término e duração padrão de `1h30`.
7. Calendário para escolha de datas.
8. Destaque visual dos dias da semana da turma no calendário.
9. Destaque de feriados nacionais no calendário.
10. Colagem direta de prints da área de transferência.
11. Anexação de imagens salvas no computador.
12. Organização das evidências em pastas por mês, turma e pauta.
13. Pré-visualização de evidências dentro da aba `Encontros`.
14. Ajuste automático das colunas das listagens.
15. Checklist mensal com pendências e totais por turma, pauta e situação.
16. Numeração de páginas nos documentos gerados.
17. Barra de progresso durante a geração de relatórios.
18. Botão para abrir a pasta das evidências.
19. Separação entre relatório de evidências e extrato financeiro.
20. Geração do extrato financeiro em documento próprio.
21. Nomes de arquivos com iniciais do professor e carimbo de data/hora.
22. Termos de uso no primeiro acesso e tela `Sobre o projeto` com créditos e contatos.
23. Compactação do layout para melhor uso em telas menores.

### Versão 1.000 — publicação pública inicial

- Estrutura base do projeto em Python.
- Interface desktop com Tkinter.
- Banco local SQLite.
- Cadastro de professor, turmas e encontros.
- Geração inicial de relatório em `DOCX`.
- Exportação opcional em `PDF`.
- Armazenamento local de evidências.

---

## Observações importantes

- O projeto está em desenvolvimento contínuo.
- O usuário deve revisar cuidadosamente os dados antes de qualquer uso oficial.
- O sistema apoia a organização e a geração documental, mas não substitui conferência humana nem validação institucional.

---

## Créditos

**Júlio César Valera**  
Professor de Matemática, Programação e Robótica

**Contato**

- `julio@projetos.tec.br`
- `juliovalera@professor.educacao.sp.gov.br`

Sugestões, críticas construtivas e observações de melhoria são bem-vindas.

---

## Licença

Este projeto está licenciado sob a licença `MIT`.

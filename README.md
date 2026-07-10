<div align="center">

<h1>📘 Multiplica Evidências</h1>

<p><strong>Linha 2 — edição avançada</strong></p>

<p><em>Repositório da evolução funcional do projeto, separado da linha estável 1.x.</em></p>

<p><strong>Versão estável 1.x:</strong> <a href="https://github.com/juliovalera/multiplica-evidencias">github.com/juliovalera/multiplica-evidencias</a></p>

<p>
  Aplicação desktop em Python para apoiar o registro local de encontros pedagógicos,
  evidências e documentos mensais, inclusive em contextos como o <strong>Programa Multiplica</strong>.
</p>

<p>
  <img alt="Python" src="https://img.shields.io/badge/Python-3.11%2B-3776AB?style=for-the-badge&logo=python&logoColor=white">
  <img alt="Tkinter" src="https://img.shields.io/badge/Interface-Tkinter-1F6FEB?style=for-the-badge">
  <img alt="SQLite" src="https://img.shields.io/badge/Banco-SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white">
  <img alt="DOCX/PDF" src="https://img.shields.io/badge/Relat%C3%B3rios-DOCX%20%2F%20PDF-8A2BE2?style=for-the-badge">
  <img alt="Licença MIT" src="https://img.shields.io/badge/Licen%C3%A7a-MIT-E0A800?style=for-the-badge">
  <img alt="Versão 2,015" src="https://img.shields.io/badge/Vers%C3%A3o-2.015-7B1FA2?style=for-the-badge">
</p>

<p>
  <strong>Versão atual:</strong> <code>2,015</code> &nbsp;•&nbsp;
  <strong>Primeira publicação pública:</strong> <code>1.000</code>
</p>

<p><em>Ferramenta experimental e independente de apoio a encontros pedagógicos, com foco em organização, evidências e documentação mensal.</em></p>

> **AVISO IMPORTANTE:** **este projeto é INDEPENDENTE e NÃO OFICIAL.**  
> **Não representa sistema oficial, homologação institucional, licenciamento de marca ou vínculo institucional automático.**  
> **Pode ser utilizado experimentalmente em encontros pedagógicos diversos, inclusive em contextos como o Programa Multiplica.**  
> **Qualquer menção ao Programa Multiplica é apenas exemplificativa e descritiva.**

</div>

---

## Visão geral

O projeto foi criado para reduzir retrabalho no registro mensal de encontros pedagógicos. A aplicação centraliza professor responsável, turmas, encontros, evidências, checklist e geração de arquivos em um fluxo local, simples e sem dependência de internet.

> **Importante:** este projeto é uma ferramenta **experimental, independente e não oficial**, desenvolvida para apoio a **encontros pedagógicos**. Pode ser utilizada em diferentes contextos, **como por exemplo o Programa Multiplica**, sem qualquer afirmação de oficialidade, homologação ou vínculo institucional automático.

## Documentação do usuário

- Guia rápido: `docs/guia_rapido.md`
- Manual completo: `docs/manual_usuario.md`
- Texto resumido para ajuda interna: `docs/ajuda_resumida.md`
- Manual em versão editorial: `docs/manual_usuario_editorial.md`

Na interface, a documentação também pode ser acessada pelo botão `Ajuda`.

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
- Módulo `Acompanhamento de Cursistas` com cadastro, ocorrências e socializações.
- Controle de busca ativa com contatos, turma, situação e observação geral do cursista.
- Registro de ocorrências como curso errado, turma errada, acesso, Teams, inscrição, busca ativa e dúvida pedagógica.
- Registro mensal de socializações com status de envio, apoio pedagógico e potencial destaque.
- Histórico de movimentações e anexos em ocorrências e socializações.
- Importação de cursistas por planilha Excel com prévia, validação e conciliação por turma.
- Aviso de divergência do valor da formação semanal para preservar relatórios antigos.
- Ajustes de usabilidade para telas menores, com filtros mais claros, rótulos legíveis e painéis com rolagem.

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
- `1,027` → última versão estável da linha pública inicial
- `2,000` → início da linha 2 em repositório público separado, com evolução funcional mais avançada
- `2,015` → pacote acumulado de ajustes publicados após o lançamento da linha 2

> Convenção adotada neste projeto: a parte fracionária representa o acumulado de implementações/correções relevantes publicadas após a base principal. A linha `2.x` inaugura um novo repositório de evolução separada.

---

## Histórico de versões

### Versão 2.015 — pacote acumulado de 15 evoluções da linha 2

1. Atualização editorial do `README` da linha avançada `2.x`.
2. Destaque visual da linha avançada e link para a linha estável `1.x`.
3. Criação dos manuais em `docs/`, com `guia rápido`, `manual completo` e `manual editorial`.
4. Inclusão de ajuda integrada no sistema com botão dedicado e atalhos na aba `Início`.
5. Identificação visual na tela inicial entre linha estável `1.x` e linha avançada `2.x`.
6. Correção de acentuação em textos do `README` e da ajuda interna.
7. Substituição de valores técnicos por rótulos amigáveis nos dropdowns de `Ocorrências`.
8. Ajuste visual da grade de cursistas com destaque para `sim/não` e melhor distribuição automática das colunas.
9. Normalização de `Participantes` para `0` em encontros sem cursistas ou deixados em branco, com preenchimento automático na interface.
10. Aviso de divergência entre `mês de referência` e `data de envio` no salvamento de socializações.
11. Ajuste do rótulo `Resolução` para `Data de resolução` na aba de ocorrências.
12. Equalização dos painéis esquerdo e direito na aba `Ocorrências`, dividindo a largura disponível em proporções iguais.
13. Fixação efetiva do divisor 50/50 na aba `Ocorrências`, posicionando o `Panedwindow` no centro da área útil.
14. Inclusão de comentários e docstrings pedagógicas nos arquivos principais, sem alterar a lógica da aplicação.
15. Ajuste de higiene do repositório com refinamento de exclusões locais no `.gitignore`.

### Versão 2.000 — início da linha 2

1. Nova linha de versionamento, separada da linha pública estável `1.x`.
2. Repositório público próprio para a evolução funcional mais avançada.
3. Criação do módulo `Acompanhamento de Cursistas` com abas de `Cursistas`, `Ocorrências` e `Socializações`.
4. Cadastro de cursistas com turma, e-mail institucional, e-mail pessoal, telefone/WhatsApp, busca ativa, ativo e observação geral.
5. Dashboard do acompanhamento com totais de cursistas ativos, busca ativa pendente, ocorrências abertas, socializações não enviadas e potenciais destaques.
6. Registro de ocorrências por cursista com categoria, status, prioridade, resumo, descrição, data de abertura, data de resolução e encaminhamento ao PEC.
7. Registro mensal de socializações por cursista com status de envio, data, necessidade de apoio e potencial destaque.
8. Criação de histórico de movimentações para ocorrências e socializações.
9. Criação de anexos para ocorrências e socializações, com armazenamento local organizado.
10. Novas pastas locais de trabalho para acompanhamentos e socializações.
11. Filtros por turma, status, categoria, anexos, movimentações e busca textual nas abas do módulo.
12. Rótulos mais amigáveis nos combos e nas listagens, substituindo valores internos com underline na interface.
13. Ajuste de cores e destaques visuais nas linhas de ocorrências e socializações.
14. Correção da apresentação dos status de busca ativa e de envio de socialização em filtros, combos e listas.
15. Aviso de divergência do valor da formação semanal ao salvar mês ou encontro em mês já existente.
16. Preservação do valor financeiro histórico por mês, evitando que reajustes futuros alterem relatórios antigos.
17. Importação de cursistas por planilha `Excel` com leitura via `openpyxl`.
18. Limpeza automática do nome importado, ignorando observações após hífen na coluna de nome.
19. Interpretação do código da turma a partir do texto da planilha PEC, conciliando com `turmas.codigo`.
20. Prévia da importação com classificação em `novo`, `atualizar`, `conflito` e `ignorado`.
21. Importação definitiva apenas das linhas processáveis, com confirmação explícita antes da gravação.
22. Filtro do dropdown de cursistas por turma nas telas de ocorrências e socializações.
23. Reorganização dos botões e redução de campos altos para melhor uso em resoluções menores.
24. Resumo do acompanhamento reorganizado em linha horizontal para economizar altura.
25. Redução da altura da listagem de socializações para liberar espaço ao formulário lateral.
26. Inclusão de painéis com rolagem própria nas áreas de `Ocorrências` e `Socializações`.
27. Suporte à roda do mouse e a `Shift + roda do mouse` nas áreas roláveis do módulo.

### Versão 1.027 — pacote acumulado de 27 implementações e correções

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
24. Reforço da comunicação de projeto independente e não oficial.
25. Correção do erro de `background` em componentes `ttk`.
26. Adoção da redação de uso experimental em avisos, README e documentos.
27. Polimento visual dos botões e inclusão de ícone no botão de calendário.

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

### O que isso significa na prática?

A licença `MIT` é uma licença aberta e bastante permissiva. Em termos simples, isso significa que outras pessoas podem:

- usar este projeto livremente;
- estudar como ele foi feito;
- copiar e adaptar o código;
- publicar versões modificadas;
- utilizar o projeto em contexto pessoal, educacional ou até comercial.

Em contrapartida, a licença também estabelece alguns pontos importantes:

- o aviso de copyright e a própria licença devem acompanhar cópias relevantes do projeto;
- o software é fornecido **“como está”**, sem garantia formal de funcionamento;
- o autor não assume responsabilidade por problemas, prejuízos, falhas, uso indevido ou consequências geradas pelo uso do sistema.

### Em linguagem direta para o usuário

Você pode utilizar, estudar e adaptar este projeto, mas deve entender que:

- o sistema é oferecido como ferramenta de apoio;
- a responsabilidade pela conferência final das informações continua sendo do usuário;
- antes de qualquer uso oficial, institucional ou administrativo, recomenda-se revisar cuidadosamente todos os dados e documentos gerados.

# Manual do Usuário — Multiplica Evidências Linha 2

## 1. Apresentação

O `Multiplica Evidências` é uma aplicação desktop em Python voltada ao apoio do trabalho do professor multiplicador.

O sistema organiza informações de forma local, facilitando o registro de:

- encontros;
- evidências;
- relatórios;
- acompanhamento de cursistas.

A `Linha 2` é a edição avançada do projeto. Ela amplia os recursos disponíveis em relação à linha estável `1.x`, especialmente no acompanhamento de cursistas e na importação de dados.

## 2. Objetivo do sistema

O sistema foi pensado para:

- apoiar a organização pedagógica e documental do trabalho mensal;
- reduzir perda de informação;
- facilitar o acompanhamento de pendências;
- melhorar a consistência dos registros usados em relatórios.

## 3. Antes de começar

Antes do uso regular, recomenda-se:

- preencher os dados do professor multiplicador;
- cadastrar as turmas;
- escolher corretamente o mês de trabalho;
- entender onde ficam as saídas e os backups.

Também é importante:

- evitar armazenar dados desnecessários;
- revisar registros antes de salvar;
- fazer cópias de segurança com frequência.

## 4. Tela principal

Na parte superior da janela, o sistema apresenta:

- seletor de mês com encontros;
- botão `Abrir saídas`;
- botão `Abrir pasta das evidências`;
- botão `Backup do banco`;
- botão `Sobre o projeto`.

As abas principais são:

- `Início`;
- `Professor Multiplicador`;
- `Turmas`;
- `Encontros`;
- `Checklist e relatório`;
- `Acompanhamento de Cursistas`.

## 5. Aba `Professor Multiplicador`

Nesta área, o usuário registra seus dados principais.

Esses dados ajudam a compor a base de documentos e relatórios do sistema.

Recomendações:

- preencher com atenção;
- revisar ortografia;
- atualizar se houver mudança de dados.

## 6. Aba `Turmas`

Permite cadastrar as turmas acompanhadas.

O ideal é manter uma identificação padronizada, para evitar divergências entre registros.

Boas práticas:

- conferir o número da turma;
- não duplicar cadastros;
- revisar antes de editar.

## 7. Aba `Encontros`

Usada para registrar os encontros pedagógicos.

Os encontros podem ser vinculados a dados que serão usados em conferência e relatórios.

Recomendações:

- conferir data;
- selecionar a turma correta;
- manter o registro consistente com as evidências existentes.

## 8. Aba `Checklist e relatório`

Auxilia na verificação do que foi preenchido e do que está faltando.

Também ajuda na preparação de relatórios mensais.

Em situações de divergência de valor, o sistema pode alertar antes de salvar, para que o usuário confirme conscientemente.

## 9. Aba `Acompanhamento de Cursistas`

É uma das principais novidades da `Linha 2`.

Foi criada para registrar e acompanhar situações que envolvem professores cursistas, sem duplicar dados de outras partes do sistema.

Ela possui três subabas:

- `Cursistas`;
- `Ocorrências`;
- `Socializações`.

## 10. Subaba `Cursistas`

Serve para o cadastro básico e acompanhamento inicial de cada cursista.

Informações que podem ser registradas:

- nome;
- turma;
- e-mail institucional;
- e-mail pessoal;
- telefone ou WhatsApp;
- observação geral;
- status de cursista ativo;
- situação da busca ativa.

Exemplos de uso:

- cursista não apareceu ainda;
- cursista está associado à turma errada;
- cursista consta em outro curso;
- necessidade de localizar contato;
- necessidade de acompanhamento inicial.

Situações de busca ativa podem incluir:

- `Não iniciado`;
- `Em contato`;
- `Aguardando retorno`;
- `Localizado`;
- `Encerrado`.

## 11. Subaba `Ocorrências`

Foi pensada para registrar problemas ou situações que exigem acompanhamento.

Exemplos:

- curso errado;
- turma errada;
- problema de inscrição;
- dificuldade de acesso;
- necessidade de encaminhamento ao PEC;
- dúvida pedagógica;
- situação resolvida ou pendente.

Campos comuns:

- cursista;
- turma;
- encontro;
- categoria;
- status;
- prioridade;
- data de abertura;
- resumo;
- resolução;
- descrição.

Também pode haver:

- movimentações;
- anexos;
- controle de encaminhamento ao PEC.

## 12. Subaba `Socializações`

Permite acompanhar se cada cursista enviou sua socialização e qual apoio pedagógico pode ser necessário.

Dados principais:

- cursista;
- turma;
- status da socialização;
- data de envio;
- necessidade de apoio;
- potencial destaque;
- observação pedagógica.

Utilidade:

- identificar não envio;
- organizar devolutivas;
- observar qualidade e potencial de destaque;
- apoiar ações voltadas à excelência e premiações.

## 13. Movimentações

As movimentações funcionam como histórico resumido do acompanhamento.

Exemplos:

- contato realizado;
- retorno aguardado;
- situação encaminhada;
- pendência resolvida.

Isso evita perda de contexto ao longo do tempo.

## 14. Anexos

O sistema pode associar arquivos a determinados registros de acompanhamento.

Exemplos de anexos:

- prints;
- comprovantes;
- documentos;
- registros úteis de consulta.

Recomendações:

- anexar apenas o necessário;
- evitar excesso de arquivos;
- tomar cuidado com conteúdo sensível.

## 15. Importação de cursistas por planilha

A linha avançada permite importar dados de uma planilha recebida dos PECs.

Antes da importação final, o sistema realiza uma análise prévia.

Essa análise pode classificar linhas como:

- novas;
- atualizáveis;
- conflitantes;
- ignoradas.

Na estrutura analisada até aqui:

- CPF deve ser ignorado;
- `di` deve ser ignorado;
- `turmaid` deve ser ignorado.

O sistema pode interpretar o número da turma a partir do campo textual da planilha.

Observações no nome, quando vierem após hífen, podem ser desconsideradas na análise, conforme a regra definida.

## 16. Filtros e pesquisa

Em várias telas, o sistema usa filtros por:

- turma;
- status;
- categoria;
- texto de busca;
- anexos;
- movimentações.

Se um registro não aparecer:

- verifique filtros ativos;
- revise a turma escolhida;
- confirme o mês selecionado.

## 17. Backup do banco

O backup é indispensável.

Recomenda-se fazer backup:

- antes de importações;
- antes de alterações maiores;
- ao fim de ciclos mensais;
- de forma periódica, mesmo sem mudanças grandes.

Sempre que possível:

- guarde cópia em mais de um local;
- use nomes fáceis de identificar;
- evite depender de uma única cópia.

## 18. Boas práticas de preenchimento

- Conferir a turma antes de salvar.
- Evitar registrar o mesmo cursista duas vezes.
- Usar observações objetivas.
- Registrar movimentações curtas e claras.
- Não armazenar dados pessoais desnecessários.
- Fazer revisão antes de concluir registros importantes.

## 19. Dúvidas frequentes

### Não encontro um cursista

Verifique filtros ativos e a turma selecionada.

### A turma não aparece corretamente

Revise o cadastro da turma e a origem da planilha.

### A importação não trouxe todos os nomes

Pode haver conflitos, dados incompletos ou linhas ignoradas.

### A socialização continua pendente

Verifique o status, a data de envio e se o registro correto foi carregado.

### Recebi um aviso antes de salvar

O sistema está pedindo conferência. Leia com atenção antes de confirmar.

## 20. Encerramento

O melhor uso do sistema depende de preenchimento regular, revisão cuidadosa e backup frequente.

A `Linha 2` oferece mais recursos, mas deve ser usada com método para não gerar complexidade desnecessária.

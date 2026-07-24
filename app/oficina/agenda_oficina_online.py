from app.database import get_connection
from app.api.conta_servico_google.config_google import config_conta_servico
from datetime import datetime, timedelta
import pandas as pd
import logging, os

# 1. QUERY_SQL parametrizada para receber o intervalo dinâmico de datas do Python
QUERY_SQL = """
select rev.cidade,
       TO_CHAR(oat.dta_agendamento, 'DD/MM/YYYY') as DATA_AGENDA,
       TO_CHAR(oat.dta_agendamento, 'HH24:MI') as HORA_INICIO,
       TO_CHAR(oat.dta_termino, 'HH24:MI') as HORA_TERMINO,
       fat.nome as CONSULTOR
  from cac_contato cc,
       ofi_parametro op,ofi_atendimento oat
 INNER JOIN fat_vendedor fat on ( fat.empresa = oat.empresa and fat.revenda = oat.revenda and oat.vendedor_agendado = fat.vendedor) 
 INNER JOIN ger_revenda rev on  ( rev.empresa = oat.empresa and rev.revenda = oat.revenda)
  left join ger_motivo mot
on ( oat.empresa = mot.empresa
   and oat.revenda = mot.revenda
   and oat.motivo_cancelamento_agenda = mot.motivo )
 where oat.empresa = cc.empresa
   and oat.revenda = cc.revenda
   and oat.contato = cc.contato
   and cc.empresa = op.empresa
   and cc.revenda = op.revenda
   and coalesce(cc.os_continuacao,'N') = 'N'
   and ( oat.empresa = 1 and oat.revenda in (1,2,3,4) )
   and ( oat.situacao_agendamento is null or oat.situacao_agendamento = 'C' )
   and ( ( oat.situacao <> 8 ) or ( ( oat.situacao = 8 ) and ( oat.situacao_agendamento = 'C' ) ) )
   and (
        ( oat.dta_agendamento >= :data_inicio and oat.dta_agendamento < :data_fim )
     or ( oat.dta_termino > :data_inicio and oat.dta_termino <= :data_fim )
     or ( oat.dta_agendamento < :data_inicio and oat.dta_termino > :data_fim )
   )
   and oat.origem = 'O'
   and oat.vendedor_agendado is not null
 order by oat.dta_agendamento, rev.cidade
"""

def retorna_agenda(data_inicio, data_fim):
    conn = get_connection('read')
    
    # Executa a query passando as datas dinâmicas como parâmetros (padrão do Oracle)
    df = pd.read_sql_query(QUERY_SQL, conn, params={"data_inicio": data_inicio, "data_fim": data_fim})
    conn.close()

    print(f"Dados extraídos com sucesso! {len(df)} agendamentos encontrados no banco de {data_inicio.strftime('%d/%m/%Y')} a {data_fim.strftime('%d/%m/%Y')}.")
    df.columns = [str(col).upper() for col in df.columns]
    df = df.fillna("")
    
    return df

def preparar_visao_ia(df_bruto, data_atual):
    lojas = [
        {'CIDADE': 'CASCAVEL', 'CAPACIDADE_MAX': 2},
        {'CIDADE': 'FOZ DO IGUACU', 'CAPACIDADE_MAX': 1},
        {'CIDADE': 'TOLEDO', 'CAPACIDADE_MAX': 1},
        {'CIDADE': 'UMUARAMA', 'CAPACIDADE_MAX': 1}
    ]

    # Definição dos blocos de horários padrão
    horarios_sabado = ['08:00', '08:30', '09:00', '09:30', '10:00', '10:30', '11:00', '11:30']
    horarios_semana_padrao = ['08:00', '08:30', '09:00', '09:30', '10:00', '10:30', '11:00', '11:30',
                              '14:00', '14:30', '15:00', '15:30', '16:00', '16:30', '17:00', '17:30']
    horarios_semana_umuarama = ['08:00', '08:30', '09:00', '09:30', '10:00', '10:30', '11:00',
                                '13:30', '14:00', '14:30', '15:00', '15:30', '16:00', '16:30', '17:00', '17:30']

    linhas_grade = []

    # Melhoria 2 & 3: Loop que gera a grade para os próximos 7 dias (Hoje + 7)
    for i in range(8):  # De 0 a 7 dias à frente
        dia_analise = data_atual + timedelta(days=i)
        dia_semana = dia_analise.weekday()  # 0=Segunda, 5=Sábado, 6=Domingo
        data_string = dia_analise.strftime('%d/%m/%Y')
        hora_atual_str = data_atual.strftime('%H:%M')

        # Melhoria 3: Se for Domingo, pula o dia inteiro e não adiciona nada à planilha
        if dia_semana == 6:
            continue

        for loja in lojas:
            # Identifica e ajusta os horários corretos baseados no dia da semana
            if dia_semana == 5:
                horarios_do_dia = horarios_sabado
            else:
                if loja['CIDADE'] == 'UMUARAMA':
                    horarios_do_dia = horarios_semana_umuarama
                else:
                    horarios_do_dia = horarios_semana_padrao

            for hora in horarios_do_dia:
                # Melhoria 1: Se o dia analisado for HOJE, ignora horários que já passaram do momento atual
                if i == 0 and hora <= hora_atual_str:
                    continue

                linhas_grade.append({
                    'DATA': data_string,
                    'CIDADE': loja['CIDADE'],
                    'HORA_INICIO': hora,
                    'CAPACIDADE_MAX': loja['CAPACIDADE_MAX']
                })
    
    df_ia = pd.DataFrame(linhas_grade)

    # Proteção caso o DataFrame seja gerado completamente vazio
    if df_ia.empty:
        return pd.DataFrame(columns=['DATA', 'CIDADE', 'HORA_INICIO', 'CAPACIDADE_MAX', 'AGENDADOS', 'STATUS'])

    # Cruzamento dos horários disponíveis mapeados com os agendamentos reais do banco
    if not df_bruto.empty:
        df_bruto['CIDADE'] = df_bruto['CIDADE'].str.upper()
        agendamentos_agrupados = df_bruto.groupby(['DATA_AGENDA', 'CIDADE', 'HORA_INICIO']).size().reset_index(name='AGENDADOS')
        
        df_ia = pd.merge(df_ia, agendamentos_agrupados, left_on=['DATA', 'CIDADE', 'HORA_INICIO'], right_on=['DATA_AGENDA', 'CIDADE', 'HORA_INICIO'], how='left')
    else:
        df_ia['AGENDADOS'] = 0

    df_ia['AGENDADOS'] = df_ia['AGENDADOS'].fillna(0).astype(int)
    
    # Regra de Status final
    df_ia['STATUS'] = df_ia.apply(lambda row: 'DISPONÍVEL' if row['AGENDADOS'] < row['CAPACIDADE_MAX'] else 'LOTADO', axis=1)

    if 'DATA_AGENDA' in df_ia.columns:
        df_ia = df_ia.drop(columns=['DATA_AGENDA'])
        
    return df_ia.astype(str)

def atualizar_sheets_com_dados_reais(df_final):
    ID_PLANILHA = "1KNKLDBmtJ3-DDCQPiFYQ6SrCHFvM535cXYzTxOriAnc"
    cliente_sheets = config_conta_servico()
    planilha = cliente_sheets.open_by_key(ID_PLANILHA)
    aba = planilha.sheet1  
    
    cabecalhos = df_final.columns.values.tolist()
    linhas_dados = df_final.values.tolist()
    formato_final_google_sheets = [cabecalhos] + linhas_dados
    
    aba.clear()
    aba.update(range_name="A3", values=formato_final_google_sheets) 
    
    carimbo = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    aba.update_acell('A1', f"Atualizado via Banco de Dados em: {carimbo}")
    
    print(f"✅ Sucesso! Planilha atualizada com a matriz de 7 dias da IA ({len(linhas_dados)} linhas).")
    
def main():
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    LOG_DIR = os.path.join(BASE_DIR, "logs")
    os.makedirs(LOG_DIR, exist_ok=True)
    LOG_FILE = os.path.join(LOG_DIR, "app.log")
    
    logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    try:
        # Melhoria 1 & 2: Captura o horário exato de execução do sistema e projeta a data fim
        hoje_agora = datetime.now()
        data_fim_pesquisa = hoje_agora + timedelta(days=7)
        
        # Ajusta a data final para contemplar até o último minuto do sétimo dia na query do banco
        data_fim_ajustada = datetime(data_fim_pesquisa.year, data_fim_pesquisa.month, data_fim_pesquisa.day, 23, 59, 59)
        
        # 1. Busca os agendamentos ocorrendo dentro dessa janela de tempo dinamicamente
        df_bruto = retorna_agenda(hoje_agora, data_fim_ajustada)
        
        print(f"*** Executando em ambiente de {os.getenv('AMBIENTE_DESCRICAO', 'PRODUÇÃO')} ******")
        
        # 2. Transforma na Matriz Inteligente para a IA ler (com regras de negócio aplicadas)
        df_pronto_para_ia = preparar_visao_ia(df_bruto, hoje_agora)
        
        # 3. Envia para o Sheets de aba única
        atualizar_sheets_com_dados_reais(df_pronto_para_ia)
        
    except Exception as e:
        print(f"❌ Ocorreu um erro geral: {e}")
        
if __name__ == "__main__":
    main()
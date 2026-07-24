import pandas as pd
import gspread
from config_google import config_conta_servico
from datetime import datetime

def rodar_automacao_incremental():
    # Abre a planilha principal
    cliente_sheets = config_conta_servico()
    planilha = cliente_sheets.open("1NZWxRdljbToWxmsvZ2XU7mnCjjHZuJBJMjNeMIF07Ds")
    
    # -----------------------------------------------------------------
    # SITUAÇÃO 1: Criar ou selecionar a aba sem excluir as existentes
    # -----------------------------------------------------------------
    nome_da_aba = "ESTOQUE_ATUALIZADO"
    try:
        # Tenta abrir a aba se ela já existir
        aba = planilha.worksheet(nome_da_aba)
        print(f"Aba '{nome_da_aba}' já existe. Selecionada.")
    except gspread.exceptions.WorksheetNotFound:
        # Se não existir, cria uma nova sem afetar as outras
        aba = planilha.add_worksheet(title=nome_da_aba, rows="1000", cols="10")
        print(f"✅ Nova aba '{nome_da_aba}' criada com sucesso!")

    # -----------------------------------------------------------------
    # SIMULAÇÃO DE DADOS NOVOS (Vindos do Banco da Honda)
    # -----------------------------------------------------------------
    # Imagine que essas duas OSs novas acabaram de entrar no sistema
    dados_novos_do_banco = {
        'OS': [10249, 10250, 10251],  # A 10249 já existia no teste anterior, a 10250 é inédita
        'Data': ['2026-06-01', '2026-06-01','2026-06-01'],
        'Modelo': ['Honda City', 'Honda Civic', 'Honda WRV'],
        'Servico': ['Instalacao Acessorios', 'Troca de Oleo', 'Revisao 10.000'],
        'Valor': [1100.00, 350.00, 500.00],
        'Status_Pagamento': ['Aberto', 'Pago', 'Aberto']
    }
    df_novos = pd.DataFrame(dados_novos_do_banco)

    # -----------------------------------------------------------------
    # SITUAÇÃO 2: Comparar e adicionar apenas o que for NOVO
    # -----------------------------------------------------------------
    print("Buscando dados existentes para comparação...")
    todas_linhas = aba.get_all_values()
    
    # Se a aba estiver vazia ou só tiver o cabeçalho inicial
    if len(todas_linhas) < 3: 
        print("Planilha vazia. Inserindo dados pela primeira vez...")
        # Cria a estrutura inicial: insere os cabeçalhos na linha 3
        aba.update(range_name="A3", values=[df_novos.columns.values.tolist()])
        df_para_adicionar = df_novos
    else:
        # Como pulamos as 2 primeiras linhas (Metadados e espaço),
        # o cabeçalho real da tabela está na linha 3 (índice 2 do array)
        cabecalhos_existentes = todas_linhas[2]
        dados_corpo = todas_linhas[3:] # Dados reais começam na linha 4
        
        df_existente = pd.DataFrame(dados_corpo, columns=cabecalhos_existentes)
        
        # Alerta de T.I.: O Sheets traz tudo como STRING. 
        # Forçamos a coluna chave (OS) a ser string em ambos para a comparação funcionar.
        df_existente['OS'] = df_existente['OS'].astype(str)
        df_novos['OS'] = df_novos['OS'].astype(str)
        
        # Mágica do Pandas: Filtra o df_novos mantendo apenas as OSs que NÃO estão no df_existente
        df_para_adicionar = df_novos[~df_novos['OS'].isin(df_existente['OS'])]

    # Se houver dados novos após a filtragem, faz o append
    if not df_para_adicionar.empty:
        print(f"Encontrado(s) {len(df_para_adicionar)} novo(s) registro(s). Adicionando...")
        # append_rows adiciona logo após a última linha preenchida do Sheets automaticamente
        aba.append_rows(df_para_adicionar.values.tolist())
        print("✅ Registros novos adicionados!")
    else:
        print("ℹ️ Nenhum registro novo detectado. Planilha já estava atualizada.")

    # -----------------------------------------------------------------
    # SITUAÇÃO 3: Adicionar a data e horário de atualização em A1
    # -----------------------------------------------------------------
    carimbo_data_hora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    texto_log = f"Última Atualização do Agente: {carimbo_data_hora}"
    
    # Atualiza especificamente a célula A1 sem mexer na tabela abaixo
    aba.update_acell('A1', texto_log)
    print(f"✅ Timestamp atualizado em A1: {carimbo_data_hora}")

if __name__ == "__main__":
    rodar_automacao_incremental()
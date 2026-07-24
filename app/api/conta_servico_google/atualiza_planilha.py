from app.api.conta_servico_google.config_google import config_conta_servico
from datetime import datetime

def atualizar_sheets_com_dados_reais(df_banco):
    # Abre a planilha pelo ID exclusivo da URL
    ID_PLANILHA = "1NZWxRdljbToWxmsvZ2XU7mnCjjHZuJBJMjNeMIF07Ds"
    cliente_sheets = config_conta_servico()
    planilha = cliente_sheets.open_by_key(ID_PLANILHA)
    aba = planilha.sheet1  # Seleciona a primeira aba
    
    # -------------------------------------------------------------
    # A TRANSFORMAÇÃO PARA O FORMATO GOOGLE SHEETS (Lista de Listas)
    # -------------------------------------------------------------
    # O gspread precisa de: [['Coluna1', 'Coluna2'], ['Linha1_A', 'Linha1_B'], ['Linha2_A', 'Linha2_B']]
    
    # Pegamos os cabeçalhos das colunas
    cabecalhos = df_banco.columns.values.tolist()
    
    # Pegamos todas as linhas de dados puras
    linhas_dados = df_banco.values.tolist()
    
    # Juntamos o cabeçalho no topo da lista de dados
    formato_final_google_sheets = [cabecalhos] + linhas_dados
    
    # Limpa a planilha antiga e atualiza com os dados novos reais
    aba.clear()
    aba.update(range_name="A3", values=formato_final_google_sheets) # Começa na A3 para manter o A1 livre para o Log
    
    # Adiciona o carimbo de data/hora em A1 (Sua Situação 3 anterior)
    carimbo = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    aba.update_acell('A1', f"Atualizado via Banco de Dados em: {carimbo}")
    
    print(f"✅ Sucesso! Planilha atualizada com as {len(linhas_dados)} linhas do banco de dados.")

if __name__ == "__main__":
    atualizar_sheets_com_dados_reais()
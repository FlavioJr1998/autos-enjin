import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

# 1. Configuração das Credenciais (Mesmo padrão que já usamos)
escopos = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
credenciais = Credentials.from_service_account_file("credenciais.json", scopes=escopos)
cliente_sheets = gspread.authorize(credenciais)

def ler_dados_planilha_compartilhada():
    # 2. Cole aqui o ID da planilha que foi compartilhada com a sua Conta de Serviço
    ID_DA_PLANILHA = "1NZWxRdljbToWxmsvZ2XU7mnCjjHZuJBJMjNeMIF07Ds"
    
    try:
        print(f"Tentando conectar à planilha compartilhada (ID: {ID_DA_PLANILHA})...")
        
        # Abrimos usando 'open_by_key' que é infalível para arquivos compartilhados
        planilha = cliente_sheets.open_by_key(ID_DA_PLANILHA)
        
        # Seleciona a primeira aba
        aba = planilha.sheet1
        print(f"✅ Conectado com sucesso à aba: '{aba.title}'")
        
        # 3. LER OS DADOS
        # get_all_records() já transforma as linhas em dicionários usando a primeira linha como cabeçalho
        dados = aba.get_all_records()
        
        if not dados:
            print("⚠️ A planilha está conectada, mas parece estar vazia ou sem cabeçalhos válidos.")
            return

        # 4. EXIBIR O TEXTO / DADOS
        # Para o terminal ficar bonito e legível, jogamos no Pandas DataFrame
        df = pd.DataFrame(dados)
        
        print("\n=== CONTEÚDO EXTRAÍDO DA PLANILHA ===")
        print(df.to_string(index=False)) # to_string exibe a tabela alinhada no terminal
        print("======================================\n")
        
    except gspread.exceptions.SpreadsheetNotFound:
        print("❌ Erro: Planilha não encontrada! Verifique se o ID está correto.")
        print("💡 Certifique-se de que você COMPARTILHOU a planilha com o e-mail da sua Conta de Serviço.")
    except Exception as e:
        print(f"❌ Ocorreu um erro inesperado: {e}")

if __name__ == "__main__":
    ler_dados_planilha_compartilhada()
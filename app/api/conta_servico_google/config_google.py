import gspread
from google.oauth2.service_account import Credentials


def config_conta_servico():
    # Configuração de Credenciais
    escopos = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    credenciais = Credentials.from_service_account_file("app/api/conta_servico_google/credenciais.json", scopes=escopos)
    cliente_sheets = gspread.authorize(credenciais)
    return cliente_sheets
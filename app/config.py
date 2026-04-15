import os
from dotenv import load_dotenv

load_dotenv()

EMPRESA = 2
# 1 = PRODUÇÃO
# 2 = HOMOLOGAÇÃO
AMBIENTE = 1
AMBIENTE_DESCRICAO = ''

if EMPRESA == 1:
    EMPRESA_DESCRICAO = "ENJIN"
elif EMPRESA == 2:
    EMPRESA_DESCRICAO = "FORÇA PARANÁ"
else:
    EMPRESA_DESCRICAO = "DESCONHECIDA"

DATA_INICIO_TESTE = "10/04/2026"
DATA_FIM_TESTE = "12/04/2026"
INTERVALO_HORAS = 6
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")

if AMBIENTE == 1:
    AMBIENTE_DESCRICAO = 'PRODUÇÃO'
    DB_DSN = os.getenv("DB_DSN_PROD")
else:
    AMBIENTE_DESCRICAO = 'TESTE'
    DB_DSN = os.getenv("DB_DSN_HOMO")



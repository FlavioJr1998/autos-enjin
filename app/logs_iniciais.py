import logging, os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_DIR = os.path.join(BASE_DIR, "logs")

os.makedirs(LOG_DIR, exist_ok=True)

LOG_FILE = os.path.join(LOG_DIR, "app.log")

def logs_iniciais( resultados ):
    logging.basicConfig(
        filename=LOG_FILE,
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    msg = f"*** Executando em ambiente de {os.getenv('AMBIENTE_DESCRICAO')} ******"
    print( msg )
    logging.info( msg )
    msg = "TOTAL DO BANCO:", resultados
    print( msg )
    logging.info( msg )
from app.service import buscar_notas, processar_notas
from app.email.email_config import enviar_email
from app.email.email_service import gerar_html
from app.logs_iniciais import logs_iniciais
import logging, os

def main():
    logging.basicConfig(
        filename='logs/app.log',
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    resultados, data_inicio, data_fim = buscar_notas()
    logs_iniciais( resultados )
    novas = processar_notas(resultados)
    
    if not novas:
        print("💤 Nenhuma nota nova")
        logging.info( "💤 Nenhuma nota nova")
        return

    msg = f"🚨 {len(novas)} novas notas!"
    print( msg )
    logging.info( msg )

    for n in novas:
        print(n)
    
    msg = "Chamando envio de email..."
    print( msg )
    logging.info( msg )
    
    html = gerar_html(novas, data_inicio, data_fim)
    enviar_email(html)

    msg = "Fim do Envio"
    print( msg )
    logging.info( msg )

if __name__ == "__main__":
    main()
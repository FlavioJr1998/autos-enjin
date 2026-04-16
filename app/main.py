from app.service import buscar_notas, processar_notas
from app.email.email_config import enviar_email
from app.email.email_service import gerar_html
import logging, os

def main():
    logging.basicConfig(
        filename='logs/app.log',
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    resultados, data_inicio, data_fim = buscar_notas()
    print(f"*** Executando em ambiente de {os.getenv('AMBIENTE_DESCRICAO')} ******")
    print("TOTAL DO BANCO:", resultados)  # 👈 DEBUG
    novas = processar_notas(resultados)

    print ( novas )

    if not novas:
        print("💤 Nenhuma nota nova")
        return

    print(f"🚨 {len(novas)} novas notas!")
    for n in novas:
        print(n)
    
    print("Chamando envio de email...")
    html = gerar_html(novas, data_inicio, data_fim)
    enviar_email(html)
    print("Fim do envio")

if __name__ == "__main__":
    main()
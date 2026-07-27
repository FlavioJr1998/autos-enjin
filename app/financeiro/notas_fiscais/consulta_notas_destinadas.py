import os, logging
from datetime import datetime, timedelta

from app.database import get_connection
from app.financeiro.notas_fiscais.query import consulta_notas_destinadas, busca_notas_lancadas, busca_revendas
from core.email.email_config import enviar_email
from app.logs_iniciais import logs_iniciais


def buscar_notas():
    inicio, fim = obter_periodo()

    data_inicio = inicio.strftime("%d/%m/%Y")
    data_fim = fim.strftime("%d/%m/%Y")

    filtro = f"""
    AND DW.DT_EMISSAO BETWEEN 
        TO_DATE('{data_inicio} 00:00:00', 'DD/MM/YYYY HH24:MI:SS')
    AND TO_DATE('{data_fim} 23:59:59', 'DD/MM/YYYY HH24:MI:SS')
    """
    
    #filtro += montar_filtro()
    query = consulta_notas_destinadas( filtro )

    conn = get_connection( 'read')
    cursor = conn.cursor()

    cursor.execute(query)
    resultados = cursor.fetchall()

    cursor.close()
    conn.close()

    return resultados, data_inicio, data_fim

def processar_notas(resultados):
    lista_notas = [row[2] for row in resultados]
    lista_revendas = [row[7] for row in resultados]

    notas_lancadas = buscar_notas_lancadas(lista_notas)
    mapa_revendas = buscar_revendas(lista_revendas)

    novas_notas = []

    for row in resultados:
        nota = row[2]
        cod_revenda = row[7]

        nova = {
            "razao": row[0],
            "cnpj": row[1],
            "nota": nota,
            "chave": row[3],
            "valor": row[4],
            "data": row[6],
            "revenda": mapa_revendas.get(cod_revenda, f"Cód {cod_revenda}"),
            "entrada": nota in notas_lancadas
        }

        novas_notas.append(nova)

    return novas_notas

def buscar_notas_lancadas(lista_notas):
    if not lista_notas:
        return set()

    notas_str = ",".join(str(n) for n in lista_notas)
    query = busca_notas_lancadas( notas_str )

    conn = get_connection( 'read' )
    cursor = conn.cursor()

    cursor.execute(query)
    resultados = cursor.fetchall()

    cursor.close()
    conn.close()

    return set([r[0] for r in resultados])

def buscar_revendas(lista_revendas):
    if not lista_revendas:
        return {}

    revendas_str = ",".join(str(r) for r in set(lista_revendas))
    query = busca_revendas( revendas_str )

    conn = get_connection( 'read' )
    cursor = conn.cursor()

    cursor.execute(query)
    resultados = cursor.fetchall()

    cursor.close()
    conn.close()

    return {r[0]: r[1] for r in resultados}

def formatar_cnpj(cnpj):
    cnpj = str(cnpj).zfill(14)
    return f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}"

def obter_periodo():
    hoje = datetime.now()
    dia_semana = hoje.weekday()  # segunda=0, sexta=4

    if dia_semana == 0:  # segunda
        inicio = hoje - timedelta(days=2)
        fim = hoje
    
    elif dia_semana == 2: # quarta
        inicio = hoje - timedelta(days=2)
        fim = hoje

    elif dia_semana == 4:  # sexta
        inicio = hoje - timedelta(days=4)
        fim = hoje

    else:
        inicio = hoje
        fim = hoje

    return inicio, fim

def gerar_html(novas, data_inicio, data_fim):
    html = f"""
    <html>
    <body style="font-family: Arial, sans-serif;">

    <h2 style="color:#d9534f;">
    🚨 Notas Fiscais Detectadas - { "ENJIN" if os.getenv('EMPRESA') == '1' else "FORÇA PARANÁ MOTORES E MÁQUINAS" } - {os.getenv('AMBIENTE_DESCRICAO')}
    </h2>

    <p style="font-size:14px;">
📅 <b>Período da consulta:</b> {data_inicio} até {data_fim}
    </p>

    <table border="1" cellpadding="8" cellspacing="0" 
           style="border-collapse: collapse; width:100%;">
    <tr style="background-color:#f2f2f2;">
        <th>Empresa</th>
        <th>CNPJ</th>
        <th>NF</th>
        <th>Chave NFe</th>
        <th>Valor</th>
        <th>Data</th>
        <th>Revenda Destino da Nota</th>
        <th>Entrada Realizada?</th>
    </tr>
    """

    for n in novas:
        valor_fmt = f"R$ {n['valor']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

        status = "✅ Sim" if n["entrada"] else "❌ Não"
        cor = "#d4edda" if n["entrada"] else "#f8d7da"

        html += f"""
        <tr style="background-color:{cor}">
            <td>{n['razao']}</td>
            <td>{n['cnpj']}</td>
            <td>{n['nota']}</td>
            <td>{n['chave']}</td>
            <td>{valor_fmt}</td>
            <td>{n['data']}</td>
            <td>{n['revenda']}</td>
            <td><b>{status}</b></td>
        </tr>
        """
    
    html += """
    </table>
    <br>
    <p style="font-size:12px;color:gray;">
    Script Captação NFe Destinadas da base de dados do Apollo<br>
    Desenvolvido por Flávio Jr 🚀
    </p>
    </body>
    </html>
    """

    return html

if __name__ == "__main__":
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
        
    else:
        msg = f"🚨 {len(novas)} novas notas!"
        print( msg )
        logging.info( msg )

        for n in novas:
            print(n)
        
        msg = "Chamando envio de email..."
        print( msg )
        logging.info( msg )
        
        html = gerar_html(novas, data_inicio, data_fim)
        
        titulo = "🚨 Novas Notas Fiscais Destinadas Detectadas"
        destinatarios = os.getenv('EMAIL_TO')
        enviar_email(titulo, destinatarios, html)
        
        msg = "Fim do Envio"
        print( msg )
        logging.info( msg )
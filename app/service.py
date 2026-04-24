from app.database import get_connection
from app.config import DATA_INICIO_TESTE, DATA_FIM_TESTE
from app.state import carregar_estado, salvar_estado
from datetime import datetime, timedelta
import os

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

    query = f"""
    SELECT 
    DW.RAZAO_SOCIAL,
    DW.CNPJ_EMITENTE,
    DW.NRO_DOCUMENTO,
    DW.CHAVE_NFE,
    DW.VAL_DOCUMENTO,
    TO_CHAR(DW.DT_EMISSAO, 'DD/MM/YYYY HH24:MI:SS'),
    TO_CHAR(DW.DT_EMISSAO, 'DD/MM/YYYY HH24:MI'),
    DW.REVENDA
    FROM FAT_NFE_DOWNLOAD DW
    WHERE DW.EMPRESA = {os.getenv('EMPRESA')}
    {filtro}
    ORDER BY DW.DT_EMISSAO ASC
    """

    conn = get_connection()
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

    query = f"""
    SELECT TITULO
    FROM FIN_TITULO
    WHERE EMPRESA = {os.getenv('EMPRESA')}
      AND TIPO = 'CP'
      AND TITULO IN ({notas_str})
    """

    conn = get_connection()
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

    query = f"""
    SELECT REVENDA, NOME_FANTASIA
    FROM GER_REVENDA
    WHERE EMPRESA = {os.getenv('EMPRESA')}
      AND REVENDA IN ({revendas_str})
    """

    conn = get_connection()
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
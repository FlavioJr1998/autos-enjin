import os 

def consulta_notas_destinadas( filtro ):
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
    return query
    
def busca_notas_lancadas( notas_str ):
    query = f"""
        SELECT TITULO
        FROM FIN_TITULO
        WHERE EMPRESA = {os.getenv('EMPRESA')}
          AND TIPO = 'CP'
          AND TITULO IN ({notas_str})
        """
    return query

def busca_revendas( revendas_str ):
    query = f"""
        SELECT REVENDA, NOME_FANTASIA
        FROM GER_REVENDA
        WHERE EMPRESA = {os.getenv('EMPRESA')}
          AND REVENDA IN ({revendas_str})
        """
    return query
from ...database import get_connection
import logging

def executa_query( query ):
    
    conn = get_connection( 'write' )
    cursor = conn.cursor()
    

    try:
        cursor.callproc("dbms_output.enable")
        cursor.execute(query)
        # PASSO 3: Buscar os logs que ficaram guardados no buffer
        chunk_size = 100  # Quantidade de linhas que vai puxar por vez
        
        # Criamos variáveis do driver para receber os dados do Oracle
        lines_var = cursor.arrayvar(str, chunk_size)
        num_lines_var = cursor.var(int)
        num_lines_var.setvalue(0, chunk_size)

        print("--- LOGS DO BANCO ORACLE ---")
        
        # Loop para esvaziar o buffer do banco e printar no Python
        while True:
            # Chama a procedure interna do Oracle que lê o buffer
            cursor.callproc("dbms_output.get_lines", (lines_var, num_lines_var))
            
            num_lines = num_lines_var.getvalue()
            lines = lines_var.getvalue()[:num_lines]
    
            # Se vieram menos linhas do que o tamanho do bloco (chunk), o buffer esvaziou
            if num_lines < chunk_size:
                break

    finally:
        resultado = lines            
        cursor.close()
        conn.close()

    return resultado

def retorna_query():
    query = """
    DECLARE
    v_DATA_ATUAL DATE := SYSDATE;
    v_LINHAS_INSERIDAS NUMBER := 0;
    v_LINHAS_ATUALIZADAS NUMBER := 0;
    v_SEQUENCIA NUMBER;
    BEGIN
        DBMS_OUTPUT.PUT_LINE('--- INICIANDO INSERÇÃO EM MASSA DE VENDEDOR AGREGADO ---');
        DBMS_OUTPUT.PUT_LINE('------------------------------------------------------------');

        -- Laço que percorre exatamente o cenário do seu grid (O.S. sem vendedor agregado)
        FOR reg IN (
            SELECT DISTINCT
                OS.EMPRESA,
                OS.REVENDA,
                OS.NRO_OS,
                OS.CONTATO,
                VP.VENDEDOR AS VENDEDOR_PROPOSTA,
                VP.PROPOSTA AS PROPOSTA_VENDA
            FROM OFI_ORDEM_SERVICO OS
            INNER JOIN OFI_ATENDIMENTO OFA 
                ON (OFA.EMPRESA = OS.EMPRESA AND OFA.REVENDA = OS.REVENDA AND OS.CONTATO = OFA.CONTATO)
            INNER JOIN VEI_VEICULO VV 
                ON (OS.EMPRESA = VV.EMPRESA AND OS.REVENDA = VV.REVENDA_ORIGEM AND OFA.CHASSI = VV.CHASSI)
            INNER JOIN VEI_PROPOSTA VP 
                ON (VP.EMPRESA = OS.EMPRESA AND VP.REVENDA = OS.REVENDA AND VP.VEICULO = VV.VEICULO)
            WHERE OS.EMPRESA = 1
            AND OS.CATEGORIA_OS IN (7, 23, 24)
            AND OS.REVENDA IN (1, 2, 3, 4)
            AND OS.DTA_EMISSAO BETWEEN TRUNC(SYSDATE, 'MM') AND TRUNC(SYSDATE)
            --AND OS.DTA_EMISSAO BETWEEN TO_DATE('01/06/2026', 'DD/MM/YYYY') AND TO_DATE('06/06/2026', 'DD/MM/YYYY')
            AND VP.VENDEDOR IS NOT NULL
            -- Filtra apenas onde o vendedor agregado está nulo (não existe o registro)
            AND NOT EXISTS (
                SELECT 1 
                FROM OFI_VENDEDOR_AGREGADO OFAG 
                WHERE OFAG.EMPRESA = OS.EMPRESA 
                    AND OFAG.REVENDA = OS.REVENDA 
                    AND OFAG.CONTATO = OS.CONTATO
            )
            ORDER BY OS.NRO_OS
        ) LOOP
            
            -- 1. Insere o registro na tabela de Vendedor Agregado com a data de inclusão (conforme o Log)
            INSERT INTO OFI_VENDEDOR_AGREGADO 
                (EMPRESA, REVENDA, CONTATO, VENDEDOR, DTA_INCLUSAO)
            VALUES 
                (reg.EMPRESA, reg.REVENDA, reg.CONTATO, reg.VENDEDOR_PROPOSTA, v_DATA_ATUAL);
                
            v_LINHAS_INSERIDAS := v_LINHAS_INSERIDAS + SQL%ROWCOUNT;

            -- 2. Atualiza a data de última alteração na Ordem de Serviço (conforme o Log)
            UPDATE OFI_ORDEM_SERVICO
            SET DTA_ULTIMA_ALTERACAO = v_DATA_ATUAL
            WHERE EMPRESA = reg.EMPRESA
            AND REVENDA = reg.REVENDA
            AND NRO_OS = reg.NRO_OS;
            
            v_LINHAS_ATUALIZADAS := v_LINHAS_ATUALIZADAS + SQL%ROWCOUNT;
            
            -- REGISTRANDO LOG NA O.S
            -- CALCULANDO A SEQUENCIA DO LOG NA O.S
            SELECT COALESCE(MAX(SEQUENCIA), 0) + 1 
            INTO v_SEQUENCIA
            FROM GER_LOG_LANCAMENTO 
            WHERE EMPRESA = reg.EMPRESA 
            AND REVENDA = reg.REVENDA 
            AND CONTATO = reg.CONTATO;
            
            -- INSERINDO O LOG
            INSERT INTO GER_LOG_LANCAMENTO (
                SEQUENCIA, EMPRESA, REVENDA, CONTATO, USUARIO, 
                DTA_ALTERACAO, DES_ALTERACAO, DES_RESUMIDA, NRO_OS, 
                VAL_ANTERIOR, VAL_ATUAL
            ) VALUES (
                -- Auto-incremento da sequência para o contato específico
                v_SEQUENCIA, 
                reg.EMPRESA, 
                reg.REVENDA, 
                reg.CONTATO, 
                499, -- ID do usuário (geralmente o seu ou o de integração automotiva)
                v_DATA_ATUAL, 
                'VENDEDOR AGREGADO <' || reg.VENDEDOR_PROPOSTA || '> ADICIONADO AUTOMATICAMENTE VIA SCRIPT COM BASE NA PROPOSTA DE VENDA NRO' || reg.PROPOSTA_VENDA, 
                'INCLUSÃO DE VENDEDOR AGREGADO', 
                reg.NRO_OS, 
                '', -- Valor anterior (estava vazio/nulo)
                reg.VENDEDOR_PROPOSTA -- Valor atual inserido
            );
            DBMS_OUTPUT.PUT_LINE('Sucesso -> OS: ' || reg.NRO_OS || ' | Contato: ' || reg.CONTATO || ' recebeu o Vendedor: ' || reg.VENDEDOR_PROPOSTA);
            
        END LOOP;

    EXCEPTION
        WHEN OTHERS THEN
            DBMS_OUTPUT.PUT_LINE('ERRO CRÍTICO NO PROCESSO: ' || SQLERRM);
            ROLLBACK;
    END;
    """

    return query

def main():
    logging.basicConfig(
        filename='logs/app.log',
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    query = retorna_query()
    log = executa_query( query )

    print( log )
    logging.info( log )

if __name__ == "__main__":
    main()
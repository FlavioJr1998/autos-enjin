import oracledb
import requests
import os
import sys
from datetime import datetime
from dotenv import load_dotenv  # <--- NOVA IMPORTAÇÃO

# --- CONFIGURAÇÕES DE CAMINHOS ---
DIRETORIO_PROJETO = "/home/impala/Documentos/PROJETOS_AUTOMACAO/Consulta_Notas_Destinadas"
ARQUIVO_CHECKPOINT = os.path.join(DIRETORIO_PROJETO, "ultimo_checkpoint.txt")
ARQUIVO_ENV = os.path.join(DIRETORIO_PROJETO, ".env") # Caminho para o arquivo de senhas

# --- CARREGAR SEGREDOS ---
# Isso lê o arquivo .env e joga as variáveis para a memória do sistema
if os.path.exists(ARQUIVO_ENV):
    load_dotenv(ARQUIVO_ENV)
else:
    print(f"❌ ERRO: Arquivo .env não encontrado em {ARQUIVO_ENV}")
    sys.exit(1)

# --- CONFIGURAÇÕES ORACLE (Lendo das variáveis carregadas) ---
# Se não achar a variável, retorna None ou da erro
DIRETORIO_CLIENT_ORACLE = "/opt/oracle/instantclient_19_29"

DB_USER = os.getenv('DB_USER')
DB_PASS = os.getenv('DB_PASS')
DB_DSN  = os.getenv('DB_DSN')

# --- CONFIGURAÇÕES TELEGRAM ---
USE_TELEGRAM = False 
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# Validação simples para não rodar sem senha
if not DB_USER or not DB_PASS:
    print("❌ ERRO: Credenciais do banco não encontradas no arquivo .env")
    sys.exit(1)

# --- REGRAS DE FILTRO ---
FILTRO_PERIODOS_PERSONALIZADOS = True
EMPRESA = 2

# Definição do Checkpoint (Lê do arquivo ou retorna None)
def carregar_checkpoint():
    if os.path.exists(ARQUIVO_CHECKPOINT):
        with open(ARQUIVO_CHECKPOINT, 'r') as f:
            return f.read().strip()
    return None

def salvar_checkpoint(data_string):
    with open(ARQUIVO_CHECKPOINT, 'w') as f:
        f.write(data_string)

# --- LÓGICA DO FILTRO ---
# Se tiver checkpoint salvo, ignoramos o filtro personalizado para seguir a automação
ultimo_checkpoint = carregar_checkpoint()

if ultimo_checkpoint:
    print(f"🔄 Checkpoint encontrado! Buscando notas após: {ultimo_checkpoint}")
    FILTRO_DATA = f"AND DW.DT_EMISSAO > TO_DATE('{ultimo_checkpoint}', 'DD/MM/YYYY HH24:MI:SS')"
elif FILTRO_PERIODOS_PERSONALIZADOS:
    print("⚠️ Modo Personalizado Ativo (Sem checkpoint anterior)")
    FILTRO_DATA = "AND DW.DT_EMISSAO BETWEEN TO_DATE('20/10/2025 00:00:00', 'DD/MM/YYYY HH24:MI:SS') AND TO_DATE('30/10/2025 23:59:59', 'DD/MM/YYYY HH24:MI:SS')"
else:
    print("🚀 Modo Produção (Últimas 24h)")
    FILTRO_DATA = "AND DW.DT_EMISSAO >= SYSDATE - 1"

# --- SQL ---
# CORREÇÃO: Adicionei mais campos no SELECT para bater com a leitura do Python (row[3] e row[4])
QUERY = f"""
select distinct
 DW.RAZAO_SOCIAL,       -- row[0]
 DW.NRO_DOCUMENTO,      -- row[1]
 DW.VAL_DOCUMENTO,      -- row[2]
 TO_CHAR(DW.DT_EMISSAO, 'DD/MM/YYYY HH24:MI:SS') as DATA_COMPLETA, -- row[3] (Para salvar no checkpoint)
 TO_CHAR(DW.DT_EMISSAO, 'DD/MM/YYYY HH24:MI') as DATA_VISUAL,       -- row[4] (Para exibir na msg)
 DW.DT_EMISSAO          -- row[5] (Adicionado para corrigir o erro ORA-01791)
 from FAT_NFE_DOWNLOAD DW
 where DW.EMPRESA = {EMPRESA}
 AND DW.COD_MODELO_NF_USOFISCAL IS NULL
 {FILTRO_DATA}
 AND (DW.CSTAT is null or DW.CSTAT not in (646,647,650,651))
 AND DW.NFE_DOWNLOAD <> 'C'
 ORDER BY DW.DT_EMISSAO ASC
"""

def verificar_notas():
    print(f"--- Iniciando execução: {datetime.now()} ---")
    try:
        # 1. ATIVA O MODO THICK (A correção principal do seu erro)
        try:
            oracledb.init_oracle_client(lib_dir=DIRETORIO_CLIENT_ORACLE)
        except Exception:
            pass # Se já estiver carregado via variável de ambiente, segue o jogo

        # 2. Conexão
        conn = oracledb.connect(user=DB_USER, password=DB_PASS, dsn=DB_DSN)
        conn.autocommit = False # Garante que não vamos salvar nada sem querer
        cursor = conn.cursor()
        cursor.execute("SET TRANSACTION READ ONLY")
        
        # 3. Execução (Note que usei QUERY maiúsculo, pois é a variável global)
        cursor.execute(QUERY)
        resultados = cursor.fetchall()

        if resultados:
            print(f"✅ Encontradas {len(resultados)} novas notas.")
            
            mensagem = f"🚨 *Novas Notas Detectadas ({len(resultados)})* 🚨\n\n"
            ultimo_horario_processado = None

            for row in resultados:
                razao = row[0]
                nf = row[1]
                valor = row[2]
                data_banco = row[3]  # Agora existe (Graças à correção no SQL)
                data_visual = row[4] # Agora existe

                # Formatação de valor
                val_fmt = f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                
                mensagem += f"🏢 {razao}\n📄 NF: {nf} | 💰 {val_fmt}\n📅 {data_visual}\n━━━━━━━━━━━━━━\n"
                
                ultimo_horario_processado = data_banco

            print(mensagem) # Exibe no log

            # Atualiza o arquivo para a próxima execução não pegar as mesmas notas
            if ultimo_horario_processado:
                salvar_checkpoint(ultimo_horario_processado)
                print(f"💾 Checkpoint atualizado para: {ultimo_horario_processado}")

        else:
            print("💤 Nenhuma nota nova encontrada.")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"❌ ERRO FATAL: {e}")

if __name__ == "__main__":
    verificar_notas()
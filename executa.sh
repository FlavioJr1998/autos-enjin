#!/bin/bash

# 1. Configura a variável do Oracle (O segredo está aqui)
export LD_LIBRARY_PATH=/opt/oracle/instantclient_19_29:$LD_LIBRARY_PATH

# 2. Entra na pasta do projeto (Importante para o Cron)
cd /home/impala/Documentos/PROJETOS_AUTOMACAO/Consulta_Notas_Destinadas

# 3. Executa o Python (Use o caminho completo do Python do seu venv, se tiver)
# Se não usar venv, pode ser /usr/bin/python3
/caminho/do/seu/venv/bin/python monitor_notas.py


# Após, dar permissão de execução 
# chmod +x rodar_notas.sh
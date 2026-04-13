import json
import os

ARQUIVO = "notas_enviadas.json"

def carregar_estado():
    if os.path.exists(ARQUIVO):
        with open(ARQUIVO, "r") as f:
            return json.load(f)
    return []

def salvar_estado(lista_notas):
    with open(ARQUIVO, "w") as f:
        json.dump(lista_notas, f)
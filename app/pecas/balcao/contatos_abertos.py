import html
from datetime import datetime, timedelta
from collections import defaultdict
from pathlib import Path

from app.pecas.balcao.querys import retorna_contatos_abertos
from app.database import get_connection
from core.email.email_config import enviar_email

def consulta_contatos() -> list[dict]:
    """Busca os contatos abertos e retorna diretamente uma lista de dicionários."""
    hoje = datetime.now().strftime("%d/%m/%Y")
    query = retorna_contatos_abertos(hoje, '1,2,3,4')
    
    conn = None
    resultados_dict = []

    try:
        conn = get_connection('read')
        cursor = conn.cursor()
        cursor.execute(query)
        
        # Mapeia dinamicamente o nome das colunas retornadas do Oracle
        colunas = [col[0].lower() for col in cursor.description]
        linhas = cursor.fetchall()
        
        # Transforma automaticamente em lista de dicionários
        resultados_dict = [dict(zip(colunas, linha)) for linha in linhas]

    except Exception as e:
        print(f"❌ Erro ao consultar banco de dados: {e}")
        # Aqui você pode adicionar log em arquivo se necessário
    finally:
        if conn:
            cursor.close()
            conn.close()

    return resultados_dict

def agrupar_contatos_por_revenda(contatos: list[dict]) -> dict:
    """Agrupa a lista de contatos por vendedor/consultor."""
    agrupado = defaultdict(list)
    for contato in contatos:
        chave = contato.get("revenda", "1")
        agrupado[chave].append(contato)
    return agrupado

def notifica_consultor_revenda(revenda: str, email: str, contatos: list[dict]):
    """Monta o e-mail consolidado e envia para o consultor/vendedor."""
    if contatos:
        corpo_email = renderizar_email_contatos( contatos )
        titulo = "Orçamentos/Contatos Abertos de Peças - Por Revenda"
        enviar_email( titulo, email, corpo_email)
    
        qtd_contatos = len(contatos)
        print(f"✉️ Enviando e-mail para o consultar da revenda '{revenda}' com {qtd_contatos} contato(s) pendente(s)...")
    
    # Exemplo de integração:
    # 1. Renderizar o HTML (email.html) passando a lista 'contatos'
    # 2. Chamar o serviço de e-mail (email_service.py)

def notifica_gerente(todos_contatos: list[dict]):
    """Envia um resumo geral de todos os orçamentos abertos para a gerência."""
    print(f"📊 Enviando relatório consolidado para a gerência ({len(todos_contatos)} total de pendências)...")
    
    if todos_contatos:
        corpo_email = renderizar_email_contatos( todos_contatos )
        titulo = "Orçamentos em Abertos de Peças"
        enviar_email( titulo, 'ti@enjin.com.br', corpo_email)
    
def gerar_corpo_email_html(novas_notas: list[dict]) -> str:
    """Carrega o template HTML e injeta os dados dinâmicos utilizando Jinja2."""
    
    # Caminho dinâmico até o arquivo email.html
    caminho_template = Path(__file__).parent / "emails" / "email.html"
    
    with open(caminho_template, "r", encoding="utf-8") as f:
        template_content = f.read()
    
    # Compila o template e renderiza os dados
    template = Template(template_content)
    html_rendered = template.render(novas=novas_notas)
    
    return html_rendered

def renderizar_email_contatos(contatos: list[dict]) -> str:
    """Monta a tabela HTML de contatos de peças usando recursos nativos do Python."""
    linhas_html = []

    for index, item in enumerate(contatos):
        # 1. Tratamento de Alerta por Dias em Aberto
        try:
            dias_aberto = int(item.get("dias_aberto_contato", 0))
        except (ValueError, TypeError):
            dias_aberto = 0

        # Destaca em amarelo/alerta caso esteja aberto há 3 ou mais dias
        if dias_aberto >= 3:
            cor_fundo = "#fff3cd"
            cor_texto = "#856404"
            badge_dias = f"<b style='color: #dc3545;'>{dias_aberto} dias</b>"
        else:
            cor_fundo = "#ffffff" if index % 2 == 0 else "#f8f9fa"  # Efeito zebrado
            cor_texto = "#333333"
            badge_dias = f"{dias_aberto} dia(s)"

        # 2. Sanitização dos campos com html.escape
        contato_num = html.escape(str(item.get("contato", "")))
        
        cod_cli = html.escape(str(item.get("cod_cliente", "")))
        nome_cli = html.escape(str(item.get("nome_cliente", item.get("nome_ciente", ""))))
        cliente_fmt = f"{cod_cli} - {nome_cli}" if cod_cli else nome_cli

        dta_contato = html.escape(str(item.get("data_contato", "")))
        qtd_itens = html.escape(str(item.get("qtd_itens", "")))
        empresa = html.escape(str(item.get("empresa", "")))
        revenda = html.escape(str(item.get("cidade", "")))
        emp_rev_fmt = f"{revenda}"
        situacao = html.escape(str(item.get("situacao_contato", "")))
        vendedor = html.escape(str(item.get("nome_vendedor", "")))

        # 3. Construção do <tr> da linha
        linha = f"""
        <tr style="background-color: {cor_fundo}; color: {cor_texto}; border-bottom: 1px solid #dee2e6;">
            <td style="font-weight: bold;">#{contato_num}</td>
            <td>{cliente_fmt}</td>
            <td>{dta_contato}</td>
            <td style="text-align: center;">{badge_dias}</td>
            <td style="text-align: center;">{qtd_itens}</td>
            <td>{emp_rev_fmt}</td>
            <td>{situacao}</td>
            <td>{vendedor}</td>
        </tr>"""
        
        linhas_html.append(linha)

    tabela_completa = "".join(linhas_html)

    # 4. Leitura do arquivo estático e interpolação do placeholder
    caminho_template = Path(__file__).resolve().parent.parent / "notificacao" / "emails" / "email.html"
    
    with open(caminho_template, "r", encoding="utf-8") as file:
        template_base = file.read()

    return template_base.format(linhas_tabela=tabela_completa)

if __name__ == "__main__":
    # 1. Busca os dados no Oracle
    contatos = consulta_contatos()
    
    if contatos:
        # 2. Agrupa os contatos por vendedor
        contatos_por_revenda = agrupar_contatos_por_revenda(contatos)
    
        # 3. Notifica cada consultor com suas pendências
        for revenda, lista_pendencias in contatos_por_revenda.items():
            email = ""
            print( revenda )
            if revenda == 1:
                print("Cascavel Selecionado")
                email = 'ti@enjin.com.br'
            elif revenda == 2:
                print("Foz Selecionado")
                email = 'ti@enjin.com.br'
            elif revenda == 3:
                print("Umuarama Selecionado")
                email = 'ti@enjin.com.br'
            elif revenda == 4:
                print("Toledo Selecionado")
                email = 'ti@enjin.com.br'
            else:
                print("Algo de errado não está certo!!!")
                break
            notifica_consultor_revenda(revenda, email, lista_pendencias)
            
        # 4. Notifica o gerente com a visão geral
        #notifica_gerente(contatos)
    else:
        print("ℹ️ Nenhum contato aberto encontrado.")
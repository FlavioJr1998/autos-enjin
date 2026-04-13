from app.config import EMPRESA_DESCRICAO

def gerar_html(novas):
    html = f"""
    <html>
    <body style="font-family: Arial, sans-serif;">

    <h2 style="color:#d9534f;">
    🚨 Notas Fiscais Detectadas - {EMPRESA_DESCRICAO}
    </h2>

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
    Script Captação NFe Destinadas por Empresa<br>
    Desenvolvido por Flávio Jr 🚀
    </p>
    </body>
    </html>
    """

    return html
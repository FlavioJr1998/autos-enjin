import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

def enviar_email(html):
    print("📤 Iniciando envio de email...")

    try:
        msg = MIMEMultipart()
        msg['Subject'] = "🚨 Novas Notas Fiscais Detectadas"
        msg['From'] = os.getenv("EMAIL_FROM")
        msg['To'] = os.getenv("EMAIL_TO")

        msg.attach(MIMEText(html, 'html'))

        print("🔌 Conectando ao servidor SMTP...")

        with smtplib.SMTP(os.getenv("SMTP_HOST"), int(os.getenv("SMTP_PORT"))) as server:
            server.starttls()

            print("🔐 Autenticando...")
            server.login(os.getenv("EMAIL_USER"), os.getenv("EMAIL_PASS"))

            print("📨 Enviando email...")
            server.send_message(msg)

        print("✅ Email enviado com sucesso!")

    except Exception as e:
        print(f"❌ Erro ao enviar email: {e}")
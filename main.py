import os
import pandas as pd
import smtplib
import logging
from datetime import datetime
from dateutil.relativedelta import relativedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from queries import QUERIES

# Configuração básica de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("automation.log"),
        logging.StreamHandler()
    ]
)

def send_notification_email(subject, body):
    """Envia um e-mail de notificação."""
    try:
        sender_email = os.getenv("EMAIL_SENDER")
        receiver_email = os.getenv("EMAIL_RECIPIENT")
        password = os.getenv("EMAIL_PASSWORD")
        smtp_server = os.getenv("SMTP_SERVER")
        smtp_port = int(os.getenv("SMTP_PORT"))

        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = receiver_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'html'))

        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, password)
            server.send_message(msg)
        logging.info("E-mail de notificação enviado com sucesso.")
    except Exception as e:
        logging.error(f"Falha ao enviar e-mail de notificação: {e}")

def run_report_job():
    """
    Função que orquestra todo o processo de extração e notificação.
    Executa uma vez e finaliza.
    """
    logging.info("Iniciando processo de extração de relatórios.")
    load_dotenv()
    
    # Determina o mês do relatório para o nome do arquivo (mês anterior)
    report_date = datetime.today() - relativedelta(months=1)
    report_month_str = report_date.strftime('%Y-%m')

    # --- 1. Preparar ambiente e conexão ---
    try:
        db_user = os.getenv("DB_USER")
        db_password = os.getenv("DB_PASSWORD")
        db_host = os.getenv("DB_HOST")
        db_port = os.getenv("DB_PORT")
        db_name = os.getenv("DB_NAME")
        export_path = os.getenv("EXPORT_FOLDER_PATH")

        if not all([db_user, db_password, db_host, db_port, db_name, export_path]):
            raise ValueError("Uma ou mais variáveis de ambiente não foram definidas no arquivo .env.")

        DATABASE_URL = f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        engine = create_engine(DATABASE_URL)
        
        file_name = f"Relatorio_Mensal_{report_month_str}.xlsx"
        full_file_path = os.path.join(export_path, file_name)

    except Exception as e:
        logging.error(f"Erro na configuração inicial: {e}")
        send_notification_email(
            subject=f"Falha Crítica na Automação de Relatórios {report_month_str}",
            body=f"<h1>Erro na Automação</h1><p>O script falhou durante a fase de configuração inicial.</p><p><b>Erro:</b> {e}</p>"
        )
        return

    # --- 2. Executar queries e gerar Excel ---
    status_report = []
    processed_sheets = set()

    try:
        with pd.ExcelWriter(full_file_path, engine='openpyxl') as writer:
            logging.info(f"Iniciando extração para {len(QUERIES)} relatórios.")
            
            for name, query in QUERIES.items():
                sheet_name = name.replace(" ", "")[:30]
                
                original_sheet_name = sheet_name.upper()
                count = 1
                while sheet_name in processed_sheets:
                    sheet_name = f"{original_sheet_name[:28]}{count}"
                    count += 1
                processed_sheets.add(sheet_name)
                
                try:
                    logging.info(f"Executando query: '{name}'...")
                    df = pd.read_sql_query(text(query), engine)
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
                    status_report.append(f"<li><b>{name}:</b> <font color='green'>Sucesso</font></li>")
                    logging.info(f"Dados da query '{name}' salvos na aba '{sheet_name}'.")
                except Exception as e:
                    logging.error(f"Falha ao executar a query '{name}': {e}")
                    status_report.append(f"<li><b>{name}:</b> <font color='red'>Falha</font> - Erro: {e}</li>")

        logging.info(f"Arquivo Excel '{file_name}' criado com sucesso em '{export_path}'.")

        # --- 3. Enviar e-mail de resumo ---
        email_subject = f"Relatórios Extraídos com Sucesso - {report_month_str}"
        email_body = f"""
        <h1>Relatório de Execução da Automação</h1>
        <p>O processo de extração de dados do mês <b>{report_month_str}</b> foi concluído.</p>
        <p>O arquivo <b>{file_name}</b> foi salvo em: {export_path}</p>
        <h2>Status de Cada Relatório:</h2>
        <ul>
        {''.join(status_report)}
        </ul>
        """
        send_notification_email(email_subject, email_body)

    except Exception as e:
        logging.error(f"Ocorreu um erro geral durante a execução do processo: {e}")
        send_notification_email(
            subject=f"Falha na Automação de Relatórios {report_month_str}",
            body=f"<h1>Erro na Automação</h1><p>Ocorreu um erro durante a geração do arquivo Excel ou envio do e-mail.</p><p><b>Erro:</b> {e}</p>"
        )

    logging.info("Processo de extração de relatórios finalizado.")


if __name__ == "__main__":
    # O script agora executa a função de trabalho diretamente e depois encerra.
    run_report_job()
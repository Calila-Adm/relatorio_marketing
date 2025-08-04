"""
Módulo principal da automação de relatórios mensais do I-Club.

Este módulo orquestra todo o processo de extração de dados do programa de fidelidade I-Club,
gerando relatórios mensais em Excel e enviando notificações por e-mail para o CEO e equipe
de Marketing do Iguatemi.

Funcionalidades principais:
- Extração de dados do PostgreSQL usando queries complexas
- Geração de arquivo Excel com múltiplas abas de análise
- Envio de e-mail com status da execução
- Tratamento robusto de erros e logging detalhado

Autor: Marketing Team - Iguatemi
Data: 2025
Versão: 2.0
"""

import os
import pandas as pd
import logging
from datetime import datetime
from dateutil.relativedelta import relativedelta
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from queries import QUERIES

# Importar novos módulos de email
from email_service import EmailService
from email_formatter import EmailFormatter

# Configuração básica de logging
# O sistema mantém logs tanto em arquivo quanto no console para facilitar monitoramento
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("automation.log"),  # Arquivo de log persistente
        logging.StreamHandler()  # Output no console para execução manual
    ]
)

def send_notification_email(subject, body, attachments=None):
    """
    Envia um e-mail de notificação sobre o status da execução da automação.
    
    Esta função usa o novo EmailService com suporte a múltiplos provedores
    e mecanismos de fallback para garantir entrega do email.
    
    Args:
        subject (str): Assunto do e-mail
        body (str): Corpo do e-mail em formato HTML
        attachments (list): Lista de arquivos para anexar (opcional)
        
    Returns:
        bool: True se enviado com sucesso, False caso contrário
    """
    email_service = EmailService()
    success = email_service.send_notification(subject, body, attachments or [])
    
    if not success:
        logging.error("Falha ao enviar email após tentar todos os provedores")
    
    return success

def run_report_job():
    """
    Função principal que orquestra todo o processo de geração de relatórios do I-Club.
    
    Esta função coordena todas as etapas da automação:
    1. Configuração do ambiente e conexão com banco de dados
    2. Execução das queries SQL para extração de dados
    3. Geração do arquivo Excel com múltiplas abas
    4. Envio de e-mail com status da execução
    
    Fluxo de Execução:
        1. Carrega variáveis de ambiente do arquivo .env
        2. Determina o período do relatório (sempre mês anterior)
        3. Estabelece conexão com PostgreSQL
        4. Executa cada query do módulo QUERIES
        5. Salva resultados em arquivo Excel
        6. Envia e-mail com resumo da execução
        
    Tratamento de Erros:
        - Fase 1: Erros de configuração (variáveis de ambiente ausentes)
        - Fase 2: Erros de execução de queries SQL
        - Fase 3: Erros de geração do Excel ou envio de e-mail
        
    Tempo de Execução:
        - Médio: 3-4 minutos para processar todas as 12 queries
        - Depende do volume de dados e performance do banco
        
    Returns:
        None - A função apenas executa e registra logs
    """
    logging.info("Iniciando processo de extração de relatórios.")
    
    # Carrega variáveis de ambiente do arquivo .env
    load_dotenv()
    
    # Determina o mês do relatório (sempre mês anterior ao atual)
    # Ex: Se executado em julho/2025, gera relatório de junho/2025
    report_date = datetime.today() - relativedelta(months=1)
    report_month_str = report_date.strftime('%Y-%m')

    # --- FASE 1: Preparação do Ambiente e Conexão com Banco ---
    try:
        # Carrega credenciais do banco de dados PostgreSQL
        db_user = os.getenv("DB_USER")
        db_password = os.getenv("DB_PASSWORD")
        db_host = os.getenv("DB_HOST")
        db_port = os.getenv("DB_PORT")
        db_name = os.getenv("DB_NAME")
        export_path = os.getenv("EXPORT_FOLDER_PATH")

        # Validação de configuração - todas as variáveis são obrigatórias
        if not all([db_user, db_password, db_host, db_port, db_name, export_path]):
            raise ValueError("Uma ou mais variáveis de ambiente não foram definidas no arquivo .env.")

        # Monta string de conexão PostgreSQL usando SQLAlchemy
        DATABASE_URL = f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        engine = create_engine(DATABASE_URL)
        
        # Define nome do arquivo de saída com padrão YYYY-MM
        file_name = f"Relatorio_Mensal_{report_month_str}.xlsx"
        full_file_path = os.path.join(export_path, file_name)

    except Exception as e:
        logging.error(f"Erro na configuração inicial: {e}")
        # Envia e-mail de notificação sobre falha crítica
        send_notification_email(
            subject=f"Falha Crítica na Automação de Relatórios {report_month_str}",
            body=f"<h1>Erro na Automação</h1><p>O script falhou durante a fase de configuração inicial.</p><p><b>Erro:</b> {e}</p>"
        )
        return

    # --- FASE 2: Execução de Queries e Geração do Excel ---
    # Lista para armazenar status de execução de cada query (sucesso/falha)
    status_report = []
    # Set para controlar nomes únicos de abas no Excel (limite 31 caracteres)
    processed_sheets = set()
    # Dicionário para armazenar DataFrames para geração do email formatado
    dataframes_dict = {}

    try:
        # Cria arquivo Excel usando pandas com engine openpyxl
        with pd.ExcelWriter(full_file_path, engine='openpyxl') as writer:
            logging.info(f"Iniciando extração para {len(QUERIES)} relatórios.")
            
            # Itera sobre todas as queries definidas no módulo queries.py
            for name, query in QUERIES.items():
                # Formata nome da aba: remove espaços e limita a 30 caracteres
                sheet_name = name.replace(" ", "")[:30]
                
                # Garante unicidade do nome da aba para evitar sobrescrita
                original_sheet_name = sheet_name.upper()
                count = 1
                while sheet_name in processed_sheets:
                    # Adiciona sufixo numérico se nome já existe
                    sheet_name = f"{original_sheet_name[:28]}{count}"
                    count += 1
                processed_sheets.add(sheet_name)
                
                try:
                    logging.info(f"Executando query: '{name}'...")
                    # Executa query SQL e converte resultado para DataFrame
                    df = pd.read_sql_query(text(query), engine)
                    # Armazena DataFrame para uso posterior
                    dataframes_dict[name] = df
                    # Salva DataFrame como aba no Excel
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
                    # Registra sucesso para relatório de status
                    status_report.append(f"<li><b>{name}:</b> <font color='green'>Sucesso</font></li>")
                    logging.info(f"Dados da query '{name}' salvos na aba '{sheet_name}'.")
                except Exception as e:
                    # Registra falha mas continua processando outras queries
                    logging.error(f"Falha ao executar a query '{name}': {e}")
                    status_report.append(f"<li><b>{name}:</b> <font color='red'>Falha</font> - Erro: {e}</li>")

        logging.info(f"Arquivo Excel '{file_name}' criado com sucesso em '{export_path}'.")

        # --- FASE 3: Envio de E-mail com Resumo da Execução ---
        # Verificar se todas as queries críticas foram executadas com sucesso
        critical_queries = [
            "Notas Fiscais Cadastradas - Comparação YoY",
            "Vendas Cadastradas - Comparação YoY",
            "Compradores Únicos",
            "Clientes por Categoria"
        ]
        
        all_critical_success = all(name in dataframes_dict for name in critical_queries)
        
        if all_critical_success:
            # Gerar email no formato especificado
            try:
                email_formatter = EmailFormatter(dataframes_dict, report_month_str)
                formatted_email_body = email_formatter.generate_email_body()
                
                # Assunto do email
                month_name = email_formatter.format_month_name(report_month_str)
                email_subject = f"Relatório Mensal I-Club - {month_name}"
                
                # Enviar email formatado com o arquivo Excel anexado
                success = send_notification_email(
                    email_subject, 
                    f"<pre style='font-family: Arial, sans-serif;'>{formatted_email_body}</pre>",
                    [full_file_path]
                )
                
                if not success:
                    # Se falhar, enviar email simples de status
                    fallback_subject = f"Relatórios Gerados (Email não formatado) - {report_month_str}"
                    fallback_body = f"""
                    <h3>Relatório gerado mas houve problema no envio do email formatado</h3>
                    <p>O arquivo Excel foi gerado com sucesso: <b>{file_name}</b></p>
                    <p>Localização: {export_path}</p>
                    <p>Por favor, verifique o arquivo manualmente.</p>
                    <h4>Status das Queries:</h4>
                    <ul>{''.join(status_report)}</ul>
                    """
                    send_notification_email(fallback_subject, fallback_body, [full_file_path])
            
            except Exception as e:
                logging.error(f"Erro ao formatar email: {e}")
                # Enviar email de status básico
                basic_subject = f"Relatórios Extraídos - {report_month_str}"
                basic_body = f"""
                <h3>Processo de extração concluído</h3>
                <p>Arquivo gerado: <b>{file_name}</b></p>
                <p>Localização: {export_path}</p>
                <h4>Status:</h4>
                <ul>{''.join(status_report)}</ul>
                """
                send_notification_email(basic_subject, basic_body, [full_file_path])
        else:
            # Enviar email de aviso sobre queries faltantes
            warning_subject = f"Relatórios Parciais - {report_month_str}"
            warning_body = f"""
            <h3>⚠️ Atenção: Algumas queries críticas falharam</h3>
            <p>O arquivo Excel foi gerado mas está incompleto: <b>{file_name}</b></p>
            <p>Localização: {export_path}</p>
            <h4>Status das Queries:</h4>
            <ul>{''.join(status_report)}</ul>
            <p><b>Queries críticas faltantes:</b></p>
            <ul>
            {''.join([f"<li>{q}</li>" for q in critical_queries if q not in dataframes_dict])}
            </ul>
            """
            send_notification_email(warning_subject, warning_body, [full_file_path])

    except Exception as e:
        # Tratamento de erro geral - captura falhas não previstas
        logging.error(f"Ocorreu um erro geral durante a execução do processo: {e}")
        # Notifica sobre falha crítica via e-mail
        send_notification_email(
            subject=f"Falha na Automação de Relatórios {report_month_str}",
            body=f"<h1>Erro na Automação</h1><p>Ocorreu um erro durante a geração do arquivo Excel ou envio do e-mail.</p><p><b>Erro:</b> {e}</p>"
        )

    logging.info("Processo de extração de relatórios finalizado.")


if __name__ == "__main__":
    """
    Ponto de entrada principal do script.
    
    Quando executado diretamente (não importado como módulo), inicia o processo
    de geração de relatórios mensais do I-Club.
    
    Formas de Execução:
        - Manual: python main.py
        - Agendada: Via cron ou agendador de tarefas do sistema
        - Automatizada: Integração com ferramentas de automação
        
    Logs de Execução:
        - Arquivo: automation.log (mesmo diretório do script)
        - Console: Output em tempo real durante execução
        
    Tempo Estimado: 3-4 minutos para execução completa
    """
    run_report_job()
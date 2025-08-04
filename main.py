"""
Módulo principal da automação de relatórios mensais do I-Club.

Este módulo orquestra todo o processo de extração de dados do programa de fidelidade I-Club,
gerando relatórios mensais em Excel.

Funcionalidades principais:
- Extração de dados do PostgreSQL usando queries complexas
- Geração de arquivo Excel com múltiplas abas de análise
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
from sqlalchemy.pool import QueuePool
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from dotenv import load_dotenv
from queries import QUERIES

# Módulos removidos: email_service e email_formatter (funcionalidade de email removida)

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

def create_performance_indexes(engine):
    """
    Cria índices de performance para otimizar as queries do I-Club
    
    Esta função cria índices estratégicos nas tabelas mais utilizadas
    para melhorar significativamente a performance das consultas.
    """
    indexes_sql = [
        # Índices para tabela de transações/vendas
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_transacao_data ON transacao(data_transacao);",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_transacao_cliente ON transacao(cliente_id);",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_transacao_loja ON transacao(loja_id);",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_transacao_status ON transacao(status);",
        
        # Índices para tabela de cupons
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_cupom_data_emissao ON cupom(data_emissao);",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_cupom_data_uso ON cupom(data_uso);",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_cupom_cliente ON cupom(cliente_id);",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_cupom_status ON cupom(status);",
        
        # Índices para tabela de clientes
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_cliente_categoria ON cliente(categoria);",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_cliente_data_cadastro ON cliente(data_cadastro);",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_cliente_ativo ON cliente(ativo);",
        
        # Índices para tabela de visitas
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_visita_data ON visita(data_visita);",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_visita_cliente ON visita(cliente_id);",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_visita_loja ON visita(loja_id);",
        
        # Índices compostos para queries YoY (Year over Year)
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_transacao_data_cliente ON transacao(data_transacao, cliente_id);",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_cupom_data_cliente ON cupom(data_emissao, cliente_id);",
        
        # Índices para performance de agregações
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_transacao_valor ON transacao(valor) WHERE valor > 0;",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_transacao_mes_ano ON transacao(EXTRACT(YEAR FROM data_transacao), EXTRACT(MONTH FROM data_transacao));",
    ]
    
    try:
        logging.info("🔧 Verificando/criando índices de performance...")
        
        with engine.connect() as conn:
            created_count = 0
            for sql in indexes_sql:
                try:
                    # Usar autocommit para CREATE INDEX CONCURRENTLY
                    conn.execute(text("COMMIT;"))  # Finalizar transação atual
                    conn.execute(text(sql))
                    created_count += 1
                except Exception as e:
                    # Índice provavelmente já existe ou erro de sintaxe
                    if "already exists" not in str(e).lower():
                        logging.debug(f"Aviso ao criar índice: {e}")
            
            logging.info(f"✅ Índices de performance verificados/criados: {created_count}/{len(indexes_sql)}")
            
    except Exception as e:
        logging.warning(f"⚠️ Não foi possível criar alguns índices: {e}")
        logging.info("Sistema continuará funcionando, mas com performance reduzida")


# Função de email removida - sistema apenas gera arquivos Excel

def run_report_job():
    """
    Função principal que orquestra todo o processo de geração de relatórios do I-Club.
    
    Esta função coordena todas as etapas da automação:
    1. Configuração do ambiente e conexão com banco de dados
    2. Execução das queries SQL para extração de dados
    3. Geração do arquivo Excel com múltiplas abas
    
    Fluxo de Execução:
        1. Carrega variáveis de ambiente do arquivo .env
        2. Determina o período do relatório (sempre mês anterior)
        3. Estabelece conexão com PostgreSQL
        4. Executa cada query do módulo QUERIES
        5. Salva resultados em arquivo Excel
        
    Tratamento de Erros:
        - Fase 1: Erros de configuração (variáveis de ambiente ausentes)
        - Fase 2: Erros de execução de queries SQL
        - Fase 3: Erros de geração do Excel
        
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
        # Criar pasta específica para o mês anterior no Windows
        base_path = "/mnt/c/Users/edgar.prado/Documents/relatorio_fechamento_mensal"
        
        # Formatação do nome da pasta: nomemes'YY (ex: janeiro'25, dezembro'24)
        meses_nomes = {
            1: "janeiro", 2: "fevereiro", 3: "março", 4: "abril",
            5: "maio", 6: "junho", 7: "julho", 8: "agosto", 
            9: "setembro", 10: "outubro", 11: "novembro", 12: "dezembro"
        }
        
        month_name = meses_nomes[report_date.month]
        year_short = report_date.strftime('%y')  # Ano com 2 dígitos
        folder_name = f"{month_name}'{year_short}"
        
        export_path = os.path.join(base_path, folder_name)

        # Validação de configuração - variáveis de banco são obrigatórias
        if not all([db_user, db_password, db_host, db_port, db_name]):
            raise ValueError("Uma ou mais variáveis de ambiente do banco de dados não foram definidas no arquivo .env.")
        
        # Criar pasta específica para o mês (sempre cria, mesmo se já existir)
        logging.info(f"Criando pasta para o mês: {folder_name}")
        logging.info(f"Caminho completo: {export_path}")
        
        try:
            os.makedirs(export_path, exist_ok=True)
            logging.info(f"✅ Pasta criada/verificada com sucesso: {export_path}")
        except Exception as e:
            logging.error(f"❌ Não foi possível criar a pasta: {e}")
            raise ValueError(f"Pasta de destino inacessível: {export_path}")

        # Monta string de conexão PostgreSQL com connection pooling otimizado
        DATABASE_URL = f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        engine = create_engine(
            DATABASE_URL,
            poolclass=QueuePool,
            pool_size=10,        # Número de conexões mantidas no pool
            max_overflow=20,     # Conexões adicionais se necessário  
            pool_pre_ping=True,  # Verifica conexões antes de usar
            pool_recycle=3600,   # Recria conexões a cada hora
            echo=False           # Desabilita log SQL para performance
        )
        
        # Criar índices de performance se não existirem
        create_performance_indexes(engine)
        
        # Define nome do arquivo de saída com padrão YYYY-MM
        file_name = f"Relatorio_Mensal_{report_month_str}.xlsx"
        full_file_path = os.path.join(export_path, file_name)

    except Exception as e:
        logging.error(f"Erro na configuração inicial: {e}")
        logging.error("Script falhou durante a fase de configuração inicial.")
        return

    # --- FASE 2: Execução Paralela de Queries e Geração de Arquivos Individuais ---
    # Lista para thread-safe status reporting
    status_report = []
    status_lock = threading.Lock()
    # Dicionário para armazenar DataFrames
    dataframes_dict = {}
    dataframes_lock = threading.Lock()
    
    def execute_query_and_save(query_info):
        """Executa uma query e salva em arquivo individual"""
        name, query = query_info
        thread_name = threading.current_thread().name
        
        try:
            logging.info(f"[{thread_name}] Executando query: '{name}'...")
            
            # Criar conexão individual para thread safety
            with engine.connect() as conn:
                # Executa query SQL e converte resultado para DataFrame
                df = pd.read_sql_query(text(query), conn)
                
                # Thread-safe storage
                with dataframes_lock:
                    dataframes_dict[name] = df
                
                # Criar nome de arquivo individual (limpar caracteres especiais)
                safe_name = name.replace(" ", "_").replace("/", "-").replace(":", "-")
                safe_name = safe_name.replace("?", "").replace("*", "").replace("<", "").replace(">", "")
                safe_name = safe_name.replace("|", "-").replace('"', "").replace("'", "")
                
                individual_file_name = f"{safe_name}_{report_month_str}.xlsx"
                individual_file_path = os.path.join(export_path, individual_file_name)
                
                # Salvar arquivo individual
                with pd.ExcelWriter(individual_file_path, engine='openpyxl') as writer:
                    df.to_excel(writer, sheet_name='Dados', index=False)
                
                # Thread-safe status reporting
                with status_lock:
                    status_report.append(f"✅ {name}: {len(df)} linhas → {individual_file_name}")
                
                logging.info(f"[{thread_name}] ✅ '{name}' salvo como '{individual_file_name}' ({len(df)} linhas)")
                return True, name, len(df), individual_file_name
                
        except Exception as e:
            # Thread-safe error reporting
            with status_lock:
                status_report.append(f"❌ {name}: ERRO - {str(e)[:100]}...")
            
            logging.error(f"[{thread_name}] ❌ Falha ao executar '{name}': {e}")
            return False, name, 0, None

    try:
        logging.info(f"🚀 Iniciando execução PARALELA para {len(QUERIES)} queries...")
        logging.info(f"📁 Cada query será salva como arquivo individual em: {export_path}")
        
        # Executar queries em paralelo com ThreadPoolExecutor
        successful_queries = 0
        failed_queries = 0
        total_rows = 0
        
        with ThreadPoolExecutor(max_workers=4, thread_name_prefix="QueryWorker") as executor:
            # Submeter todas as queries para execução paralela
            future_to_query = {executor.submit(execute_query_and_save, item): item[0] 
                             for item in QUERIES.items()}
            
            # Processar resultados conforme completam
            for future in as_completed(future_to_query):
                query_name = future_to_query[future]
                try:
                    success, name, rows, filename = future.result()
                    if success:
                        successful_queries += 1
                        total_rows += rows
                    else:
                        failed_queries += 1
                except Exception as e:
                    failed_queries += 1
                    logging.error(f"Erro não capturado para query '{query_name}': {e}")

        logging.info(f"🎉 Processamento paralelo concluído!")
        logging.info(f"📊 {successful_queries} arquivos criados com sucesso em '{export_path}'")
        logging.info(f"📈 Total de {total_rows:,} linhas de dados processadas")
        if failed_queries > 0:
            logging.warning(f"⚠️ {failed_queries} queries falharam")

        # --- FASE 3: Relatório Final de Status ---
        # Verificar se todas as queries críticas foram executadas com sucesso
        critical_queries = [
            "Notas Fiscais Cadastradas - Comparação YoY",
            "Vendas Cadastradas - Comparação YoY",
            "Compradores Únicos",
            "Clientes por Categoria"
        ]
        
        all_critical_success = all(name in dataframes_dict for name in critical_queries)
        
        # Contadores de status
        total_queries = len(QUERIES)
        successful_queries = len([s for s in status_report if 'Sucesso' in s])
        failed_queries = total_queries - successful_queries
        
        logging.info("=" * 60)
        logging.info("RELATÓRIO DE EXECUÇÃO FINAL")
        logging.info("=" * 60)
        logging.info(f"📁 Arquivo gerado: {file_name}")
        logging.info(f"📂 Localização: {export_path}")
        logging.info(f"📊 Queries executadas: {successful_queries}/{total_queries}")
        
        if failed_queries > 0:
            logging.warning(f"⚠️  Queries com falha: {failed_queries}")
        
        if all_critical_success:
            logging.info("✅ Todas as queries críticas executadas com sucesso!")
        else:
            missing_queries = [q for q in critical_queries if q not in dataframes_dict]
            logging.warning(f"❌ Queries críticas faltantes: {missing_queries}")
        
        logging.info("📋 Status detalhado:")
        for name in QUERIES.keys():
            if name in dataframes_dict:
                logging.info(f"  ✅ {name}")
            else:
                logging.error(f"  ❌ {name}")
        
        logging.info("=" * 60)

    except Exception as e:
        # Tratamento de erro geral - captura falhas não previstas
        logging.error(f"Ocorreu um erro geral durante a execução do processo: {e}")
        logging.error("Falha crítica durante a geração do arquivo Excel.")

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
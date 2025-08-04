#!/usr/bin/env python3
"""
Verificação básica do sistema sem dependências externas
"""

import os
import sys
from datetime import datetime

def check_system():
    """Verifica se o sistema está configurado corretamente"""
    print("=" * 70)
    print("VERIFICAÇÃO DO SISTEMA I-CLUB")
    print("=" * 70)
    
    # Data do relatório (aproximada, sem dateutil)
    today = datetime.today()
    if today.month == 1:
        report_month = 12
        report_year = today.year - 1
    else:
        report_month = today.month - 1
        report_year = today.year
    
    report_month_str = f"{report_year}-{report_month:02d}"
    
    print(f"\n📅 Mês do relatório: {report_month_str}")
    
    # Verificar arquivos essenciais
    print(f"\n📁 Verificando arquivos essenciais...")
    essential_files = ['main.py', 'queries.py', 'requirements.txt']
    
    for file in essential_files:
        if os.path.exists(file):
            print(f"   ✅ {file}")
        else:
            print(f"   ❌ {file} - FALTANDO")
    
    # Verificar .env
    print(f"\n🔍 Verificando configuração...")
    if os.path.exists('.env'):
        print("✅ Arquivo .env encontrado")
    else:
        print("❌ Arquivo .env NÃO ENCONTRADO")
        if os.path.exists('.env.example'):
            print("   💡 Use .env.example como base:")
            print("   cp .env.example .env")
        else:
            print("   💡 Crie arquivo .env com as configurações do banco")
    
    # Verificar pasta de destino (Windows via WSL)
    base_path = "/mnt/c/Users/edgar.prado/Documents/relatorio_fechamento_mensal"
    
    # Formatação do nome da pasta: nomemes'YY
    meses_nomes = {
        1: "janeiro", 2: "fevereiro", 3: "março", 4: "abril",
        5: "maio", 6: "junho", 7: "julho", 8: "agosto", 
        9: "setembro", 10: "outubro", 11: "novembro", 12: "dezembro"
    }
    
    # Calcular mês anterior
    if today.month == 1:
        prev_month = 12
        prev_year = today.year - 1
    else:
        prev_month = today.month - 1
        prev_year = today.year
    
    month_name = meses_nomes[prev_month]
    year_short = str(prev_year)[-2:]  # Últimos 2 dígitos do ano
    folder_name = f"{month_name}'{year_short}"
    
    export_path = os.path.join(base_path, folder_name)
    
    print(f"\n📂 Sistema de pastas:")
    print(f"   📁 Pasta base: {base_path}")
    print(f"   📅 Pasta do mês: {folder_name}")
    print(f"   🗂️ Caminho completo: {export_path}")
    
    # Verificar pasta base
    if os.path.exists(base_path):
        print("   ✅ Pasta base existe")
    else:
        print("   ❌ Pasta base não existe (será criada)")
    
    # Verificar pasta do mês
    if os.path.exists(export_path):
        print("   ✅ Pasta do mês já existe")
    else:
        print("   📅 Pasta do mês será criada automaticamente")
    
    # Testar criação e escrita
    try:
        os.makedirs(export_path, exist_ok=True)
        test_file = os.path.join(export_path, "test.tmp")
        with open(test_file, 'w') as f:
            f.write("teste")
        os.remove(test_file)
        print("   ✅ Teste de criação e escrita OK")
    except Exception as e:
        print(f"   ❌ Erro ao criar/escrever: {e}")
    
    # Verificar queries
    print(f"\n📊 Verificando queries...")
    if os.path.exists('queries.py'):
        try:
            with open('queries.py', 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Contar queries (aproximado)
            query_count = content.count('SELECT')
            print(f"   ✅ Arquivo queries.py OK")
            print(f"   📈 Aproximadamente {query_count} queries encontradas")
            
        except Exception as e:
            print(f"   ❌ Erro ao ler queries.py: {e}")
    else:
        print("   ❌ queries.py não encontrado")
    
    # Arquivo de saída esperado
    file_name = f"Relatorio_Mensal_{report_month_str}.xlsx"
    print(f"\n📄 Arquivo que será gerado:")
    print(f"   📝 {file_name}")
    
    # Status das dependências
    print(f"\n📦 Status das dependências:")
    dependencies = [
        ('pandas', 'Manipulação de dados'),
        ('openpyxl', 'Geração de Excel'),
        ('sqlalchemy', 'Conexão com banco'),
        ('psycopg2', 'Driver PostgreSQL'),
        ('dotenv', 'Variáveis de ambiente')
    ]
    
    installed_count = 0
    for dep, desc in dependencies:
        try:
            if dep == 'dotenv':
                __import__('dotenv')
            else:
                __import__(dep)
            print(f"   ✅ {dep} - {desc}")
            installed_count += 1
        except ImportError:
            print(f"   ❌ {dep} - {desc} (NÃO INSTALADO)")
    
    # Relatório final
    print("\n" + "=" * 70)
    print("RELATÓRIO FINAL")
    print("=" * 70)
    
    if installed_count == len(dependencies):
        if os.path.exists('.env'):
            print("🎉 SISTEMA PRONTO PARA EXECUÇÃO!")
            print("\n🚀 Para executar:")
            print("   python main.py")
        else:
            print("⚠️  SISTEMA QUASE PRONTO - Configure o .env")
            print("\n📝 Configure o banco de dados no arquivo .env")
    else:
        print("❌ DEPENDÊNCIAS FALTANDO")
        print("\n📦 Para instalar:")
        print("   pip install -r requirements.txt")
        print("\n   ou instale individualmente:")
        for dep, desc in dependencies:
            try:
                if dep == 'dotenv':
                    __import__('dotenv')
                else:
                    __import__(dep)
            except ImportError:
                print(f"   pip install {dep}")
    
    print("=" * 70)

if __name__ == "__main__":
    check_system()
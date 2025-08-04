"""
Script de teste para verificar configuração de email

Este script testa a configuração de email e ajuda a diagnosticar
problemas de autenticação SMTP.

Uso: python test_email.py
"""

import os
import sys
from dotenv import load_dotenv
from email_service import EmailService
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def test_email_configuration():
    """Testa a configuração de email"""
    print("=" * 50)
    print("TESTE DE CONFIGURAÇÃO DE EMAIL I-CLUB")
    print("=" * 50)
    
    # Carregar variáveis de ambiente
    load_dotenv()
    
    # Verificar variáveis necessárias
    required_vars = [
        "EMAIL_SENDER",
        "EMAIL_RECIPIENT",
        "SMTP_SERVER",
        "SMTP_PORT"
    ]
    
    print("\n1. Verificando variáveis de ambiente:")
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if value:
            if var in ["EMAIL_PASSWORD", "EMAIL_APP_PASSWORD"]:
                print(f"   ✓ {var}: ***configurado***")
            else:
                print(f"   ✓ {var}: {value}")
        else:
            print(f"   ✗ {var}: NÃO CONFIGURADO")
            missing_vars.append(var)
    
    # Verificar senhas
    password = os.getenv("EMAIL_PASSWORD")
    app_password = os.getenv("EMAIL_APP_PASSWORD")
    
    if password:
        print(f"   ✓ EMAIL_PASSWORD: ***configurado***")
    else:
        print(f"   ✗ EMAIL_PASSWORD: NÃO CONFIGURADO")
        
    if app_password:
        print(f"   ✓ EMAIL_APP_PASSWORD: ***configurado*** (RECOMENDADO)")
    else:
        print(f"   ! EMAIL_APP_PASSWORD: não configurado (configurar se usar 2FA)")
    
    if missing_vars:
        print(f"\n❌ ERRO: Variáveis obrigatórias faltando: {', '.join(missing_vars)}")
        print("Configure essas variáveis no arquivo .env")
        return False
    
    # Testar conexão
    print("\n2. Testando conexão com servidor de email:")
    
    try:
        email_service = EmailService()
        
        # Testar cada provider
        results = email_service.test_connection()
        
        print("\n3. Resultados dos testes:")
        for provider, success in results.items():
            if success:
                print(f"   ✓ {provider}: SUCESSO")
            else:
                print(f"   ✗ {provider}: FALHOU")
        
        # Tentar enviar email de teste
        if any(results.values()):
            print("\n4. Enviando email de teste...")
            
            test_subject = "Teste de Configuração - I-Club Automation"
            test_body = """
            <h2>Teste de Email - I-Club Automation</h2>
            <p>Este é um email de teste para verificar a configuração do sistema.</p>
            <p>Se você recebeu este email, a configuração está correta!</p>
            <hr>
            <p><small>Enviado pelo script de teste de configuração</small></p>
            """
            
            success = email_service.send_notification(test_subject, test_body)
            
            if success:
                print("   ✓ Email de teste enviado com sucesso!")
                print(f"   → Verifique a caixa de entrada de: {os.getenv('EMAIL_RECIPIENT')}")
                return True
            else:
                print("   ✗ Falha ao enviar email de teste")
                return False
        else:
            print("\n❌ Nenhum provider de email funcionou")
            print("\nDicas de solução:")
            print("1. Se usar Office 365 com 2FA, crie um App Password:")
            print("   https://account.microsoft.com/security")
            print("2. Verifique se o email e senha estão corretos")
            print("3. Confirme se o servidor SMTP está correto")
            print("4. Verifique se há firewall bloqueando a porta", os.getenv('SMTP_PORT'))
            return False
            
    except Exception as e:
        print(f"\n❌ Erro durante teste: {e}")
        return False

if __name__ == "__main__":
    print("\nIniciando teste de configuração de email...\n")
    
    success = test_email_configuration()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ TESTE CONCLUÍDO COM SUCESSO!")
    else:
        print("❌ TESTE FALHOU - Verifique as configurações acima")
    print("=" * 50)
    
    sys.exit(0 if success else 1)
# 📧 Configuração de Email - I-Club Automation

## 🚨 Solução para Erro 535 (Autenticação SMTP)

O erro 535 indica falha de autenticação SMTP. Este guia ajuda a resolver esse problema.

## 📋 Opções de Configuração

### Opção 1: App Password (RECOMENDADO para Office 365)

Se você usa Office 365 com autenticação de dois fatores (2FA), você DEVE usar um App Password.

#### Como criar um App Password:

1. Acesse: https://account.microsoft.com/security
2. Faça login com sua conta Office 365
3. Clique em "Opções de segurança avançadas"
4. Em "Senhas de aplicativo", clique em "Criar uma nova senha de aplicativo"
5. Dê um nome (ex: "I-Club Automation")
6. Copie a senha gerada (16 caracteres)
7. Configure no arquivo `.env`:

```env
EMAIL_PASSWORD=sua_senha_normal
EMAIL_APP_PASSWORD=senha_de_16_caracteres_gerada
```

### Opção 2: Desabilitar 2FA (NÃO recomendado)

Se não puder usar App Password, você precisará desabilitar a autenticação de dois fatores na sua conta.

### Opção 3: Usar conta de serviço

Crie uma conta específica para automação sem 2FA habilitado.

## 🔧 Configuração do .env

```env
# Email principal
EMAIL_SENDER=seu.email@empresa.com
EMAIL_RECIPIENT=destinatario@empresa.com

# Senha normal (tente primeiro)
EMAIL_PASSWORD=sua_senha_normal

# App Password (se usar 2FA)
EMAIL_APP_PASSWORD=xxxx-xxxx-xxxx-xxxx

# Servidor SMTP
SMTP_SERVER=smtp.office365.com
SMTP_PORT=587
```

## 🧪 Testando a Configuração

Execute o script de teste:

```bash
python test_email.py
```

O script irá:
1. Verificar todas as variáveis de ambiente
2. Testar conexão com o servidor SMTP
3. Enviar um email de teste
4. Mostrar mensagens de erro detalhadas

## 🔍 Troubleshooting

### Erro 535 continua aparecendo?

1. **Verifique o App Password**: Certifique-se de copiar corretamente (sem espaços)
2. **Aguarde propagação**: Após criar o App Password, aguarde 5-10 minutos
3. **Verifique o servidor**: 
   - Office 365: `smtp.office365.com` porta `587`
   - Gmail: `smtp.gmail.com` porta `587`
4. **Firewall**: Verifique se a porta 587 não está bloqueada

### Outros erros comuns:

- **Timeout**: Verifique conexão de internet e firewall
- **Connection refused**: Servidor SMTP incorreto
- **Invalid credentials**: Email ou senha incorretos

## 📊 Fluxo de Autenticação

```
1. Tenta EMAIL_APP_PASSWORD (se configurado)
   ↓ (se falhar)
2. Tenta EMAIL_PASSWORD
   ↓ (se falhar)
3. Registra erro e tenta próximo provider
```

## 🛡️ Segurança

- **NUNCA** commite o arquivo `.env` no git
- Use senhas fortes e únicas
- Prefira App Passwords ao invés de senha principal
- Considere usar uma conta de serviço dedicada

## 📞 Suporte

Se continuar com problemas:
1. Execute `python test_email.py` e salve o output
2. Verifique os logs em `automation.log`
3. Contate o administrador do sistema com os detalhes do erro
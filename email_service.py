"""
Módulo de Serviço de Email para Automação I-Club

Este módulo implementa um sistema robusto de envio de emails com suporte
a múltiplos provedores e mecanismos de fallback para garantir entrega.

Funcionalidades:
- Suporte para OAuth2 (Office 365)
- Suporte para App Password
- Fallback para SMTP tradicional
- Retry automático com backoff
- Logging detalhado de tentativas

Autor: Marketing Team - Iguatemi
Data: 2025
Versão: 2.0
"""

import os
import smtplib
import logging
import time
from typing import Optional, Dict, List
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from abc import ABC, abstractmethod
from dataclasses import dataclass
import ssl


@dataclass
class EmailConfig:
    """Configuração para envio de email"""
    sender: str
    recipient: str
    smtp_server: str
    smtp_port: int
    password: Optional[str] = None
    app_password: Optional[str] = None
    use_tls: bool = True
    use_oauth: bool = False
    max_retries: int = 3
    retry_delay: int = 5


class EmailProvider(ABC):
    """Interface abstrata para provedores de email"""
    
    @abstractmethod
    def send(self, subject: str, body: str, attachments: List[str] = None) -> bool:
        """Envia email e retorna True se sucesso"""
        pass


class SMTPProvider(EmailProvider):
    """Provedor SMTP tradicional com suporte melhorado"""
    
    def __init__(self, config: EmailConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    def send(self, subject: str, body: str, attachments: List[str] = None) -> bool:
        """
        Envia email via SMTP com tratamento robusto de erros
        
        Args:
            subject: Assunto do email
            body: Corpo do email em HTML
            attachments: Lista de caminhos de arquivos para anexar
            
        Returns:
            bool: True se enviado com sucesso
        """
        for attempt in range(self.config.max_retries):
            try:
                # Criar mensagem
                msg = MIMEMultipart()
                msg['From'] = self.config.sender
                msg['To'] = self.config.recipient
                msg['Subject'] = subject
                
                # Adicionar corpo HTML
                msg.attach(MIMEText(body, 'html'))
                
                # Adicionar anexos se houver
                if attachments:
                    for file_path in attachments:
                        if os.path.isfile(file_path):
                            self._attach_file(msg, file_path)
                
                # Tentar enviar
                self._send_message(msg)
                self.logger.info(f"Email enviado com sucesso para {self.config.recipient}")
                return True
                
            except smtplib.SMTPAuthenticationError as e:
                self.logger.error(f"Erro de autenticação SMTP (tentativa {attempt + 1}): {e}")
                if "535" in str(e):
                    self.logger.info("Erro 535 detectado - Tentando com App Password")
                    if self.config.app_password and attempt < self.config.max_retries - 1:
                        # Trocar para app password na próxima tentativa
                        self.config.password = self.config.app_password
                        time.sleep(self.config.retry_delay)
                        continue
                        
            except Exception as e:
                self.logger.error(f"Erro ao enviar email (tentativa {attempt + 1}): {e}")
                
            if attempt < self.config.max_retries - 1:
                time.sleep(self.config.retry_delay)
        
        return False
    
    def _send_message(self, msg: MIMEMultipart):
        """Envia mensagem via SMTP com configurações otimizadas"""
        # Criar contexto SSL seguro
        context = ssl.create_default_context()
        
        # Tentar diferentes portas e métodos
        if self.config.smtp_port == 587:
            # STARTTLS
            with smtplib.SMTP(self.config.smtp_server, self.config.smtp_port, timeout=30) as server:
                server.ehlo()
                server.starttls(context=context)
                server.ehlo()
                server.login(self.config.sender, self.config.password)
                server.send_message(msg)
                
        elif self.config.smtp_port == 465:
            # SSL direto
            with smtplib.SMTP_SSL(self.config.smtp_server, self.config.smtp_port, context=context, timeout=30) as server:
                server.ehlo()
                server.login(self.config.sender, self.config.password)
                server.send_message(msg)
                
        else:
            # Porta customizada
            with smtplib.SMTP(self.config.smtp_server, self.config.smtp_port, timeout=30) as server:
                if self.config.use_tls:
                    server.starttls(context=context)
                server.login(self.config.sender, self.config.password)
                server.send_message(msg)
    
    def _attach_file(self, msg: MIMEMultipart, file_path: str):
        """Anexa arquivo ao email"""
        try:
            with open(file_path, "rb") as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
                
            encoders.encode_base64(part)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename= {os.path.basename(file_path)}'
            )
            msg.attach(part)
            
        except Exception as e:
            self.logger.warning(f"Não foi possível anexar arquivo {file_path}: {e}")


class Office365Provider(EmailProvider):
    """Provedor para Office 365 com App Password"""
    
    def __init__(self, config: EmailConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        # Forçar configurações específicas do Office 365
        self.config.smtp_server = "smtp.office365.com"
        self.config.smtp_port = 587
        self.config.use_tls = True
    
    def send(self, subject: str, body: str, attachments: List[str] = None) -> bool:
        """Envia email via Office 365"""
        # Usar o SMTPProvider com configurações do Office 365
        smtp_provider = SMTPProvider(self.config)
        return smtp_provider.send(subject, body, attachments)


class EmailService:
    """Serviço principal de email com suporte a múltiplos provedores"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.providers: List[EmailProvider] = []
        self._setup_providers()
    
    def _setup_providers(self):
        """Configura provedores disponíveis baseado nas variáveis de ambiente"""
        # Configuração base
        base_config = EmailConfig(
            sender=os.getenv("EMAIL_SENDER", ""),
            recipient=os.getenv("EMAIL_RECIPIENT", ""),
            smtp_server=os.getenv("SMTP_SERVER", "smtp.office365.com"),
            smtp_port=int(os.getenv("SMTP_PORT", "587")),
            password=os.getenv("EMAIL_PASSWORD", ""),
            app_password=os.getenv("EMAIL_APP_PASSWORD", ""),
            use_tls=True
        )
        
        # Se tem app password, adicionar Office365Provider primeiro
        if base_config.app_password:
            self.logger.info("Configurando Office365Provider com App Password")
            office_config = EmailConfig(
                sender=base_config.sender,
                recipient=base_config.recipient,
                smtp_server="smtp.office365.com",
                smtp_port=587,
                password=base_config.app_password,  # Usar app password
                use_tls=True
            )
            self.providers.append(Office365Provider(office_config))
        
        # Adicionar provider SMTP padrão como fallback
        if base_config.password:
            self.logger.info("Configurando SMTPProvider padrão")
            self.providers.append(SMTPProvider(base_config))
    
    def send_notification(self, subject: str, body: str, attachments: List[str] = None) -> bool:
        """
        Envia notificação tentando todos os provedores configurados
        
        Args:
            subject: Assunto do email
            body: Corpo HTML do email
            attachments: Lista de arquivos para anexar
            
        Returns:
            bool: True se algum provider conseguiu enviar
        """
        if not self.providers:
            self.logger.error("Nenhum provedor de email configurado")
            return False
        
        for i, provider in enumerate(self.providers):
            provider_name = provider.__class__.__name__
            self.logger.info(f"Tentando enviar com {provider_name} ({i+1}/{len(self.providers)})")
            
            try:
                if provider.send(subject, body, attachments):
                    self.logger.info(f"Email enviado com sucesso via {provider_name}")
                    return True
            except Exception as e:
                self.logger.error(f"Falha no provider {provider_name}: {e}")
        
        self.logger.error("Todos os provedores falharam ao enviar email")
        return False
    
    def test_connection(self) -> Dict[str, bool]:
        """Testa conexão com todos os provedores configurados"""
        results = {}
        
        for provider in self.providers:
            provider_name = provider.__class__.__name__
            try:
                # Tentar enviar email de teste
                success = provider.send(
                    "Teste de Conexão - I-Club Automation",
                    "<p>Este é um email de teste da automação I-Club.</p>",
                    []
                )
                results[provider_name] = success
            except Exception as e:
                self.logger.error(f"Erro ao testar {provider_name}: {e}")
                results[provider_name] = False
        
        return results


# Função helper para manter compatibilidade
def send_notification_email(subject: str, body: str) -> bool:
    """
    Função de compatibilidade para o código existente
    
    Args:
        subject: Assunto do email
        body: Corpo HTML do email
        
    Returns:
        bool: True se enviado com sucesso
    """
    service = EmailService()
    return service.send_notification(subject, body)
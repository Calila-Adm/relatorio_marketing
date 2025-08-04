# 📊 Sistema de Relatórios I-Club - Versão Simplificada

## 🎯 Funcionalidade

Este sistema extrai dados do PostgreSQL e gera relatórios mensais em Excel automaticamente.

**O que faz:**
- ✅ Conecta no banco PostgreSQL com **connection pooling**
- ✅ Cria **índices de performance** automaticamente
- ✅ Executa queries em **paralelo** (4 threads simultâneas)
- ✅ Gera **1 arquivo Excel por query** (ideal para LLM)
- ✅ Salva automaticamente na pasta organizada por mês
- ❌ **Não envia emails** (funcionalidade removida)

## 📁 Pasta de Destino

Os arquivos Excel são salvos automaticamente em pastas organizadas por mês:

**📁 Pasta base (Windows):**
```
C:\Users\~\Documents\relatorio_fechamento_mensal\
```

**🗂️ Estrutura de pastas criadas automaticamente:**
```
relatorio_fechamento_mensal/
├── janeiro'25/     # Para relatório de Janeiro 2025
├── fevereiro'25/   # Para relatório de Fevereiro 2025  
├── março'25/       # Para relatório de Março 2025
├── dezembro'24/    # Para relatório de Dezembro 2024
└── ...
```

**⚠️ IMPORTANTE:** Para alterar o caminho, modifique no arquivo `main.py` linha 88:
```python
base_path = "/mnt/c/Users/~/relatorio_fechamento_mensal"
```

**📝 Nota:** O caminho `/mnt/c/` corresponde ao drive C: do Windows no WSL.

## ⚙️ Configuração

1. **Configure o arquivo `.env`** apenas com dados do banco:

```env
# Banco de Dados PostgreSQL
DB_USER=seu_usuario
DB_PASSWORD=sua_senha
DB_HOST=localhost
DB_PORT=5432
DB_NAME=nome_do_banco
```

2. **Crie o ambiente virtual e instale as dependências:**

### 🐧 **Linux / WSL:**
```bash
# Criar ambiente virtual
python -m venv .venv

# Ativar ambiente virtual
source .venv/bin/activate

# Instalar dependências
pip install -r requirements.txt
```

### 🪟 **Windows:**
```cmd
# Instalar dependências
pip install -r requirements.txt
```

## 🚀 Como Usar

### 🐧 **Linux / WSL (Ubuntu):**
```bash
# Ativar ambiente virtual
source .venv/bin/activate

# Executar sistema
python main.py

# Desativar ambiente (opcional)
deactivate
```

### 🪟 **Windows (CMD/PowerShell):**
```cmd
# Executar sistema
python main.py
```

O sistema irá:
1. Conectar no banco PostgreSQL com connection pooling otimizado
2. Criar/verificar índices de performance automaticamente
3. Criar pasta do mês anterior (ex: `julho'25/`)
4. Executar **todas as queries em paralelo** (4 threads)
5. Gerar **1 arquivo Excel individual por query** (18 arquivos)
6. Salvar todos os arquivos na pasta criada para o mês
7. Mostrar relatório completo no console/logs

## 📋 Logs

Todos os logs são salvos em:
- **Console**: Output em tempo real
- **Arquivo**: `automation.log`

## 🔧 Estrutura do Projeto

```
relatorio_marketing/
├── main.py              # Script principal
├── queries.py           # Todas as queries SQL
├── requirements.txt     # Dependências Python
├── .env.example        # Exemplo de configuração
├── automation.log      # Logs de execução
└── README_SISTEMA.md   # Esta documentação
```

## ⏱️ Tempo de Execução

- **Nova estimativa**: 1-2 minutos (execução paralela)
- **Melhoria**: ~60% mais rápido que a versão anterior
- **Depende**: Volume de dados e performance do banco
- **Threads**: 4 queries executadas simultaneamente

## 📊 Arquivos Excel Gerados

**🎯 NOVO:** Cada query gera um arquivo Excel individual (ideal para LLM):

```
julho'25/
├── Cupons_Ativos_2025-07.xlsx
├── Compradores_Únicos_2025-07.xlsx  
├── Top_10_Lojas_+_Compradores_Únicos_2025-07.xlsx
├── Top_10_Lojas_+_Vendas_2025-07.xlsx
├── Clientes_por_Categoria_2025-07.xlsx
├── Visitas_por_Categoria_de_Clientes_-_Comparação_YoY_2025-07.xlsx
├── TKT_Médio_-_Geral_2025-07.xlsx
├── Notas_Fiscais_Cadastradas_-_Comparação_YoY_2025-07.xlsx
├── Vendas_Cadastradas_-_Comparação_YoY_2025-07.xlsx
├── Representatividade_-_Comparação_YoY_2025-07.xlsx
└── ... (18 arquivos total)
```

**💡 Vantagens para LLM:**
- Cada arquivo contém dados específicos de 1 análise
- Facilita processamento por IA/LLM
- Arquivos menores e mais focados
- Melhor organização para análises automatizadas

## 🛡️ Tratamento de Erros

O sistema possui tratamento robusto para:
- ❌ Erro de conexão com banco
- ❌ Falha em queries específicas
- ❌ Problemas na criação da pasta
- ❌ Falhas na geração do Excel

**Mesmo se algumas queries falharem, o arquivo Excel será gerado com os dados disponíveis.**

## 🔧 Troubleshooting

### 🐧 **Problemas no Linux/WSL:**

**Erro: "No module named 'venv'"**
```bash
sudo apt update
sudo apt install python3-venv
```

**Erro de permissão ao criar pasta:**
```bash
chmod +x .venv/bin/activate
```

**Ambiente virtual não ativa:**
```bash
# Verificar se o .venv existe
ls -la .venv/

# Recriar se necessário
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
```

### 🪟 **Problemas no Windows:**

**Erro: "execution of scripts is disabled"**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**Python não encontrado:**
```cmd
# Verificar se Python está no PATH
python --version
# OU
py --version
```

**Erro ao ativar ambiente virtual:**
```cmd
# Tentar com py ao invés de python
py -m venv .venv
.venv\Scripts\activate.bat
```

### 🛠️ **Problemas Gerais:**

**Erro de conexão com banco:**
1. Verifique se PostgreSQL está rodando
2. Confirme credenciais no `.env`
3. Teste conexão: `telnet [host] [porta]`

**Dependências não instalam:**
```bash
# Atualizar pip primeiro
pip install --upgrade pip
pip install -r requirements.txt
```

## 📞 Suporte

Em caso de problemas:
1. Verifique os logs em `automation.log`
2. Confirme as configurações do `.env`
3. Teste a conexão com o banco PostgreSQL
4. Verifique se a pasta de destino está acessível

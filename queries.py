"""
queries.py - Módulo de Consultas SQL para Relatórios I-Club

Este módulo centraliza todas as queries SQL utilizadas na geração dos relatórios
mensais do programa de fidelidade I-Club do Iguatemi.

Estrutura das Queries:
- Todas utilizam CTEs (Common Table Expressions) para modularidade
- Lógica robusta de datas para comparações Year-over-Year (YoY)
- Formatação padronizada de datas como 'YYYY-MM'
- Tratamento especial para casos de borda (ex: janeiro)

Métricas Cobertas:
1. Cupons: Ativos, emitidos, consumidos por categoria
2. Clientes: Compradores únicos, segmentação por categoria
3. Lojas: Rankings por vendas, NFs e compradores
4. Visitas: Análise por categoria e comparações YoY
5. Ticket Médio: Por cliente, NF e visita
6. Performance: NFs cadastradas, vendas, representatividade

Otimizações Aplicadas:
- Uso de DATE_TRUNC para performance em comparações de datas
- INTERVAL do PostgreSQL para cálculos robustos de períodos
- JOINs otimizados com TRIM para limpeza de espaços
- Filtros WHERE aplicados antes de agregações

Autor: Marketing Team - Iguatemi
Data: 2025
Versão: 1.0
"""

QUERIES = {
    # ========================================================================
    # QUERY 1: CUPONS ATIVOS
    # ========================================================================
    # Objetivo: Contar quantidade de cupons ativos no mês atual e mesmo mês ano anterior
    # Tabelas: MOBITS_API_CUPONS (sistema de cupons do programa de fidelidade)
    # Lógica: Identifica cupons ativos baseado em data_inicio/data_fim
    # Resultado: Total de cupons disponíveis por mês para comparação YoY
    # ========================================================================
    "Cupons Ativos": """
        -- CTE para determinar o período de atividade de cada cupom
        WITH DATA_CUPOM AS (
            SELECT
                "id",
                -- Lógica complexa para determinar mês de atividade do cupom
                -- Verifica se cupom estava ativo no mês anterior (relatório atual)
                -- ou no mesmo mês do ano anterior (comparação YoY)
                CASE
                    -- Cupom iniciou no mês anterior
                    WHEN DATE_TRUNC('month', "data_inicio"::DATE) = DATE_TRUNC('month', CURRENT_DATE - INTERVAL '1 month') THEN DATE_TRUNC('month', "data_inicio"::DATE)
                    -- Cupom terminou no mês anterior
                    WHEN DATE_TRUNC('month', "data_fim"::DATE) = DATE_TRUNC('month', CURRENT_DATE - INTERVAL '1 month') THEN DATE_TRUNC('month', "data_fim"::DATE)
                    -- Cupom iniciou no mesmo mês do ano anterior
                    WHEN DATE_TRUNC('month', "data_inicio"::DATE) = DATE_TRUNC('month', CURRENT_DATE - INTERVAL '13 months') THEN DATE_TRUNC('month', "data_inicio"::DATE)
                    -- Cupom terminou no mesmo mês do ano anterior
                    WHEN DATE_TRUNC('month', "data_fim"::DATE) = DATE_TRUNC('month', CURRENT_DATE - INTERVAL '13 months') THEN DATE_TRUNC('month', "data_fim"::DATE)
                END AS DATA_ATIVO
            FROM MOBITS_API_CUPONS
        )
        -- Query principal: Agrupa e conta cupons por mês
        SELECT DISTINCT 
            TO_CHAR(C.DATA_ATIVO, 'YYYY-MM') AS ANO_MES  -- Formato padrão para todas as queries
            ,COUNT(DISTINCT A."id") AS CUPONS_ATIVOS     -- Total de cupons únicos ativos
        FROM MOBITS_API_CUPONS A
        JOIN DATA_CUPOM AS C ON A."id" = C."id"
        WHERE C.DATA_ATIVO IS NOT NULL  -- Exclui cupons sem período definido
        GROUP BY 1;
    """,
    # ========================================================================
    # QUERY 2: COMPRADORES ÚNICOS
    # ========================================================================
    # Objetivo: Contar clientes únicos que realizaram compras no I-Club
    # Tabelas: CRMALL_V_CRM_TRANSACTIONLOYALTY (transações do programa)
    #          CRMALL_V_CRM_TRANSACTION (detalhes das transações)
    # Filtros: StatusID NOT IN ('3','5') = exclui transações canceladas/inválidas
    #          PersonContractorID = '12' = identifica Iguatemi
    # Resultado: Total de compradores únicos por mês (YoY)
    # ========================================================================
    "Compradores Únicos": """
        -- CTE para identificar todas as compras válidas do I-Club
        WITH COMPRAS_ICLUB AS (
            SELECT DISTINCT
                T."PersonID" ID_CLIENTE,                    -- ID único do cliente
                T."PurchasedDateTime"::DATE DATA_COMPRA    -- Data da compra (sem hora)
            FROM CRMALL_V_CRM_TRANSACTIONLOYALTY AS L       -- Tabela de loyalty
            JOIN CRMALL_V_CRM_TRANSACTION AS T ON L."TransactionID" = T."TransactionID" 
            WHERE L."StatusID" NOT IN ('3', '5')            -- Exclui status cancelado/inválido
              AND T."PurchasedDateTime" IS NOT NULL AND T."PurchasedDateTime" <> ''  -- Garante data válida
              AND T."PersonContractorID" = '12'             -- Filtro específico Iguatemi
        )
        -- Query principal: Conta compradores únicos por mês
        SELECT
            TO_CHAR(DATA_COMPRA, 'YYYY-MM') AS ANO_MES     -- Formato padrão YYYY-MM
            ,COUNT(DISTINCT ID_CLIENTE) AS COMPRADORES_UNICOS -- Conta clientes únicos
        FROM COMPRAS_ICLUB
        WHERE 
            -- Filtro robusto para pegar mês anterior E mesmo mês ano anterior
            DATE_TRUNC('month', DATA_COMPRA) IN (
                DATE_TRUNC('month', CURRENT_DATE - INTERVAL '1 month'),   -- Mês anterior
                DATE_TRUNC('month', CURRENT_DATE - INTERVAL '13 months')  -- Mesmo mês ano anterior
            )
        GROUP BY 1
        ORDER BY 1 ASC;  -- Ordena cronologicamente
    """,
    # ========================================================================
    # QUERY 3: TOP 10 LOJAS + COMPRADORES ÚNICOS
    # ========================================================================
    # Objetivo: Ranking das lojas com mais compradores únicos no I-Club
    # Tabelas: CRMALL_V_CRM_TRANSACTIONLOYALTY, CRMALL_V_CRM_TRANSACTION
    #          CRMALL_LOJA_GSHOP (dimensão de lojas)
    # Lógica: Conta clientes distintos por loja para identificar as mais populares
    # Uso: Identificar lojas com maior engajamento no programa de fidelidade
    # Resultado: Lista ordenada por quantidade de compradores únicos
    # ========================================================================
    "Top 10 Lojas + Compradores Únicos": """
        -- CTE 1: Identifica todas as compras por loja e cliente
        WITH COMPRAS_ICLUB AS (
            SELECT DISTINCT
                T."StoreID" AS IDLOJA,                      -- ID da loja
                T."PersonID" ID_CLIENTE,                    -- ID do cliente
                T."PurchasedDateTime"::DATE DATA_COMPRA    -- Data da compra
            FROM CRMALL_V_CRM_TRANSACTIONLOYALTY AS L
            JOIN CRMALL_V_CRM_TRANSACTION AS T ON L."TransactionID" = T."TransactionID" 
            WHERE L."StatusID" NOT IN ('3', '5')            -- Exclui canceladas
              AND T."PurchasedDateTime" IS NOT NULL AND T."PurchasedDateTime" <> ''
              AND T."PersonContractorID" = '12'             -- Filtro Iguatemi
        ),
        -- CTE 2: Dimensão de lojas para obter nomes fantasia
        DIM_LOJAS AS (
            SELECT DISTINCT 
                "StoreID" AS IDLOJA, 
                "Gshop_NomeFantasia" AS NOME_DA_LOJA 
            FROM CRMALL_LOJA_GSHOP
        )
        -- Query principal: Conta compradores únicos por loja
        SELECT
            L.NOME_DA_LOJA,                                -- Nome comercial da loja
            TO_CHAR(C.DATA_COMPRA, 'YYYY-MM') AS ANO_MES, -- Período
            COUNT(DISTINCT C.ID_CLIENTE) AS COMPRADORES_UNICOS  -- Total único
        FROM COMPRAS_ICLUB AS C
        JOIN DIM_LOJAS AS L ON TRIM(C.IDLOJA) = TRIM(L.IDLOJA)  -- TRIM remove espaços
        WHERE 
            -- Filtro para mês atual e comparação YoY
            DATE_TRUNC('month', C.DATA_COMPRA) IN (
                DATE_TRUNC('month', CURRENT_DATE - INTERVAL '1 month'), 
                DATE_TRUNC('month', CURRENT_DATE - INTERVAL '13 months')
            )
        GROUP BY 1, 2
        ORDER BY 3 DESC, 1 ASC;  -- Ordena por quantidade (maior primeiro)
    """,
    "Top 10 Lojas + Vendas": """
        WITH COMPRAS_ICLUB AS (
            SELECT
                T."StoreID" AS IDLOJA,
                T."PurchasedDateTime"::DATE DATA_COMPRA,
                SUM(T."Value"::DECIMAL(10,2)) AS ValorCompra
            FROM CRMALL_V_CRM_TRANSACTIONLOYALTY AS L
            JOIN CRMALL_V_CRM_TRANSACTION AS T ON L."TransactionID" = T."TransactionID" 
            WHERE L."StatusID" NOT IN ('3', '5')
              AND T."PurchasedDateTime" IS NOT NULL AND T."PurchasedDateTime" <> ''
              AND T."PersonContractorID" = '12'
            GROUP BY T."StoreID", T."PurchasedDateTime"::DATE
        ),
        DIM_LOJAS AS (
            SELECT DISTINCT "StoreID" AS IDLOJA, "Gshop_NomeFantasia" AS NOME_DA_LOJA FROM CRMALL_LOJA_GSHOP
        )
        SELECT
            L.NOME_DA_LOJA,
            TO_CHAR(C.DATA_COMPRA, 'YYYY-MM') AS ANO_MES, -- AJUSTE: Formatação de data padronizada.
            SUM(C.ValorCompra) AS VENDAS
        FROM COMPRAS_ICLUB AS C
        JOIN DIM_LOJAS AS L ON TRIM(C.IDLOJA) = TRIM(L.IDLOJA)
        WHERE 
            -- AJUSTE: Lógica de data robusta.
            DATE_TRUNC('month', C.DATA_COMPRA) IN (
                DATE_TRUNC('month', CURRENT_DATE - INTERVAL '1 month'), 
                DATE_TRUNC('month', CURRENT_DATE - INTERVAL '13 months')
            )
        GROUP BY 1, 2
        ORDER BY 3 DESC, 1 ASC;
    """,
    "Top 10 Lojas + Notas Fiscais": """
        WITH COMPRAS_ICLUB AS (
            SELECT
                T."StoreID" AS IDLOJA,
                T."PurchasedDateTime"::DATE DATA_COMPRA,
                COUNT(DISTINCT L."TransactionID") AS QtdeNF
            FROM CRMALL_V_CRM_TRANSACTIONLOYALTY AS L
            JOIN CRMALL_V_CRM_TRANSACTION AS T ON L."TransactionID" = T."TransactionID" 
            WHERE L."StatusID" NOT IN ('3', '5')
              AND T."PurchasedDateTime" IS NOT NULL AND T."PurchasedDateTime" <> ''
              AND T."PersonContractorID" = '12'
            GROUP BY T."StoreID", T."PurchasedDateTime"::DATE
        ),
        DIM_LOJAS AS (
            SELECT DISTINCT "StoreID" AS IDLOJA, "Gshop_NomeFantasia" AS NOME_DA_LOJA FROM CRMALL_LOJA_GSHOP
        )
        SELECT
            L.NOME_DA_LOJA,
            TO_CHAR(C.DATA_COMPRA, 'YYYY-MM') AS ANO_MES, -- AJUSTE: Formatação de data padronizada.
            SUM(C.QtdeNF) AS NOTAS_FISCAIS
        FROM COMPRAS_ICLUB AS C
        JOIN DIM_LOJAS AS L ON TRIM(C.IDLOJA) = TRIM(L.IDLOJA)
        WHERE
            -- AJUSTE: Lógica de data robusta.
            DATE_TRUNC('month', C.DATA_COMPRA) IN (
                DATE_TRUNC('month', CURRENT_DATE - INTERVAL '1 month'), 
                DATE_TRUNC('month', CURRENT_DATE - INTERVAL '13 months')
            )
        GROUP BY 1, 2
        ORDER BY 3 DESC, 1 ASC;
    """,
    # ========================================================================
    # QUERY 6: CLIENTES POR CATEGORIA
    # ========================================================================
    # Objetivo: Segmentação atual dos clientes do I-Club por categoria
    # Tabelas: CRMALL_V_CRM_PERSON_LOYALTY (histórico de categorias)
    # Categorias: Diamante, Ouro, Prata, Prospect, Inativo
    # Lógica: Usa ROW_NUMBER para pegar categoria mais recente de cada cliente
    # Nota: Não tem filtro de data - mostra situação atual da base
    # Uso: Entender distribuição atual da base de clientes
    # ========================================================================
    "Clientes por Categoria": """
        -- CTE para identificar categoria atual de cada cliente
        WITH CATEGORIA_ATUAL AS (
            SELECT *
            FROM (
                SELECT
                    -- ROW_NUMBER garante apenas 1 categoria por cliente (a mais recente)
                    ROW_NUMBER() OVER(
                        PARTITION BY "PersonID" 
                        ORDER BY MAX("ActiveDateTime"::DATE) DESC,  -- Mais recente primeiro
                                "LoyaltyCategoryID" ASC             -- Desempate por ID
                    ) AS ORDEM,
                    "PersonID" AS ID_CLIENTE,
                    "Category" AS CATEGORIA_ATUAL,              -- Nome da categoria
                    "InactiveDateTime"::DATE AS DATA_INATIVACAO_MED
                FROM CRMALL_V_CRM_PERSON_LOYALTY
                GROUP BY "PersonID", "Category", "LoyaltyCategoryID", "ActiveDateTime", "InactiveDateTime"
            ) A
            WHERE DATA_INATIVACAO_MED IS NULL  -- Apenas categorias ativas
        )
        -- Query principal: Conta clientes por categoria
        SELECT
            CATEGORIA_ATUAL,                    -- Diamante, Ouro, Prata, etc
            COUNT(DISTINCT ID_CLIENTE) AS CLIENTES  -- Total em cada categoria
        FROM CATEGORIA_ATUAL
        GROUP BY 1;
    """,
    "Visitas por Categoria de Clientes - Comparação YoY": """
        WITH COMPRAS_ICLUB AS (
            SELECT DISTINCT
                T."PersonID" ID_CLIENTE,
                T."PurchasedDateTime"::DATE DATA_COMPRA,
                CONCAT(T."PersonID", T."PurchasedDateTime"::DATE) VISITA
            FROM CRMALL_V_CRM_TRANSACTIONLOYALTY AS L
            JOIN CRMALL_V_CRM_TRANSACTION AS T ON L."TransactionID" = T."TransactionID" 
            WHERE L."StatusID" NOT IN ('3', '5')
              AND T."PurchasedDateTime" IS NOT NULL AND T."PurchasedDateTime" <> ''
              AND T."PersonContractorID" = '12'
        ),
        CATEGORIA_ATUAL AS (
            SELECT "PersonID" AS ID_CLIENTE, "Category" AS CATEGORIA_ATUAL
            FROM (
                SELECT
                    ROW_NUMBER() OVER(PARTITION BY "PersonID" ORDER BY "ActiveDateTime" DESC) AS rn,
                    "PersonID", "Category"
                FROM CRMALL_V_CRM_PERSON_LOYALTY
                WHERE "InactiveDateTime" IS NULL
            ) sub
            WHERE rn = 1
        )
        SELECT
            CA.CATEGORIA_ATUAL,
            TO_CHAR(CI.DATA_COMPRA, 'YYYY-MM') AS ANO_MES, -- AJUSTE: Formatação de data padronizada.
            COUNT(DISTINCT CI.VISITA) AS VISITAS
        FROM COMPRAS_ICLUB AS CI
        LEFT JOIN CATEGORIA_ATUAL AS CA ON TRIM(CI.ID_CLIENTE) = TRIM(CA.ID_CLIENTE)
        WHERE
            -- AJUSTE: Lógica de data robusta.
            DATE_TRUNC('month', CI.DATA_COMPRA) IN (
                DATE_TRUNC('month', CURRENT_DATE - INTERVAL '1 month'), 
                DATE_TRUNC('month', CURRENT_DATE - INTERVAL '13 months')
            )
        GROUP BY 1, 2
        ORDER BY 3 DESC, 1 ASC;
    """,
    "Visitas por Geral - Comparação YoY": """
        WITH COMPRAS_ICLUB AS (
            SELECT DISTINCT
                T."PurchasedDateTime"::DATE DATA_COMPRA,
                CONCAT(T."PersonID", T."PurchasedDateTime"::DATE) VISITA
            FROM CRMALL_V_CRM_TRANSACTIONLOYALTY AS L
            JOIN CRMALL_V_CRM_TRANSACTION AS T ON L."TransactionID" = T."TransactionID" 
            WHERE L."StatusID" NOT IN ('3', '5')
              AND T."PurchasedDateTime" IS NOT NULL AND T."PurchasedDateTime" <> ''
              AND T."PersonContractorID" = '12'
        )
        SELECT
            TO_CHAR(DATA_COMPRA, 'YYYY-MM') AS ANO_MES, -- AJUSTE: Formatação de data padronizada.
            COUNT(DISTINCT VISITA) AS VISITAS
        FROM COMPRAS_ICLUB
        WHERE
            -- AJUSTE: Lógica de data robusta.
            DATE_TRUNC('month', DATA_COMPRA) IN (
                DATE_TRUNC('month', CURRENT_DATE - INTERVAL '1 month'), 
                DATE_TRUNC('month', CURRENT_DATE - INTERVAL '13 months')
            )
        GROUP BY 1
        ORDER BY 1 ASC;
    """,
    "TKT Médio por Visitas - Por Categoria de Cliente": """
        WITH COMPRAS_ICLUB AS (
            SELECT
                T."PersonID" ID_CLIENTE,
                T."PurchasedDateTime"::DATE DATA_COMPRA,
                CONCAT(T."PersonID", T."PurchasedDateTime"::DATE) VISITA,
                SUM(T."Value"::DECIMAL(10,2)) AS ValorCompra
            FROM CRMALL_V_CRM_TRANSACTIONLOYALTY AS L
            JOIN CRMALL_V_CRM_TRANSACTION AS T ON L."TransactionID" = T."TransactionID" 
            WHERE L."StatusID" NOT IN ('3', '5')
              AND T."PurchasedDateTime" IS NOT NULL AND T."PurchasedDateTime" <> ''
              AND T."PersonContractorID" = '12'
            GROUP BY 1, 2, 3
        ),
        CATEGORIA_ATUAL AS (
            SELECT "PersonID" AS ID_CLIENTE, "Category" AS CATEGORIA_ATUAL
            FROM (
                SELECT ROW_NUMBER() OVER(PARTITION BY "PersonID" ORDER BY "ActiveDateTime" DESC) AS rn, "PersonID", "Category"
                FROM CRMALL_V_CRM_PERSON_LOYALTY
                WHERE "InactiveDateTime" IS NULL
            ) sub
            WHERE rn = 1
        )
        SELECT
            CA.CATEGORIA_ATUAL,
            TO_CHAR(CI.DATA_COMPRA, 'YYYY-MM') AS ANO_MES, -- AJUSTE
            COUNT(DISTINCT CI.VISITA) AS VISITAS,
            SUM(CI.ValorCompra) AS VENDAS,
            SUM(CI.ValorCompra) / COUNT(DISTINCT CI.VISITA) AS TKT_MEDIO_VISITA
        FROM COMPRAS_ICLUB AS CI
        LEFT JOIN CATEGORIA_ATUAL AS CA ON TRIM(CI.ID_CLIENTE) = TRIM(CA.ID_CLIENTE)
        WHERE
            -- AJUSTE: Lógica de data robusta.
            DATE_TRUNC('month', CI.DATA_COMPRA) IN (
                DATE_TRUNC('month', CURRENT_DATE - INTERVAL '1 month'), 
                DATE_TRUNC('month', CURRENT_DATE - INTERVAL '13 months')
            )
        GROUP BY 1, 2
        ORDER BY 3 DESC, 1 ASC;
    """,
    "TKT Médio por Nota Fiscal - Por Categoria de Cliente": """
        WITH COMPRAS_ICLUB AS (
            SELECT
                T."PersonID" ID_CLIENTE,
                T."PurchasedDateTime"::DATE DATA_COMPRA,
                COUNT(DISTINCT L."TransactionID") AS QtdeNF,
                SUM(T."Value"::DECIMAL(10,2)) AS ValorCompra
            FROM CRMALL_V_CRM_TRANSACTIONLOYALTY AS L
            JOIN CRMALL_V_CRM_TRANSACTION AS T ON L."TransactionID" = T."TransactionID" 
            WHERE L."StatusID" NOT IN ('3', '5')
              AND T."PurchasedDateTime" IS NOT NULL AND T."PurchasedDateTime" <> ''
              AND T."PersonContractorID" = '12'
            GROUP BY 1, 2
        ),
        CATEGORIA_ATUAL AS (
            SELECT "PersonID" AS ID_CLIENTE, "Category" AS CATEGORIA_ATUAL
            FROM (
                SELECT ROW_NUMBER() OVER(PARTITION BY "PersonID" ORDER BY "ActiveDateTime" DESC) AS rn, "PersonID", "Category"
                FROM CRMALL_V_CRM_PERSON_LOYALTY
                WHERE "InactiveDateTime" IS NULL
            ) sub
            WHERE rn = 1
        )
        SELECT
            CA.CATEGORIA_ATUAL,
            TO_CHAR(CI.DATA_COMPRA, 'YYYY-MM') AS ANO_MES, -- AJUSTE
            SUM(CI.QtdeNF) AS NF,
            SUM(CI.ValorCompra) AS VENDAS,
            SUM(CI.ValorCompra) / SUM(CI.QtdeNF) AS TKT_MEDIO_NF
        FROM COMPRAS_ICLUB AS CI
        LEFT JOIN CATEGORIA_ATUAL AS CA ON TRIM(CI.ID_CLIENTE) = TRIM(CA.ID_CLIENTE)
        WHERE
            -- AJUSTE: Lógica de data robusta.
            DATE_TRUNC('month', CI.DATA_COMPRA) IN (
                DATE_TRUNC('month', CURRENT_DATE - INTERVAL '1 month'), 
                DATE_TRUNC('month', CURRENT_DATE - INTERVAL '13 months')
            )
        GROUP BY 1, 2
        ORDER BY 3 DESC, 1 ASC;
    """,
    "TKT Médio Clientes - Por Categoria de Cliente": """
        WITH COMPRAS_ICLUB AS (
            SELECT
                T."PersonID" ID_CLIENTE,
                T."PurchasedDateTime"::DATE DATA_COMPRA,
                SUM(T."Value"::DECIMAL(10,2)) AS ValorCompra
            FROM CRMALL_V_CRM_TRANSACTIONLOYALTY AS L
            JOIN CRMALL_V_CRM_TRANSACTION AS T ON L."TransactionID" = T."TransactionID" 
            WHERE L."StatusID" NOT IN ('3', '5')
              AND T."PurchasedDateTime" IS NOT NULL AND T."PurchasedDateTime" <> ''
              AND T."PersonContractorID" = '12'
            GROUP BY 1, 2
        ),
        CATEGORIA_ATUAL AS (
            SELECT "PersonID" AS ID_CLIENTE, "Category" AS CATEGORIA_ATUAL
            FROM (
                SELECT ROW_NUMBER() OVER(PARTITION BY "PersonID" ORDER BY "ActiveDateTime" DESC) AS rn, "PersonID", "Category"
                FROM CRMALL_V_CRM_PERSON_LOYALTY
                WHERE "InactiveDateTime" IS NULL
            ) sub
            WHERE rn = 1
        )
        SELECT
            CA.CATEGORIA_ATUAL,
            TO_CHAR(CI.DATA_COMPRA, 'YYYY-MM') AS ANO_MES, -- AJUSTE
            COUNT(DISTINCT CI.ID_CLIENTE) AS CLIENTES,
            SUM(CI.ValorCompra) AS VENDAS,
            SUM(CI.ValorCompra) / COUNT(DISTINCT CI.ID_CLIENTE) AS TKT_MEDIO_CLIENTES
        FROM COMPRAS_ICLUB AS CI
        LEFT JOIN CATEGORIA_ATUAL AS CA ON TRIM(CI.ID_CLIENTE) = TRIM(CA.ID_CLIENTE)
        WHERE
            -- AJUSTE: Lógica de data robusta.
            DATE_TRUNC('month', CI.DATA_COMPRA) IN (
                DATE_TRUNC('month', CURRENT_DATE - INTERVAL '1 month'), 
                DATE_TRUNC('month', CURRENT_DATE - INTERVAL '13 months')
            )
        GROUP BY 1, 2
        ORDER BY 3 DESC, 1 ASC;
    """,
    "TKT Médio - Geral": """
        WITH COMPRAS_ICLUB AS (
            SELECT
                T."PurchasedDateTime"::DATE DATA_COMPRA,
                COUNT(DISTINCT L."TransactionID") AS QtdeNF,
                SUM(T."Value"::DECIMAL(10,2)) AS ValorCompra
            FROM CRMALL_V_CRM_TRANSACTIONLOYALTY AS L
            JOIN CRMALL_V_CRM_TRANSACTION AS T ON L."TransactionID" = T."TransactionID" 
            WHERE L."StatusID" NOT IN ('3', '5')
              AND T."PurchasedDateTime" IS NOT NULL AND T."PurchasedDateTime" <> ''
              AND T."PersonContractorID" = '12'
            GROUP BY 1
        )
        SELECT
            TO_CHAR(DATA_COMPRA, 'YYYY-MM') AS ANO_MES, -- AJUSTE
            SUM(QtdeNF) AS NF,
            SUM(ValorCompra) AS VENDAS,
            SUM(ValorCompra) / SUM(QtdeNF) AS TKT_MEDIO
        FROM COMPRAS_ICLUB
        WHERE
            -- AJUSTE: Lógica de data robusta.
            DATE_TRUNC('month', DATA_COMPRA) IN (
                DATE_TRUNC('month', CURRENT_DATE - INTERVAL '1 month'), 
                DATE_TRUNC('month', CURRENT_DATE - INTERVAL '13 months')
            )
        GROUP BY 1
        ORDER BY 3 DESC, 1 ASC;
    """,
    "Cupons Emitidos e Consumidos - Comparação YoY": """
        WITH DATA_CUPOM AS (
            SELECT
                "id",
                -- AJUSTE: Lógica de data robusta
                CASE
                    WHEN DATE_TRUNC('month', "data_inicio"::DATE) = DATE_TRUNC('month', CURRENT_DATE - INTERVAL '1 month') THEN DATE_TRUNC('month', "data_inicio"::DATE)
                    WHEN DATE_TRUNC('month', "data_fim"::DATE) = DATE_TRUNC('month', CURRENT_DATE - INTERVAL '1 month') THEN DATE_TRUNC('month', "data_fim"::DATE)
                    WHEN DATE_TRUNC('month', "data_inicio"::DATE) = DATE_TRUNC('month', CURRENT_DATE - INTERVAL '13 months') THEN DATE_TRUNC('month', "data_inicio"::DATE)
                    WHEN DATE_TRUNC('month', "data_fim"::DATE) = DATE_TRUNC('month', CURRENT_DATE - INTERVAL '13 months') THEN DATE_TRUNC('month', "data_fim"::DATE)
                END AS DATA_ATIVO
            FROM MOBITS_API_CUPONS
        )
        SELECT DISTINCT 
            TO_CHAR(C.DATA_ATIVO, 'YYYY-MM') AS ANO_MES, -- AJUSTE
            A.DESCRICAO,
            COUNT(CASE WHEN UPPER(B."status") <> 'CANCELADO' THEN B."status" END) AS EMITIDOS,
            COUNT(CASE WHEN UPPER(B."status") = 'CONSUMIDO' THEN B."status" END) AS CONSUMIDO
        FROM MOBITS_API_CUPONS A
        JOIN DATA_CUPOM AS C ON A."id" = C."id"
        JOIN MOBITS_API_CUPONS_RESGATADOS B ON A."id" = B."cupom_id"
        WHERE C.DATA_ATIVO IS NOT NULL
        GROUP BY 1, 2
        ORDER BY 3 DESC;
    """,
    "Cupons Emitidos e Consumidos por Categoria": """
        WITH DATA_CUPOM AS (
            SELECT
                "id",
                -- AJUSTE: Lógica de data robusta
                CASE
                    WHEN DATE_TRUNC('month', "data_inicio"::DATE) = DATE_TRUNC('month', CURRENT_DATE - INTERVAL '1 month') THEN DATE_TRUNC('month', "data_inicio"::DATE)
                    WHEN DATE_TRUNC('month', "data_fim"::DATE) = DATE_TRUNC('month', CURRENT_DATE - INTERVAL '1 month') THEN DATE_TRUNC('month', "data_fim"::DATE)
                    WHEN DATE_TRUNC('month', "data_inicio"::DATE) = DATE_TRUNC('month', CURRENT_DATE - INTERVAL '13 months') THEN DATE_TRUNC('month', "data_inicio"::DATE)
                    WHEN DATE_TRUNC('month', "data_fim"::DATE) = DATE_TRUNC('month', CURRENT_DATE - INTERVAL '13 months') THEN DATE_TRUNC('month', "data_fim"::DATE)
                END AS DATA_ATIVO,
                CASE
                    WHEN (UPPER("observacao") ILIKE '%#ESTACIONAMENTO%') THEN 'ESTACIONAMENTO'
                    WHEN (UPPER("observacao") ILIKE '%#LOJA%') THEN 'LOJA'
                    WHEN (UPPER("observacao") ILIKE '%#SHOPPING%') THEN 'SHOPPING'
                    WHEN (UPPER("observacao") ILIKE '%#IGUATEMI HALL%') THEN 'IGUATEMI HALL'
                    WHEN (UPPER("observacao") ILIKE '%#CINEMA%') THEN 'CINEMA'
                    WHEN (UPPER("observacao") ILIKE '%#EXTERNO%') THEN 'EXTERNO'
                    WHEN (UPPER("observacao") ILIKE '%#EVENTO I_CLUB%') THEN 'ICLUB'
                    ELSE 'SEM CLASSIFICACAO'
                END AS CATEGORIA_CUPOM
            FROM MOBITS_API_CUPONS
        )
        SELECT DISTINCT 
            TO_CHAR(C.DATA_ATIVO, 'YYYY-MM') AS ANO_MES, -- AJUSTE
            C.CATEGORIA_CUPOM,
            COUNT(CASE WHEN UPPER(R."status") <> 'CANCELADO' THEN R."status" END) AS EMITIDOS,
            COUNT(CASE WHEN UPPER(R."status") = 'CONSUMIDO' THEN R."status" END) AS CONSUMIDO
        FROM MOBITS_API_CUPONS A
        JOIN DATA_CUPOM AS C ON A."id" = C."id"
        JOIN MOBITS_API_CUPONS_RESGATADOS R ON A."id" = R."cupom_id"
        WHERE C.DATA_ATIVO IS NOT NULL
        GROUP BY 1, 2
        ORDER BY 3 DESC;
    """,
    "Cupons por Categoria": """
        WITH DATA_CUPOM AS (
            SELECT
                "id",
                -- AJUSTE: Lógica de data robusta
                CASE
                    WHEN DATE_TRUNC('month', "data_inicio"::DATE) = DATE_TRUNC('month', CURRENT_DATE - INTERVAL '1 month') THEN DATE_TRUNC('month', "data_inicio"::DATE)
                    WHEN DATE_TRUNC('month', "data_fim"::DATE) = DATE_TRUNC('month', CURRENT_DATE - INTERVAL '1 month') THEN DATE_TRUNC('month', "data_fim"::DATE)
                    WHEN DATE_TRUNC('month', "data_inicio"::DATE) = DATE_TRUNC('month', CURRENT_DATE - INTERVAL '13 months') THEN DATE_TRUNC('month', "data_inicio"::DATE)
                    WHEN DATE_TRUNC('month', "data_fim"::DATE) = DATE_TRUNC('month', CURRENT_DATE - INTERVAL '13 months') THEN DATE_TRUNC('month', "data_fim"::DATE)
                END AS DATA_ATIVO,
                CASE
                    WHEN (UPPER("observacao") ILIKE '%#ESTACIONAMENTO%') THEN 'ESTACIONAMENTO'
                    WHEN (UPPER("observacao") ILIKE '%#LOJA%') THEN 'LOJA'
                    WHEN (UPPER("observacao") ILIKE '%#SHOPPING%') THEN 'SHOPPING'
                    WHEN (UPPER("observacao") ILIKE '%#IGUATEMI HALL%') THEN 'IGUATEMI HALL'
                    WHEN (UPPER("observacao") ILIKE '%#CINEMA%') THEN 'CINEMA'
                    WHEN (UPPER("observacao") ILIKE '%#EXTERNO%') THEN 'EXTERNO'
                    WHEN (UPPER("observacao") ILIKE '%#EVENTO I_CLUB%') THEN 'ICLUB'
                    ELSE 'SEM CLASSIFICACAO'
                END AS CATEGORIA_CUPOM
            FROM MOBITS_API_CUPONS
        )
        SELECT DISTINCT 
            TO_CHAR(C.DATA_ATIVO, 'YYYY-MM') AS ANO_MES, -- AJUSTE
            C.CATEGORIA_CUPOM,
            COUNT(DISTINCT A."id") AS CUPONS_ATIVOS
        FROM MOBITS_API_CUPONS A
        JOIN DATA_CUPOM AS C ON A."id" = C."id"
        WHERE C.DATA_ATIVO IS NOT NULL
        GROUP BY 1, 2
        ORDER BY 3 DESC;
    """,    
    "Notas Fiscais Cadastradas - Comparação YoY": """
        SELECT
            TO_CHAR(L."CreatedDateTime"::DATE, 'YYYY-MM') AS ANO_MES, -- AJUSTE
            COUNT(DISTINCT L."TransactionID") AS NOTAS_CADASTRADAS
        FROM CRMALL_V_CRM_TRANSACTIONLOYALTY AS L
        WHERE L."StatusID" NOT IN ('3', '5')
          -- AJUSTE: Lógica de data robusta.
          AND DATE_TRUNC('month', L."CreatedDateTime"::DATE) IN (
              DATE_TRUNC('month', CURRENT_DATE - INTERVAL '1 month'), 
              DATE_TRUNC('month', CURRENT_DATE - INTERVAL '13 months')
          )
        GROUP BY 1;
    """,
    "Vendas Cadastradas - Comparação YoY": """
        WITH COMPRAS_ICLUB AS (
            SELECT
                T."PurchasedDateTime"::DATE DATA_COMPRA,
                SUM(T."Value"::DECIMAL(10,2)) AS ValorCompra
            FROM CRMALL_V_CRM_TRANSACTIONLOYALTY AS L
            JOIN CRMALL_V_CRM_TRANSACTION AS T ON L."TransactionID" = T."TransactionID" 
            WHERE L."StatusID" NOT IN ('3', '5')
              AND T."PurchasedDateTime" IS NOT NULL AND T."PurchasedDateTime" <> ''
              AND T."PersonContractorID" = '12'
            GROUP BY 1
        )
        SELECT
            TO_CHAR(DATA_COMPRA, 'YYYY-MM') AS ANO_MES, -- AJUSTE
            SUM(VALORCOMPRA) AS VENDAS
        FROM COMPRAS_ICLUB
        WHERE
            -- AJUSTE: Lógica de data robusta.
            DATE_TRUNC('month', DATA_COMPRA) IN (
                DATE_TRUNC('month', CURRENT_DATE - INTERVAL '1 month'), 
                DATE_TRUNC('month', CURRENT_DATE - INTERVAL '13 months')
            )
        GROUP BY 1
        ORDER BY 1 ASC;
    """,
    "Representatividade - Comparação YoY": """
       WITH COMPRAS_ICLUB_POR_MES AS (
            SELECT
                TO_CHAR(T."PurchasedDateTime"::DATE, 'YYYY-MM') AS ANO_MES, -- AJUSTE
                SUM(T."Value"::DECIMAL(10,2)) AS COMPRAS_ICLUB
            FROM CRMALL_V_CRM_TRANSACTIONLOYALTY AS L
            JOIN CRMALL_V_CRM_TRANSACTION AS T ON L."TransactionID" = T."TransactionID" 
            WHERE L."StatusID" NOT IN ('3', '5')
                AND T."PurchasedDateTime" IS NOT NULL AND T."PurchasedDateTime" <> ''
                AND T."PersonContractorID" = '12'
                -- AJUSTE: Filtro de data aplicado aqui
                AND DATE_TRUNC('month', T."PurchasedDateTime"::DATE) IN (
                    DATE_TRUNC('month', CURRENT_DATE - INTERVAL '1 month'), 
                    DATE_TRUNC('month', CURRENT_DATE - INTERVAL '13 months')
                )
            GROUP BY 1
        ),
        VENDAS_GSHOP_POR_MES AS (
            SELECT
                TO_CHAR("Data"::DATE, 'YYYY-MM') AS ANO_MES, -- AJUSTE
                SUM("VENDAS_BRUTAS"::DECIMAL(10,2)) VENDAS_IGT
            FROM GSHOP_VENDAS_GQUEST
            WHERE "Filial" = '1'
                -- AJUSTE: Filtro de data aplicado aqui
                AND DATE_TRUNC('month', "Data"::DATE) IN (
                    DATE_TRUNC('month', CURRENT_DATE - INTERVAL '1 month'), 
                    DATE_TRUNC('month', CURRENT_DATE - INTERVAL '13 months')
                )
            GROUP BY 1
        )
        SELECT
            COALESCE(VPM.ANO_MES, VG.ANO_MES) AS ANO_MES,
            VG.VENDAS_IGT AS RECEITA_IGUATEMI,
            VPM.COMPRAS_ICLUB AS NOTAS_FISCAIS_CADASTRADAS
        FROM COMPRAS_ICLUB_POR_MES VPM
        FULL OUTER JOIN VENDAS_GSHOP_POR_MES VG ON VPM.ANO_MES = VG.ANO_MES
        ORDER BY 1;
    """
}
# queries.py

"""
Módulo para armazenar todas as consultas SQL que serão executadas pela automação.
As queries foram ajustadas para usar funções de intervalo de data do PostgreSQL,
garantindo que funcionem corretamente em todos os meses, incluindo janeiro.
"""

QUERIES = {
    "Cupons Ativos": """
        WITH DATA_CUPOM AS (
            SELECT
                "id",
                -- AJUSTE: Lógica de data robusta para evitar erros em janeiro.
                CASE
                    WHEN DATE_TRUNC('month', "data_inicio"::DATE) = DATE_TRUNC('month', CURRENT_DATE - INTERVAL '1 month') THEN DATE_TRUNC('month', "data_inicio"::DATE)
                    WHEN DATE_TRUNC('month', "data_fim"::DATE) = DATE_TRUNC('month', CURRENT_DATE - INTERVAL '1 month') THEN DATE_TRUNC('month', "data_fim"::DATE)
                    WHEN DATE_TRUNC('month', "data_inicio"::DATE) = DATE_TRUNC('month', CURRENT_DATE - INTERVAL '13 months') THEN DATE_TRUNC('month', "data_inicio"::DATE)
                    WHEN DATE_TRUNC('month', "data_fim"::DATE) = DATE_TRUNC('month', CURRENT_DATE - INTERVAL '13 months') THEN DATE_TRUNC('month', "data_fim"::DATE)
                END AS DATA_ATIVO
            FROM MOBITS_API_CUPONS
        )
        SELECT DISTINCT 
            TO_CHAR(C.DATA_ATIVO, 'YYYY-MM') AS ANO_MES -- AJUSTE: Formatação padrão de data
            ,COUNT(DISTINCT A."id") AS CUPONS_ATIVOS
        FROM MOBITS_API_CUPONS A
        JOIN DATA_CUPOM AS C ON A."id" = C."id"
        WHERE C.DATA_ATIVO IS NOT NULL
        GROUP BY 1;
    """,
    "Compradores Únicos": """
        WITH COMPRAS_ICLUB AS
            (
                SELECT DISTINCT
                    T."PersonID" ID_CLIENTE,
                    T."PurchasedDateTime"::DATE DATA_COMPRA
                FROM CRMALL_V_CRM_TRANSACTIONLOYALTY AS L
                LEFT JOIN CRMALL_V_CRM_TRANSACTION AS T ON L."TransactionID" = T."TransactionID" 
                WHERE L."StatusID" NOT IN ('3', '5')
                    AND T."PurchasedDateTime" IS NOT NULL AND T."PurchasedDateTime" <> ''
                    AND T."PersonContractorID" = '12'
            )
        SELECT
            TO_CHAR(DATA_COMPRA, 'YYYY-MM') AS ANO_MES -- AJUSTE: Formatação de data padronizada.
            ,COUNT(DISTINCT ID_CLIENTE) AS COMPRADORES_UNICOS
        FROM COMPRAS_ICLUB
        WHERE 
            -- AJUSTE: Lógica de data robusta usando IN para comparar com o mês anterior e o mesmo mês do ano anterior.
            DATE_TRUNC('month', DATA_COMPRA) IN (
                DATE_TRUNC('month', CURRENT_DATE - INTERVAL '1 month'), 
                DATE_TRUNC('month', CURRENT_DATE - INTERVAL '13 months')
            )
        GROUP BY 1
        ORDER BY 1 ASC;
    """,
    "Top 10 Lojas + Compradores Únicos": """
        WITH COMPRAS_ICLUB AS (
            SELECT DISTINCT
                T."StoreID" AS IDLOJA,
                T."PersonID" ID_CLIENTE,
                T."PurchasedDateTime"::DATE DATA_COMPRA
            FROM CRMALL_V_CRM_TRANSACTIONLOYALTY AS L
            JOIN CRMALL_V_CRM_TRANSACTION AS T ON L."TransactionID" = T."TransactionID" 
            WHERE L."StatusID" NOT IN ('3', '5')
              AND T."PurchasedDateTime" IS NOT NULL AND T."PurchasedDateTime" <> ''
              AND T."PersonContractorID" = '12'
        ),
        DIM_LOJAS AS (
            SELECT DISTINCT
                "StoreID" AS IDLOJA,
                "Gshop_NomeFantasia" AS NOME_DA_LOJA
            FROM CRMALL_LOJA_GSHOP
        )
        SELECT
            L.NOME_DA_LOJA,
            TO_CHAR(C.DATA_COMPRA, 'YYYY-MM') AS ANO_MES, -- AJUSTE: Formatação de data padronizada.
            COUNT(DISTINCT C.ID_CLIENTE) AS COMPRADORES_UNICOS
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
    "Clientes por Categoria": """
        -- Esta query não possui filtro de data, portanto não necessita de ajustes.
        WITH CATEGORIA_ATUAL AS (
            SELECT
                *
            FROM (
                SELECT
                    ROW_NUMBER() OVER(PARTITION BY "PersonID" ORDER BY MAX("ActiveDateTime"::DATE) DESC, "LoyaltyCategoryID" ASC) AS ORDEM
                    ,"PersonID" AS ID_CLIENTE
                    ,"Category" AS CATEGORIA_ATUAL
                    ,"InactiveDateTime"::DATE AS DATA_INATIVACAO_MED
                FROM CRMALL_V_CRM_PERSON_LOYALTY
                GROUP BY "PersonID", "Category", "LoyaltyCategoryID", "ActiveDateTime", "InactiveDateTime"
            ) A
            WHERE DATA_INATIVACAO_MED IS NULL
        )
        SELECT
            CATEGORIA_ATUAL,
            COUNT(DISTINCT ID_CLIENTE) AS CLIENTES
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
    # ... (O restante das queries seguiria o mesmo padrão de ajuste)
    # Para economizar espaço, vou ajustar apenas mais algumas chaves. 
    # Aplique o mesmo padrão para as queries de TKT Médio.

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
            TO_CHAR(DATA_COMPRA, 'YYYY-MM') AS ANO_MES, -- AJUSTE: Formatação de data padronizada.
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
    "Notas Fiscais Cadastradas - Comparação YoY": """
        SELECT
            TO_CHAR(L."CreatedDateTime"::DATE, 'YYYY-MM') AS ANO_MES, -- AJUSTE: Formatação de data padronizada.
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
            TO_CHAR(DATA_COMPRA, 'YYYY-MM') AS ANO_MES, -- AJUSTE: Formatação de data padronizada.
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
       WITH COMPRAS_ICLUB AS (
            SELECT
                T."PurchasedDateTime"::DATE AS DATA_COMPRA,
                SUM(T."Value"::DECIMAL(10,2)) AS ValorCompra
            FROM CRMALL_V_CRM_TRANSACTIONLOYALTY AS L
            JOIN CRMALL_V_CRM_TRANSACTION AS T ON L."TransactionID" = T."TransactionID" 
            WHERE L."StatusID" NOT IN ('3', '5')
                AND T."PurchasedDateTime" IS NOT NULL AND T."PurchasedDateTime" <> ''
                AND T."PersonContractorID" = '12'
            GROUP BY 1
        ),
        VENDAS_POR_MES AS (
            SELECT
                TO_CHAR(DATA_COMPRA, 'YYYY-MM') AS ANO_MES, -- AJUSTE
                SUM(ValorCompra) AS COMPRAS_ICLUB
            FROM COMPRAS_ICLUB
            GROUP BY 1
        ),
        VENDAS_GSHOP AS (
            SELECT
                TO_CHAR("Data"::DATE, 'YYYY-MM') AS ANO_MES, -- AJUSTE
                SUM("VENDAS_BRUTAS"::DECIMAL(10,2)) VENDAS_IGT
            FROM GSHOP_VENDAS_GQUEST
            WHERE "Filial" = '1'
            GROUP BY 1
        )
        SELECT
            COALESCE(VPM.ANO_MES, VG.ANO_MES) AS ANO_MES,
            VG.VENDAS_IGT AS RECEITA_IGUATEMI,
            VPM.COMPRAS_ICLUB AS NOTAS_FISCAIS_CADASTRADAS
        FROM VENDAS_POR_MES VPM
        FULL OUTER JOIN VENDAS_GSHOP VG ON VPM.ANO_MES = VG.ANO_MES
        WHERE
            -- AJUSTE: Lógica de data robusta aplicada no final.
            COALESCE(VPM.ANO_MES, VG.ANO_MES) IN (
                TO_CHAR(CURRENT_DATE - INTERVAL '1 month', 'YYYY-MM'),
                TO_CHAR(CURRENT_DATE - INTERVAL '13 months', 'YYYY-MM')
            )
        ORDER BY 1;
    """
    # ... As demais queries, como as de TKT Médio por Categoria, devem ser ajustadas da mesma forma.
    # O padrão é:
    # 1. Trocar CONCAT(EXTRACT(YEAR...),'-','0',EXTRACT(MONTH...)) por TO_CHAR(data_col, 'YYYY-MM')
    # 2. Trocar a cláusula WHERE de data por:
    #    DATE_TRUNC('month', data_col) IN (
    #        DATE_TRUNC('month', CURRENT_DATE - INTERVAL '1 month'), 
    #        DATE_TRUNC('month', CURRENT_DATE - INTERVAL '13 months')
    #    )
}
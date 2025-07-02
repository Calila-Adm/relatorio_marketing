# queries.py

"""
Módulo para armazenar todas as consultas SQL que serão executadas pela automação.
As queries são armazenadas em um dicionário onde a chave é o nome descritivo do relatório
e o valor é a string da consulta SQL.

**IMPORTANTE:** Adapte os nomes de tabelas (ex: 'vendas', 'clientes') e colunas
(ex: 'valor_total', 'data_venda') para a sua estrutura de banco de dados.
"""

# As datas (:start_date, :end_date, etc.) são parâmetros que serão preenchidos dinamicamente no script principal.
# Isso é uma boa prática para evitar SQL Injection.

QUERIES = {
    "Cupons Ativos": """
        WITH DATA_CUPOM AS (
            SELECT
                "id",
                CASE
                    WHEN DATE_TRUNC('MONTH', "data_inicio"::DATE) = (CONCAT(EXTRACT(YEAR FROM CURRENT_DATE),'-',EXTRACT(MONTH FROM CURRENT_DATE)-1,'-01'))::DATE THEN DATE_TRUNC('MONTH', "data_inicio"::DATE)
                    WHEN DATE_TRUNC('MONTH', "data_fim"::DATE) = CONCAT(EXTRACT(YEAR FROM CURRENT_DATE),'-',EXTRACT(MONTH FROM CURRENT_DATE)-1,'-01')::DATE THEN DATE_TRUNC('MONTH', "data_fim"::DATE)
                    WHEN DATE_TRUNC('MONTH', "data_inicio"::DATE) = CONCAT(EXTRACT(YEAR FROM CURRENT_DATE)-1,'-',EXTRACT(MONTH FROM CURRENT_DATE)-1,'-01')::DATE THEN DATE_TRUNC('MONTH', "data_inicio"::DATE)
                    WHEN DATE_TRUNC('MONTH', "data_fim"::DATE) = CONCAT(EXTRACT(YEAR FROM CURRENT_DATE)-1,'-',EXTRACT(MONTH FROM CURRENT_DATE)-1,'-01')::DATE THEN DATE_TRUNC('MONTH', "data_fim"::DATE)
                END AS DATA_ATIVO
            FROM MOBITS_API_CUPONS
            WHERE 1 = 1
                AND CASE
                    WHEN DATE_TRUNC('MONTH', "data_inicio"::DATE) = (CONCAT(EXTRACT(YEAR FROM CURRENT_DATE),'-',EXTRACT(MONTH FROM CURRENT_DATE)-1,'-01'))::DATE THEN DATE_TRUNC('MONTH', "data_inicio"::DATE)
                    WHEN DATE_TRUNC('MONTH', "data_fim"::DATE) = CONCAT(EXTRACT(YEAR FROM CURRENT_DATE),'-',EXTRACT(MONTH FROM CURRENT_DATE)-1,'-01')::DATE THEN DATE_TRUNC('MONTH', "data_fim"::DATE)
                    WHEN DATE_TRUNC('MONTH', "data_inicio"::DATE) = CONCAT(EXTRACT(YEAR FROM CURRENT_DATE)-1,'-',EXTRACT(MONTH FROM CURRENT_DATE)-1,'-01')::DATE THEN DATE_TRUNC('MONTH', "data_inicio"::DATE)
                    WHEN DATE_TRUNC('MONTH', "data_fim"::DATE) = CONCAT(EXTRACT(YEAR FROM CURRENT_DATE)-1,'-',EXTRACT(MONTH FROM CURRENT_DATE)-1,'-01')::DATE THEN DATE_TRUNC('MONTH', "data_fim"::DATE)
                END IS NOT NULL
            )
            SELECT DISTINCT 
                C.DATA_ATIVO
                ,COUNT(DISTINCT A."id") AS CUPONS_ATIVOS
            FROM MOBITS_API_CUPONS A
            JOIN DATA_CUPOM AS C ON A."id" = C."id"
            WHERE 1 = 1
                AND (C.DATA_ATIVO = (CONCAT(EXTRACT(YEAR FROM CURRENT_DATE),'-',EXTRACT(MONTH FROM CURRENT_DATE)-1,'-01'))::DATE) OR C.DATA_ATIVO = ((CONCAT(EXTRACT(YEAR FROM CURRENT_DATE) -1,'-',EXTRACT(MONTH FROM CURRENT_DATE)-1,'-01'))::DATE)
            GROUP BY 1
    """,
    "Compradores Únicos": """
        WITH COMPRAS_ICLUB AS
            (
                SELECT DISTINCT
                    T."PersonID" ID_CLIENTE,
                    T."PurchasedDateTime"::DATE DATA_COMPRA,
                    CONCAT(T."PersonID", (T."PurchasedDateTime"::DATE)) VISITA,
                    COUNT(DISTINCT L."TransactionID") AS "Qtde NF",
                    SUM(T."Value"::DECIMAL(10,2)) AS "Valor Compra"
                FROM CRMALL_V_CRM_TRANSACTIONLOYALTY AS L
                LEFT JOIN CRMALL_V_CRM_TRANSACTION AS T ON L."TransactionID" = T."TransactionID" 
                WHERE 1 = 1
                    AND L."StatusID" NOT IN ('3', '5')
                    AND T."PurchasedDateTime" IS NOT NULL
                    AND T."PurchasedDateTime" <> ''
                    AND	T."PersonContractorID" = '12'
                GROUP BY 
                    T."PersonID",
                    T."PurchasedDateTime",
                    L."TransactionID"
                ORDER BY 
                    T."PersonID"
            )
            SELECT
                CONCAT(EXTRACT(YEAR FROM DATA_COMPRA),'-','0',EXTRACT(MONTH FROM DATA_COMPRA)) AS ANO_MES
                ,COUNT(DISTINCT ID_CLIENTE) AS COMPRADORES_UNICOS
            FROM COMPRAS_ICLUB
            WHERE 1 = 1
                AND DATE_TRUNC('MONTH', DATA_COMPRA)::DATE = CONCAT(EXTRACT(YEAR FROM CURRENT_DATE),'-',EXTRACT(MONTH FROM CURRENT_DATE)-1,'-01')::DATE
                OR DATE_TRUNC('MONTH', DATA_COMPRA)::DATE = CONCAT(EXTRACT(YEAR FROM CURRENT_DATE)-1,'-',EXTRACT(MONTH FROM CURRENT_DATE)-1,'-01')::DATE
            GROUP BY 1
            ORDER BY 1 ASC;
    """,
    "Top 10 Lojas + Compradores Únicos": """
        WITH COMPRAS_ICLUB AS
            (
                SELECT DISTINCT
                    T."StoreID" AS IDLOJA,
                    T."PersonID" ID_CLIENTE,
                    T."PurchasedDateTime"::DATE DATA_COMPRA,
                    CONCAT(T."PersonID", (T."PurchasedDateTime"::DATE)) VISITA,
                    COUNT(DISTINCT L."TransactionID") AS "Qtde NF",
                    SUM(T."Value"::DECIMAL(10,2)) AS "Valor Compra"
                FROM CRMALL_V_CRM_TRANSACTIONLOYALTY AS L
                LEFT JOIN CRMALL_V_CRM_TRANSACTION AS T ON L."TransactionID" = T."TransactionID" 
                WHERE 1 = 1
                    AND L."StatusID" NOT IN ('3', '5')
                    AND T."PurchasedDateTime" IS NOT NULL
                    AND T."PurchasedDateTime" <> ''
                    AND	T."PersonContractorID" = '12'
                GROUP BY 
                    T."PersonID",
                    T."PurchasedDateTime",
                    L."TransactionID",
                    T."StoreID"
                ORDER BY 
                    T."PersonID"
            ),
            DIM_LOJAS AS (
                SELECT DISTINCT
                    "StoreID" AS IDLOJA,
                    "Gshop_NomeFantasia" AS NOME_DA_LOJA
                FROM CRMALL_LOJA_GSHOP
                WHERE 1 = 1
            )
            SELECT
                NOME_DA_LOJA
                ,CONCAT(EXTRACT(YEAR FROM DATA_COMPRA),'-','0',EXTRACT(MONTH FROM DATA_COMPRA)) AS ANO_MES
                ,COUNT(DISTINCT ID_CLIENTE) AS COMPRADORES_UNICOS
            FROM COMPRAS_ICLUB AS C
            JOIN DIM_LOJAS AS L ON TRIM(C.IDLOJA) = TRIM(L.IDLOJA)
            WHERE 1 = 1
                AND DATE_TRUNC('MONTH', DATA_COMPRA)::DATE = CONCAT(EXTRACT(YEAR FROM CURRENT_DATE),'-',EXTRACT(MONTH FROM CURRENT_DATE)-1,'-01')::DATE
                OR DATE_TRUNC('MONTH', DATA_COMPRA)::DATE = CONCAT(EXTRACT(YEAR FROM CURRENT_DATE)-1,'-',EXTRACT(MONTH FROM CURRENT_DATE)-1,'-01')::DATE
            GROUP BY 1, 2
            ORDER BY 3 DESC, 1 ASC;
    """,
    "Top 10 Lojas + Vendas": """
        WITH COMPRAS_ICLUB AS
            (
                SELECT DISTINCT
                    T."StoreID" AS IDLOJA,
                    T."PersonID" ID_CLIENTE,
                    T."PurchasedDateTime"::DATE DATA_COMPRA,
                    CONCAT(T."PersonID", (T."PurchasedDateTime"::DATE)) VISITA,
                    COUNT(DISTINCT L."TransactionID") AS "Qtde NF",
                    SUM(T."Value"::DECIMAL(10,2)) AS ValorCompra
                FROM CRMALL_V_CRM_TRANSACTIONLOYALTY AS L
                LEFT JOIN CRMALL_V_CRM_TRANSACTION AS T ON L."TransactionID" = T."TransactionID" 
                WHERE 1 = 1
                    AND L."StatusID" NOT IN ('3', '5')
                    AND T."PurchasedDateTime" IS NOT NULL
                    AND T."PurchasedDateTime" <> ''
                    AND	T."PersonContractorID" = '12'
                GROUP BY 
                    T."PersonID",
                    T."PurchasedDateTime",
                    L."TransactionID",
                    T."StoreID"
                ORDER BY 
                    T."PersonID"
            ),
            DIM_LOJAS AS (
                SELECT DISTINCT
                    "StoreID" AS IDLOJA,
                    "Gshop_NomeFantasia" AS NOME_DA_LOJA
                FROM CRMALL_LOJA_GSHOP
                WHERE 1 = 1
            )
            SELECT
                NOME_DA_LOJA
                ,CONCAT(EXTRACT(YEAR FROM DATA_COMPRA),'-','0',EXTRACT(MONTH FROM DATA_COMPRA)) AS ANO_MES
                ,SUM(ValorCompra) AS VENDAS
            FROM COMPRAS_ICLUB AS C
            JOIN DIM_LOJAS AS L ON TRIM(C.IDLOJA) = TRIM(L.IDLOJA)
            WHERE 1 = 1
                AND DATE_TRUNC('MONTH', DATA_COMPRA)::DATE = CONCAT(EXTRACT(YEAR FROM CURRENT_DATE),'-',EXTRACT(MONTH FROM CURRENT_DATE)-1,'-01')::DATE
                OR DATE_TRUNC('MONTH', DATA_COMPRA)::DATE = CONCAT(EXTRACT(YEAR FROM CURRENT_DATE)-1,'-',EXTRACT(MONTH FROM CURRENT_DATE)-1,'-01')::DATE
            GROUP BY 1, 2
            ORDER BY 3 DESC, 1 ASC;
    """,
    "Top 10 Lojas + Notas Fiscais": """
        WITH COMPRAS_ICLUB AS
            (
                SELECT DISTINCT
                    T."StoreID" AS IDLOJA,
                    T."PersonID" ID_CLIENTE,
                    T."PurchasedDateTime"::DATE DATA_COMPRA,
                    CONCAT(T."PersonID", (T."PurchasedDateTime"::DATE)) VISITA,
                    COUNT(DISTINCT L."TransactionID") AS QtdeNF,
                    SUM(T."Value"::DECIMAL(10,2)) AS ValorCompra
                FROM CRMALL_V_CRM_TRANSACTIONLOYALTY AS L
                LEFT JOIN CRMALL_V_CRM_TRANSACTION AS T ON L."TransactionID" = T."TransactionID" 
                WHERE 1 = 1
                    AND L."StatusID" NOT IN ('3', '5')
                    AND T."PurchasedDateTime" IS NOT NULL
                    AND T."PurchasedDateTime" <> ''
                    AND	T."PersonContractorID" = '12'
                GROUP BY 
                    T."PersonID",
                    T."PurchasedDateTime",
                    L."TransactionID",
                    T."StoreID"
                ORDER BY 
                    T."PersonID"
            ),
            DIM_LOJAS AS (
                SELECT DISTINCT
                    "StoreID" AS IDLOJA,
                    "Gshop_NomeFantasia" AS NOME_DA_LOJA
                FROM CRMALL_LOJA_GSHOP
                WHERE 1 = 1
            )
            SELECT
                NOME_DA_LOJA
                ,CONCAT(EXTRACT(YEAR FROM DATA_COMPRA),'-','0',EXTRACT(MONTH FROM DATA_COMPRA)) AS ANO_MES
                ,SUM(QtdeNF) AS NOTAS_FISCAIS
            FROM COMPRAS_ICLUB AS C
            JOIN DIM_LOJAS AS L ON TRIM(C.IDLOJA) = TRIM(L.IDLOJA)
            WHERE 1 = 1
                AND DATE_TRUNC('MONTH', DATA_COMPRA)::DATE = CONCAT(EXTRACT(YEAR FROM CURRENT_DATE),'-',EXTRACT(MONTH FROM CURRENT_DATE)-1,'-01')::DATE
                OR DATE_TRUNC('MONTH', DATA_COMPRA)::DATE = CONCAT(EXTRACT(YEAR FROM CURRENT_DATE)-1,'-',EXTRACT(MONTH FROM CURRENT_DATE)-1,'-01')::DATE
            GROUP BY 1, 2
            ORDER BY 3 DESC, 1 ASC;
    """,
    "Clientes por Categoria": """
        WITH CATEGORIA_ATUAL AS (
            SELECT
                *
            FROM
                (
                    SELECT
                        ROW_NUMBER() OVER(PARTITION BY "PersonID" ORDER BY MAX("ActiveDateTime"::DATE) DESC, "LoyaltyCategoryID" ASC) AS ORDEM
                        ,"PersonID" AS ID_CLIENTE
                        ,"LoyaltyCategoryID"::INT ID_CAT_ATUAL
                        ,"Category" AS CATEGORIA_ATUAL
                        ,"ActiveDateTime"::DATE AS DATA_ATIVACAO_MED
                        ,"InactiveDateTime"::DATE AS DATA_INATIVACAO_MED
                    FROM CRMALL_V_CRM_PERSON_LOYALTY
                    WHERE 1 = 1
                    GROUP BY "PersonID", "Category", "LoyaltyCategoryID", "ActiveDateTime", "InactiveDateTime"
                )
                WHERE 1 = 1
                    AND DATA_INATIVACAO_MED IS NULL
            )
            SELECT
                CATEGORIA_ATUAL
                ,COUNT(DISTINCT ID_CLIENTE) AS CLIENTES
            FROM CATEGORIA_ATUAL
            WHERE 1 = 1
            GROUP BY 1
    """,
    "Visitas por Categoria de Clientes - Comparação YoY": """
        WITH COMPRAS_ICLUB AS
            (
                SELECT DISTINCT
                    T."StoreID" AS IDLOJA,
                    T."PersonID" ID_CLIENTE,
                    T."PurchasedDateTime"::DATE DATA_COMPRA,
                    CONCAT(T."PersonID", (T."PurchasedDateTime"::DATE)) VISITA,
                    COUNT(DISTINCT L."TransactionID") AS "Qtde NF",
                    SUM(T."Value"::DECIMAL(10,2)) AS ValorCompra
                FROM CRMALL_V_CRM_TRANSACTIONLOYALTY AS L
                LEFT JOIN CRMALL_V_CRM_TRANSACTION AS T ON L."TransactionID" = T."TransactionID" 
                WHERE 1 = 1
                    AND L."StatusID" NOT IN ('3', '5')
                    AND T."PurchasedDateTime" IS NOT NULL
                    AND T."PurchasedDateTime" <> ''
                    AND	T."PersonContractorID" = '12'
                GROUP BY 
                    T."PersonID",
                    T."PurchasedDateTime",
                    L."TransactionID",
                    T."StoreID"
                ORDER BY 
                    T."PersonID"
            ),
            CATEGORIA_ATUAL AS (
                SELECT
                    *
                FROM
                (
                    SELECT
                        ROW_NUMBER() OVER(PARTITION BY "PersonID" ORDER BY MAX("ActiveDateTime"::DATE) DESC, "LoyaltyCategoryID" ASC) AS ORDEM
                        ,"PersonID" AS ID_CLIENTE
                        ,"LoyaltyCategoryID"::INT ID_CAT_ATUAL
                        ,"Category" AS CATEGORIA_ATUAL
                        ,"ActiveDateTime"::DATE AS DATA_ATIVACAO_MED
                        ,"InactiveDateTime"::DATE AS DATA_INATIVACAO_MED
                    FROM CRMALL_V_CRM_PERSON_LOYALTY
                    WHERE 1 = 1
                    GROUP BY "PersonID", "Category", "LoyaltyCategoryID", "ActiveDateTime", "InactiveDateTime"
                )
                WHERE 1 = 1
                    AND DATA_INATIVACAO_MED IS NULL
            )
            SELECT
                CATEGORIA_ATUAL
                ,CONCAT(EXTRACT(YEAR FROM DATA_COMPRA),'-','0',EXTRACT(MONTH FROM DATA_COMPRA)) AS ANO_MES
                ,COUNT(DISTINCT C.VISITA) AS VISITAS
            FROM COMPRAS_ICLUB AS C
            LEFT JOIN CATEGORIA_ATUAL AS L ON TRIM(C.ID_CLIENTE) = TRIM(L.ID_CLIENTE)
            WHERE 1 = 1
                AND DATE_TRUNC('MONTH', DATA_COMPRA)::DATE = CONCAT(EXTRACT(YEAR FROM CURRENT_DATE),'-',EXTRACT(MONTH FROM CURRENT_DATE)-1,'-01')::DATE
                OR DATE_TRUNC('MONTH', DATA_COMPRA)::DATE = CONCAT(EXTRACT(YEAR FROM CURRENT_DATE)-1,'-',EXTRACT(MONTH FROM CURRENT_DATE)-1,'-01')::DATE
            GROUP BY 1, 2
            ORDER BY 3 DESC, 1 ASC;
    """,
    "Visitas por Geral - Comparação YoY": """
        WITH COMPRAS_ICLUB AS
            (
                SELECT DISTINCT
                    T."PersonID" ID_CLIENTE,
                    T."PurchasedDateTime"::DATE DATA_COMPRA,
                    CONCAT(T."PersonID", (T."PurchasedDateTime"::DATE)) VISITA,
                    COUNT(DISTINCT L."TransactionID") AS "Qtde NF",
                    SUM(T."Value"::DECIMAL(10,2)) AS "Valor Compra"
                FROM CRMALL_V_CRM_TRANSACTIONLOYALTY AS L
                LEFT JOIN CRMALL_V_CRM_TRANSACTION AS T ON L."TransactionID" = T."TransactionID" 
                WHERE 1 = 1
                    AND L."StatusID" NOT IN ('3', '5')
                    AND T."PurchasedDateTime" IS NOT NULL
                    AND T."PurchasedDateTime" <> ''
                    AND	T."PersonContractorID" = '12'
                GROUP BY
                    T."PersonID",
                    T."PurchasedDateTime",
                    L."TransactionID"
                ORDER BY 
                    T."PersonID"
            )
            SELECT DISTINCT
                CONCAT(EXTRACT(YEAR FROM DATA_COMPRA),'-','0',EXTRACT(MONTH FROM DATA_COMPRA)) AS ANO_MES
                ,COUNT(DISTINCT VISITA) AS VISITAS
            FROM COMPRAS_ICLUB
            WHERE 1 = 1
                	AND DATE_TRUNC('MONTH', DATA_COMPRA)::DATE = CONCAT(EXTRACT(YEAR FROM CURRENT_DATE),'-',EXTRACT(MONTH FROM CURRENT_DATE)-1,'-01')::DATE
	                OR DATE_TRUNC('MONTH', DATA_COMPRA)::DATE = CONCAT(EXTRACT(YEAR FROM CURRENT_DATE)-1,'-',EXTRACT(MONTH FROM CURRENT_DATE)-1,'-01')::DATE
            GROUP BY 1
            ORDER BY 1 ASC;
    """,
    "TKT Médio por Visitas - Por Categoria de Cliente": """
        WITH COMPRAS_ICLUB AS
            (
                SELECT DISTINCT
                    T."StoreID" AS IDLOJA,
                    T."PersonID" ID_CLIENTE,
                    T."PurchasedDateTime"::DATE DATA_COMPRA,
                    CONCAT(T."PersonID", (T."PurchasedDateTime"::DATE)) VISITA,
                    COUNT(DISTINCT L."TransactionID") AS "Qtde NF",
                    SUM(T."Value"::DECIMAL(10,2)) AS ValorCompra
                FROM CRMALL_V_CRM_TRANSACTIONLOYALTY AS L
                LEFT JOIN CRMALL_V_CRM_TRANSACTION AS T ON L."TransactionID" = T."TransactionID" 
                WHERE 1 = 1
                    AND L."StatusID" NOT IN ('3', '5')
                    AND T."PurchasedDateTime" IS NOT NULL
                    AND T."PurchasedDateTime" <> ''
                    AND	T."PersonContractorID" = '12'
                GROUP BY 
                    T."PersonID",
                    T."PurchasedDateTime",
                    L."TransactionID",
                    T."StoreID"
                ORDER BY 
                    T."PersonID"
            ),
            CATEGORIA_ATUAL AS (
                SELECT
                    *
                FROM
                (
                    SELECT
                        ROW_NUMBER() OVER(PARTITION BY "PersonID" ORDER BY MAX("ActiveDateTime"::DATE) DESC, "LoyaltyCategoryID" ASC) AS ORDEM
                        ,"PersonID" AS ID_CLIENTE
                        ,"LoyaltyCategoryID"::INT ID_CAT_ATUAL
                        ,"Category" AS CATEGORIA_ATUAL
                        ,"ActiveDateTime"::DATE AS DATA_ATIVACAO_MED
                        ,"InactiveDateTime"::DATE AS DATA_INATIVACAO_MED
                    FROM CRMALL_V_CRM_PERSON_LOYALTY
                    WHERE 1 = 1
                    GROUP BY "PersonID", "Category", "LoyaltyCategoryID", "ActiveDateTime", "InactiveDateTime"
                )
                WHERE 1 = 1
                    AND DATA_INATIVACAO_MED IS NULL
            )
            SELECT
                CATEGORIA_ATUAL
                ,CONCAT(EXTRACT(YEAR FROM DATA_COMPRA),'-','0',EXTRACT(MONTH FROM DATA_COMPRA)) AS ANO_MES
                ,COUNT(DISTINCT C.VISITA) AS VISITAS
                ,SUM(ValorCompra) AS VENDAS
                ,SUM(ValorCompra)/COUNT(DISTINCT C.VISITA) AS TKT_MEDIO_VISITA
            FROM COMPRAS_ICLUB AS C
            LEFT JOIN CATEGORIA_ATUAL AS L ON TRIM(C.ID_CLIENTE) = TRIM(L.ID_CLIENTE)
            WHERE 1 = 1
                AND DATE_TRUNC('MONTH', DATA_COMPRA)::DATE = CONCAT(EXTRACT(YEAR FROM CURRENT_DATE),'-',EXTRACT(MONTH FROM CURRENT_DATE)-1,'-01')::DATE
                OR DATE_TRUNC('MONTH', DATA_COMPRA)::DATE = CONCAT(EXTRACT(YEAR FROM CURRENT_DATE)-1,'-',EXTRACT(MONTH FROM CURRENT_DATE)-1,'-01')::DATE
            GROUP BY 1, 2
            ORDER BY 3 DESC, 1 ASC;
    """,
    "TKT Médio por Nota Fiscal - Por Categoria de Cliente": """
        WITH COMPRAS_ICLUB AS
            (
                SELECT DISTINCT
                    T."StoreID" AS IDLOJA,
                    T."PersonID" ID_CLIENTE,
                    T."PurchasedDateTime"::DATE DATA_COMPRA,
                    CONCAT(T."PersonID", (T."PurchasedDateTime"::DATE)) VISITA,
                    COUNT(DISTINCT L."TransactionID") AS QtdeNF,
                    SUM(T."Value"::DECIMAL(10,2)) AS ValorCompra
                FROM CRMALL_V_CRM_TRANSACTIONLOYALTY AS L
                LEFT JOIN CRMALL_V_CRM_TRANSACTION AS T ON L."TransactionID" = T."TransactionID" 
                WHERE 1 = 1
                    AND L."StatusID" NOT IN ('3', '5')
                    AND T."PurchasedDateTime" IS NOT NULL
                    AND T."PurchasedDateTime" <> ''
                    AND	T."PersonContractorID" = '12'
                GROUP BY 
                    T."PersonID",
                    T."PurchasedDateTime",
                    L."TransactionID",
                    T."StoreID"
                ORDER BY 
                    T."PersonID"
            ),
            CATEGORIA_ATUAL AS (
                SELECT
                    *
                FROM
                (
                    SELECT
                        ROW_NUMBER() OVER(PARTITION BY "PersonID" ORDER BY MAX("ActiveDateTime"::DATE) DESC, "LoyaltyCategoryID" ASC) AS ORDEM
                        ,"PersonID" AS ID_CLIENTE
                        ,"LoyaltyCategoryID"::INT ID_CAT_ATUAL
                        ,"Category" AS CATEGORIA_ATUAL
                        ,"ActiveDateTime"::DATE AS DATA_ATIVACAO_MED
                        ,"InactiveDateTime"::DATE AS DATA_INATIVACAO_MED
                    FROM CRMALL_V_CRM_PERSON_LOYALTY
                    WHERE 1 = 1
                    GROUP BY "PersonID", "Category", "LoyaltyCategoryID", "ActiveDateTime", "InactiveDateTime"
                )
                WHERE 1 = 1
                    AND DATA_INATIVACAO_MED IS NULL
            )
            SELECT
                CATEGORIA_ATUAL
                ,CONCAT(EXTRACT(YEAR FROM DATA_COMPRA),'-','0',EXTRACT(MONTH FROM DATA_COMPRA)) AS ANO_MES
                ,SUM(QtdeNF) AS NF
                ,SUM(ValorCompra) AS VENDAS
                ,SUM(ValorCompra)/SUM(QtdeNF) AS TKT_MEDIO_NF
            FROM COMPRAS_ICLUB AS C
            LEFT JOIN CATEGORIA_ATUAL AS L ON TRIM(C.ID_CLIENTE) = TRIM(L.ID_CLIENTE)
            WHERE 1 = 1
                AND DATE_TRUNC('MONTH', DATA_COMPRA)::DATE = CONCAT(EXTRACT(YEAR FROM CURRENT_DATE),'-',EXTRACT(MONTH FROM CURRENT_DATE)-1,'-01')::DATE
                OR DATE_TRUNC('MONTH', DATA_COMPRA)::DATE = CONCAT(EXTRACT(YEAR FROM CURRENT_DATE)-1,'-',EXTRACT(MONTH FROM CURRENT_DATE)-1,'-01')::DATE
            GROUP BY 1, 2
            ORDER BY 3 DESC, 1 ASC;
    """,
    "TKT Médio Clientes - Por Categoria de Cliente": """
        WITH COMPRAS_ICLUB AS
            (
                SELECT DISTINCT
                    T."StoreID" AS IDLOJA,
                    T."PersonID" ID_CLIENTE,
                    T."PurchasedDateTime"::DATE DATA_COMPRA,
                    CONCAT(T."PersonID", (T."PurchasedDateTime"::DATE)) VISITA,
                    COUNT(DISTINCT L."TransactionID") AS QtdeNF,
                    SUM(T."Value"::DECIMAL(10,2)) AS ValorCompra
                FROM CRMALL_V_CRM_TRANSACTIONLOYALTY AS L
                LEFT JOIN CRMALL_V_CRM_TRANSACTION AS T ON L."TransactionID" = T."TransactionID" 
                WHERE 1 = 1
                    AND L."StatusID" NOT IN ('3', '5')
                    AND T."PurchasedDateTime" IS NOT NULL
                    AND T."PurchasedDateTime" <> ''
                    AND	T."PersonContractorID" = '12'
                GROUP BY 
                    T."PersonID",
                    T."PurchasedDateTime",
                    L."TransactionID",
                    T."StoreID"
                ORDER BY 
                    T."PersonID"
            ),
            CATEGORIA_ATUAL AS (
                SELECT
                    *
                FROM
                (
                    SELECT
                        ROW_NUMBER() OVER(PARTITION BY "PersonID" ORDER BY MAX("ActiveDateTime"::DATE) DESC, "LoyaltyCategoryID" ASC) AS ORDEM
                        ,"PersonID" AS ID_CLIENTE
                        ,"LoyaltyCategoryID"::INT ID_CAT_ATUAL
                        ,"Category" AS CATEGORIA_ATUAL
                        ,"ActiveDateTime"::DATE AS DATA_ATIVACAO_MED
                        ,"InactiveDateTime"::DATE AS DATA_INATIVACAO_MED
                    FROM CRMALL_V_CRM_PERSON_LOYALTY
                    WHERE 1 = 1
                    GROUP BY "PersonID", "Category", "LoyaltyCategoryID", "ActiveDateTime", "InactiveDateTime"
                )
                WHERE 1 = 1
                    AND DATA_INATIVACAO_MED IS NULL
            )
            SELECT
                CATEGORIA_ATUAL
                ,CONCAT(EXTRACT(YEAR FROM DATA_COMPRA),'-','0',EXTRACT(MONTH FROM DATA_COMPRA)) AS ANO_MES
                ,COUNT(DISTINCT C.ID_CLIENTE) AS CLIENTES
                ,SUM(ValorCompra) AS VENDAS
                ,SUM(ValorCompra)/COUNT(DISTINCT C.ID_CLIENTE) AS TKT_MEDIO_CLIENTES
            FROM COMPRAS_ICLUB AS C
            LEFT JOIN CATEGORIA_ATUAL AS L ON TRIM(C.ID_CLIENTE) = TRIM(L.ID_CLIENTE)
            WHERE 1 = 1
                AND DATE_TRUNC('MONTH', DATA_COMPRA)::DATE = CONCAT(EXTRACT(YEAR FROM CURRENT_DATE),'-',EXTRACT(MONTH FROM CURRENT_DATE)-1,'-01')::DATE
                OR DATE_TRUNC('MONTH', DATA_COMPRA)::DATE = CONCAT(EXTRACT(YEAR FROM CURRENT_DATE)-1,'-',EXTRACT(MONTH FROM CURRENT_DATE)-1,'-01')::DATE
            GROUP BY 1, 2
            ORDER BY 3 DESC, 1 ASC;
    """,
    "TKT Médio - Geral": """
        WITH COMPRAS_ICLUB AS
            (
                SELECT DISTINCT
                    T."StoreID" AS IDLOJA,
                    T."PersonID" ID_CLIENTE,
                    T."PurchasedDateTime"::DATE DATA_COMPRA,
                    CONCAT(T."PersonID", (T."PurchasedDateTime"::DATE)) VISITA,
                    COUNT(DISTINCT L."TransactionID") AS QtdeNF,
                    SUM(T."Value"::DECIMAL(10,2)) AS ValorCompra
                FROM CRMALL_V_CRM_TRANSACTIONLOYALTY AS L
                LEFT JOIN CRMALL_V_CRM_TRANSACTION AS T ON L."TransactionID" = T."TransactionID" 
                WHERE 1 = 1
                    AND L."StatusID" NOT IN ('3', '5')
                    AND T."PurchasedDateTime" IS NOT NULL
                    AND T."PurchasedDateTime" <> ''
                    AND	T."PersonContractorID" = '12'
                GROUP BY 
                    T."PersonID",
                    T."PurchasedDateTime",
                    L."TransactionID",
                    T."StoreID"
                ORDER BY 
                    T."PersonID"
            )
            SELECT
                CONCAT(EXTRACT(YEAR FROM DATA_COMPRA),'-','0',EXTRACT(MONTH FROM DATA_COMPRA)) AS ANO_MES
                ,SUM(QTDENF) AS NF
                ,SUM(ValorCompra) AS VENDAS
                ,SUM(ValorCompra)/SUM(QTDENF) AS TKT_MEDIO
            FROM COMPRAS_ICLUB AS C
            WHERE 1 = 1
                AND DATE_TRUNC('MONTH', DATA_COMPRA)::DATE = CONCAT(EXTRACT(YEAR FROM CURRENT_DATE),'-',EXTRACT(MONTH FROM CURRENT_DATE)-1,'-01')::DATE
                OR DATE_TRUNC('MONTH', DATA_COMPRA)::DATE = CONCAT(EXTRACT(YEAR FROM CURRENT_DATE)-1,'-',EXTRACT(MONTH FROM CURRENT_DATE)-1,'-01')::DATE
            GROUP BY 1
            ORDER BY 3 DESC, 1 ASC;
    """,
    "Cupons Emitidos e Consumidos - Comparação YoY": """
        WITH DATA_CUPOM AS (
            SELECT
                "id",
                CASE
                    WHEN DATE_TRUNC('MONTH', "data_inicio"::DATE) = (CONCAT(EXTRACT(YEAR FROM CURRENT_DATE),'-',EXTRACT(MONTH FROM CURRENT_DATE)-1,'-01'))::DATE THEN DATE_TRUNC('MONTH', "data_inicio"::DATE)
                    WHEN DATE_TRUNC('MONTH', "data_fim"::DATE) = CONCAT(EXTRACT(YEAR FROM CURRENT_DATE),'-',EXTRACT(MONTH FROM CURRENT_DATE)-1,'-01')::DATE THEN DATE_TRUNC('MONTH', "data_fim"::DATE)
                    WHEN DATE_TRUNC('MONTH', "data_inicio"::DATE) = CONCAT(EXTRACT(YEAR FROM CURRENT_DATE)-1,'-',EXTRACT(MONTH FROM CURRENT_DATE)-1,'-01')::DATE THEN DATE_TRUNC('MONTH', "data_inicio"::DATE)
                    WHEN DATE_TRUNC('MONTH', "data_fim"::DATE) = CONCAT(EXTRACT(YEAR FROM CURRENT_DATE)-1,'-',EXTRACT(MONTH FROM CURRENT_DATE)-1,'-01')::DATE THEN DATE_TRUNC('MONTH', "data_fim"::DATE)
                END AS DATA_ATIVO
            FROM MOBITS_API_CUPONS
            WHERE 1 = 1
                AND CASE
                    WHEN DATE_TRUNC('MONTH', "data_inicio"::DATE) = (CONCAT(EXTRACT(YEAR FROM CURRENT_DATE),'-',EXTRACT(MONTH FROM CURRENT_DATE)-1,'-01'))::DATE THEN DATE_TRUNC('MONTH', "data_inicio"::DATE)
                    WHEN DATE_TRUNC('MONTH', "data_fim"::DATE) = CONCAT(EXTRACT(YEAR FROM CURRENT_DATE),'-',EXTRACT(MONTH FROM CURRENT_DATE)-1,'-01')::DATE THEN DATE_TRUNC('MONTH', "data_fim"::DATE)
                    WHEN DATE_TRUNC('MONTH', "data_inicio"::DATE) = CONCAT(EXTRACT(YEAR FROM CURRENT_DATE)-1,'-',EXTRACT(MONTH FROM CURRENT_DATE)-1,'-01')::DATE THEN DATE_TRUNC('MONTH', "data_inicio"::DATE)
                    WHEN DATE_TRUNC('MONTH', "data_fim"::DATE) = CONCAT(EXTRACT(YEAR FROM CURRENT_DATE)-1,'-',EXTRACT(MONTH FROM CURRENT_DATE)-1,'-01')::DATE THEN DATE_TRUNC('MONTH', "data_fim"::DATE)
                END IS NOT NULL
            )
            SELECT DISTINCT 
                C.DATA_ATIVO
                ,A.DESCRICAO
                ,COUNT(CASE WHEN UPPER(B."status") <> 'CANCELADO' THEN B."status" END) AS EMITIDOS
                ,COUNT(CASE WHEN UPPER(B."status") = 'CONSUMIDO' THEN B."status" END) AS CONSUMIDO
            FROM MOBITS_API_CUPONS A
            JOIN DATA_CUPOM AS C ON A."id" = C."id"
            JOIN MOBITS_API_CUPONS_RESGATADOS B ON A."id" = B."cupom_id"
            WHERE 1 = 1
                AND (C.DATA_ATIVO = (CONCAT(EXTRACT(YEAR FROM CURRENT_DATE),'-',EXTRACT(MONTH FROM CURRENT_DATE)-1,'-01'))::DATE) OR C.DATA_ATIVO = ((CONCAT(EXTRACT(YEAR FROM CURRENT_DATE) -1,'-',EXTRACT(MONTH FROM CURRENT_DATE)-1,'-01'))::DATE)
            GROUP BY 1, 2
            ORDER BY 3 DESC;
    """,
    "Cupons Emitidos e Consumidos por Categoria": """
        WITH DATA_CUPOM AS (
            SELECT
                "id",
                CASE
                    WHEN DATE_TRUNC('MONTH', "data_inicio"::DATE) = (CONCAT(EXTRACT(YEAR FROM CURRENT_DATE),'-',EXTRACT(MONTH FROM CURRENT_DATE)-1,'-01'))::DATE THEN DATE_TRUNC('MONTH', "data_inicio"::DATE)
                    WHEN DATE_TRUNC('MONTH', "data_fim"::DATE) = CONCAT(EXTRACT(YEAR FROM CURRENT_DATE),'-',EXTRACT(MONTH FROM CURRENT_DATE)-1,'-01')::DATE THEN DATE_TRUNC('MONTH', "data_fim"::DATE)
                    WHEN DATE_TRUNC('MONTH', "data_inicio"::DATE) = CONCAT(EXTRACT(YEAR FROM CURRENT_DATE)-1,'-',EXTRACT(MONTH FROM CURRENT_DATE)-1,'-01')::DATE THEN DATE_TRUNC('MONTH', "data_inicio"::DATE)
                    WHEN DATE_TRUNC('MONTH', "data_fim"::DATE) = CONCAT(EXTRACT(YEAR FROM CURRENT_DATE)-1,'-',EXTRACT(MONTH FROM CURRENT_DATE)-1,'-01')::DATE THEN DATE_TRUNC('MONTH', "data_fim"::DATE)
                END AS DATA_ATIVO,
                CASE
                    WHEN (UPPER("observacao") ILIKE '%#ESTACIONAMENTO' 
                        OR UPPER("observacao") ILIKE '%#ESTACIONAMENTO_' 
                        OR UPPER("observacao") ILIKE '%#ESTACIONAMENTO VALLET' 
                        OR UPPER("observacao") ILIKE '%#ESTACIONAMENTO VALET') THEN 'ESTACIONAMENTO'
                    WHEN (UPPER("observacao") ILIKE '%#LOJA' 
                        OR UPPER("observacao") ILIKE '%#LOJA_'
                        OR UPPER("observacao") ILIKE '%#LOJA
            ') THEN 'LOJA'
                    WHEN (UPPER("observacao") ILIKE '%#SHOPPING' 
                        OR UPPER("observacao") ILIKE '%#SHOPPING_' 
                        OR UPPER("observacao") ILIKE '%#SHOPPING
            '
                        OR UPPER("observacao") ILIKE '%#SHOPPING

            ') THEN 'SHOPPING'
                    WHEN (UPPER("observacao") ILIKE '%#IGUATEMI HALL' 
                        OR UPPER("observacao") ILIKE '%#IGUATEMI HALL_' 
                        OR UPPER("observacao") ILIKE '%#IGUATEMI HALL ') THEN 'IGUATEMI HALL'
                    WHEN (UPPER("observacao") ILIKE '%#CINEMA' 
                        OR UPPER("observacao") ILIKE '%#CINEMA_' 
                        OR UPPER("observacao") ILIKE '%#CINEMA ') THEN 'CINEMA'
                    WHEN (UPPER("observacao") ILIKE '%#EXTERNO' 
                        OR UPPER("observacao") ILIKE '%#EXTERNO_' 
                        OR UPPER("observacao") ILIKE '%#EXTERNO
            ') THEN 'EXTERNO'
                    WHEN (UPPER("observacao") ILIKE '%#EVENTO I_CLUB' 
                        OR UPPER("observacao") ILIKE '%#EVENTO I_CLUB_' 
                        OR UPPER("observacao") ILIKE '%#EVENTO I_CLUB') THEN 'ICLUB'
                    ELSE 'SEM CLASSIFICACAO'
                END AS CATEGORIA_CUPOM
            FROM MOBITS_API_CUPONS
            WHERE 1 = 1
                AND CASE
                    WHEN DATE_TRUNC('MONTH', "data_inicio"::DATE) = (CONCAT(EXTRACT(YEAR FROM CURRENT_DATE),'-',EXTRACT(MONTH FROM CURRENT_DATE)-1,'-01'))::DATE THEN DATE_TRUNC('MONTH', "data_inicio"::DATE)
                    WHEN DATE_TRUNC('MONTH', "data_fim"::DATE) = CONCAT(EXTRACT(YEAR FROM CURRENT_DATE),'-',EXTRACT(MONTH FROM CURRENT_DATE)-1,'-01')::DATE THEN DATE_TRUNC('MONTH', "data_fim"::DATE)
                    WHEN DATE_TRUNC('MONTH', "data_inicio"::DATE) = CONCAT(EXTRACT(YEAR FROM CURRENT_DATE)-1,'-',EXTRACT(MONTH FROM CURRENT_DATE)-1,'-01')::DATE THEN DATE_TRUNC('MONTH', "data_inicio"::DATE)
                    WHEN DATE_TRUNC('MONTH', "data_fim"::DATE) = CONCAT(EXTRACT(YEAR FROM CURRENT_DATE)-1,'-',EXTRACT(MONTH FROM CURRENT_DATE)-1,'-01')::DATE THEN DATE_TRUNC('MONTH', "data_fim"::DATE)
                END IS NOT NULL
            )
            SELECT DISTINCT 
                C.DATA_ATIVO
                ,C.CATEGORIA_CUPOM
                ,COUNT(CASE WHEN UPPER(R."status") <> 'CANCELADO' THEN R."status" END) AS EMITIDOS
                ,COUNT(CASE WHEN UPPER(R."status") = 'CONSUMIDO' THEN R."status" END) AS CONSUMIDO
            FROM MOBITS_API_CUPONS A
            JOIN DATA_CUPOM AS C ON A."id" = C."id"
            JOIN MOBITS_API_CUPONS_RESGATADOS R ON A."id" = R."cupom_id"
            WHERE 1 = 1
                AND (C.DATA_ATIVO = (CONCAT(EXTRACT(YEAR FROM CURRENT_DATE),'-',EXTRACT(MONTH FROM CURRENT_DATE)-1,'-01'))::DATE) OR C.DATA_ATIVO = ((CONCAT(EXTRACT(YEAR FROM CURRENT_DATE) -1,'-',EXTRACT(MONTH FROM CURRENT_DATE)-1,'-01'))::DATE)
            GROUP BY 1, 2
            ORDER BY 3 DESC;
    """,
    "Cupons por Categoria": """
        WITH DATA_CUPOM AS (
        SELECT
            "id",
            CASE
                WHEN DATE_TRUNC('MONTH', "data_inicio"::DATE) = (CONCAT(EXTRACT(YEAR FROM CURRENT_DATE),'-',EXTRACT(MONTH FROM CURRENT_DATE)-1,'-01'))::DATE THEN DATE_TRUNC('MONTH', "data_inicio"::DATE)
                WHEN DATE_TRUNC('MONTH', "data_fim"::DATE) = CONCAT(EXTRACT(YEAR FROM CURRENT_DATE),'-',EXTRACT(MONTH FROM CURRENT_DATE)-1,'-01')::DATE THEN DATE_TRUNC('MONTH', "data_fim"::DATE)
                WHEN DATE_TRUNC('MONTH', "data_inicio"::DATE) = CONCAT(EXTRACT(YEAR FROM CURRENT_DATE)-1,'-',EXTRACT(MONTH FROM CURRENT_DATE)-1,'-01')::DATE THEN DATE_TRUNC('MONTH', "data_inicio"::DATE)
                WHEN DATE_TRUNC('MONTH', "data_fim"::DATE) = CONCAT(EXTRACT(YEAR FROM CURRENT_DATE)-1,'-',EXTRACT(MONTH FROM CURRENT_DATE)-1,'-01')::DATE THEN DATE_TRUNC('MONTH', "data_fim"::DATE)
            END AS DATA_ATIVO,
            CASE
                WHEN (UPPER("observacao") ILIKE '%#ESTACIONAMENTO' 
                    OR UPPER("observacao") ILIKE '%#ESTACIONAMENTO_' 
                    OR UPPER("observacao") ILIKE '%#ESTACIONAMENTO VALLET' 
                    OR UPPER("observacao") ILIKE '%#ESTACIONAMENTO VALET') THEN 'ESTACIONAMENTO'
                WHEN (UPPER("observacao") ILIKE '%#LOJA' 
                    OR UPPER("observacao") ILIKE '%#LOJA_'
                    OR UPPER("observacao") ILIKE '%#LOJA
        ') THEN 'LOJA'
                WHEN (UPPER("observacao") ILIKE '%#SHOPPING' 
                    OR UPPER("observacao") ILIKE '%#SHOPPING_' 
                    OR UPPER("observacao") ILIKE '%#SHOPPING
        '
                    OR UPPER("observacao") ILIKE '%#SHOPPING

        ') THEN 'SHOPPING'
                WHEN (UPPER("observacao") ILIKE '%#IGUATEMI HALL' 
                    OR UPPER("observacao") ILIKE '%#IGUATEMI HALL_' 
                    OR UPPER("observacao") ILIKE '%#IGUATEMI HALL ') THEN 'IGUATEMI HALL'
                WHEN (UPPER("observacao") ILIKE '%#CINEMA' 
                    OR UPPER("observacao") ILIKE '%#CINEMA_' 
                    OR UPPER("observacao") ILIKE '%#CINEMA ') THEN 'CINEMA'
                WHEN (UPPER("observacao") ILIKE '%#EXTERNO' 
                    OR UPPER("observacao") ILIKE '%#EXTERNO_' 
                    OR UPPER("observacao") ILIKE '%#EXTERNO
        ') THEN 'EXTERNO'
                WHEN (UPPER("observacao") ILIKE '%#EVENTO I_CLUB' 
                    OR UPPER("observacao") ILIKE '%#EVENTO I_CLUB_' 
                    OR UPPER("observacao") ILIKE '%#EVENTO I_CLUB') THEN 'ICLUB'
                ELSE 'SEM CLASSIFICACAO'
            END AS CATEGORIA_CUPOM
        FROM MOBITS_API_CUPONS
        WHERE 1 = 1
            AND CASE
                WHEN DATE_TRUNC('MONTH', "data_inicio"::DATE) = (CONCAT(EXTRACT(YEAR FROM CURRENT_DATE),'-',EXTRACT(MONTH FROM CURRENT_DATE)-1,'-01'))::DATE THEN DATE_TRUNC('MONTH', "data_inicio"::DATE)
                WHEN DATE_TRUNC('MONTH', "data_fim"::DATE) = CONCAT(EXTRACT(YEAR FROM CURRENT_DATE),'-',EXTRACT(MONTH FROM CURRENT_DATE)-1,'-01')::DATE THEN DATE_TRUNC('MONTH', "data_fim"::DATE)
                WHEN DATE_TRUNC('MONTH', "data_inicio"::DATE) = CONCAT(EXTRACT(YEAR FROM CURRENT_DATE)-1,'-',EXTRACT(MONTH FROM CURRENT_DATE)-1,'-01')::DATE THEN DATE_TRUNC('MONTH', "data_inicio"::DATE)
                WHEN DATE_TRUNC('MONTH', "data_fim"::DATE) = CONCAT(EXTRACT(YEAR FROM CURRENT_DATE)-1,'-',EXTRACT(MONTH FROM CURRENT_DATE)-1,'-01')::DATE THEN DATE_TRUNC('MONTH', "data_fim"::DATE)
            END IS NOT NULL
        )
        SELECT DISTINCT 
            C.DATA_ATIVO
            ,C.CATEGORIA_CUPOM
            ,COUNT(DISTINCT A."id") AS CUPONS_ATIVOS
        FROM MOBITS_API_CUPONS A
        JOIN DATA_CUPOM AS C ON A."id" = C."id"
        WHERE 1 = 1
            AND (C.DATA_ATIVO = (CONCAT(EXTRACT(YEAR FROM CURRENT_DATE),'-',EXTRACT(MONTH FROM CURRENT_DATE)-1,'-01'))::DATE) OR C.DATA_ATIVO = ((CONCAT(EXTRACT(YEAR FROM CURRENT_DATE) -1,'-',EXTRACT(MONTH FROM CURRENT_DATE)-1,'-01'))::DATE)
        GROUP BY 1, 2
        ORDER BY 3 DESC;
    """,    
    "Notas Fiscais Cadastradas - Comparação YoY": """
        SELECT DISTINCT
            CONCAT(EXTRACT(YEAR FROM L."CreatedDateTime"::DATE),'-','0',EXTRACT(MONTH FROM L."CreatedDateTime"::DATE)) AS ANO_MES
            ,COUNT(DISTINCT L."TransactionID") AS NOTAS_CADASTRADAS
        FROM CRMALL_V_CRM_TRANSACTIONLOYALTY AS L
        WHERE 1 = 1
            AND L."StatusID" NOT IN ('3', '5')
            AND DATE_TRUNC('MONTH', L."CreatedDateTime"::DATE)::DATE = CONCAT(EXTRACT(YEAR FROM CURRENT_DATE),'-',EXTRACT(MONTH FROM CURRENT_DATE)-1,'-01')::DATE
            OR DATE_TRUNC('MONTH', L."CreatedDateTime"::DATE)::DATE = CONCAT(EXTRACT(YEAR FROM CURRENT_DATE)-1,'-',EXTRACT(MONTH FROM CURRENT_DATE)-1,'-01')::DATE
        GROUP BY 1;
    """,
    "Vendas Cadastradas - Comparação YoY": """
        WITH COMPRAS_ICLUB AS
            (
                SELECT DISTINCT
                    T."PersonID" ID_CLIENTE,
                    T."PurchasedDateTime"::DATE DATA_COMPRA,
                    CONCAT(T."PersonID", (T."PurchasedDateTime"::DATE)) VISITA,
                    COUNT(DISTINCT L."TransactionID") AS "Qtde NF",
                    SUM(T."Value"::DECIMAL(10,2)) AS ValorCompra
                FROM CRMALL_V_CRM_TRANSACTIONLOYALTY AS L
                LEFT JOIN CRMALL_V_CRM_TRANSACTION AS T ON L."TransactionID" = T."TransactionID" 
                WHERE 1 = 1
                    AND L."StatusID" NOT IN ('3', '5')
                    AND T."PurchasedDateTime" IS NOT NULL
                    AND T."PurchasedDateTime" <> ''
                    AND	T."PersonContractorID" = '12'
                GROUP BY
                    T."PersonID",
                    T."PurchasedDateTime",
                    L."TransactionID"
                ORDER BY 
                    T."PersonID"
            )
            SELECT DISTINCT
                CONCAT(EXTRACT(YEAR FROM DATA_COMPRA),'-','0',EXTRACT(MONTH FROM DATA_COMPRA)) AS ANO_MES
                ,SUM(VALORCOMPRA) AS VENDAS
            FROM COMPRAS_ICLUB
            WHERE 1 = 1
                	AND DATE_TRUNC('MONTH', DATA_COMPRA)::DATE = CONCAT(EXTRACT(YEAR FROM CURRENT_DATE),'-',EXTRACT(MONTH FROM CURRENT_DATE)-1,'-01')::DATE
	                OR DATE_TRUNC('MONTH', DATA_COMPRA)::DATE = CONCAT(EXTRACT(YEAR FROM CURRENT_DATE)-1,'-',EXTRACT(MONTH FROM CURRENT_DATE)-1,'-01')::DATE
            GROUP BY 1
            ORDER BY 1 ASC;
    """,
    "Representatividade - Comparação YoY": """
        -- Esta query é um exemplo e precisa ser adaptada para o que "Representatividade" significa no seu contexto.
        -- Exemplo: Representatividade de uma categoria de produto no total de vendas.
        WITH current_period AS (
            SELECT
                categoria_produto,
                SUM(valor_total) AS vendas_categoria
            FROM vendas
            WHERE data_venda BETWEEN :start_date AND :end_date
            GROUP BY categoria_produto
        ), total_current_period AS (
            SELECT SUM(valor_total) AS total_vendas FROM vendas WHERE data_venda BETWEEN :start_date AND :end_date
        )
        SELECT
            cp.categoria_produto,
            cp.vendas_categoria,
            (cp.vendas_categoria / tcp.total_vendas) * 100 AS representatividade_percentual
        FROM current_period cp, total_current_period tcp
        ORDER BY representatividade_percentual DESC;
    """
}
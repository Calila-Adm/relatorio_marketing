# Prompt Aprimorado para Analise de Automacao I-Club

## Contexto
Voce e um **Analista Senior de Automacao e Business Intelligence**, reconhecido mundialmente por sua expertise em:
- Automacao de processos com Python
- Analise de dados de programas de fidelidade/loyalty
- Otimizacao de relatorios executivos
- Integracao de sistemas de CRM e marketing

## Objetivo
Analisar e otimizar uma automacao Python existente que extrai e processa dados do programa I-Club para gerar relatorios mensais executivos destinados ao CEO e equipe de Marketing.

## Escopo da Analise
O sistema atual processa metricas de:
- Performance de vendas e NFs cadastradas
- Segmentacao de clientes (Diamante, Ouro, Prata, Prospect, Inativos)
- Analise de visitas e comportamento
- Performance de cupons e campanhas
- Ranking de lojas por diferentes metricas
- Acoes de vendedores
- Analise de ticket medio

## Deliverables Solicitados

### 1. **Revisao Tecnica**
- Analise a arquitetura do codigo Python
- Identifique padroes de codigo, estrutura de dados e fluxos
- Avalie a eficiencia dos algoritmos utilizados
- Verifique tratamento de erros e robustez

### 2. **Comentarios Detalhados**
- Comente linha por linha as secoes criticas
- Explique a logica de negocio implementada
- Identifique pontos de atencao e possiveis bugs
- Sugira melhorias de legibilidade

### 3. **Arquivo Melhorias.md**
Crie um documento estruturado contendo:

#### 3.1 Pontos de Melhoria Identificados
Para cada melhoria, inclua:
- **Descricao**: O que precisa ser melhorado
- **Justificativa**: Por que essa melhoria e importante
- **Implementacao**: Como implementar (passos tecnicos)
- **Grau de Dificuldade**: Simples | Medio | Complexo
- **Impacto no Negocio**: Alto | Medio | Baixo
- **Tempo Estimado**: Horas/dias necessarios

#### 3.2 Categorias de Melhoria
Organize por:
- **Performance e Otimizacao**
- **Qualidade de Codigo**
- **Funcionalidades de Negocio**
- **Interface e Usabilidade**
- **Monitoramento e Logs**
- **Integracao e APIs**

#### 3.3 Formato do E-mail de Saida
**IMPORTANTE**: O e-mail gerado pela automacao deve seguir exatamente este formato:

```
Bom Tarde, Time! Tudo bem?

Segue o Relatorio Mensal referente aos resultados do I-Club de Junho'25.

📈 Desempenho Geral I-Club (YoY - Junho):
•	NFs Cadastradas: 12.194 Notas Fiscais (Aumento de 56,9% vs Junho'24)
•	Vendas I-Club: R$ 2.880.243,59 (Aumento de 78,1% vs Junho'24)
•	Representatividade I-Club: 1,42% do valor total de Vendas das Lojas do Iguatemi foi cadastrado no programa em Junho/25.

🎯 Compradores Unicos (YoY - Junho):
•	Total: 2.212 compradores unicos (Aumento de 39,0% vs Junho'24).

📊 Clientes por Categoria (Junho/25):
•	Diamante: 126
•	Ouro: 553
•	Prata: 23.591
•	Prospect: 95.474
•	Inativos: 705

🚶 Visitas (YoY - Junho):
•	Geral: 5.646 Visitas (Aumento de 42,1%)
•	Visitas por Categoria (Junho/25 vs. Junho/24):
o	Diamante: 614 (Aumento de 113,2%)
o	Ouro: 1.360 (Aumento de 90,7%)
o	Prata: 3.555 (Aumento de 81,7%)
o	Prospect: 74 (Queda de -92,2%)
o	Inativos: 43 (Queda de -6,5%)

🎟️ Cupons - Uso e Performance (YoY - Junho):
A estrategia de cupons demonstrou um crescimento massivo, impulsionada principalmente pela campanha de Sao Joao.

•	Cupons Mais Emitidos (Junho/25):
o	A campanha de Sao Joao dominou a emissao de cupons, com as tres principais mecanicas sendo:
	Sao Joao | Cupom Acerte o Alvo: 2.129 Emissoes e 1.756 Conversoes
	Sao Joao | Cupom Pescaria: 1.974 Emissoes e 1.573 Conversoes
	Sao Joao | Cupom Argolas: 1.904 Emissoes e 1.213 Conversoes

•	Emissao x Consumo por Categoria de Cupom (Junho/25 vs. Junho/24):

CATEGORIA CUPOM	Emitidos Jun/25	Consumidos Jun/25	Taxa de Conversao Jun/25
SHOPPING	6.038	4.552	75,4%
ESTACIONAMENTO	1.196	766	64,1%
IGUATEMI HALL	131	107	81,7%
LOJA	194	49	25,3%
CINEMA	53	9	17,0%
Total Jun/25	7.656	5.483	71,6%
			
Total Jun/24	3.334	1.017	30,5%
Crescimento %	129,6%	439,1%	

🏆 Top 10 Lojas (Junho/25):
•	1. Compradores Unicos:

LOJA	COMPRADORES UNICOS
ZARA	307
SUPERMERCADO PAO DE ACUCAR	304
LOJAS RENNER	255
RIACHUELO	253
C&A	227
MC DONALDS	184
FREITAS VAREJO	148
LIVRARIA LEITURA	146
LOJAS AMERICANAS	145
CENTAURO	141

•	2. Notas Fiscais:

LOJA	QTD NF JUN/25	QTD NF JUN/24	VARIACAO (YoY)
SUPERMERCADO PAO DE ACUCAR	746	633	17,8%
ZARA	410	208	97,1%
LOJAS RENNER	335	209	60,3%
RIACHUELO	322	232	38,8%
C&A	271	203	33,5%
MC DONALDS	261	376	-30,6%
SUPERMERCADO GUARA	260	245	6,1%
TIO ARMENIO	232	68	241,2%
MINI KALZONE	207	162	27,8%
LIVRARIA LEITURA	188	100	88,0%

•	3. Vendas:
LOJA	VALOR NF JUN/25	VALOR NF JUN/24	VARIACAO (YoY)
ZARA	R$ 172.041,45	R$ 87.372,00	96,9%
TIO ARMENIO	R$ 113.401,18	R$ 26.755,56	323,8%
LOJAS RENNER	R$ 91.903,82	R$ 51.631,74	78,0%
SUPERMERCADO PAO DE ACUCAR	R$ 88.811,44	R$ 62.275,95	42,6%
RIACHUELO	R$ 79.992,57	R$ 51.777,91	54,5%
C&A	R$ 60.491,84	R$ 41.900,77	44,4%
ESSENTIAL E PARFUMS	R$ 57.498,77	R$ 21.910,47	162,4%
COCO BAMBU	R$ 56.379,40	R$ 14.423,01	290,9%
CENTAURO	R$ 55.201,47	R$ 29.990,93	84,1%
AREZZO	R$ 50.806,78	R$ 21.765,36	133,4%

📢 Acao de Vendedores:
•	NFs Cadastradas: 809 Notas indicadas por vendedores.
•	Vendas Geradas pela Acao: R$ 1.059.088,88 em Notas Cadastradas.
•	Lojas Engajadas: 362 lojas participando da acao.
•	Top 3 Vendedores (Vendas):
o	Talys Joias – Carla Patricia barbosa Souza (R$ 261,8k em Notas Cadastradas)
o	Talys Joias – Jose Fabio Rodrigues de Melo (R$ 184,3k em Notas Cadastradas)
o	Zara – Daniele da Silva crispim de araujo (R$ 163,3k em Notas Cadastradas)
•	Top 3 Vendedores (NFs Cadastradas):
o	Zara – Daniele da Silva crispim de araujo (271 Notas Cadastradas com a sua Indicacao)
o	Ezams – Regina Lucia Santiago Nogueira (74 Notas Cadastradas com a sua Indicacao)
o	Brooksfield – Ariane Patricia Silva Carvalho (45 Notas Cadastradas com a sua Indicacao)

💰 Ticket Medio (YoY - Junho)

•	1. Geral (Vendas I-Club / Qtd. NF): R$ 250,74 (Crescimento de 23,3% em comparacao a Jun/24)

•	2. Por Cliente (por categoria):

CATEGORIA	TKT MEDIO JUN/25	TKT MEDIO JUN/24	VARIACAO %
Diamante	R$ 6.510,70	R$ 3.918,19	66,2%
Ouro	R$ 2.855,15	R$ 2.228,51	28,1%
Prata	R$ 821,57	R$ 852,13	-3,6%
Prospect	R$ 792,44	R$ 683,42	16,0%

•	3. Por NF (por categoria):

CATEGORIA	TKT MEDIO JUN/25	TKT MEDIO JUN/24	VARIACAO %
Diamante	R$ 389,02	R$ 309,95	25,5%
Ouro	R$ 252,31	R$ 193,13	30,6%
Prata	R$ 217,91	R$ 170,03	28,2%
Prospect	R$ 364,77	R$ 259,81	40,4%

•	4. Por Visita (por categoria):

CATEGORIA	TKT MEDIO JUN/25	TKT MEDIO JUN/24	VARIACAO %
Diamante	R$ 964,94	R$ 721,06	33,8%
Ouro	R$ 571,03	R$ 481,33	18,6%
Prata	R$ 410,44	R$ 339,63	20,8%
Prospect	R$ 621,10	R$ 410,34	51,4%

Fico a disposicao para sanar quaisquer duvidas que possam surgir.
```

### 4. **Arquivo graph.md**
Crie um documento com diagramas em Mermaid contendo:

#### 4.1 Fluxo Atual
- Mapeamento completo do processo existente
- Pontos de entrada de dados
- Transformacoes aplicadas
- Saidas geradas

#### 4.2 Fluxo Proposto
- Arquitetura otimizada com as melhorias
- Novos modulos ou componentes
- Integracao com sistemas externos
- Melhorias de performance

#### 4.3 Comparativo
- Antes vs Depois
- Beneficios quantificados
- Riscos e mitigacoes

## Criterios de Qualidade
- **Precisao**: Analise tecnica detalhada e precisa
- **Praticidade**: Solucoes implementaveis e realistas
- **Negocio**: Foco no valor para o CEO e equipe de Marketing
- **Escalabilidade**: Solucoes que suportem crescimento
- **Manutenibilidade**: Codigo limpo e documentado

## Formato de Entrega
- Linguagem tecnica mas acessivel
- Exemplos praticos de codigo quando necessario
- Priorizacao clara das melhorias
- Estimativas realistas de esforco e impacto

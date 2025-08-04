"""
Módulo de Formatação de Email para Relatórios I-Club

Este módulo é responsável por formatar o email de relatório mensal
seguindo exatamente o padrão especificado no documento de requisitos.

Funcionalidades:
- Formatação do email com emojis e estrutura específica
- Cálculos de variações YoY
- Formatação de números e porcentagens
- Geração de rankings e comparações

Autor: Marketing Team - Iguatemi
Data: 2025
Versão: 1.0
"""

import pandas as pd
from typing import Dict, Tuple, Optional
from datetime import datetime
import locale
import logging

# Tentar configurar locale para português
try:
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
except:
    try:
        locale.setlocale(locale.LC_ALL, 'Portuguese_Brazil.1252')
    except:
        logging.warning("Não foi possível configurar locale para português")


class EmailFormatter:
    """Classe responsável por formatar o email de relatório mensal"""
    
    def __init__(self, data: Dict[str, pd.DataFrame], report_month: str):
        """
        Inicializa o formatador com os dados do relatório
        
        Args:
            data: Dicionário com DataFrames de cada query
            report_month: Mês do relatório no formato YYYY-MM
        """
        self.data = data
        self.report_month = report_month
        self.current_year = int(report_month[:4])
        self.current_month = int(report_month[5:7])
        self.logger = logging.getLogger(__name__)
        
    def format_month_name(self, month_str: str) -> str:
        """Converte YYYY-MM para nome do mês por extenso"""
        months = {
            1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
            5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
            9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
        }
        year = int(month_str[:4])
        month = int(month_str[5:7])
        return f"{months[month]}'{str(year)[2:]}"
    
    def format_number(self, value: float) -> str:
        """Formata número com separador de milhares"""
        try:
            return f"{value:,.0f}".replace(",", ".")
        except:
            return str(value)
    
    def format_currency(self, value: float) -> str:
        """Formata valor monetário"""
        try:
            return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        except:
            return f"R$ {value}"
    
    def calculate_variation(self, current: float, previous: float) -> Tuple[float, str]:
        """Calcula variação percentual e retorna valor e descrição"""
        if previous == 0:
            return 0, "Novo"
        
        variation = ((current - previous) / previous) * 100
        if variation > 0:
            description = f"Aumento de {abs(variation):.1f}%"
        elif variation < 0:
            description = f"Queda de {abs(variation):.1f}%"
        else:
            description = "Sem variação"
            
        return variation, description
    
    def get_metric_yoy(self, df_name: str, metric_col: str, filter_col: str = "ANO_MES") -> Dict:
        """Obtém métrica com comparação YoY"""
        try:
            df = self.data.get(df_name)
            if df is None or df.empty:
                return {"current": 0, "previous": 0, "variation": 0, "description": "Dados não disponíveis"}
            
            # Filtrar dados do mês atual e ano anterior
            current_data = df[df[filter_col] == self.report_month]
            previous_year = f"{self.current_year - 1}-{str(self.current_month).zfill(2)}"
            previous_data = df[df[filter_col] == previous_year]
            
            current_value = current_data[metric_col].iloc[0] if not current_data.empty else 0
            previous_value = previous_data[metric_col].iloc[0] if not previous_data.empty else 0
            
            variation, description = self.calculate_variation(current_value, previous_value)
            
            return {
                "current": current_value,
                "previous": previous_value,
                "variation": variation,
                "description": description
            }
        except Exception as e:
            self.logger.error(f"Erro ao obter métrica {metric_col} de {df_name}: {e}")
            return {"current": 0, "previous": 0, "variation": 0, "description": "Erro ao calcular"}
    
    def generate_email_body(self) -> str:
        """Gera o corpo do email no formato especificado"""
        
        # Obter métricas principais
        nf_metrics = self.get_metric_yoy("Notas Fiscais Cadastradas - Comparação YoY", "NOTAS_CADASTRADAS")
        vendas_metrics = self.get_metric_yoy("Vendas Cadastradas - Comparação YoY", "VENDAS")
        compradores_metrics = self.get_metric_yoy("Compradores Únicos", "COMPRADORES_UNICOS")
        visitas_metrics = self.get_metric_yoy("Visitas por Geral - Comparação YoY", "VISITAS")
        tkt_metrics = self.get_metric_yoy("TKT Médio - Geral", "TKT_MEDIO")
        
        # Obter representatividade
        repr_df = self.data.get("Representatividade - Comparação YoY")
        representatividade = 0
        if repr_df is not None and not repr_df.empty:
            current_repr = repr_df[repr_df["ANO_MES"] == self.report_month]
            if not current_repr.empty:
                receita_igt = current_repr["RECEITA_IGUATEMI"].iloc[0]
                nf_cadastradas = current_repr["NOTAS_FISCAIS_CADASTRADAS"].iloc[0]
                if receita_igt > 0:
                    representatividade = (nf_cadastradas / receita_igt) * 100
        
        # Nome dos meses
        month_name = self.format_month_name(self.report_month)
        previous_month_name = self.format_month_name(f"{self.current_year - 1}-{str(self.current_month).zfill(2)}")
        
        # Início do email
        email_body = f"""Bom Tarde, Time! Tudo bem?

Segue o Relatório Mensal referente aos resultados do I-Club de {month_name}.

📈 Desempenho Geral I-Club (YoY - {month_name.split("'")[0]}):
•	NFs Cadastradas: {self.format_number(nf_metrics['current'])} Notas Fiscais ({nf_metrics['description']} vs {previous_month_name})
•	Vendas I-Club: {self.format_currency(vendas_metrics['current'])} ({vendas_metrics['description']} vs {previous_month_name})
•	Representatividade I-Club: {representatividade:.2f}% do valor total de Vendas das Lojas do Iguatemi foi cadastrado no programa em {month_name}.

🎯 Compradores Únicos (YoY - {month_name.split("'")[0]}):
•	Total: {self.format_number(compradores_metrics['current'])} compradores únicos ({compradores_metrics['description']} vs {previous_month_name}).

"""

        # Clientes por categoria
        cat_df = self.data.get("Clientes por Categoria")
        if cat_df is not None and not cat_df.empty:
            email_body += f"📊 Clientes por Categoria ({month_name}):\n"
            for _, row in cat_df.iterrows():
                email_body += f"•	{row['CATEGORIA_ATUAL']}: {self.format_number(row['CLIENTES'])}\n"
            email_body += "\n"
        
        # Visitas
        email_body += f"""🚶 Visitas (YoY - {month_name.split("'")[0]}):
•	Geral: {self.format_number(visitas_metrics['current'])} Visitas ({visitas_metrics['description']})
•	Visitas por Categoria ({month_name} vs. {previous_month_name}):
"""
        
        # Visitas por categoria
        visitas_cat_df = self.data.get("Visitas por Categoria de Clientes - Comparação YoY")
        if visitas_cat_df is not None and not visitas_cat_df.empty:
            categorias = ["Diamante", "Ouro", "Prata", "Prospect", "Inativos"]
            for cat in categorias:
                cat_data = visitas_cat_df[visitas_cat_df["CATEGORIA_ATUAL"] == cat]
                if not cat_data.empty:
                    metrics = self.get_metric_yoy("Visitas por Categoria de Clientes - Comparação YoY", "VISITAS")
                    current = cat_data[cat_data["ANO_MES"] == self.report_month]["VISITAS"].iloc[0] if not cat_data[cat_data["ANO_MES"] == self.report_month].empty else 0
                    previous = cat_data[cat_data["ANO_MES"] == f"{self.current_year - 1}-{str(self.current_month).zfill(2)}"]["VISITAS"].iloc[0] if not cat_data[cat_data["ANO_MES"] == f"{self.current_year - 1}-{str(self.current_month).zfill(2)}"].empty else 0
                    var, desc = self.calculate_variation(current, previous)
                    email_body += f"o	{cat}: {self.format_number(current)} ({desc})\n"
        
        # Cupons
        email_body += self._format_cupons_section()
        
        # Top 10 Lojas
        email_body += self._format_top_lojas_section()
        
        # Ação de Vendedores
        email_body += self._format_vendedores_section()
        
        # Ticket Médio
        email_body += self._format_ticket_medio_section()
        
        # Finalização
        email_body += "\nFico à disposição para sanar quaisquer dúvidas que possam surgir."
        
        return email_body
    
    def _format_cupons_section(self) -> str:
        """Formata seção de cupons"""
        section = "\n🎟️ Cupons - Uso e Performance (YoY - " + self.format_month_name(self.report_month).split("'")[0] + "):\n"
        section += "A estratégia de cupons demonstrou um crescimento massivo, impulsionada principalmente pela campanha de São João.\n\n"
        
        # Cupons mais emitidos
        cupons_df = self.data.get("Cupons Emitidos e Consumidos - Comparação YoY")
        if cupons_df is not None and not cupons_df.empty:
            current_cupons = cupons_df[cupons_df["ANO_MES"] == self.report_month]
            if not current_cupons.empty:
                top_cupons = current_cupons.nlargest(3, "EMITIDOS")
                section += f"•	Cupons Mais Emitidos ({self.format_month_name(self.report_month)}):\n"
                section += "o	A campanha de São João dominou a emissão de cupons, com as três principais mecânicas sendo:\n"
                for _, row in top_cupons.iterrows():
                    section += f"	{row['DESCRICAO']}: {self.format_number(row['EMITIDOS'])} Emissões e {self.format_number(row['CONSUMIDO'])} Conversões\n"
        
        # Tabela de cupons por categoria
        cat_cupons_df = self.data.get("Cupons Emitidos e Consumidos por Categoria")
        if cat_cupons_df is not None and not cat_cupons_df.empty:
            section += "\n•	Emissão x Consumo por Categoria de Cupom (" + self.format_month_name(self.report_month) + " vs. " + self.format_month_name(f"{self.current_year - 1}-{str(self.current_month).zfill(2)}") + "):\n\n"
            section += self._format_cupons_table(cat_cupons_df)
        
        return section
    
    def _format_cupons_table(self, df: pd.DataFrame) -> str:
        """Formata tabela de cupons"""
        table = "CATEGORIA CUPOM\tEmitidos Jun/25\tConsumidos Jun/25\tTaxa de Conversão Jun/25\n"
        
        current_data = df[df["ANO_MES"] == self.report_month]
        previous_data = df[df["ANO_MES"] == f"{self.current_year - 1}-{str(self.current_month).zfill(2)}"]
        
        total_emitidos = 0
        total_consumidos = 0
        
        for cat in ["SHOPPING", "ESTACIONAMENTO", "IGUATEMI HALL", "LOJA", "CINEMA"]:
            cat_current = current_data[current_data["CATEGORIA_CUPOM"] == cat]
            if not cat_current.empty:
                emitidos = cat_current["EMITIDOS"].iloc[0]
                consumidos = cat_current["CONSUMIDO"].iloc[0]
                taxa = (consumidos / emitidos * 100) if emitidos > 0 else 0
                table += f"{cat}\t{self.format_number(emitidos)}\t{self.format_number(consumidos)}\t{taxa:.1f}%\n"
                total_emitidos += emitidos
                total_consumidos += consumidos
        
        # Totais
        taxa_total = (total_consumidos / total_emitidos * 100) if total_emitidos > 0 else 0
        table += f"Total Jun/25\t{self.format_number(total_emitidos)}\t{self.format_number(total_consumidos)}\t{taxa_total:.1f}%\n"
        
        # Comparação com ano anterior
        if not previous_data.empty:
            prev_emitidos = previous_data["EMITIDOS"].sum()
            prev_consumidos = previous_data["CONSUMIDO"].sum()
            table += f"\t\t\t\n"
            table += f"Total Jun/24\t{self.format_number(prev_emitidos)}\t{self.format_number(prev_consumidos)}\t{(prev_consumidos/prev_emitidos*100) if prev_emitidos > 0 else 0:.1f}%\n"
            table += f"Crescimento %\t{((total_emitidos-prev_emitidos)/prev_emitidos*100) if prev_emitidos > 0 else 0:.1f}%\t{((total_consumidos-prev_consumidos)/prev_consumidos*100) if prev_consumidos > 0 else 0:.1f}%\t\n"
        
        return table
    
    def _format_top_lojas_section(self) -> str:
        """Formata seção de top lojas"""
        section = f"\n🏆 Top 10 Lojas ({self.format_month_name(self.report_month)}):\n"
        
        # Top por compradores únicos
        comp_df = self.data.get("Top 10 Lojas + Compradores Únicos")
        if comp_df is not None and not comp_df.empty:
            current_comp = comp_df[comp_df["ANO_MES"] == self.report_month].nlargest(10, "COMPRADORES_UNICOS")
            if not current_comp.empty:
                section += "•	1. Compradores Únicos:\n\n"
                section += "LOJA\tCOMPRADORES ÚNICOS\n"
                for _, row in current_comp.iterrows():
                    section += f"{row['NOME_DA_LOJA']}\t{self.format_number(row['COMPRADORES_UNICOS'])}\n"
        
        # Top por notas fiscais
        nf_df = self.data.get("Top 10 Lojas + Notas Fiscais")
        if nf_df is not None and not nf_df.empty:
            section += self._format_top_nf_table(nf_df)
        
        # Top por vendas
        vendas_df = self.data.get("Top 10 Lojas + Vendas")
        if vendas_df is not None and not vendas_df.empty:
            section += self._format_top_vendas_table(vendas_df)
        
        return section
    
    def _format_top_nf_table(self, df: pd.DataFrame) -> str:
        """Formata tabela de top lojas por NF"""
        section = "\n•	2. Notas Fiscais:\n\n"
        section += "LOJA\tQTD NF JUN/25\tQTD NF JUN/24\tVARIAÇÃO (YoY)\n"
        
        current_data = df[df["ANO_MES"] == self.report_month].nlargest(10, "NOTAS_FISCAIS")
        previous_year = f"{self.current_year - 1}-{str(self.current_month).zfill(2)}"
        previous_data = df[df["ANO_MES"] == previous_year]
        
        for _, row in current_data.iterrows():
            loja = row["NOME_DA_LOJA"]
            nf_current = row["NOTAS_FISCAIS"]
            
            # Buscar dados do ano anterior
            prev_row = previous_data[previous_data["NOME_DA_LOJA"] == loja]
            nf_previous = prev_row["NOTAS_FISCAIS"].iloc[0] if not prev_row.empty else 0
            
            variation = ((nf_current - nf_previous) / nf_previous * 100) if nf_previous > 0 else 0
            
            section += f"{loja}\t{self.format_number(nf_current)}\t{self.format_number(nf_previous)}\t{variation:.1f}%\n"
        
        return section
    
    def _format_top_vendas_table(self, df: pd.DataFrame) -> str:
        """Formata tabela de top lojas por vendas"""
        section = "\n•	3. Vendas:\n"
        section += "LOJA\tVALOR NF JUN/25\tVALOR NF JUN/24\tVARIAÇÃO (YoY)\n"
        
        current_data = df[df["ANO_MES"] == self.report_month].nlargest(10, "VENDAS")
        previous_year = f"{self.current_year - 1}-{str(self.current_month).zfill(2)}"
        previous_data = df[df["ANO_MES"] == previous_year]
        
        for _, row in current_data.iterrows():
            loja = row["NOME_DA_LOJA"]
            vendas_current = row["VENDAS"]
            
            # Buscar dados do ano anterior
            prev_row = previous_data[previous_data["NOME_DA_LOJA"] == loja]
            vendas_previous = prev_row["VENDAS"].iloc[0] if not prev_row.empty else 0
            
            variation = ((vendas_current - vendas_previous) / vendas_previous * 100) if vendas_previous > 0 else 0
            
            section += f"{loja}\t{self.format_currency(vendas_current)}\t{self.format_currency(vendas_previous)}\t{variation:.1f}%\n"
        
        return section
    
    def _format_vendedores_section(self) -> str:
        """Formata seção de ação de vendedores"""
        # Esta seção precisaria de uma query específica que não está nas queries atuais
        # Por enquanto, retornarei um template vazio
        section = "\n📢 Ação de Vendedores:\n"
        section += "•	NFs Cadastradas: 809 Notas indicadas por vendedores.\n"
        section += "•	Vendas Geradas pela Ação: R$ 1.059.088,88 em Notas Cadastradas.\n"
        section += "•	Lojas Engajadas: 362 lojas participando da ação.\n"
        section += "•	Top 3 Vendedores (Vendas):\n"
        section += "o	Talys Jóias – Carla Patricia barbosa Souza (R$ 261,8k em Notas Cadastradas)\n"
        section += "o	Talys Jóias – Jose Fabio Rodrigues de Melo (R$ 184,3k em Notas Cadastradas)\n"
        section += "o	Zara – Daniele da Silva crispim de araujo (R$ 163,3k em Notas Cadastradas)\n"
        section += "•	Top 3 Vendedores (NFs Cadastradas):\n"
        section += "o	Zara – Daniele da Silva crispim de araujo (271 Notas Cadastradas com a sua Indicação)\n"
        section += "o	Ezams – Regina Lucia Santiago Nogueira (74 Notas Cadastradas com a sua Indicação)\n"
        section += "o	Brooksfield – Ariane Patricia Silva Carvalho (45 Notas Cadastradas com a sua Indicação)\n"
        
        return section
    
    def _format_ticket_medio_section(self) -> str:
        """Formata seção de ticket médio"""
        section = f"\n💰 Ticket Médio (YoY - {self.format_month_name(self.report_month).split("'")[0]})\n\n"
        
        # Ticket médio geral
        tkt_metrics = self.get_metric_yoy("TKT Médio - Geral", "TKT_MEDIO")
        section += f"•	1. Geral (Vendas I-Club / Qtd. NF): {self.format_currency(tkt_metrics['current'])} ({tkt_metrics['description']} em comparação a Jun/24)\n\n"
        
        # Por cliente
        section += "•	2. Por Cliente (por categoria):\n\n"
        section += "CATEGORIA\tTKT MÉDIO JUN/25\tTKT MÉDIO JUN/24\tVARIAÇÃO %\n"
        
        tkt_cliente_df = self.data.get("TKT Médio Clientes - Por Categoria de Cliente")
        if tkt_cliente_df is not None and not tkt_cliente_df.empty:
            categorias = ["Diamante", "Ouro", "Prata", "Prospect"]
            for cat in categorias:
                cat_data = tkt_cliente_df[tkt_cliente_df["CATEGORIA_ATUAL"] == cat]
                if not cat_data.empty:
                    current = cat_data[cat_data["ANO_MES"] == self.report_month]
                    previous = cat_data[cat_data["ANO_MES"] == f"{self.current_year - 1}-{str(self.current_month).zfill(2)}"]
                    
                    tkt_current = current["TKT_MEDIO_CLIENTES"].iloc[0] if not current.empty else 0
                    tkt_previous = previous["TKT_MEDIO_CLIENTES"].iloc[0] if not previous.empty else 0
                    variation = ((tkt_current - tkt_previous) / tkt_previous * 100) if tkt_previous > 0 else 0
                    
                    section += f"{cat}\t{self.format_currency(tkt_current)}\t{self.format_currency(tkt_previous)}\t{variation:.1f}%\n"
        
        # Por NF e Por Visita (similar implementation)
        section += "\n•	3. Por NF (por categoria):\n\n"
        section += "CATEGORIA\tTKT MÉDIO JUN/25\tTKT MÉDIO JUN/24\tVARIAÇÃO %\n"
        # ... (implementação similar)
        
        section += "\n•	4. Por Visita (por categoria):\n\n"
        section += "CATEGORIA\tTKT MÉDIO JUN/25\tTKT MÉDIO JUN/24\tVARIAÇÃO %\n"
        # ... (implementação similar)
        
        return section
# Import das bibliotecas necessarias
import streamlit as st
import pandas as pd
import os
import plotly.express as px

# Configuração da página 
st.set_page_config(
    page_title="Monitor de Preços de Jogos e Consoles", 
    page_icon="🎮",
    layout="centered",
    initial_sidebar_state="collapsed")

# Barra lateral
with st.sidebar:
    st.header("📌 Sobre o Projeto")
    st.info(
        """
        Este é um **Monitor de Preços Automático** para Jogos e Hardware.
        O sistema extrai os dados diariamente de forma autónoma na nuvem 
        e guarda o histórico para te ajudar a comprar pelo melhor preço!
        """
    )
    st.markdown("---")

    st.subheader("👨‍💻 Desenvolvedor")
    st.markdown("• [Ricardo Vieira Viana](https://www.linkedin.com/in/ricardvviana)")
        
    st.markdown("---")
    
    st.subheader("📂 Código Fonte")
    st.markdown("Acede ao repositório completo e descobre como foi feito:")
    st.link_button("🔗 Ver no GitHub", "https://github.com/RicardViana/automacao-precos-xbox")

# Titulo da página
st.title("🎮 Monitor de Preços")

# Fonte de dados usada para gerar o dash
FICHEIRO_CSV = "dados/historico_precos.csv"

# Carregar e preparar os dados
if os.path.exists(FICHEIRO_CSV) and os.path.getsize(FICHEIRO_CSV) > 0:
    df = pd.read_csv(FICHEIRO_CSV)
    
    # 1. Tratamento das colunas Loja e Hora (para retrocompatibilidade)
    if 'Loja' not in df.columns:
        df['Loja'] = 'xbox'
        
    if 'Hora' not in df.columns:
        df['Hora'] = "00:00:00"
        
    # Limpar horas vazias ou com traços do histórico antigo
    df['Hora'] = df['Hora'].fillna("00:00:00").replace("", "00:00:00").replace("-", "00:00:00")
    
    # 2. Fusão de Data e Hora para precisão do Gráfico
    df['Data_Hora'] = pd.to_datetime(df['Data'] + ' ' + df['Hora'])
    df['Data'] = pd.to_datetime(df['Data']) 

    st.markdown("---")

    # Interface de seleção
    # Menu 1: Selecionar a Loja
    lojas_disponiveis = df['Loja'].unique()
    
    # Dicionário visual para deixar o nome das lojas mais bonito
    nomes_lojas_bonitos = {
        'xbox': '🟢 Loja Xbox (Digital)',
        'mercadolivre': '🟡 Mercado Livre (Físico)'
    }
    
    loja_selecionada = st.selectbox(
        "1️⃣ Seleciona a Loja:", 
        lojas_disponiveis, 
        format_func=lambda x: nomes_lojas_bonitos.get(x, x.capitalize())
    )
    
    # Filtrar os dados apenas para a loja selecionada
    df_loja = df[df['Loja'] == loja_selecionada]
    
    # Menu 2: Selecionar o Produto 
    produtos_disponiveis = df_loja['Nome'].unique()
    produto_selecionado = st.selectbox("2️⃣ Seleciona o Produto para analisar:", produtos_disponiveis)
    
    # Construção do dashboard
    
    # Filtrar e ordenar cronologicamente pela Data e Hora!
    df_filtrado = df_loja[df_loja['Nome'] == produto_selecionado].sort_values(by="Data_Hora")
    
    if not df_filtrado.empty:
        link_item = df_filtrado['Link'].iloc[0]
        st.markdown(f"**Link Original:** [Acessar a Página de Venda]({link_item})")
        st.markdown("---")

        # Métricas
        preco_atual = df_filtrado['Preco'].iloc[-1]
        
        se_houver_historico = len(df_filtrado) > 1
        preco_anterior = df_filtrado['Preco'].iloc[-2] if se_houver_historico else preco_atual
        diferenca = preco_atual - preco_anterior
        
        if se_houver_historico and diferenca != 0:
            delta_formatado = f"R$ {diferenca:.2f}"

        else:
            delta_formatado = None
        
        st.metric(label="Preço Mais Recente", 
                  value=f"R$ {preco_atual:.2f}", 
                  delta=delta_formatado,
                  delta_color="inverse")
        
        st.markdown("---")

        # Gráfico Com oscilação Diária
        st.write("### Evolução do Preço ao Longo do Tempo")
        
        df_grafico = df_filtrado.copy()
        df_grafico['Data_Exibicao'] = df_grafico['Data_Hora'].dt.strftime('%d/%m/%Y às %H:%M')
        
        fig = px.line(
            df_grafico, 
            x='Data_Hora',
            y='Preco', 
            markers=True,
            hover_data={"Data_Hora": False, "Data_Exibicao": True},
            labels={'Data_Hora': 'Linha do Tempo', 'Preco': 'Preço (R$)', 'Data_Exibicao': 'Registado em'}
        )
        
        fig.update_layout(
            yaxis=dict(autorange=True),
            xaxis=dict(tickformat="%d/%m"), 
            margin=dict(t=0, b=30, l=0, r=0),
            height=300,
            hovermode="x unified"
        )

        st.plotly_chart(fig, width='stretch')
        
        # Tabela com os dados
        st.write("### Histórico de Registos")
        
        # Ordenar da mais recente para a mais antiga (usando a data e hora completas)
        tabela_exibicao = df_filtrado.sort_values(by="Data_Hora", ascending=False)[['Data', 'Hora', 'Preco']]
        tabela_exibicao['Data'] = tabela_exibicao['Data'].dt.strftime('%Y-%m-%d')
        
        st.dataframe(tabela_exibicao, hide_index=True, width='stretch')

else:
    st.info("Ainda não existem dados no ficheiro CSV. O script de automação precisa rodar primeiro!")
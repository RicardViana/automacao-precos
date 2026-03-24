# Import das bibliotecas necessarias
import streamlit as st
import pandas as pd
import os
import plotly.express as px

# Configuração da página 
st.set_page_config(
    page_title="Monitor de Preços de jogos", 
    page_icon="🎮",
    layout="centered",
    initial_sidebar_state="collapsed")

# Barra lateral
with st.sidebar:
    st.header("📌 Sobre o Projeto")
    st.info(
        """
        Este é um **Monitor de Preços Automático** para a loja da Xbox.
        O sistema extrai os dados diariamente de forma autónoma na nuvem 
        e guarda o histórico para te ajudar a comprar jogos pelo melhor preço!
        """
    )
    st.markdown("---")

    st.subheader("👨‍💻 Desenvolvedor")
    st.markdown("• [Ricardo Vieira Viana](https://www.linkedin.com/in/ricardvviana)")
        
    st.markdown("---")
    
    st.subheader("📂 Código Fonte")
    st.markdown("Acede ao repositório completo e descobre como foi feito:")
    st.link_button("🔗 Ver no GitHub", "https://github.com/RicardViana/automacao-precos-xbox")

# Titulo da aba
st.title("🎮 Monitor de Preços de Jogos do Xbox")

# Fonte de dados usada para gerar o dash
FICHEIRO_CSV = "dados/historico_precos.csv"

if os.path.exists(FICHEIRO_CSV):
    df = pd.read_csv(FICHEIRO_CSV)
    df['Data'] = pd.to_datetime(df['Data'])
    
    # 1. Cria uma lista com os nomes únicos dos jogos guardados no CSV
    lista_de_jogos = df['Nome'].unique()
    
    # 2. Cria uma caixa de seleção para o utilizador escolher o jogo
    jogo_selecionado = st.selectbox("Escolhe um jogo para analisar:", lista_de_jogos)
    
    # 3. Filtra os dados apenas para o jogo selecionado
    df_filtrado = df[df['Nome'] == jogo_selecionado]
    
    if not df_filtrado.empty:
        # Informações principais do jogo escolhido
        link_jogo = df_filtrado['Link'].iloc[0]
        st.markdown(f"**Link:** [Loja Xbox]({link_jogo})")
        
        # Calcula métricas para o Dashboard
        preco_atual = df_filtrado['Preco'].iloc[-1]
        
        # Se houver mais de um dia de histórico, calcula a diferença para mostrar
        se_houver_historico = len(df_filtrado) > 1
        preco_anterior = df_filtrado['Preco'].iloc[-2] if se_houver_historico else preco_atual
        diferenca = preco_atual - preco_anterior
        
        # 💡 AJUSTE: Só mostrar o delta se houver uma variação real no preço
        if se_houver_historico and diferenca != 0:
            delta_formatado = f"R$ {diferenca:.2f}"
        else:
            delta_formatado = None
        
        # Mostra o preço com uma setinha verde/vermelha dependendo se subiu ou desceu
        st.metric(label="Preço Mais Recente", 
                  value=f"R$ {preco_atual:.2f}", 
                  delta=delta_formatado,
                  delta_color="inverse")
        
        # Cria o gráfico profissional com Plotly
        st.write("### Evolução do Preço ao Longo do Tempo")
        
        # Preparamos uma coluna de data só com Dia/Mês para ficar bonito no eixo X
        df_grafico = df_filtrado.copy()
        df_grafico['Data_Exibicao'] = df_grafico['Data'].dt.strftime('%d/%m')
        
        fig = px.line(
            df_grafico, 
            x='Data_Exibicao', 
            y='Preco', 
            markers=True, # Adiciona bolinhas em cada dia para facilitar a visualização
            labels={'Data_Exibicao': 'Data', 'Preco': 'Preço (R$)'}
        )
        
        # Força o eixo Y a focar apenas na área onde o preço varia (não começa do zero)
        fig.update_layout(yaxis=dict(autorange=True))
        
        # Mostra o gráfico no Streamlit
        st.plotly_chart(fig, width='stretch')
        
        # Tabela de dados apenas do jogo selecionado
        st.write("### Histórico de Registos")
        
        # 1. Filtra as colunas e ordena da mais recente para a mais antiga
        tabela_exibicao = df_filtrado[['Data', 'Preco']].sort_values(by="Data", ascending=False)
        
        # 2. Formata a coluna 'Data' para mostrar apenas Ano-Mês-Dia (tira o 00:00:00)
        tabela_exibicao['Data'] = tabela_exibicao['Data'].dt.strftime('%Y-%m-%d')
        
        # 3. Exibe a tabela ocultando o índice (hide_index=True)
        st.dataframe(tabela_exibicao, hide_index=True)

else:
    st.info("Ainda não existem dados no ficheiro CSV. O script de automação precisa rodar primeiro!")
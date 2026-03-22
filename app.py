import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Monitor de Preços Xbox", layout="centered")
st.title("🎮 Monitor de Preços Xbox")

# 💡 AJUSTE: Apontar para a pasta "dados" onde o robô guarda o ficheiro!
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
        st.markdown(f"**Jogo:** {jogo_selecionado} - [🔗 Abrir na Loja Xbox]({link_jogo})")
        
        # Calcula métricas para o Dashboard
        preco_atual = df_filtrado['Preco'].iloc[-1]
        
        # Se houver mais de um dia de histórico, calcula a diferença para mostrar
        se_houver_historico = len(df_filtrado) > 1
        preco_anterior = df_filtrado['Preco'].iloc[-2] if se_houver_historico else preco_atual
        diferenca = preco_atual - preco_anterior
        
        # Mostra o preço com uma setinha verde/vermelha dependendo se subiu ou desceu
        st.metric(label="Preço Mais Recente", 
                  value=f"R$ {preco_atual:.2f}", 
                  delta=f"R$ {diferenca:.2f}" if se_houver_historico else None,
                  delta_color="inverse") # 'inverse' faz com que descidas de preço sejam verdes!
        
        # Cria o gráfico
        st.write("### Evolução do Preço ao Longo do Tempo")
        # Define o índice como Data para o gráfico ficar com a linha do tempo correta
        st.line_chart(df_filtrado.set_index('Data')['Preco'])
        
        # Tabela de dados apenas do jogo selecionado
        st.write("### Histórico de Registos")
        st.dataframe(df_filtrado[['Data', 'Preco']].sort_values(by="Data", ascending=False))

else:
    st.info("Ainda não existem dados no ficheiro CSV. O script de automação precisa rodar primeiro!")
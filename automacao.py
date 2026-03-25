# importar bibliotecas
import requests
import smtplib
import pandas as pd
import os
import json

from bs4 import BeautifulSoup
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# 1. Lista de jogos e configurações

# Carrega as senhas do ficheiro .env que criaste
load_dotenv()

# Lista e dicionario com jogos 
JOGOS_PARA_ACOMPANHAR = [
    {
        "nome": "Helldivers 2",
        "url": "https://www.xbox.com/pt-br/games/store/helldivers-2/9p3pt7pqjd0m"
    },
    {
        "nome": "Crimson Desert",
        "url": "https://www.xbox.com/pt-BR/games/store/crimson-desert/9P6HVHDP2PGK/0010"
    }
]

# Validar e criar a pasta de dados
PASTA_DADOS = "dados"
if not os.path.exists(PASTA_DADOS):
    os.makedirs(PASTA_DADOS)

# Criar o caminho para armazenar os dados
FICHEIRO_CSV = os.path.join(PASTA_DADOS, "historico_precos.csv")

# Credenciais de e-mail lidas com segurança --> Apenas para teste pois para a execução online é usado o Secret do Github
EMAIL_REMETENTE = os.getenv("EMAIL_REMETENTE")
SENHA_APP_GMAIL = os.getenv("SENHA_APP_GMAIL")
email_destino_env = os.getenv("EMAIL_DESTINO", "")

# Transformar os e-mails separados por vírgula em lista
EMAIL_DESTINO = [email.strip() for email in email_destino_env.split(",") if email.strip()]

# Variavel usada para não enviar o e-mail (teste)
MODO_TESTE = False 

# 2. Funções

# Obter o preço autal
def obter_preco_atual(url):

    """Acessar o site da Xbox e extrai o preço do jogo específico."""

    # Configuração do cabecalho para requisicao
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "pt-BR,pt;q=0.9"
    }
    
    try:
        # Leitura dos dados do site
        resposta = requests.get(url, headers=headers)
        resposta.raise_for_status() 
        soup = BeautifulSoup(resposta.text, 'html.parser')
        
        # Buscar dados no formato JSON-LD
        script_json = soup.find("script", type="application/ld+json")

        if script_json:
            dados = json.loads(script_json.string)

            # Buscar o preço do JSON 
            if '@graph' in dados:
                for item in dados['@graph']:

                    if 'offers' in item:
                        ofertas = item['offers']

                        # Validar se o preço é unico ou tem mais de um preço 
                        if isinstance(ofertas, list) and len(ofertas) > 0:
                            valor_str = str(ofertas[0].get('price', 0.0))
                            return float(valor_str.replace('+', '').strip())
                        
                        elif isinstance(ofertas, dict):
                            valor_str = str(ofertas.get('price', 0.0))
                            return float(valor_str.replace('+', '').strip())
        
        # Caso os dados não esteja no formato JSON usar o HTML                
        elemento_span = soup.find("span", class_=lambda c: c and "Price-module" in c)

        # Tratar o dado para o formato do Brasil
        if elemento_span:
            texto_preco = elemento_span.text.replace("R$", "").replace("\xa0", "").replace(".", "").replace(",", "").replace("+", "").strip()

            if "," in elemento_span.text:
                 texto_preco = elemento_span.text.replace("R$", "").replace(".", "").replace(",", ".").replace("+", "").strip()

            return float(texto_preco)
            
    except Exception as e:
        print(f"⚠️ Erro ao procurar preço para o link {url}: {e}")
        
    print(f"Preço não encontrado para {url}. A estrutura da página pode ter mudado.")

    return 0.0

# Atualizar CSV e comparar os dados
def atualizar_dados_e_comparar(nome_jogo, url_jogo, preco_atual):

    """
    Guarda o preço no CSV (evitando duplicados no mesmo dia) 
    e calcula a diferença em relação ao último preço conhecido.
    """

    data_hoje = datetime.now().strftime("%Y-%m-%d")
    preco_anterior = preco_atual
    
    if os.path.exists(FICHEIRO_CSV) and os.path.getsize(FICHEIRO_CSV) > 0:
        df = pd.read_csv(FICHEIRO_CSV)
        
        # Filtrar todos os registos anteriores
        historico_jogo = df[df['Nome'] == nome_jogo]
        
        # Verificar se existe historico do jogo
        if not historico_jogo.empty:
            registo_hoje = historico_jogo[historico_jogo['Data'] == data_hoje]
            
            # Verificar se os dados de hoje já estão no CSV 
            if not registo_hoje.empty:
                historico_antes_de_hoje = historico_jogo[historico_jogo['Data'] != data_hoje]

                # Verificar se há dado do dia anterior
                if not historico_antes_de_hoje.empty:
                     preco_anterior = historico_antes_de_hoje.iloc[-1]['Preco']
                
                indice = registo_hoje.index[0]
                df.at[indice, 'Preco'] = preco_atual
                df_final = df
                
            else:
                preco_anterior = historico_jogo.iloc[-1]['Preco']
                novo_registo = pd.DataFrame([{"Data": data_hoje, "Nome": nome_jogo, "Preco": preco_atual, "Link": url_jogo}])
                df_final = pd.concat([df, novo_registo], ignore_index=True)

        # Inserir um novo registro que não consta no CSV     
        else:
            novo_registo = pd.DataFrame([{"Data": data_hoje, "Nome": nome_jogo, "Preco": preco_atual, "Link": url_jogo}])
            df_final = pd.concat([df, novo_registo], ignore_index=True)

    # Criar arquivo CSV ainda não existe      
    else:
        df_final = pd.DataFrame([{"Data": data_hoje, "Nome": nome_jogo, "Preco": preco_atual, "Link": url_jogo}])

    # Fazer os cálculos de diferença baseados no preço anterior encontrado
    diferenca_valor = preco_atual - preco_anterior
    
    if preco_anterior > 0:
        diferenca_perc = (diferenca_valor / preco_anterior) * 100

    else:
        diferenca_perc = 0.0

    df_final.to_csv(FICHEIRO_CSV, index=False)

    return preco_anterior, diferenca_valor, diferenca_perc

# Enviar o e-mail
def enviar_email(corpo_mensagem):

    """Enviar o e-mail com o preço do dia"""

    # Link do Dashboard ao final da mensagem original
    texto_final = corpo_mensagem + "📊 Acompanha os gráficos e o histórico completo no nosso Dashboard:\nhttps://historico-preco.streamlit.app/"

    msg = MIMEMultipart()

    # Quem envia o e-mail
    msg['From'] = EMAIL_REMETENTE

    # Quem recebe
    msg['To'] = ", ".join(EMAIL_DESTINO) 

    # Assunto do e-mail
    msg['Subject'] = f"Atualização Diária de Preços Xbox - {datetime.now().strftime('%d/%m/%Y')}"
    
    # Criar o texto do e-mail
    msg.attach(MIMEText(texto_final, 'plain'))
    
    # Enviar o e-mail
    try:
        servidor = smtplib.SMTP('smtp.gmail.com', 587)
        servidor.starttls()
        servidor.login(EMAIL_REMETENTE, SENHA_APP_GMAIL)
        servidor.sendmail(EMAIL_REMETENTE, EMAIL_DESTINO, msg.as_string())
        servidor.quit()
        print(f"E-mail enviado com sucesso")

    except Exception as e:
        print(f"Erro ao enviar e-mail: {e}")

# Executar a automação
if __name__ == "__main__":

    texto_email = "Relatório Diário de Preços:\n\n"
    
    for jogo in JOGOS_PARA_ACOMPANHAR:
        print(f"A processar: {jogo['nome']}...")
        
        preco_hoje = obter_preco_atual(jogo["url"])
        p_ant, diff_v, diff_p = atualizar_dados_e_comparar(jogo["nome"], jogo["url"], preco_hoje)
        
        texto_jogo = f"{jogo['nome']}\n"
        texto_jogo += f"{preco_hoje:.2f} ({p_ant:.2f} | {diff_v:.2f} | {diff_p:.2f}%)\n"
        texto_jogo += f"{jogo['url']}\n\n"
        
        texto_email += texto_jogo
        
    print("\n" + "="*40)
    print("RESULTADO DO PROCESSAMENTO:")
    print("="*40)
    print(texto_email)
    print("="*40)
    
    if MODO_TESTE:
        print("\n💡 MODO_TESTE está ativado. O e-mail NÃO foi enviado.")

    else:
        print("\nA enviar o e-mail...")
        enviar_email(texto_email)
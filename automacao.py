import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import json
from dotenv import load_dotenv

# ==========================================
# 1. LISTA DE JOGOS E CONFIGURAÇÕES
# ==========================================
# Carrega as senhas do ficheiro .env que criaste
load_dotenv()

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

# Configuração da pasta de dados
PASTA_DADOS = "dados"
if not os.path.exists(PASTA_DADOS):
    os.makedirs(PASTA_DADOS)

FICHEIRO_CSV = os.path.join(PASTA_DADOS, "historico_precos.csv")

# Credenciais de E-mail lidas com segurança
EMAIL_REMETENTE = os.getenv("EMAIL_REMETENTE")
SENHA_APP_GMAIL = os.getenv("SENHA_APP_GMAIL")

# 💡 AJUSTE 1: Prepara o código para receber vários e-mails (lista)
email_destino_env = os.getenv("EMAIL_DESTINO", "")
# Transforma os e-mails separados por vírgula numa lista do Python
EMAIL_DESTINO = [email.strip() for email in email_destino_env.split(",") if email.strip()]

# 💡 AJUSTE 2: MODO_TESTE para False (O robô vai agora enviar o e-mail a sério!)
MODO_TESTE = False 

# ==========================================
# 2. FUNÇÃO PARA EXTRAIR O PREÇO
# ==========================================
def obter_preco_atual(url):
    """Acede ao site da Xbox e extrai o preço do jogo específico."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "pt-BR,pt;q=0.9"
    }
    
    try:
        resposta = requests.get(url, headers=headers)
        resposta.raise_for_status() 
        soup = BeautifulSoup(resposta.text, 'html.parser')
        
        script_json = soup.find("script", type="application/ld+json")
        if script_json:
            dados = json.loads(script_json.string)
            if '@graph' in dados:
                for item in dados['@graph']:
                    if 'offers' in item:
                        ofertas = item['offers']
                        # 💡 AJUSTE 3: Proteção preventiva contra o sinal '+'
                        if isinstance(ofertas, list) and len(ofertas) > 0:
                            valor_str = str(ofertas[0].get('price', 0.0))
                            return float(valor_str.replace('+', '').strip())
                        elif isinstance(ofertas, dict):
                            valor_str = str(ofertas.get('price', 0.0))
                            return float(valor_str.replace('+', '').strip())
                            
        elemento_span = soup.find("span", class_=lambda c: c and "Price-module" in c)
        if elemento_span:
            texto_preco = elemento_span.text.replace("R$", "").replace("\xa0", "").replace(".", "").replace(",", "").replace("+", "").strip()
            # Tratamento da vírgula do padrão brasileiro para o ponto do Python
            if "," in elemento_span.text:
                 texto_preco = elemento_span.text.replace("R$", "").replace(".", "").replace(",", ".").replace("+", "").strip()
            return float(texto_preco)
            
    except Exception as e:
        print(f"⚠️ Erro ao procurar preço para o link {url}: {e}")
        
    print(f"Preço não encontrado para {url}. A estrutura da página pode ter mudado.")
    return 0.0

# ==========================================
# 3. LÓGICA DE DADOS E COMPARAÇÃO
# ==========================================
def atualizar_dados_e_comparar(nome_jogo, url_jogo, preco_atual):
    """
    Guarda o preço no CSV e calcula a diferença em relação ao dia anterior.
    """
    data_hoje = datetime.now().strftime("%Y-%m-%d")
    preco_anterior = preco_atual
    
    novo_registo = pd.DataFrame([{
        "Data": data_hoje, 
        "Nome": nome_jogo, 
        "Preco": preco_atual, 
        "Link": url_jogo
    }])
    
    if os.path.exists(FICHEIRO_CSV) and os.path.getsize(FICHEIRO_CSV) > 0:
        df = pd.read_csv(FICHEIRO_CSV)
        historico_jogo = df[df['Nome'] == nome_jogo]
        
        if not historico_jogo.empty:
            preco_anterior = historico_jogo.iloc[-1]['Preco'] 
            
        df_final = pd.concat([df, novo_registo], ignore_index=True)
    else:
        df_final = novo_registo

    diferenca_valor = preco_atual - preco_anterior
    
    if preco_anterior > 0:
        diferenca_perc = (diferenca_valor / preco_anterior) * 100
    else:
        diferenca_perc = 0.0

    df_final.to_csv(FICHEIRO_CSV, index=False)
    return preco_anterior, diferenca_valor, diferenca_perc

# ==========================================
# 4. ENVIO DE E-MAIL CONSOLIDADO
# ==========================================
def enviar_email(corpo_mensagem):
    # 💡 AJUSTE 1: Nova lógica compatível com listas de e-mails
    msg = MIMEMultipart()
    msg['From'] = EMAIL_REMETENTE
    # Junta a lista de e-mails com vírgula para aparecer certinho no cabeçalho
    msg['To'] = ", ".join(EMAIL_DESTINO) 
    msg['Subject'] = f"Atualização Diária de Preços Xbox - {datetime.now().strftime('%d/%m/%Y')}"
    
    msg.attach(MIMEText(corpo_mensagem, 'plain'))
    
    try:
        servidor = smtplib.SMTP('smtp.gmail.com', 587)
        servidor.starttls()
        servidor.login(EMAIL_REMETENTE, SENHA_APP_GMAIL)
        # O sendmail é o comando correto para enviar para múltiplos destinatários no Python
        servidor.sendmail(EMAIL_REMETENTE, EMAIL_DESTINO, msg.as_string())
        servidor.quit()
        print(f"E-mail enviado com sucesso para: {', '.join(EMAIL_DESTINO)}")
    except Exception as e:
        print(f"Erro ao enviar e-mail: {e}")

# ==========================================
# EXECUÇÃO DO FLUXO
# ==========================================
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
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
        "url": "https://www.xbox.com/pt-BR/games/store/crimson-desert/9NG592G0W474"
    }
]

# Configuração da pasta de dados (como definimos para o GitHub)
PASTA_DADOS = "dados"
if not os.path.exists(PASTA_DADOS):
    os.makedirs(PASTA_DADOS)

FICHEIRO_CSV = os.path.join(PASTA_DADOS, "historico_precos.csv")

# Credenciais de E-mail lidas com segurança
EMAIL_REMETENTE = os.getenv("EMAIL_REMETENTE")
SENHA_APP_GMAIL = os.getenv("SENHA_APP_GMAIL")
EMAIL_DESTINO = os.getenv("EMAIL_DESTINO")

# 💡 VARIÁVEL DE CONTROLO DE TESTE
MODO_TESTE = True # Muda para False quando quiseres enviar e-mails a sério!

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
                        if isinstance(ofertas, list) and len(ofertas) > 0:
                            return float(ofertas[0].get('price', 0.0))
                        elif isinstance(ofertas, dict):
                            return float(ofertas.get('price', 0.0))
                            
        elemento_span = soup.find("span", class_=lambda c: c and "Price-module" in c)
        if elemento_span:
            texto_preco = elemento_span.text.replace("R$", "").replace("\xa0", "").replace(".", "").replace(",", ".").strip()
            return float(texto_preco)
            
    except Exception as e:
        print(f"⚠️ Erro ao procurar preço para o link {url}: {e}")
        
    print(f"Preço não encontrado para {url}. A estrutura da página pode ter mudado.")
    return 0.0

# ==========================================
# 3. LÓGICA DE DADOS E COMPARAÇÃO
# ==========================================
def atualizar_dados_e_comparar(nome_jogo, url_jogo, preco_atual):
    data_hoje = datetime.now().strftime("%Y-%m-%d")
    preco_anterior = preco_atual
    
    if os.path.exists(FICHEIRO_CSV):
        df = pd.read_csv(FICHEIRO_CSV)
    else:
        df = pd.DataFrame(columns=["Data", "Nome", "Preco", "Link"])

    historico_jogo = df[df['Nome'] == nome_jogo]
    
    if not historico_jogo.empty:
        preco_anterior = historico_jogo.iloc[-1]['Preco'] 

    diferenca_valor = preco_atual - preco_anterior
    diferenca_perc = (diferenca_valor / preco_anterior * 100) if preco_anterior > 0 else 0.0

    novo_registo = pd.DataFrame([{
        "Data": data_hoje, 
        "Nome": nome_jogo, 
        "Preco": preco_atual, 
        "Link": url_jogo
    }])
    df = pd.concat([df, novo_registo], ignore_index=True)
    df.to_csv(FICHEIRO_CSV, index=False)
    
    return preco_anterior, diferenca_valor, diferenca_perc

# ==========================================
# 4. ENVIO DE E-MAIL CONSOLIDADO
# ==========================================
def enviar_email(corpo_mensagem):
    msg = MIMEMultipart()
    msg['From'] = EMAIL_REMETENTE
    msg['To'] = EMAIL_DESTINO
    msg['Subject'] = f"Atualização Diária de Preços Xbox - {datetime.now().strftime('%d/%m/%Y')}"
    
    msg.attach(MIMEText(corpo_mensagem, 'plain'))
    
    try:
        servidor = smtplib.SMTP('smtp.gmail.com', 587)
        servidor.starttls()
        servidor.login(EMAIL_REMETENTE, SENHA_APP_GMAIL)
        servidor.send_message(msg)
        servidor.quit()
        print("E-mail com todos os jogos enviado com sucesso!")
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
        
    # Imprime no ecrã para tu veres o resultado do teste
    print("\n" + "="*40)
    print("RESULTADO DO PROCESSAMENTO:")
    print("="*40)
    print(texto_email)
    print("="*40)
    
    # Verifica a nossa flag antes de enviar
    if MODO_TESTE:
        print("\n💡 MODO_TESTE está ativado. O e-mail NÃO foi enviado para a tua caixa.")
    else:
        print("\nA enviar o e-mail...")
        enviar_email(texto_email)
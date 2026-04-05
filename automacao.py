# importar bibliotecas
import requests
import smtplib
import pandas as pd
import os
import json
import re

from bs4 import BeautifulSoup
from datetime import datetime
from zoneinfo import ZoneInfo 
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# 1. Lista de jogos e configurações

# Variavel usada para não enviar o e-mail (teste)
MODO_TESTE = False 

# Carrega as senhas do ficheiro .env
load_dotenv()

# Lista e dicionario com jogos e produtos
ITENS_PARA_ACOMPANHAR = [
    {
        "nome": "Helldivers 2",
        "url": "https://www.xbox.com/pt-br/games/store/helldivers-2/9p3pt7pqjd0m",
        "loja": "xbox"
    },
    {
        "nome": "Crimson Desert",
        "url": "https://www.xbox.com/pt-BR/games/store/crimson-desert/9P6HVHDP2PGK/0010",
        "loja": "xbox"
    },
    {
        "nome": "PlayStation 5 Slim Digital",
        "url": "https://www.mercadolivre.com.br/console-playstation-5-slim-edico-digital-825-gb/p/MLB54963150",
        "loja": "mercadolivre"
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

# 2. Funções (DEF)

def extrair_preco_xbox(soup):

    """
    Especialista em ler o site da Xbox.
    Lida com a estrutura dinâmica do JSON e aplica a Regra da Realidade Numérica no HTML
    para ignorar descontos pequenos do Game Pass.
    """

    # PLANO A--> Procurar no JSON-LD (O mais limpo)
    script_json = soup.find("script", type="application/ld+json")

    if script_json:

        try:
            dados = json.loads(script_json.string)
            precos_json = []

            # Função interna para varrer o JSON recursivamente procurando por "price"
            def procurar_preco_json(obj):

                if isinstance(obj, dict):
                    if 'price' in obj and obj.get('price') != 0:
                        valor_str = str(obj.get('price')).replace('+', '').strip()

                        try:
                            precos_json.append(float(valor_str))

                        except ValueError:
                            pass

                    for k, v in obj.items():
                        procurar_preco_json(v)

                elif isinstance(obj, list):
                    for item in obj:
                        procurar_preco_json(item)

            procurar_preco_json(dados)

            if precos_json:
                precos_json = [p for p in precos_json if p > 0]

                if precos_json:
                    return min(precos_json)
                
        except Exception:
            pass

    # PLANO B --> Leitura do HTML (Regra da Realidade)
    precos_html = []
    elementos_preco = soup.find_all(class_=lambda c: c and "Price-module" in c)
    
    for el in elementos_preco:
        texto = el.get_text(separator=' ')

        # Procura o padrão de dinheiro do Brasil
        matches = re.findall(r'R\$\s*([\d\.]+(?:,\d{2})?)', texto)
        
        for m in matches:
            valor_str = m.replace('.', '').replace(',', '.')

            try:
                valor = float(valor_str)
                if valor > 0:
                    precos_html.append(valor)

            except ValueError:
                continue

    if precos_html:

        # Filtramos a lista removendo duplicados
        precos_unicos = list(set(precos_html))
        
        # Se encontrou mais de um preço (ex: [229.90, 172.42, 11.50])
        if len(precos_unicos) > 1:
            preco_maximo = max(precos_unicos)
            
            # Filtramos a lista ignorando qualquer valor que seja menor que 30% do preço máximo.
            precos_validos = [p for p in precos_unicos if p >= (preco_maximo * 0.3)]
            
            if precos_validos:
                return min(precos_validos)
                
        # Se só houver um preço ou a lógica acima falhar
        return min(precos_unicos)

    return 0.0

def extrair_preco_mercadolivre(soup):

    """
    Regra de Ouro: Analisa a página, recolhe os preços disponíveis 
    (Tela, Parcelas e Código Fonte) e retorna o MAIOR valor.
    Se houver apenas um preço, ele será o maior e o único.
    """

    precos_encontrados = []
    html_string = str(soup)

    # 1. Pegar o preço GIGANTE que aparece na tela
    bloco_principal = soup.find("div", class_=lambda c: c and "ui-pdp-price__second-line" in c)
    if bloco_principal:
        fracao = bloco_principal.find("span", class_="andes-money-amount__fraction")
        if fracao:
            valor_str = fracao.text.replace(".", "")
            centavos = bloco_principal.find("span", class_="andes-money-amount__cents")
            if centavos:
                valor_str += "." + centavos.text
            
            precos_encontrados.append(float(valor_str))

    # 2. Pegar a matemática real das parcelas (ex: "em 10x R$ 359,90")
    bloco_pagamento = soup.find(class_=lambda c: c and "ui-pdp-payment-price" in c)
    if bloco_pagamento:
        match_parcela = re.search(r'(\d+)\s*x.*?R\$\s*([\d.,]+)', bloco_pagamento.text, re.IGNORECASE)
        if match_parcela:
            num_parcelas = int(match_parcela.group(1))
            valor_parcela = float(match_parcela.group(2).replace(".", "").replace(",", "."))
            precos_encontrados.append(round(num_parcelas * valor_parcela, 2))

    # 3. Pegar o valor real escondido no código (React State)
    match_estado = re.search(r'"localItemPrice":(\d+(?:\.\d+)?)', html_string)
    if match_estado:
        precos_encontrados.append(float(match_estado.group(1)))

    # Filtra a lista para garantir que não temos zeros a atrapalhar
    precos_validos = [p for p in precos_encontrados if p > 0.0]

    # Devolver o maior preço da lista!
    if precos_validos:
        return max(precos_validos)
        
    return 0.0

# Obter o preço atual 
def obter_preco_atual(url, loja):

    """Acessa o site usando os headers reforçados e redireciona o HTML para o especialista da loja."""

    # Configuração do cabecalho
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Referer": "https://www.google.com.br/",
        "Sec-Ch-Ua": '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Windows"',
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "cross-site",
        "Upgrade-Insecure-Requests": "1"
    }
    
    try:
        # Leitura dos dados do site
        resposta = requests.get(url, headers=headers)
        resposta.raise_for_status() 
        soup = BeautifulSoup(resposta.text, 'html.parser')
        
        preco_final = 0.0

        # Redireciona para o especialista correto
        if loja == "xbox":
            preco_final = extrair_preco_xbox(soup)
        
        elif loja == "mercadolivre":
            preco_final = extrair_preco_mercadolivre(soup)
        
        else:
            print(f"⚠️ Loja desconhecida: {loja}")
            return 0.0

        # Se voltar ZERO, vamos ver o que nos entregou!
        if preco_final == 0.0:
            titulo_pagina = soup.title.text if soup.title else "Sem título"
            print(f"🕵️‍♂️ ALERTA: Preço 0.0 encontrado! O título da página lida foi: '{titulo_pagina}'")

        return preco_final
            
    except Exception as e:
        print(f"⚠️ Erro ao procurar preço para o link {url}: {e}")
        
    print(f"Preço não encontrado para {url}. A estrutura da página pode ter mudado.")

    return 0.0

# Atualizar CSV e comparar os dados
def atualizar_dados_e_comparar(nome_jogo, url_jogo, preco_atual, loja):

    """
    Guarda o preço, hora e loja no CSV.
    Permite até 2 registos por dia (Manhã: 00:00-12:00 / Tarde: 12:01-23:59).
    Calcula a diferença em relação ao último preço conhecido na MESMA loja.
    """

    if preco_atual <= 0.0:
        print(f"⚠️ Gravação ignorada para {nome_jogo} devido a preço zerado.")
        return 0.0, 0.0, 0.0

    fuso_br = ZoneInfo("America/Sao_Paulo")
    
    data_hoje = datetime.now(fuso_br).strftime("%Y-%m-%d")
    hora_atual = datetime.now(fuso_br).strftime("%H:%M:%S")
    limite_meio_dia = "12:00:00" 
    
    preco_anterior = preco_atual
    
    if os.path.exists(FICHEIRO_CSV) and os.path.getsize(FICHEIRO_CSV) > 0:
        df = pd.read_csv(FICHEIRO_CSV)
        
        # Adicionar a coluna Hora e Loja se não existir
        if 'Hora' not in df.columns:
            df.insert(1, 'Hora', "")
            
        if 'Loja' not in df.columns:
            df.insert(2, 'Loja', "")

        # Atualiza o histórico antigo
        df.loc[df['Nome'] == nome_jogo, 'Loja'] = loja
        
        historico_jogo = df[(df['Nome'] == nome_jogo) & (df['Loja'] == loja)]
        
        if not historico_jogo.empty:
            registos_hoje = historico_jogo[historico_jogo['Data'] == data_hoje]
            
            # Regra dos turnos
            if hora_atual <= limite_meio_dia:
                registo_turno = registos_hoje[registos_hoje['Hora'] <= limite_meio_dia]

            else:
                registo_turno = registos_hoje[registos_hoje['Hora'] > limite_meio_dia]
            
            # Fazer o update usando a regra do turno
            if not registo_turno.empty:
                indice = registo_turno.index[0]
                
                # Para saber o preço anterior, temos de olhar para o histórico ignorando esta linha que estamos a alterar
                historico_antes = historico_jogo.drop(index=indice)
                if not historico_antes.empty:
                    preco_anterior = historico_antes.iloc[-1]['Preco']
                
                df.at[indice, 'Preco'] = preco_atual
                df.at[indice, 'Hora'] = hora_atual
                df_final = df

            # Insert da primeira vez que do turno   
            else:
                
                preco_anterior = historico_jogo.iloc[-1]['Preco']
                novo_registo = pd.DataFrame([{"Data": data_hoje, "Hora": hora_atual, "Loja": loja, "Nome": nome_jogo, "Preco": preco_atual, "Link": url_jogo}])
                df_final = pd.concat([df, novo_registo], ignore_index=True)
        
        # Jogo novo no CSV
        else:
            novo_registo = pd.DataFrame([{"Data": data_hoje, "Hora": hora_atual, "Loja": loja, "Nome": nome_jogo, "Preco": preco_atual, "Link": url_jogo}])
            df_final = pd.concat([df, novo_registo], ignore_index=True)

    # Ficheiro CSV criado pela primeira vez
    else:
        df_final = pd.DataFrame([{"Data": data_hoje, "Hora": hora_atual, "Loja": loja, "Nome": nome_jogo, "Preco": preco_atual, "Link": url_jogo}])

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
    fuso_br = ZoneInfo("America/Sao_Paulo")
    msg['Subject'] = f"Atualização Diária de Preços - {datetime.now(fuso_br).strftime('%d/%m/%Y')}"
    
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

# Limpar dados inválidos (Preços zerados)
def limpar_dados_invalidos_csv():

    """
    Abre o CSV existente e remove todas as linhas onde o preço seja 0.0.
    Isto garante que o gráfico do Streamlit não tenha quedas falsas para zero.
    """

    if os.path.exists(FICHEIRO_CSV) and os.path.getsize(FICHEIRO_CSV) > 0:
        try:
            df = pd.read_csv(FICHEIRO_CSV)
            tamanho_original = len(df)
            
            # Filtrar o dataframe para manter APENAS linhas onde o Preço é maior que 0
            df_limpo = df[df['Preco'] > 0.0]
            
            linhas_removidas = tamanho_original - len(df_limpo)
            
            if linhas_removidas > 0:

                # Guardar o ficheiro limpo por cima do antigo
                df_limpo.to_csv(FICHEIRO_CSV, index=False)
                print(f"🧹 FAXINA: {linhas_removidas} registo(s) com preço 0.0 foram removidos do histórico!\n")

            else:
                print("✨ FAXINA: O histórico já está limpo. Nenhum valor zerado encontrado.\n")
                
        except Exception as e:
            print(f"⚠️ Erro ao tentar limpar o CSV: {e}\n")

# Executar a automação
if __name__ == "__main__":

    print("\nA iniciar verificação de integridade dos dados...")
    limpar_dados_invalidos_csv()
    
    texto_email = "Relatório Diário de Preços:\n\n"
    
    for jogo in ITENS_PARA_ACOMPANHAR:
        print(f"A processar: {jogo['nome']}...")
        
        preco_hoje = obter_preco_atual(jogo["url"], jogo["loja"])
        p_ant, diff_v, diff_p = atualizar_dados_e_comparar(jogo["nome"], jogo["url"], preco_hoje, jogo["loja"])
        
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
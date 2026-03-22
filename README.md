# 🎮 Monitor e Automação de Preços Xbox

![Python](https://img.shields.io/badge/Python-3.12-blue) 
![Status](https://img.shields.io/badge/Status-Em%20Desenvolvimento-yellow)

Este projeto é uma automação desenvolvida em Python para monitorizar diariamente os preços de jogos na loja digital da Xbox. Ele extrai os valores atualizados, guarda o histórico numa base de dados local (CSV), envia um relatório por e-mail e disponibiliza um Dashboard interativo para visualização da evolução dos preços.

## ✨ Funcionalidades

* **Web Scraping Dinâmico:** Acede às páginas da Xbox e extrai os preços de forma fiável através da leitura de metadados invisíveis (JSON-LD) ou elementos HTML.
* **Cálculo de Variação:** Compara o preço atual com o dia anterior, calculando a diferença em valor e em percentagem.
* **Notificações por E-mail:** Envio automatizado de um relatório diário consolidado com todos os jogos monitorizados.
* **Dashboard Interativo:** Uma interface web construída com **Streamlit** para visualizar o histórico de preços em gráficos de linha.
* **Setup Automatizado:** Script `.bat` que baixa e configura todo o ambiente virtual de forma automática usando o gestor de pacotes ultra-rápido `uv`.

## 📂 Estrutura do Projeto

```text
automacao_preco/
│
├── dados/                      # Pasta onde é guardado o histórico (historico_precos.csv)
├── app.py                      # Dashboard interativo (Frontend / Streamlit)
├── automacao.py                # Script principal de extração e e-mail (Backend)
├── instalar_ambiente.bat       # Script de instalação automática do ambiente
├── pyproject.toml              # Receita de dependências do projeto
└── uv.lock                     # Versões exatas das bibliotecas para replicação segura
```

## 🚀 Como Replicar e Instalar este Projeto

Se quiseres testar este projeto na tua máquina, o processo é incrivelmente simples.

### 1. Clonar o Repositório
Baixa o código para o teu computador:
```bash
git clone [https://github.com/RicardViana/automacao-precos-xbox.git](https://github.com/RicardViana/automacao-precos-xbox.git)
cd automacao-precos-xbox
```
*(Substitui `TEU_USUARIO` pelo teu nome de utilizador do GitHub)*

### 2. Configurar as Credenciais Seguras
Para que o envio de e-mails funcione, precisas de criar um ficheiro de variáveis de ambiente.
1. Na raiz do projeto, cria um ficheiro chamado exatamente **`.env`**
2. Adiciona as seguintes linhas com as tuas informações:
```text
EMAIL_REMETENTE=teu_email@gmail.com
SENHA_APP_GMAIL=tua_senha_de_aplicativo_do_google
EMAIL_DESTINO=email_que_vai_receber_o_alerta@gmail.com
```
> **Nota de Segurança:** Nunca partilhes o ficheiro `.env` ou a tua senha real. Usa sempre uma "Senha de Aplicativo" gerada nas configurações de segurança da tua conta Google.

### 3. Instalar o Ambiente (A Magia do `.bat`)
Para Windows, basta dar um duplo clique no ficheiro **`instalar_ambiente.bat`**. 
O que ele faz por ti:
* Verifica se tens o gestor de pacotes `uv` instalado. Se não tiveres, ele baixa e instala automaticamente.
* Cria um ambiente virtual isolado (`.venv`) com Python 3.12.
* Lê os ficheiros `.toml` e `.lock` e instala todas as dependências exatas para que o código funcione à primeira.

## 🕹️ Como Usar

Com o ambiente configurado, abre o teu terminal na pasta do projeto e executa os seguintes comandos:

**Para extrair os preços e enviar o e-mail:**
```bash
uv run automacao.py
```

**Para abrir o Dashboard interativo:**
```bash
uv run streamlit run app.py
```
*(O teu navegador irá abrir-se automaticamente com a interface gráfica!)*

## 🛠️ Tecnologias Utilizadas

* **Linguagem:** Python 3.12+
* **Gestor de Pacotes:** uv (Astral)
* **Bibliotecas Principais:** * `requests` e `beautifulsoup4` (Web Scraping)
  * `pandas` (Manipulação de Dados)
  * `streamlit` (Dashboard Frontend)
  * `python-dotenv` (Gestão de Variáveis de Ambiente)
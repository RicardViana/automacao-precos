# 🎮 Monitor e Automação de Preços Xbox

![Python](https://img.shields.io/badge/Python-3.12-blue) 
![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-Automated-success)
![Status](https://img.shields.io/badge/Status-Concluído-brightgreen)

🔴 **Live Demo:** [Acessar Dashboard](https://historico-preco.streamlit.app/)

Este projeto é um sistema automatizado **100% na nuvem** desenvolvido em Python para monitorizar diariamente os preços de jogos na loja digital da Xbox. O sistema extrai os valores atualizados de forma autónoma, guarda o histórico numa base de dados (CSV) versionada no próprio repositório, envia relatórios por e-mail e disponibiliza um Dashboard interativo na web.

## 🧠 Como a Arquitetura Funciona

O projeto foi desenhado para funcionar de forma completamente autónoma (*Serverless*), sem a necessidade de manter um servidor local ligado. O fluxo de dados acontece em 4 etapas:

1. **Agendamento (CRON):** Todos os dias de manhã, o GitHub Actions "acorda" um servidor virtual e executa o script Python.
2. **Web Scraping:** O robô entra nas páginas da Xbox e extrai o preço atualizado dos jogos (usando leitura de metadados invisíveis JSON-LD para maior fiabilidade).
3. **Persistência de Dados (Upsert):** O Pandas processa o preço. Se houver alteração ou for um dia novo, atualiza o ficheiro `historico_precos.csv` e faz um *commit* automático de volta para o repositório.
4. **Alerta e Visualização:** O sistema envia um e-mail formatado com os preços do dia e o Dashboard no Streamlit Cloud atualiza os gráficos automaticamente lendo o novo CSV.

## ✨ Funcionalidades

* **Automação na Nuvem:** Execução diária via GitHub Actions.
* **Web Scraping Dinâmico:** Extração resiliente com "Plano A" (JSON) e "Plano B" (HTML).
* **Base de Dados Efémera:** O próprio GitHub atua como base de dados (CSV).
* **Notificações por E-mail:** Relatório diário consolidado usando o protocolo SMTP do Gmail.
* **Dashboard Interativo:** Interface web pública construída com Streamlit e gráficos Plotly.

## 📂 Estrutura do Projeto

```text
automacao-precos-xbox/
│
├── .github/workflows/
│   └── automacao_diaria.yml    # O "cérebro" da automação (Agendamento no GitHub Actions)
├── .streamlit/
│   └── config.toml             # Configurações visuais e de tema do Dashboard Streamlit
├── dados/
│   └── historico_precos.csv    # Base de dados em nuvem (Ficheiro atualizado diariamente)
├── .gitignore                  # Quais ficheiros ignorar (ex: .env, pastas locais)
├── app.py                      # Dashboard interativo (Frontend / Streamlit)
├── automacao.py                # Script principal de extração e e-mail (Backend)
├── pyproject.toml              # Bibliotecas do projeto (uv)
├── README.md                   # Documentação e apresentação do projeto
├── requirements.txt            # Lista de dependências lida pelo Streamlit Cloud no Deploy
└── uv.lock                     # Versões exatas das bibliotecas para replicação segura
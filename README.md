# 🎮 Monitor e Automação de Preços

![Python](https://img.shields.io/badge/Python-3.12-blue) 
![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-Automated-success)
![Status](https://img.shields.io/badge/Status-Produção-brightgreen)

🔴 **Live Demo:** [Acessar Dashboard](https://historico-preco.streamlit.app/)

Este projeto é um sistema automatizado **100% na nuvem** desenvolvido em Python para monitorizar preços de jogos digitais e hardware (consoles) em múltiplas lojas online (Xbox e Mercado Livre). O sistema extrai os valores atualizados de forma autónoma, guarda o histórico com precisão de data e hora numa base de dados (CSV) versionada no próprio repositório, envia relatórios por e-mail e disponibiliza um Dashboard interativo na web.

## 🧠 Como a Arquitetura Funciona

O projeto foi desenhado para funcionar de forma completamente autónoma (*Serverless*), sem a necessidade de manter um servidor local ligado. O fluxo de dados acontece em 4 etapas:

1. **Agendamento Bi-diário (CRON):** O GitHub Actions "acorda" um servidor virtual em turnos (ex: manhã e noite) para capturar a volatilidade e promoções relâmpago ao longo do dia.
2. **Web Scraping Multi-loja:** O robô entra nas páginas dos produtos e é redirecionado para funções "especialistas" de cada loja:
   * **Xbox:** Lê metadados invisíveis via JSON-LD (`schema.org`).
3. **Persistência de Dados (Smart Upsert):** O Pandas processa o preço. A lógica de armazenamento permite até dois registos por dia (AM/PM), garantindo um ficheiro `historico_precos.csv` limpo, sem registos duplicados no mesmo turno, fazendo *commit* automático de volta para o repositório.
4. **Alerta e Visualização:** O sistema envia um e-mail formatado com os preços atuais e o seu *Delta* (Variação). O Dashboard no Streamlit Cloud atualiza os gráficos automaticamente lendo o novo CSV.

## ✨ Funcionalidades

* 🏬 **Suporte Multi-loja:** Arquitetura expansível, atualmente monitorizando Jogos (Xbox) e Hardware/Consoles (Mercado Livre).
* ⏱️ **Monitorização Intradiária:** Captura e exibe as oscilações de preços dentro do mesmo dia (Turnos da Manhã e Tarde/Noite).
* 📊 **Dashboard Dinâmico em Cascata:** Interface inteligente no Streamlit (Seleção de Loja ➔ Seleção de Produto) para navegação fluida.
* 🛡️ **Extração Resiliente (Plano A, B e C):** O script contorna técnicas antifraude das lojas procurando o preço no JSON, no React State ou reconstruindo o valor pelo HTML visível.
* ☁️ **Base de Dados Efémera:** O próprio GitHub atua como base de dados temporal.
* 📧 **Notificações por E-mail:** Relatório de atualização via protocolo SMTP.

## 📂 Estrutura do Projeto

```text
automacao-precos-xbox/
│
├── .github/workflows/
│   └── automacao_diaria.yml    # O "cérebro" da automação (Agendamentos CRON)
├── .streamlit/
│   └── config.toml             # Configurações visuais e de tema do Dashboard Streamlit
├── dados/
│   └── historico_precos.csv    # Base de dados em nuvem (Atualizada bi-diariamente)
├── .gitignore                  # Quais ficheiros ignorar (ex: .env, pastas locais)
├── app.py                      # Dashboard interativo (Frontend / Streamlit)
├── automacao.py                # Script principal de extração, lógica de turnos e e-mail (Backend)
├── pyproject.toml              # Bibliotecas do projeto (Gestor UV)
├── README.md                   # Documentação e apresentação do projeto
├── requirements.txt            # Lista de dependências lida pelo Streamlit Cloud no Deploy
└── uv.lock                     # Versões exatas das bibliotecas para replicação segura
```
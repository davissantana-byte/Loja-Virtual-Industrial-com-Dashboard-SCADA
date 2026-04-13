# 🏭 Loja Virtual Industrial & Monitoramento SCADA (SFRC)

Este projeto consiste num ecossistema integrado para a **Indústria 4.0**, unindo uma plataforma de e-commerce de componentes industriais a um sistema de monitorização e controlo em tempo real (SCADA).



## 📝 Sobre o Projeto

O sistema **SFRC (Squad de Alto Desempenho)** foi desenvolvido para simular o ciclo de vida completo de um produto industrial: desde a venda no marketplace até ao fabrico automatizado no chão de fábrica, com monitorização de sensores críticos.

## 🚀 Fluxo de Funcionamento

1.  **Marketplace (`home.html`):** Interface para compra de componentes. Se o stock baixar de um nível crítico, uma Ordem de Produção (OP) é gerada automaticamente via API.
2.  **Backend (`main.py`):** Desenvolvido em **FastAPI**, gere as rotas, a base de dados e a comunicação entre os módulos.
3.  **Simulador CLP (`simulador_clp.py`):** Script Python que atua como um controlador lógico programável, processando as ordens pendentes e gerando telemetria realística.
4.  **Dashboard SCADA (`scada.html`):** Painel de controlo com gráficos em tempo real (Chart.js), visualização de ativos e botões de comando operacional (Emergência/Reset).
5.  **Autenticação (`login.html`):** Sistema de acesso seguro via **Firebase** com distinção entre perfil de Cliente e Operador.

## 🛠️ Tecnologias Utilizadas

* **Linguagem:** Python 3.10+
* **Framework Web:** FastAPI (Uvicorn)
* **Base de Dados:** MySQL
* **Frontend:** HTML5, CSS3, JavaScript (ES6+)
* **Gráficos:** Chart.js
* **Autenticação:** Firebase Realtime Database
* **Automação de E-mail:** Make.com (Webhooks)

## 🔧 Como Executar

### 1. Preparar a Base de Dados
Crie a base de dados no MySQL e execute o comando para a tabela de telemetria:
```sql
CREATE DATABASE sfrc_db;
USE sfrc_db;

ALTER TABLE maquinas_telemetria ADD COLUMN produto_id INT;

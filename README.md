# 📊 Máquina de Renda - Painel de Controle e IA Preditiva

Um sistema completo (Full-Stack) para gestão patrimonial, monitoramento de fundos imobiliários (FIIs/Fiagros) em tempo real, rebalanceamento inteligente de carteira e previsão de dividendos utilizando Inteligência Artificial (Machine Learning).

O projeto adota uma arquitetura de **Monorepo**, dividindo as responsabilidades entre um backend robusto em **Python (FastAPI)** e um frontend dinâmico e moderno em **Angular**.

---

## ✨ Funcionalidades Principais

1. **📈 Monitoramento B3 em Tempo Real:** Conexão direta com a API da [Brapi](https://brapi.dev/) para busca de cotações e variações diárias em tempo real. Possui um sistema de *Fallback* (Plano B) automático para o Yahoo Finance caso a API principal falhe.
   
2. **💾 Gestão de Carteira Local:** Sistema de persistência de dados em arquivo `.json` local. Permite editar quantidades e preços médios diretamente pela interface, calculando o Lucro/Prejuízo de cada ativo automaticamente.

3. **⚖️ Motor de Rebalanceamento (Algoritmo Guloso):** Um algoritmo de otimização que recebe o valor do seu aporte mensal e calcula exatamente quantas cotas comprar de cada fundo para manter a carteira perfeitamente balanceada e diversificada.

4. **🔮 Oráculo Preditivo (Machine Learning):** Integração do motor de Inteligência Artificial usando **Random Forest** (`scikit-learn`). O modelo treina em tempo real com o histórico de dividendos dos últimos 5 anos de um ativo e prevê o valor do próximo rendimento antes do mercado precificar.

---

## 🛠️ Tecnologias Utilizadas

### Frontend (Interface Visual)
* **Angular 17+** (Framework principal)
* **TypeScript** & **HTML/CSS**
* Comunicação via `HttpClient` (Integração com API REST)

### Backend (Cérebro e IA)
* **Python 3.12+**
* **FastAPI** & **Uvicorn** (Criação de API REST de altíssima performance)
* **Scikit-Learn** (Treinamento do modelo de Random Forest)
* **Pandas** & **NumPy** (Engenharia de Variáveis e processamento de dados)
* **YFinance** & **Requests** (Coleta de dados financeiros)

---

## 🚀 Como Rodar o Projeto na Sua Máquina

Siga o passo a passo abaixo para ligar os dois motores do sistema (Backend e Frontend).

### Pré-requisitos
Certifique-se de ter instalado no seu computador:
- [Node.js e npm](https://nodejs.org/)
- [Angular CLI](https://angular.dev/tools/cli) (`npm install -g @angular/cli`)
- [Python 3.10 ou superior](https://www.python.org/)

### Passo 1: Clonar o Repositório
Abra o seu terminal e clone este repositório:
```bash
git clone [https://github.com/SEU_USUARIO/NOME_DO_REPOSITORIO.git](https://github.com/SEU_USUARIO/NOME_DO_REPOSITORIO.git)
cd NOME_DO_REPOSITORIO
```

### Passo 2: Iniciar o Servidor Python (Backend)
O Cérebro da aplicação precisa ser ligado primeiro.
```bash
# 1. Entre na pasta do backend
cd backend

# 2. Instale as bibliotecas necessárias
pip install -r requirements.txt

# 3. Ligue o servidor na porta 8080
uvicorn main:app --port 8080 --reload
```

### Passo 3: Iniciar a Interface Angular (Frontend)
Abra um novo terminal na pasta raiz do projeto.

```bash
# 1. Instale as dependências do Angular
npm install

# 2. Ligue o servidor visual
ng serve
```

### Passo 4: Acessar a Plataforma
Com os dois terminais rodando, abra o seu navegador de preferência e acesse:

👉 http://localhost:4200


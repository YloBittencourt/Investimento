from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error
import requests
import json
import os

app = FastAPI(title="API de Gestão Patrimonial e IA")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BRAPI_TOKEN = "BvJ5zR7WXXR2VqJj9R5T5J"
ARQUIVO_CARTEIRA = "carteira_banco_de_dados.json"

CARTEIRA_INICIAL = {
    "MANA11": {"quantidade": 1963, "preco_medio": 9.27},
    "VGIR11": {"quantidade": 1371, "preco_medio": 9.47},
    "RZTR11": {"quantidade": 86, "preco_medio": 92.47},
    "GGRC11": {"quantidade": 602, "preco_medio": 9.98},
    "LIFE11": {"quantidade": 2300, "preco_medio": 8.83},
    "CPTI11": {"quantidade": 125, "preco_medio": 88.50}
}

def ler_carteira():
    if not os.path.exists(ARQUIVO_CARTEIRA):
        with open(ARQUIVO_CARTEIRA, "w") as f:
            json.dump(CARTEIRA_INICIAL, f, indent=4)
        return CARTEIRA_INICIAL
    try:
        with open(ARQUIVO_CARTEIRA, "r") as f:
            dados = json.load(f)
            if not dados: raise ValueError("Vazio")
            return dados
    except Exception:
        with open(ARQUIVO_CARTEIRA, "w") as f:
            json.dump(CARTEIRA_INICIAL, f, indent=4)
        return CARTEIRA_INICIAL

def salvar_carteira(dados):
    with open(ARQUIVO_CARTEIRA, "w") as f:
        json.dump(dados, f, indent=4)

class EdicaoAtivo(BaseModel):
    quantidade: int
    preco_medio: float

class RebalanceamentoRequest(BaseModel):
    aporte: float

@app.get("/api/cotacoes")
def obter_cotacoes():
    carteira = ler_carteira()
    tickers = list(carteira.keys())
    dados_carteira = []
    try:
        url = f"https://brapi.dev/api/quote/{','.join(tickers)}?token={BRAPI_TOKEN}"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            resposta = response.json()
            if "results" in resposta:
                resultados_brapi = {ativo["symbol"]: ativo for ativo in resposta["results"]}
                for t in tickers:
                    if t in resultados_brapi:
                        ativo = resultados_brapi[t]
                        dados_carteira.append({
                            "fundo": t,
                            "precoAtual": ativo.get("regularMarketPrice", 0.0),
                            "variacao": ativo.get("regularMarketChangePercent", 0.0),
                            "quantidade": carteira[t]["quantidade"],
                            "precoMedio": carteira[t]["preco_medio"],
                            "status": "✅ Conectado (Brapi)"
                        })
                return {"ativos": dados_carteira}
        raise ValueError("Falha na Brapi")
    except Exception:
        for t in tickers:
            try:
                ativo = yf.Ticker(f"{t}.SA")
                hist = ativo.history(period="2d")
                if len(hist) >= 1:
                    preco_atual = float(hist['Close'].iloc[-1])
                    variacao = ((preco_atual - float(hist['Close'].iloc[-2])) / float(hist['Close'].iloc[-2])) * 100 if len(hist) >= 2 else 0.0
                    dados_carteira.append({
                        "fundo": t, "precoAtual": preco_atual, "variacao": variacao,
                        "quantidade": carteira[t]["quantidade"], "precoMedio": carteira[t]["preco_medio"],
                        "status": "⚠️ Conectado (Yahoo)"
                    })
                else:
                    dados_carteira.append({"fundo": t, "precoAtual": 0.0, "variacao": 0.0, "quantidade": carteira[t]["quantidade"], "precoMedio": carteira[t]["preco_medio"], "status": "Sem dados"})
            except Exception:
                dados_carteira.append({"fundo": t, "precoAtual": 0.0, "variacao": 0.0, "quantidade": carteira[t]["quantidade"], "precoMedio": carteira[t]["preco_medio"], "status": "Erro Geral"})
    return {"ativos": dados_carteira}

@app.put("/api/ativos/{fundo}")
def atualizar_ativo(fundo: str, edicao: EdicaoAtivo):
    carteira = ler_carteira()
    if fundo in carteira:
        carteira[fundo]["quantidade"] = edicao.quantidade
        carteira[fundo]["preco_medio"] = edicao.preco_medio
        salvar_carteira(carteira)
        return {"status": "sucesso"}
    return {"status": "erro"}

@app.post("/api/rebalancear")
def rebalancear_carteira(req: RebalanceamentoRequest):
    carteira = ler_carteira()
    tickers = list(carteira.keys())
    precos = {}
    try:
        url = f"https://brapi.dev/api/quote/{','.join(tickers)}?token={BRAPI_TOKEN}"
        response = requests.get(url, timeout=10)
        if response.status_code == 200 and "results" in response.json():
            for ativo in response.json()["results"]:
                precos[ativo["symbol"]] = ativo.get("regularMarketPrice", 0.0)
    except: pass
    for t in tickers:
        if t not in precos or precos[t] == 0.0:
            try: precos[t] = float(yf.Ticker(f"{t}.SA").history(period="1d")['Close'].iloc[-1])
            except: precos[t] = 0.0

    patrimonio_total = sum([carteira[t]["quantidade"] * precos[t] for t in tickers if precos[t] > 0])
    patrimonio_alvo = patrimonio_total + req.aporte
    peso_ideal = 1.0 / len(tickers)
    distancias = []
    for t in tickers:
        if precos[t] <= 0: continue
        valor_atual = carteira[t]["quantidade"] * precos[t]
        valor_ideal = patrimonio_alvo * peso_ideal
        falta = valor_ideal - valor_atual
        distancias.append({"fundo": t, "falta": falta, "preco": precos[t]})

    distancias = sorted(distancias, key=lambda x: x["falta"], reverse=True)
    compras = []
    dinheiro_disponivel = req.aporte
    for d in distancias:
        if d["falta"] > 0 and dinheiro_disponivel >= d["preco"]:
            qtd_comprar = int(min(d["falta"], dinheiro_disponivel) // d["preco"])
            if qtd_comprar > 0:
                custo = qtd_comprar * d["preco"]
                dinheiro_disponivel -= custo
                compras.append({
                    "fundo": d["fundo"], "quantidade": qtd_comprar, "preco_estimado": d["preco"], "total": custo
                })
    return {"compras": compras, "sobra": dinheiro_disponivel}

@app.get("/api/previsao/{ticker}")
def prever_rendimento(ticker: str):
    try:
        ticker_sa = f"{ticker.upper()}.SA"
        fundo = yf.Ticker(ticker_sa)
        hist = fundo.history(period="5y")
        if hist.empty or 'Dividends' not in hist.columns: return {"sucesso": False, "erro": "A B3 não tem o histórico deste ativo."}
        df = hist[hist['Dividends'] > 0][['Dividends']].reset_index()
        if len(df) < 15: return {"sucesso": False, "erro": f"O ativo tem apenas {len(df)} pagamentos. A IA exige 15 meses."}
        
        df['Date'] = pd.to_datetime(df['Date']).dt.tz_localize(None)
        df = df.rename(columns={'Dividends': 'Dividendo_Atual'}).set_index('Date').resample('ME').sum()
        df = df[df['Dividendo_Atual'] > 0]
        
        df['Lag_1_Mes'] = df['Dividendo_Atual'].shift(1)
        df['Lag_2_Meses'] = df['Dividendo_Atual'].shift(2)
        df['Lag_3_Meses'] = df['Dividendo_Atual'].shift(3)
        df['Media_Movel_3M'] = df['Dividendo_Atual'].rolling(window=3).mean().shift(1)
        df['Media_Movel_6M'] = df['Dividendo_Atual'].rolling(window=6).mean().shift(1)
        df['Alvo_Proximo_Mes'] = df['Dividendo_Atual'].shift(-1)
        
        df_limpo = df.dropna()
        X, y = df_limpo[['Dividendo_Atual', 'Lag_1_Mes', 'Lag_2_Meses', 'Lag_3_Meses', 'Media_Movel_3M', 'Media_Movel_6M']], df_limpo['Alvo_Proximo_Mes']
        
        X_treino, y_treino, X_teste, y_teste = X.iloc[:-3], y.iloc[:-3], X.iloc[-3:], y.iloc[-3:]
        modelo = RandomForestRegressor(n_estimators=100, random_state=42, max_depth=5)
        modelo.fit(X_treino, y_treino)
        
        return {
            "sucesso": True, "ticker": ticker.upper(),
            "mae": float(mean_absolute_error(y_teste, modelo.predict(X_teste))),
            "previsao": float(modelo.predict(X.iloc[[-1]])[0])
        }
    except Exception as e:
        return {"sucesso": False, "erro": f"Falha na IA: {str(e)}"}

# =========================================================
# NOVA ROTA: IA PARA A CARTEIRA COMPLETA
# =========================================================
@app.get("/api/previsao_carteira")
def prever_rendimento_carteira():
    carteira = ler_carteira()
    total_passado = 0.0
    total_previsto = 0.0
    
    for ticker, info in carteira.items():
        qtd = info["quantidade"]
        if qtd <= 0: continue
        
        try:
            fundo = yf.Ticker(f"{ticker}.SA")
            hist = fundo.history(period="5y")
            if hist.empty or 'Dividends' not in hist.columns: continue
            
            df = hist[hist['Dividends'] > 0][['Dividends']].reset_index()
            if len(df) < 15: continue
            
            df['Date'] = pd.to_datetime(df['Date']).dt.tz_localize(None)
            df = df.rename(columns={'Dividends': 'Dividendo_Atual'}).set_index('Date').resample('ME').sum()
            df = df[df['Dividendo_Atual'] > 0]
            
            # Último dividendo real que o fundo pagou (mês anterior)
            ultimo_dividendo = float(df['Dividendo_Atual'].iloc[-1])
            
            # Preparação das features para a IA
            df['Lag_1_Mes'] = df['Dividendo_Atual'].shift(1)
            df['Lag_2_Meses'] = df['Dividendo_Atual'].shift(2)
            df['Lag_3_Meses'] = df['Dividendo_Atual'].shift(3)
            df['Media_Movel_3M'] = df['Dividendo_Atual'].rolling(window=3).mean().shift(1)
            df['Media_Movel_6M'] = df['Dividendo_Atual'].rolling(window=6).mean().shift(1)
            df['Alvo_Proximo_Mes'] = df['Dividendo_Atual'].shift(-1)
            
            df_limpo = df.dropna()
            X = df_limpo[['Dividendo_Atual', 'Lag_1_Mes', 'Lag_2_Meses', 'Lag_3_Meses', 'Media_Movel_3M', 'Media_Movel_6M']]
            y = df_limpo['Alvo_Proximo_Mes']
            
            # Treino do Modelo
            X_treino, y_treino = X.iloc[:-3], y.iloc[:-3]
            modelo = RandomForestRegressor(n_estimators=100, random_state=42, max_depth=5)
            modelo.fit(X_treino, y_treino)
            
            # Previsão da Cota para o próximo mês
            previsao_cota = float(modelo.predict(X.iloc[[-1]])[0])
            
            # Multiplicamos pelo número de cotas que você possui!
            total_passado += (ultimo_dividendo * qtd)
            total_previsto += (previsao_cota * qtd)
            
        except Exception:
            pass # Se houver erro num fundo, ignora-o e soma os restantes
            
    if total_passado == 0:
        return {"sucesso": False, "erro": "Não foi possível resgatar o histórico da B3."}
        
    variacao_pct = ((total_previsto - total_passado) / total_passado) * 100
    
    return {
        "sucesso": True,
        "total_passado": total_passado,
        "total_previsto": total_previsto,
        "variacao_pct": variacao_pct
    }

    # =========================================================
# NOVA ROTA: PESQUISA LIVRE DE FUNDOS (PÁGINA INICIAL)
# =========================================================
@app.get("/api/fii/{ticker}")
def buscar_fii_individual(ticker: str):
    ticker_upper = ticker.upper().strip()
    preco = 0.0
    variacao = 0.0
    ultimo_div = 0.0

    # 1. Tentar pegar o preço atual na Brapi
    try:
        url = f"https://brapi.dev/api/quote/{ticker_upper}?token={BRAPI_TOKEN}"
        res = requests.get(url, timeout=5)
        if res.status_code == 200 and "results" in res.json():
            dados = res.json()["results"][0]
            preco = dados.get("regularMarketPrice", 0.0)
            variacao = dados.get("regularMarketChangePercent", 0.0)
    except Exception:
        pass

    # Se a Brapi falhar, tenta o Yahoo como Plano B
    if preco == 0.0:
        try:
            hist = yf.Ticker(f"{ticker_upper}.SA").history(period="2d")
            if len(hist) > 0:
                preco = float(hist['Close'].iloc[-1])
                if len(hist) > 1:
                    variacao = ((preco - float(hist['Close'].iloc[-2])) / float(hist['Close'].iloc[-2])) * 100
        except Exception:
            pass

    # 2. Pegar o último dividendo pago (Yahoo)
    try:
        fundo = yf.Ticker(f"{ticker_upper}.SA")
        hist_div = fundo.history(period="1y")
        if not hist_div.empty and 'Dividends' in hist_div.columns:
            df_div = hist_div[hist_div['Dividends'] > 0]
            if not df_div.empty:
                ultimo_div = float(df_div['Dividends'].iloc[-1])
    except Exception:
        pass

    if preco == 0.0:
        return {"sucesso": False, "erro": f"Fundo '{ticker_upper}' não encontrado na B3."}

    return {
        "sucesso": True,
        "ticker": ticker_upper,
        "preco": preco,
        "variacao": variacao,
        "ultimo_dividendo": ultimo_div
    }
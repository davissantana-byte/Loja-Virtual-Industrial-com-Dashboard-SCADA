from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import mysql.connector
import google.generativeai as genai

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# CONFIGURAÇÃO DA IA GENERATIVA (GEMINI)
# ⚠️ COLE SUA CHAVE AQUI ABAIXO
genai.configure(api_key="AIzaSyCMR2UNCe-nCmabz_nVTpLD8EWhidnSUpg")
model = genai.GenerativeModel('models/gemini-2.5-flash')

def get_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="password", # <--- SUA SENHA DO MYSQL
        database="sfrc_db"
    )

class Venda(BaseModel):
    usuario: str
    itens: str
    total: float
    produto_id: int
    quantidade: int

@app.post("/venda")
async def realizar_venda(v: Venda):
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO vendas (usuario, itens, total) VALUES (%s, %s, %s)", (v.usuario, v.itens, v.total))
        cursor.execute("INSERT INTO ordens_producao (produto_id, quantidade_solicitada, status) VALUES (%s, %s, 'pendente')", (v.produto_id, v.quantidade))
        conn.commit()
        conn.close()
        return {"status": "sucesso"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/status-geral")
def get_status_geral():
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM maquinas_telemetria ORDER BY id DESC LIMIT 1")
        telemetria = cursor.fetchone()
        cursor.execute("SELECT nome, quantidade_atual FROM produtos")
        estoque = cursor.fetchall()
        cursor.execute("SELECT * FROM ordens_producao WHERE status = 'processando' LIMIT 1")
        producao_ativa = cursor.fetchone()
        conn.close()
        return {"telemetria": telemetria, "estoque": estoque, "producao_ativa": producao_ativa}
    except Exception as e:
        return {"erro": str(e)}

# ROTA DA IA QUE ESTAVA DANDO ERRO
@app.get("/ia-analise")
def analisar_com_ia():
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        # Pega os últimos 5 registros para a IA analisar a tendência
        cursor.execute("SELECT temperatura, vibracao FROM maquinas_telemetria ORDER BY id DESC LIMIT 5")
        historico = cursor.fetchall()
        conn.close()

        if not historico:
            return {"analise": "Aguardando dados de telemetria para diagnóstico..."}

        # O prompt que enviamos para o "Cérebro" do Google
        prompt = f"""
        Como engenheiro de IA da Squad, analise estes dados: {historico}. 
        Dê um parecer técnico curto (1 frase) sobre o estado da máquina e se há risco iminente.
        """
        
        response = model.generate_content(prompt)
        return {"analise": response.text}
    except Exception as e:
        print(f"Erro na IA: {e}") # Log para você ver no terminal
        return {"analise": "O Agente de IA está processando os dados, aguarde..."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
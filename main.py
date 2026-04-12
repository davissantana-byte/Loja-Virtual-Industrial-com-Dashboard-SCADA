from fastapi import FastAPI, HTTPException
import mysql.connector
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

app = FastAPI()

# --- CONFIGURAÇÃO DE ACESSO (CORS) ---
# Essencial para o seu home.html conseguir falar com esta API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],  
)

# --- CONFIGURAÇÃO DE IMAGENS ---
PASTA_FOTOS = "assets" 
if not os.path.exists(PASTA_FOTOS):
    os.makedirs(PASTA_FOTOS)

# Faz o link http://localhost:8000/assets/foto.png funcionar
app.mount("/assets", StaticFiles(directory=PASTA_FOTOS), name="assets")

# Status global da fábrica (Parada de Emergência)
sistema_status = {"parada_emergencia": False}

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="password", # Certifique-se que sua senha é 'password'
        database="sfrc_db"
    )

class Venda(BaseModel):
    produto_id: int
    quantidade: int

@app.get("/")
def home():
    return {"status": "Sistema SFRC Operacional", "versao": "1.6 - Integrada"}

# --- ROTA DE VENDA (CORRIGIDA) ---
@app.get("/realizar-venda") 
@app.post("/venda") # Aceita POST do site novo também
def realizar_venda(produto_id: int, quantidade: int):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # 1. Tira do estoque
        cursor.execute("UPDATE estoque SET quantidade_atual = quantidade_atual - %s WHERE produto_id = %s", (quantidade, produto_id))
        
        # 2. Registra a venda (CORRIGIDO: de id_produto para produto_id)
        cursor.execute("INSERT INTO vendas (produto_id, quantidade, data_venda) VALUES (%s, %s, NOW())", (produto_id, quantidade))
        
        # 3. GATILHO DE PRODUÇÃO: Se baixar do nível crítico, cria ordem
        cursor.execute("SELECT quantidade_atual, nivel_critico FROM estoque WHERE produto_id = %s", (produto_id,))
        estoque = cursor.fetchone()
        
        if estoque and estoque['quantidade_atual'] <= estoque['nivel_critico']:
            # Cria a ordem pendente que o simulador_clp.py vai detectar
            cursor.execute(
                "INSERT INTO ordens_producao (produto_id, quantidade_solicitada, status) VALUES (%s, %s, 'pendente')",
                (produto_id, 500) 
            )
            print(f"✅ Ordem de produção gerada para ID {produto_id}")

        conn.commit()
        return {"status": "sucesso"}
    except Exception as e:
        conn.rollback()
        return {"status": "erro", "erro": str(e)}
    finally:
        cursor.close()
        conn.close()

@app.post("/emergencia")
def disparar_emergencia():
    sistema_status["parada_emergencia"] = True
    return {"mensagem": "🛑 COMANDO DE EMERGÊNCIA ATIVADO!"}

@app.post("/reset-sistema")
def reset_sistema():
    sistema_status["parada_emergencia"] = False
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE ordens_producao SET status = 'pendente' WHERE status = 'interrompida'")
        conn.commit()
        msg = "✅ Sistema resetado e ordens retomadas."
    except Exception as e:
        msg = f"Erro ao resetar: {str(e)}"
    finally:
        cursor.close()
        conn.close()
    return {"mensagem": msg}

@app.get("/status-fabrica")
def checar_status():
    return sistema_status

@app.get("/telemetria")
def ler_telemetria():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    # Pega as últimas 15 leituras para os gráficos do Dashboard
    cursor.execute("SELECT * FROM maquinas_telemetria ORDER BY id DESC LIMIT 15")
    dados = cursor.fetchall()
    cursor.close()
    conn.close()
    return dados

@app.get("/historico-vendas")
def historico_vendas():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT v.data_venda, p.nome, v.quantidade 
        FROM vendas v 
        JOIN produtos p ON v.produto_id = p.id 
        ORDER BY v.id DESC LIMIT 5
    """)
    vendas = cursor.fetchall()
    cursor.close()
    conn.close()
    return vendas

@app.get("/estoque-atual")
def get_estoque_completo():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    query = """
        SELECT p.id, p.nome, e.quantidade_atual, e.nivel_critico 
        FROM produtos p 
        JOIN estoque e ON p.id = e.produto_id
    """
    cursor.execute(query)
    estoque = cursor.fetchall()
    cursor.close()
    conn.close()
    return estoque

@app.post("/reestocar-tudo")
def reestocar_tudo():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE estoque SET quantidade_atual = 500")
        conn.commit()
        cursor.close()
        conn.close()
        return {"status": "sucesso", "mensagem": "Estoque resetado para 500 unidades."}
    except Exception as e:
        return {"status": "erro", "detalhes": str(e)}

@app.get("/produto/{produto_id}")
def get_produto_detalhes(produto_id: int):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    # Busca detalhes do produto para o Card do Dashboard
    cursor.execute("SELECT id, nome, descricao, preco, dimensoes, imagem FROM produtos WHERE id = %s", (produto_id,))
    produto = cursor.fetchone()
    cursor.close()
    conn.close()
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    return produto

@app.post("/produzir-faltantes")
def produzir_faltantes():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # 1. Busca todos os produtos com estoque baixo (menos de 50)
        cursor.execute("""
            SELECT produto_id FROM estoque 
            WHERE quantidade_atual < 50
        """)
        produtos_baixos = cursor.fetchall()
        
        if not produtos_baixos:
            return {"status": "info", "mensagem": "Estoque estável. Nenhum item abaixo de 50 unidades."}

        # 2. Para cada produto, cria uma Ordem de Produção de 500 peças
        for item in produtos_baixos:
            cursor.execute("""
                INSERT INTO ordens_producao (produto_id, quantidade_solicitada, status) 
                VALUES (%s, 500, 'pendente')
            """, (item['produto_id'],))
        
        conn.commit()
        return {"status": "sucesso", "mensagem": f"{len(produtos_baixos)} ordens enviadas para a fábrica!"}
    
    except Exception as e:
        conn.rollback()
        return {"status": "erro", "erro": str(e)}
    finally:
        cursor.close()
        conn.close()
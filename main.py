from fastapi import FastAPI, HTTPException
import mysql.connector
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles # Adicionado
import os # Adicionado

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],  
)

# --- CONFIGURAÇÃO DE IMAGENS ---
# IMPORTANTE: Mude 'NOME_DA_SUA_PASTA' para o nome real da pasta onde estão suas fotos
PASTA_FOTOS = "assets" 

if not os.path.exists(PASTA_FOTOS):
    os.makedirs(PASTA_FOTOS)

# Isso faz o link http://IP:8000/assets/foto.png funcionar
app.mount("/assets", StaticFiles(directory=PASTA_FOTOS), name="assets")
# -------------------------------

sistema_status = {"parada_emergencia": False}

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="password", # Verifique se sua senha continua sendo 'password'
        database="sfrc_db"
    )

class Venda(BaseModel):
    produto_id: int
    quantidade: int

@app.get("/")
def home():
    return {"status": "Sistema SFRC Operacional", "versao": "1.5 - Foto e Detalhes"}

@app.get("/realizar-venda") # Deixei GET também para você testar no navegador se quiser
def realizar_venda(produto_id: int, quantidade: int):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # 1. Tira do estoque
        cursor.execute("UPDATE estoque SET quantidade_atual = quantidade_atual - %s WHERE produto_id = %s", (quantidade, produto_id))
        
        # 2. Registra a venda
        cursor.execute("INSERT INTO vendas (produto_id, quantidade, data_venda) VALUES (%s, %s, NOW())", (produto_id, quantidade))
        
        # 3. O PULO DO GATO: Se o estoque baixou do nível crítico, cria ordem de produção
        cursor.execute("SELECT quantidade_atual, nivel_critico FROM estoque WHERE produto_id = %s", (produto_id,))
        estoque = cursor.fetchone()
        
        if estoque['quantidade_atual'] <= estoque['nivel_critico']:
            # Cria a ordem de produção que o simulador vai ler
            cursor.execute(
                "INSERT INTO ordens_producao (produto_id, quantidade_solicitada, status) VALUES (%s, %s, 'pendente')",
                (produto_id, 500) # Produz lote de 500
            )
            print(f"Ordem de produção gerada automaticamente para ID {produto_id}")

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
        msg = "✅ Sistema resetado."
    except Exception as e:
        msg = f"Erro: {str(e)}"
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
    cursor.execute("SELECT * FROM maquinas_telemetria ORDER BY id DESC LIMIT 15")
    dados = cursor.fetchall()
    cursor.close()
    conn.close()
    return dados

@app.get("/historico-vendas")
def historico_vendas():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT v.data_venda, p.nome, v.quantidade FROM vendas v JOIN produtos p ON v.produto_id = p.id ORDER BY v.id DESC LIMIT 5")
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
        return {"status": "sucesso", "mensagem": "Reestocado."}
    except Exception as e:
        return {"status": "erro", "detalhes": str(e)}

# ROTA CORRIGIDA (Adicionado a barra / inicial)
@app.get("/produto/{produto_id}")
def get_produto_detalhes(produto_id: int):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    # Verifique se o nome da coluna é 'imagem' ou 'imagem_url' no seu banco
    cursor.execute("SELECT id, nome, descricao, preco, dimensoes, imagem FROM produtos WHERE id = %s", (produto_id,))
    produto = cursor.fetchone()
    cursor.close()
    conn.close()
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado no banco de dados")
    return produto
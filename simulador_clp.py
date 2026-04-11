import mysql.connector
import time
import random
import requests 

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="password", # Certifique-se que sua senha está correta aqui
        database="sfrc_db"
    )

def rodar_fabrica():
    print("--- SIMULADOR SCADA / CHÃO DE FÁBRICA ATIVO ---")
    
    while True:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # 1. Procura ordens pendentes
        cursor.execute("SELECT * FROM ordens_producao WHERE status = 'pendente' LIMIT 1")
        ordem = cursor.fetchone()
        
        if ordem:
            id_ordem = ordem['id']
            qtd_total = ordem['quantidade_solicitada']
            interrompida = False # Variável de controle
            
            print(f"\n[FÁBRICA] Nova Ordem Detectada! ID: {id_ordem} | Lote: {qtd_total}")
            
            cursor.execute("UPDATE ordens_producao SET status = 'em_producao' WHERE id = %s", (id_ordem,))
            conn.commit()
            
            # 2. Loop de produção com Trava de Emergência
            for i in range(1, qtd_total + 1):
                
                # --- CHECAGEM DE EMERGÊNCIA (O Pulo do Gato) ---
                try:
                    res_status = requests.get("http://127.0.0.1:8000/status-fabrica").json()
                    if res_status.get("parada_emergencia"):
                        print(f"\n🛑 EMERGÊNCIA ATIVADA! Interrompendo produção da Ordem {id_ordem}...")
                        interrompida = True
                        break # Sai do loop de produção imediatamente
                except Exception as e:
                    print(f"Erro ao checar status da API: {e}")

                inicio_ciclo = time.time()
                time.sleep(random.uniform(0.4, 0.8)) 
                
                temp = round(random.uniform(45.0, 72.0), 2)
                vibracao = round(random.uniform(0.8, 4.5), 2)
                consumo = round(random.uniform(1.1, 2.8), 4)
                ciclo = round(time.time() - inicio_ciclo, 2)
                rejeito = 1 if random.random() < 0.03 else 0

                cursor.execute("""
                INSERT INTO maquinas_telemetria 
                (maquina_id, ordem_producao_id, produto_id, status_ligada, pecas_produzidas, 
                temperatura, consumo_kwh, vibracao, ciclo_segundos, pecas_rejeitadas)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, ("INJETORA_01", id_ordem, ordem['produto_id'], True, i, temp, consumo, vibracao, ciclo, rejeito))
                
                conn.commit()
                print(f"   -> Peça: {i}/{qtd_total} | Temp: {temp}°C | Vib: {vibracao}mm/s", end='\r')
            
            # 3. Finalização ou Interrupção
            if interrompida:
                # Se parou por emergência, avisa o banco que a ordem falhou
                cursor.execute("UPDATE ordens_producao SET status = 'interrompida' WHERE id = %s", (id_ordem,))
                status_final = "INTERROMPIDA POR EMERGÊNCIA"
            else:
                # Produção normal concluída
                cursor.execute("UPDATE ordens_producao SET status = 'concluida', data_conclusao = CURRENT_TIMESTAMP WHERE id = %s", (id_ordem,))
                cursor.execute("UPDATE estoque SET quantidade_atual = quantidade_atual + %s WHERE produto_id = %s", (qtd_total, ordem['produto_id']))
                status_final = "CONCLUÍDA"

            # Desliga a telemetria da máquina
            cursor.execute("""
                INSERT INTO maquinas_telemetria 
                (maquina_id, ordem_producao_id, status_ligada, pecas_produzidas, 
                 temperatura, consumo_kwh, vibracao, ciclo_segundos, pecas_rejeitadas)
                VALUES (%s, %s, %s, %s, 0, 0, 0, 0, 0)
            """, ("INJETORA_01", id_ordem, False, 0)) 
            
            conn.commit()
            print(f"\n[FÁBRICA] Ordem {id_ordem} status final: {status_final}.")

        cursor.close()
        conn.close()
        time.sleep(2) 

if __name__ == '__main__':
    rodar_fabrica()
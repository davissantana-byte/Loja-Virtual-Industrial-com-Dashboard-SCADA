import mysql.connector
import time
import random

# CONFIGURAÇÃO DO BANCO DE DADOS
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "password", # <--- COLOQUE SUA SENHA DO MYSQL AQUI
    "database": "sfrc_db"
}

def rodar_simulador():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        print("🏭 SQUAD SIMULATOR 4.0: Automação e Gestão de Estoque Online.")
        print("⏳ Aguardando ordens de produção...")

        while True:
            # Sincroniza para enxergar novos dados (evita o problema de 'travamento')
            conn.commit()

            # Busca a próxima ordem pendente
            cursor.execute("SELECT * FROM ordens_producao WHERE status = 'pendente' ORDER BY id ASC LIMIT 1")
            ordem = cursor.fetchone()

            if ordem:
                ordem_id = ordem['id']
                produto_id = ordem['produto_id']
                qtd_total = ordem['quantidade_solicitada']
                
                print(f"\n📦 Ordem #{ordem_id} detectada. Iniciando lote de {qtd_total} unidades.")
                
                # Marca como processando
                cursor.execute("UPDATE ordens_producao SET status = 'processando' WHERE id = %s", (ordem_id,))
                conn.commit()

                bloqueado = False
                for i in range(1, qtd_total + 1):
                    # Verifica se o 'agente_ia.py' bloqueou a máquina
                    conn.commit() 
                    cursor.execute("SELECT status FROM ordens_producao WHERE id = %s", (ordem_id,))
                    status_atual = cursor.fetchone()['status']

                    if status_atual == 'BLOQUEADO_POR_IA':
                        print(f"\n🛑 BLOQUEIO DE SEGURANÇA: Produção interrompida pela IA no ciclo {i}!")
                        bloqueado = True
                        break

                    # Geração de Telemetria (Simulando aquecimento gradual)
                    # A cada ciclo a temperatura sobe um pouco para testar a IA
                    temp = round(60.0 + (i * 0.5) + random.uniform(0, 5), 2)
                    vib = round(random.uniform(2, 7), 2)

                    # Grava telemetria (o Agente IA e o Dashboard leem isso)
                    cursor.execute(
                        "INSERT INTO maquinas_telemetria (temperatura, vibracao, ciclo_atual) VALUES (%s, %s, %s)",
                        (temp, vib, i)
                    )
                    conn.commit()

                    print(f"⚙️ Ciclo {i}/{qtd_total} | Temp: {temp}°C | Vib: {vib}mm/s")
                    time.sleep(0.5) # Velocidade da linha de produção

                if not bloqueado:
                    # 1. Finaliza a ordem
                    cursor.execute("UPDATE ordens_producao SET status = 'concluido' WHERE id = %s", (ordem_id,))
                    
                    # 2. ATUALIZA O ESTOQUE REAL (Soma as peças produzidas ao saldo atual)
                    cursor.execute(
                        "UPDATE produtos SET quantidade_atual = quantidade_atual + %s WHERE id = %s",
                        (qtd_total, produto_id)
                    )
                    
                    conn.commit()
                    print(f"✅ Lote finalizado. Estoque do Produto {produto_id} atualizado (+{qtd_total}).")
                
                print("\n⏳ Aguardando próxima ordem...")

            time.sleep(3) # Intervalo de respiro do loop

    except mysql.connector.Error as err:
        print(f"❌ Erro de banco de dados: {err}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            conn.close()

if __name__ == "__main__":
    rodar_simulador()
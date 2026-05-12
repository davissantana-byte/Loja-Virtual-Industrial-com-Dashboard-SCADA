import mysql.connector
import time

# CONFIGURAÇÃO DO BANCO DE DADOS
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "password", # <--- COLOQUE SUA SENHA AQUI
    "database": "sfrc_db"
}

def supervisor_ia():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        print("🧠 AGENTE SQUAD IA: Monitoramento de Segurança Ativo.")
        print("🔍 Analisando telemetria em tempo real...\n")

        while True:
            # CRÍTICO: Força o MySQL a atualizar os dados e ver o que o simulador acabou de inserir
            conn.commit()

            # Pega o dado mais recente da telemetria
            cursor.execute("SELECT * FROM maquinas_telemetria ORDER BY id DESC LIMIT 1")
            dado = cursor.fetchone()

            if dado:
                temp = dado['temperatura']
                vib = dado['vibracao']
                ciclo = dado['ciclo_atual']

                print(f"📊 [Log Produção] Ciclo: {ciclo} | Temp: {temp}°C | Vib: {vib}")

                # Lógica de Decisão Autônoma (Entrega 3)
                if temp > 90:
                    print(f"🚨 CRÍTICO: Superaquecimento detectado ({temp}°C)!")
                    print("⚡ AÇÃO IA: Enviando comando de BLOQUEIO para a fábrica...")
                    
                    # Comando que "mata" o simulador mudando o status no banco
                    cursor.execute("UPDATE ordens_producao SET status = 'BLOQUEADO_POR_IA' WHERE status = 'processando'")
                    conn.commit()
                    print("✅ Fábrica Bloqueada. Aguardando intervenção ou nova ordem.")
                
                elif temp > 80:
                    print(f"⚠️ AVISO: Temperatura subindo ({temp}°C). IA monitorando preventivamente.")
                
                else:
                    print(f"🟢 STATUS: Operação estável.")
            
            print("-" * 50)
            time.sleep(2) # Verifica a cada 2 segundos

    except mysql.connector.Error as err:
        print(f"❌ Erro no Agente: {err}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            conn.close()

if __name__ == "__main__":
    supervisor_ia()
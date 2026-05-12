import google.generativeai as genai

# Coloque sua chave aqui para o teste
genai.configure(api_key="AIzaSyCMR2UNCe-nCmabz_nVTpLD8EWhidnSUpg")

print("--- Modelos Disponíveis para sua Chave ---")
for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print(f"Nome: {m.name}")
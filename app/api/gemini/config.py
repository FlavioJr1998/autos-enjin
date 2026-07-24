from google import genai
import os

def envia_prompt( prompt ):
    print("Conectando ao Gemini usando o novo SDK e gerando o resumo...")
    
    # Inicializa o cliente seguindo o novo padrão do Google
    client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))
    
    # Chamada atualizada usando o modelo estável mais recente
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
    )
    
    return response.text
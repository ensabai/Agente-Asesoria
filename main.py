import logging
from fastapi import FastAPI
from dotenv import load_dotenv
from langchain_core.messages import SystemMessage, HumanMessage

load_dotenv()

# Importaciones locales (asumiendo que están en la misma carpeta o paquete)
from intern.models import ConsultaModel
from intern.graph import compilar_grafo


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Compilamos el grafo una sola vez al inicio
app_graph = compilar_grafo()

app = FastAPI(title="NovaGestión AI Workflow")

@app.post("/asesoria/novagestion")
async def enviar_mensaje(consulta: ConsultaModel):
    try:
        logger.info(f"Recibido: {consulta.message[:50]}...")
        
        # Prompt de Sistema (Contexto Global)
        # Este prompt viaja en el historial, útil para el clasificador y el formateador
        sys_msg = """Eres el asistente virtual de Asesoría NovaGestión.
        Tu objetivo es ayudar a clientes con dudas fiscales y administrativas.
        """
        
        messages = [SystemMessage(content=sys_msg)]
        
        # Inyectar contexto previo si existe
        if consulta.context:
            messages.append(HumanMessage(content=f"CONTEXTO PREVIO:\n{consulta.context}"))
            
        messages.append(HumanMessage(content=consulta.message))
        
        # Ejecutar grafo
        # Inicializamos 'intencion' como 'otro' por defecto para evitar errores de tipo
        inputs = {"messages": messages, "intencion": "otro"}
        
        final_state = await app_graph.ainvoke(inputs)
        
        respuesta = final_state["messages"][-1].content
        return {"response": respuesta}

    except Exception as e:
        logger.error(f"Error crítico en endpoint: {e}", exc_info=True)
        return {"response": "Lo siento, ha ocurrido un error interno. Por favor contacta a la oficina."}
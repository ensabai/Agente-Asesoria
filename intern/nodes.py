import os
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from intern.models import AgentState, DecisionMaestra, DecisionInfoGeneral
from intern.tools import consultar_informacion_despacho, consultar_calendario_contribuyentes

# Configuración LLM
MODELO_ROUTER = os.getenv("MODELO_ROUTER")
MODELO_WRITER = os.getenv("MODELO_WRITER") # O el que uses para redactar
LITELLM_API_KEY = os.getenv("LITELLM_API_KEY")
LITELLM_API_BASE = os.getenv("LITELLM_API_BASE")
EXTERNAL_API_KEY = os.getenv("EXTERNAL_API_KEY")
EXTERNAL_API_BASE = os.getenv("EXTERNAL_API_BASE")

llm_router = ChatOpenAI(model=MODELO_ROUTER,
                        openai_api_base=LITELLM_API_BASE,
                        openai_api_key=LITELLM_API_KEY,
                        temperature=0)

llm_writer = ChatOpenAI(model=MODELO_WRITER,
                        openai_api_base=EXTERNAL_API_BASE,
                        openai_api_key=EXTERNAL_API_KEY,
                        temperature=0.2)

# --- NIVEL 1: DISCRIMINADOR MAESTRO ---

async def discriminador_maestro_node(state: AgentState):
    """
    Router Principal: Decide a qué 'Departamento' enviar la consulta.
    """
    messages = state["messages"]
    
    # Prompt del sistema para el router maestro
    system_prompt = """Eres el clasificador principal de la Asesoría.
    Tu trabajo es derivar la consulta al departamento correcto.
    
    1. 'informacion_general': Preguntas sobre la asesoría, impuestos, fechas, plazos, ubicación, noticias.
    2. 'otro': Saludos, despedidas, o temas fuera de lugar.
    """
    
    try:
        structured_llm = llm_router.with_structured_output(DecisionMaestra)
        decision = await structured_llm.ainvoke([SystemMessage(content=system_prompt)] + messages)
        categoria = decision.categoria
    except:
        # Fallback simple si falla el estructurado
        categoria = "otro"

    return {"categoria_principal": categoria}

# --- NIVEL 2: ROUTER DE INFORMACIÓN GENERAL ---

async def router_info_general_node(state: AgentState):
    """
    Sub-Router: Dentro del departamento de Información General, decide la herramienta específica.
    """
    messages = state["messages"]
    
    system_prompt = """Eres el especialista en Información General.
    Clasifica la consulta en una de las siguientes herramientas:
    
    1. 'calendario': Preguntas sobre FECHAS, PLAZOS, PAGOS, MODELOS de impuestos (303, 111, IRPF, IVA), vencimientos.
    2. 'despacho': Preguntas sobre la OFICINA, horarios, teléfono, quiénes somos, servicios, noticias generales.
    3. 'desconocido': Si no encaja claramente en las anteriores.
    """
    
    try:
        structured_llm = llm_router.with_structured_output(DecisionInfoGeneral)
        decision = await structured_llm.ainvoke([SystemMessage(content=system_prompt)] + messages)
        sub_cat = decision.tipo
    except:
        sub_cat = "desconocido"
    
    print(sub_cat)

    return {"sub_categoria": sub_cat}

# --- WORKERS (TRABAJADORES) ---

async def worker_calendario_node(state: AgentState):
    """Ejecuta herramienta calendario"""
    res = await consultar_calendario_contribuyentes.ainvoke("")
    return {"messages": [AIMessage(content=f"DATOS CALENDARIO:\n{res}")]}

async def worker_info_despacho_node(state: AgentState):
    """Ejecuta herramienta RAG despacho"""
    last_msg = state["messages"][-1].content
    res = await consultar_informacion_despacho.ainvoke(last_msg)
    return {"messages": [AIMessage(content=f"DATOS DESPACHO:\n{res}")]}

async def worker_charla_node(state: AgentState):
    """Responde a saludos u otros"""
    res = await llm_writer.ainvoke(state["messages"])
    return {"messages": [res]}

# --- FORMATEADOR FINAL ---

async def formateador_node(state: AgentState):
    """Unifica el estilo de respuesta"""
    last_message = state["messages"][-1]
    
    # Si viene del nodo de charla (ej. un saludo), a veces no queremos re-formatear,
    # pero para mantener consistencia lo pasamos igual.
    
    prompt = ChatPromptTemplate.from_template(
        """Formatea esto para WhatsApp (breve, emojis, negritas):
        {texto}"""
    )
    chain = prompt | llm_writer | StrOutputParser()
    res = await chain.ainvoke({"texto": last_message.content})
    return {"messages": [AIMessage(content=res)]}
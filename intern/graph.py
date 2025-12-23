from langgraph.graph import StateGraph, START, END
from intern.models import AgentState
from intern.nodes import (
    discriminador_maestro_node,
    router_info_general_node,
    worker_calendario_node,
    worker_info_despacho_node,
    worker_charla_node,
    formateador_node
)
from intern.routers import router_maestro_edge, router_info_general_edge

def compilar_grafo():
    workflow = StateGraph(AgentState)

    # ---------------- NODOS ----------------
    
    # Nivel 1: Entrada
    workflow.add_node("maestro", discriminador_maestro_node)
    
    # Nivel 2: Departamento Info General
    workflow.add_node("informacion_general", router_info_general_node)
    
    # Nivel 3: Workers (Herramientas)
    workflow.add_node("calendario_node", worker_calendario_node)
    workflow.add_node("info_despacho_node", worker_info_despacho_node)
    workflow.add_node("chat_generico", worker_charla_node) # Para "otro"
    
    # Final: Salida
    workflow.add_node("formateador", formateador_node)

    # ---------------- ARISTAS (FLUJO) ----------------

    # 1. Start -> Maestro
    workflow.add_edge(START, "maestro")

    # 2. Decisión Maestra (Conditional Edge)
    workflow.add_conditional_edges(
        "maestro",
        router_maestro_edge,
        {
            "rama_info_general": "informacion_general", # Va al sub-router
            "rama_otro": "chat_generico"                # Va directo al chat
        }
    )

    # 3. Decisión Departamento Info General (Conditional Edge)
    workflow.add_conditional_edges(
        "informacion_general",
        router_info_general_edge,
        {
            "ir_calendario": "calendario_node",
            "ir_despacho": "info_despacho_node",
            "ir_fallback": "info_despacho_node" # Default
        }
    )

    # 4. Convergencia hacia el Formateador
    workflow.add_edge("calendario_node", "formateador")
    workflow.add_edge("info_despacho_node", "formateador")
    workflow.add_edge("chat_generico", "formateador")

    # 5. Fin
    workflow.add_edge("formateador", END)

    return workflow.compile()
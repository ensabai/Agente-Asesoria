from typing import Literal
from intern.models import AgentState

def router_maestro_edge(state: AgentState) -> Literal["rama_info_general", "rama_otro"]:
    """Lee la categoría principal y dirige el tráfico."""
    cat = state.get("categoria_principal", "otro")
    
    if cat == "informacion_general":
        return "rama_info_general"
    else:
        return "rama_otro"

def router_info_general_edge(state: AgentState) -> Literal["ir_calendario", "ir_despacho", "ir_fallback"]:
    """Lee la sub-categoría y elige el worker."""
    sub = state.get("sub_categoria", "desconocido")
    
    if sub == "calendario":
        return "ir_calendario"
    elif sub == "despacho":
        return "ir_despacho"
    else:
        # Si entra en info general pero no sabemos qué es, 
        # podríamos mandarlo a despacho (búsqueda genérica) o a charla.
        return "ir_despacho"
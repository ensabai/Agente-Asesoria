from typing import Annotated, Literal, Optional
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field

# Definimos las categorías posibles
CategoriaPrincipal = Literal["informacion_general", "otro"]
SubCategoriaInfo = Literal["calendario", "despacho", "desconocido"]

class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    # Nivel 1: ¿De qué tema macro estamos hablando?
    categoria_principal: Optional[CategoriaPrincipal]
    # Nivel 2: ¿Qué herramienta específica necesito dentro de ese tema?
    sub_categoria: Optional[SubCategoriaInfo]

class ConsultaModel(BaseModel):
    message: str = Field(..., description="Consulta actual del usuario")
    context: str = Field(default="", description="Historial previo")

# Modelos para Output Estructurado (Structured Outputs)

class DecisionMaestra(BaseModel):
    """Clasificación de Nivel 1"""
    categoria: CategoriaPrincipal = Field(..., description="Categoría principal de la consulta")

class DecisionInfoGeneral(BaseModel):
    """Clasificación de Nivel 2 (Sub-departamento)"""
    tipo: SubCategoriaInfo = Field(..., description="Tipo específico de información solicitada")
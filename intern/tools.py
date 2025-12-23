import re
import html
import os
import httpx
import logging
from datetime import datetime, timedelta
from langchain_core.tools import tool

# Configuración de Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

FILESEARCHSTORE_INF_GEN = os.getenv("FILESEARCHSTORE_INF_GEN")
GEMINI_KEY = os.getenv("GEMINI_KEY")
URL_RAG = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_KEY}"


async def _consultar_base_datos_raw(message: str, fileSearchStore: str) -> str:
    """Función auxiliar privada para consultar Gemini RAG."""
    if not URL_RAG or not GEMINI_KEY:
        return "Error: Configuración de Gemini RAG incompleta."
        
    content = {
        "contents": [{"parts": [{"text": message}]}],
        "generationConfig": {"temperature": 0},
        "tools": [{"fileSearch": {"fileSearchStoreNames": [fileSearchStore]}}]
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(URL_RAG, json=content, timeout=30.0)
            if response.status_code != 200:
                logger.error(f"Error Gemini: {response.text}")
                return "Error técnico al consultar la base de conocimiento."
            
            respuesta_json = response.json()
            # Navegación segura por el JSON de respuesta de Google
            try:
                candidates = respuesta_json.get("candidates", [])
                if not candidates: return "No se encontró información relevante."
                
                parts = candidates[0].get("content", {}).get("parts", [])
                text = parts[0].get("text", "")
                return text if text else "No se encontró contexto suficiente."
            except (IndexError, KeyError):
                return "Formato de respuesta de base de datos inesperado."
                
    except Exception as e:
        logger.error(f"Excepción RAG: {e}")
        return f"Error de conexión: {str(e)}"

# --- HERRAMIENTAS PÚBLICAS ---

@tool
async def consultar_informacion_despacho(query: str):
    """Buscar información corporativa: horarios, ubicación, servicios, empleados."""
    return await _consultar_base_datos_raw(query, FILESEARCHSTORE_INF_GEN)

@tool
async def consultar_calendario_contribuyentes(dummy_arg: str = ""):
    """Consultar calendario fiscal. Devuelve lista de eventos limpios."""
    logger.info("Tool: Consultando calendario contribuyentes...")
    
    url = "https://www.nmb.es/content/getAgendaContent"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "X-Requested-With": "XMLHttpRequest"
    }

    now = datetime.now()
    # Lógica de fechas
    dateStart = now.strftime("%Y-%m-%d")
    proximo_mes = now.replace(year=now.year + 1, month=1, day=1) if now.month == 12 else now.replace(month=now.month + 1, day=1)
    dateEnd = (proximo_mes - timedelta(days=1)).strftime("%Y-%m-%d")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, data={"dateStart": dateStart, "dateEnd": dateEnd}, timeout=10.0)
            
            if response.status_code == 200:
                data = response.json()
                eventos_raw = data.get('data', [])
                eventos_limpios = []
                
                for evento in eventos_raw:
                    if not evento.get("date_end") or datetime.strptime(evento.get("date_end"), "%Y-%m-%d") > datetime.now():
                        title = evento.get("title")
                        if not ("hasta" in title.lower() and int(re.search("\\d+",title.lower()).group()) < datetime.now().day):
                            content = evento.get("content", "")
                            if content:
                                content = html.unescape(content)
                                content = re.sub(r'<[^>]+>', '', content)
                                content = re.sub(r'[\r\t]', "", content)
                                content = re.sub(r'\n+', "\n", content)
                                content = re.sub(r"\n|\xa0", " ", content)

                            evento_adecuado = {
                                        "title": title,
                                        "date_start": evento.get("date_start"),
                                        "date_end": evento.get("date_end"),
                                        "content": content
                                    }
                            eventos_limpios.append(f"📌 {title} (Fecha Inicio: {evento.get('date_start')} - Fecha Fin: {evento.get('date_end')}): {content}")

                if not eventos_limpios: return "No hay eventos próximos."
                return "\n\n".join(eventos_limpios)
            return "Error al obtener calendario externo."
    except Exception as e:

        return f"Excepción calendario: {str(e)}"

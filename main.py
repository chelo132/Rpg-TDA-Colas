"""
API para gestión de personajes y misiones en un sistema RPG

Esta API permite:
- Crear y listar personajes
- Crear y asignar misiones
- Gestionar el progreso de misiones (pendientes, activas, completadas)
- Seguir la experiencia (XP) de los personajes

Endpoints principales:
- /personajes: Gestión de personajes
- /misiones: Gestión de misiones
- /personajes/{id}/misiones: Gestión de misiones por personaje

Autenticación: Actualmente no implementada
"""

from fastapi import FastAPI, HTTPException, Depends, Query
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session, joinedload
from database import SessionLocal, engine, get_db, Personaje, Mision, personaje_misiones_completadas, personaje_misiones_pendientes, Base
from pydantic import BaseModel
from typing import List

app = FastAPI()

from fastapi import HTTPException
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.get("/personajes")
def listar_personajes(db: Session = Depends(get_db)):
    try:
        logger.info("Iniciando consulta de personajes")
        
        # Verificación de conexión a la base de datos
        # Se ejecuta una consulta simple para confirmar que la conexión está activa
        db.execute(text("SELECT 1"))
        logger.info("Conexión a la base de datos verificada")

        # Consulta para obtener todos los personajes con sus atributos básicos:
        # - ID
        # - Nombre
        # - XP
        # - ID de misión activa
        personajes = db.query(
            Personaje.id,
            Personaje.nombre,
            Personaje.xp,
            Personaje.mision_activa_id
        ).all()
        logger.info(f"Encontrados {len(personajes)} personajes")

        if not personajes:
            return []

        # Obtener IDs de misiones activas de todos los personajes
        # Filtramos los personajes que no tienen misión activa (mision_activa_id es None)
        mision_ids = [p.mision_activa_id for p in personajes if p.mision_activa_id]
        
        # Consulta para obtener detalles de las misiones activas
        # Solo se ejecuta si hay al menos un personaje con misión activa
        misiones_activas = {}
        if mision_ids:
            misiones = db.query(
                Mision.id,
                Mision.titulo
            ).filter(Mision.id.in_(mision_ids)).all()
            
            # Convertimos los resultados a un diccionario {id: misión}
            # para fácil acceso posterior
            misiones_activas = {m.id: m for m in misiones}
            logger.info(f"Encontradas {len(misiones_activas)} misiones activas")

        return [{
            "id": p.id,
            "nombre": p.nombre,
            "xp": p.xp,
            "mision_activa": {
                "id": p.mision_activa_id,
                "titulo": misiones_activas[p.mision_activa_id].titulo
            } if p.mision_activa_id and p.mision_activa_id in misiones_activas else None
        } for p in personajes]

    except Exception as e:
        logger.error(f"Error en listar_personajes: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Error interno al obtener personajes"
        )

@app.post("/personajes")
def crear_personaje(personaje: dict, db: Session = Depends(get_db)):
    """
    Crea un nuevo personaje en el sistema

    Args:
        personaje (dict): Datos del personaje a crear. Debe contener:
            - nombre (str): Nombre del personaje (requerido)
        db (Session): Sesión de base de datos (inyectada)

    Returns:
        dict: Datos del personaje creado:
            - id (int)
            - nombre (str)
            - xp (int) - Inicializado en 0

    Raises:
        HTTPException: 400 si falta el nombre o ya existe el personaje

    Example:
        Request body:
        {"nombre": "Nuevo Héroe"}

        Response:
        {
            "id": 10,
            "nombre": "Nuevo Héroe", 
            "xp": 0
        }
    """
    try:
        # Validar datos del personaje
        if not personaje.get("nombre"):
            raise HTTPException(status_code=400, detail="El nombre es requerido")
            
        # Verificar si el personaje ya existe
        existe = db.query(Personaje).filter(Personaje.nombre == personaje["nombre"]).first()
        if existe:
            raise HTTPException(status_code=400, detail="Ya existe un personaje con este nombre")
            
        nuevo_personaje = Personaje(nombre=personaje["nombre"], xp=0)
        db.add(nuevo_personaje)
        db.commit()
        db.refresh(nuevo_personaje)
        return {
            "id": nuevo_personaje.id,
            "nombre": nuevo_personaje.nombre,
            "xp": nuevo_personaje.xp
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"Error creando personaje: {str(e)}"
        )

@app.post("/misiones")
def crear_mision(
    titulo: str = Query(..., min_length=3),
    xp: int = Query(..., gt=0),
    db: Session = Depends(get_db)
):
    """
    Crea una nueva misión en el sistema

    Args:
        titulo (str): Título de la misión (mínimo 3 caracteres)
        xp (int): Experiencia (XP) que otorga la misión (mayor que 0)
        db (Session): Sesión de base de datos (inyectada)

    Returns:
        dict: Datos de la misión creada:
            - id (int)
            - titulo (str)
            - xp (int)
            - mensaje (str)

    Raises:
        HTTPException: 400 si el título ya existe o datos inválidos

    Example:
        Request:
        /misiones?titulo=Derrotar al jefe&xp=100

        Response:
        {
            "id": 15,
            "titulo": "Derrotar al jefe",
            "xp": 100,
            "mensaje": "Misión creada exitosamente"
        }
    """
    try:
        # Verificar si la misión ya existe
        existe = db.query(Mision).filter(Mision.titulo == titulo).first()
        if existe:
            raise HTTPException(
                status_code=400,
                detail="Ya existe una misión con este título"
            )
            
        mission = Mision(titulo=titulo, xp=xp)
        db.add(mission)
        db.commit()
        db.refresh(mission)
        return {
            "id": mission.id,
            "titulo": mission.titulo,
            "xp": mission.xp,
            "mensaje": "Misión creada exitosamente"
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"Error creando misión: {str(e)}"
        )

@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)

# [Previous endpoints remain unchanged...]

@app.get("/personajes/{personaje_id}/misiones")
def listar_misiones_personaje(personaje_id: int, db: Session = Depends(get_db)):
    """
    Obtiene todas las misiones relacionadas con un personaje

    Args:
        personaje_id (int): ID del personaje
        db (Session): Sesión de base de datos (inyectada)

    Returns:
        dict: Contiene:
            - personaje_id (int)
            - mision_activa (dict|None): Misión actual con:
                * id (int)
                * titulo (str)
                * xp (int)
            - misiones_pendientes (List[dict]): Misiones en cola
            - misiones_completadas (List[dict]): Misiones finalizadas
            - misiones_disponibles (List[dict]): Misiones asignables

    Raises:
        HTTPException: 404 si no existe el personaje
        HTTPException: 500 si hay error interno

    Example:
        Response:
        {
            "personaje_id": 1,
            "mision_activa": {
                "id": 5,
                "titulo": "Derrota al dragón",
                "xp": 100
            },
            "misiones_pendientes": [
                {"id": 6, "titulo": "Rescata al príncipe", "xp": 50}
            ],
            "misiones_completadas": [
                {"id": 1, "titulo": "Tutorial", "xp": 10}
            ],
            "misiones_disponibles": [
                {"id": 7, "titulo": "Explora la cueva", "xp": 30}
            ]
        }
    """
    try:
        logger.info(f"Obteniendo misiones para personaje {personaje_id}")
        
        # Verificar que el personaje existe
        personaje = db.query(Personaje).get(personaje_id)
        if not personaje:
            raise HTTPException(status_code=404, detail="Personaje no encontrado")
            
        # Obtener misión activa si existe
        mision_activa = None
        if personaje.mision_activa_id:
            mision_activa = db.query(Mision).get(personaje.mision_activa_id)
            if not mision_activa:
                logger.error(f"Misión activa {personaje.mision_activa_id} no encontrada")
                raise HTTPException(
                    status_code=500,
                    detail="Misión activa no encontrada"
                )
        
        # Obtener misiones pendientes usando la relación
        misiones_pendientes = []
        if hasattr(personaje, 'misiones_pendientes'):
            try:
                misiones_pendientes = [
                    {"id": m.id, "titulo": m.titulo, "xp": m.xp}
                    for m in personaje.misiones_pendientes
                ]
                logger.info(f"Encontradas {len(misiones_pendientes)} misiones pendientes")
            except Exception as e:
                logger.error(f"Error obteniendo misiones pendientes: {str(e)}")
        
        # Obtener misiones completadas usando la relación
        misiones_completadas = []
        if hasattr(personaje, 'misiones_completadas'):
            try:
                misiones_completadas = [
                    {"id": m.id, "titulo": m.titulo, "xp": m.xp}
                    for m in personaje.misiones_completadas
                ]
                logger.info(f"Encontradas {len(misiones_completadas)} misiones completadas")
            except Exception as e:
                logger.error(f"Error obteniendo misiones completadas: {str(e)}")
        
        # Obtener todas las misiones disponibles (no asignadas ni completadas)
        misiones_disponibles = []
        try:
            subquery_pendientes = db.query(personaje_misiones_pendientes.c.mision_id).filter(
                personaje_misiones_pendientes.c.personaje_id == personaje_id
            )
            subquery_completadas = db.query(personaje_misiones_completadas.c.mision_id).filter(
                personaje_misiones_completadas.c.personaje_id == personaje_id
            )
            
            misiones_disponibles = db.query(Mision).filter(
                Mision.id.notin_(subquery_pendientes),
                Mision.id.notin_(subquery_completadas),
                Mision.id != (personaje.mision_activa_id or 0)
            ).all()
            
            misiones_disponibles = [
                {"id": m.id, "titulo": m.titulo, "xp": m.xp}
                for m in misiones_disponibles
            ]
            logger.info(f"Encontradas {len(misiones_disponibles)} misiones disponibles")
        except Exception as e:
            logger.error(f"Error obteniendo misiones disponibles: {str(e)}")
        
        return {
            "personaje_id": personaje_id,
            "mision_activa": {
                "id": mision_activa.id,
                "titulo": mision_activa.titulo,
                "xp": mision_activa.xp
            } if mision_activa else None,
            "misiones_pendientes": misiones_pendientes,
            "misiones_completadas": misiones_completadas,
            "misiones_disponibles": misiones_disponibles
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error interno al obtener misiones: {str(e)}"
        )

@app.get("/personajes/{personaje_id}/misiones/disponibles")
def listar_misiones_disponibles(personaje_id: int, db: Session = Depends(get_db)):
    try:
        # Verificar que el personaje existe
        personaje = db.query(Personaje).get(personaje_id)
        if not personaje:
            raise HTTPException(status_code=404, detail="Personaje no encontrado")
            
        # Obtener IDs de misiones ya asignadas o completadas
        misiones_pendientes = db.query(
            personaje_misiones_pendientes.c.mision_id
        ).filter(
            personaje_misiones_pendientes.c.personaje_id == personaje_id
        )
        
        misiones_completadas = db.query(
            personaje_misiones_completadas.c.mision_id
        ).filter(
            personaje_misiones_completadas.c.personaje_id == personaje_id
        )
        
        misiones = db.query(Mision).filter(
            ~Mision.id.in_(misiones_pendientes),
            ~Mision.id.in_(misiones_completadas),
            Mision.id != personaje.mision_activa_id if personaje.mision_activa_id else True
        ).all()
        
        return [
            {"id": m.id, "titulo": m.titulo, "xp": m.xp}
            for m in misiones
        ]
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error obteniendo misiones disponibles: {str(e)}"
        )

@app.post("/personajes/{personaje_id}/misiones/{mision_id}")
def asignar_mision(
    personaje_id: int, 
    mision_id: int,
    db: Session = Depends(get_db)
):
    """
    Asigna una misión a un personaje (sistema FIFO)

    Comportamiento:
    - Si el personaje no tiene misión activa, la asigna directamente
    - Si ya tiene misión activa, la nueva misión se añade a la cola
    - Las misiones se asignarán en orden FIFO cuando se completen las activas

    Args:
        personaje_id (int): ID del personaje
        mision_id (int): ID de la misión a asignar
        db (Session): Sesión de base de datos (inyectada)

    Returns:
        dict: Contiene:
            - mensaje (str)
            - mision_activa (bool): True si se asignó como misión activa
            - en_cola (bool): True si se añadió a la cola

    Raises:
        HTTPException: 404 si no existe personaje o misión
        HTTPException: 400 si hay error en la asignación

    Example:
        Response exitosa:
        {
            "mensaje": "Misión asignada correctamente",
            "mision_activa": true,
            "en_cola": false
        }
    """
    try:
        # Verificar que existan el personaje y la misión
        personaje = db.query(Personaje).get(personaje_id)
        if not personaje:
            raise HTTPException(status_code=404, detail="Personaje no encontrado")
            
        mision = db.query(Mision).get(mision_id)
        if not mision:
            raise HTTPException(status_code=404, detail="Misión no encontrada")
        
        # Si no tiene misión activa, asignarla directamente
        if not personaje.mision_activa_id:
            personaje.mision_activa_id = mision_id
        else:
            # Si ya tiene misión activa, agregar a la cola
            max_orden = db.execute(
                text("SELECT MAX(orden) FROM personaje_misiones_pendientes "
                     "WHERE personaje_id = :pid"),
                {"pid": personaje_id}
            ).scalar() or 0
            
            db.execute(
                text("INSERT INTO personaje_misiones_pendientes "
                     "(personaje_id, mision_id, orden) "
                     "VALUES (:pid, :mid, :ord)"),
                {"pid": personaje_id, "mid": mision_id, "ord": max_orden + 1}
            )
        
        db.commit()
        return {
            "mensaje": "Misión asignada correctamente",
            "mision_activa": personaje.mision_activa_id == mision_id,
            "en_cola": personaje.mision_activa_id != mision_id
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"Error asignando misión: {str(e)}"
        )

@app.post("/personajes/{personaje_id}/completar")
def completar_mision(personaje_id: int, db: Session = Depends(get_db)):
    """
    Completa la misión activa de un personaje y asigna la siguiente

    Flujo:
    1. Verifica que el personaje tenga misión activa
    2. Añade la XP de la misión al personaje
    3. Mueve la misión a completadas
    4. Asigna la siguiente misión de la cola (si existe)
    5. Elimina la misión asignada de la cola

    Args:
        personaje_id (int): ID del personaje
        db (Session): Sesión de base de datos (inyectada)

    Returns:
        dict: Contiene:
            - mensaje (str)
            - xp_ganada (int): XP obtenida
            - xp_total (int): XP acumulada

    Raises:
        HTTPException: 404 si no existe el personaje
        HTTPException: 400 si no tiene misión activa
        HTTPException: 500 si hay error interno

    Example:
        Response exitosa:
        {
            "mensaje": "Misión completada exitosamente",
            "xp_ganada": 100,
            "xp_total": 250
        }
    """
    try:
        personaje = db.query(Personaje).get(personaje_id)
        if not personaje:
            raise HTTPException(status_code=404, detail="Personaje no encontrado")
            
        if not personaje.mision_activa_id:
            raise HTTPException(status_code=400, detail="El personaje no tiene misión activa")
            
        mision = db.query(Mision).get(personaje.mision_activa_id)
        if not mision:
            raise HTTPException(status_code=404, detail="Misión activa no encontrada")
            
        # Obtener siguiente misión de la cola FIFO
        siguiente_mision = db.execute(
            text("SELECT mision_id FROM personaje_misiones_pendientes "
                 "WHERE personaje_id = :pid ORDER BY orden ASC LIMIT 1"),
            {"pid": personaje_id}
        ).fetchone()
        
        # Calcular XP ganada
        xp_ganada = mision.xp
        personaje.xp += xp_ganada
        
        # Mover misión actual a completadas
        db.execute(
            text("INSERT INTO personaje_misiones_completadas "
                 "(personaje_id, mision_id) VALUES (:pid, :mid)"),
            {"pid": personaje_id, "mid": personaje.mision_activa_id}
        )
        
        # Asignar siguiente misión o limpiar
        if siguiente_mision:
            personaje.mision_activa_id = siguiente_mision[0]
            db.execute(
                text("DELETE FROM personaje_misiones_pendientes "
                     "WHERE personaje_id = :pid AND mision_id = :mid"),
                {"pid": personaje_id, "mid": siguiente_mision[0]}
            )
        else:
            personaje.mision_activa_id = None
            
        db.commit()
        
        return {
            "mensaje": "Misión completada exitosamente",
            "xp_ganada": xp_ganada,  # Cambiado a "xp_ganada" para coincidir con frontend
            "xp_total": personaje.xp
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error completando misión: {str(e)}"
        )

# [Rest of the file remains unchanged...]

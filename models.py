"""
Definición de modelos de base de datos para el sistema RPG

Contiene:
- Tablas de asociación para relaciones many-to-many
- Modelos principales (Personaje y Mision)
- Relaciones entre entidades

Las tablas incluyen:
- personajes: Almacena los personajes del juego
- misiones: Registra las misiones disponibles
- tablas de asociación para misiones completadas/pendientes
"""

from sqlalchemy import Column, Integer, String, ForeignKey, Table
from sqlalchemy.orm import relationship
from database import Base

# Tabla de asociación para misiones completadas
personaje_misiones_completadas = Table(
    'personaje_misiones_completadas', 
    Base.metadata,
    Column('personaje_id', Integer, ForeignKey('personajes.id', ondelete="CASCADE"), primary_key=True),
    Column('mision_id', Integer, ForeignKey('misiones.id', ondelete="CASCADE"), primary_key=True)
)

# Tabla de asociación para misiones pendientes (cola)
personaje_misiones_pendientes = Table(
    'personaje_misiones_pendientes',
    Base.metadata,
    Column('personaje_id', Integer, ForeignKey('personajes.id', ondelete="CASCADE"), primary_key=True),
    Column('mision_id', Integer, ForeignKey('misiones.id', ondelete="CASCADE"), primary_key=True),
    Column('orden', Integer)  # Para mantener orden FIFO
)

class Personaje(Base):
    """
    Modelo que representa un personaje del juego RPG

    Atributos:
        id (int): Identificador único
        nombre (str): Nombre del personaje
        xp (int): Puntos de experiencia acumulados
        mision_activa_id (int): FK a la misión actual

    Relaciones:
        mision_activa: Misión que el personaje está realizando actualmente
        misiones_completadas: Lista de misiones finalizadas
        misiones_pendientes: Cola de misiones asignadas (orden FIFO)
    """
    __tablename__ = 'personajes'
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String)
    xp = Column(Integer, default=0)
    mision_activa_id = Column(Integer, ForeignKey('misiones.id'))
    
    # Relaciones
    mision_activa = relationship("Mision", foreign_keys=[mision_activa_id])
    misiones_completadas = relationship(
        "Mision",
        secondary=personaje_misiones_completadas,
        backref="personajes_completaron"
    )
    misiones_pendientes = relationship(
        "Mision",
        secondary=personaje_misiones_pendientes,
        backref="personajes_en_cola",
        order_by="personaje_misiones_pendientes.c.orden"
    )

class Mision(Base):
    """
    Modelo que representa una misión en el juego RPG

    Atributos:
        id (int): Identificador único
        titulo (str): Nombre/descripción de la misión
        xp (int): Experiencia que otorga al completarse

    Relaciones:
        personajes_completaron: Lista de personajes que finalizaron esta misión
        personajes_en_cola: Personajes que tienen esta misión en su cola pendiente
    """
    __tablename__ = 'misiones'
    
    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String)
    xp = Column(Integer)

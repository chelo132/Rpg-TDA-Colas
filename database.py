"""
CONFIGURACIÓN DE BASE DE DATOS RPG - SQLAlchemy

Componentes principales:
- Motor SQLite: sqlite:///./rpg.db
- SessionLocal: Fábrica de sesiones
- Base: Modelos declarativos
- Modelos: 
  * Personaje (id, nombre, xp, relaciones)
  * Mision (id, título, xp, relaciones)
- Funcionalidad:
  * get_db(): Generador de sesiones para FastAPI
"""
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Table
from sqlalchemy.orm import relationship, sessionmaker, declarative_base

SQLALCHEMY_DATABASE_URL = "sqlite:///./rpg.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Tablas de relación many-to-many
personaje_misiones_completadas = Table(
    'personaje_misiones_completadas', 
    Base.metadata,
    Column('personaje_id', Integer, ForeignKey('personajes.id', ondelete="CASCADE"), primary_key=True),
    Column('mision_id', Integer, ForeignKey('misiones.id', ondelete="CASCADE"), primary_key=True)
)

personaje_misiones_pendientes = Table(
    'personaje_misiones_pendientes',
    Base.metadata,
    Column('personaje_id', Integer, ForeignKey('personajes.id', ondelete="CASCADE"), primary_key=True),
    Column('mision_id', Integer, ForeignKey('misiones.id', ondelete="CASCADE"), primary_key=True),
    Column('orden', Integer)  # Para mantener orden FIFO
)

# Definir modelos aquí mismo para evitar importaciones circulares
class Personaje(Base):
    """Modelo de personaje RPG con:
    - Atributos básicos (id, nombre, xp)
    - Relaciones:
      * mision_activa: Misión actual
      * misiones_completadas: Historial
      * misiones_pendientes: Cola FIFO
    """
    __tablename__ = 'personajes'
    id = Column(Integer, primary_key=True)
    nombre = Column(String)
    xp = Column(Integer, default=0)
    mision_activa_id = Column(Integer, ForeignKey('misiones.id'), nullable=True)
    
    mision_activa = relationship("Mision", back_populates="personajes_asignados")
    misiones_completadas = relationship(
        "Mision",
        secondary=personaje_misiones_completadas,
        back_populates="personajes_completaron"
    )
    misiones_pendientes = relationship(
        "Mision",
        secondary=personaje_misiones_pendientes,
        backref="personajes_pendientes",
        order_by="personaje_misiones_pendientes.c.orden"
    )

class Mision(Base):
    """Modelo de misión RPG con:
    - Atributos (id, título único, xp)
    - Relaciones:
      * personajes_asignados: Activos
      * personajes_completaron: Historial
    """
    __tablename__ = 'misiones'
    id = Column(Integer, primary_key=True)
    titulo = Column(String, unique=True)
    xp = Column(Integer)
    
    personajes_asignados = relationship("Personaje", back_populates="mision_activa")
    personajes_completaron = relationship(
        "Personaje",
        secondary=personaje_misiones_completadas,
        back_populates="misiones_completadas"
    )

def get_db():
    """Generador de sesiones para inyección de dependencias
    
    Uso:
    - yield db: Proporciona sesión activa
    - finally: Cierra sesión automáticamente
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
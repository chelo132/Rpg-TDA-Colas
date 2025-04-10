"""
Implementación de Cola (TDA) para manejo de misiones RPG

Proporciona una estructura FIFO (First In First Out) para:
- Gestionar misiones pendientes de personajes
- Mantener orden de ejecución (primero en entrar, primero en salir)
- Operaciones O(1) usando collections.deque
"""
from collections import deque

class ColaMisiones:
    """Implementación de cola para gestión de misiones RPG
    
    Atributos:
        items: deque que almacena IDs de misiones en orden FIFO
    
    Ejemplo:
        >>> cola = ColaMisiones()
        >>> cola.enqueue(101)
        >>> cola.enqueue(102)
        >>> cola.dequeue()
        101
    """
    def __init__(self):
        self.items = deque()

    def enqueue(self, mission_id: int):
        """Añade una misión al final de la cola
        
        Args:
            mission_id: ID numérico de la misión a encolar
        """
        self.items.append(mission_id)

    def dequeue(self):
        """Remueve y retorna la primera misión de la cola
        
        Returns:
            int: ID de la misión removida
            None: Si la cola está vacía
        """
        if not self.is_empty():
            return self.items.popleft()
        return None

    def first(self):
        """Consulta la próxima misión sin removerla
        
        Returns:
            int: ID de la próxima misión
            None: Si la cola está vacía
        """
        return self.items[0] if not self.is_empty() else None

    def is_empty(self):
        """Verifica si la cola está vacía
        
        Returns:
            bool: True si vacía, False si tiene misiones
        """
        return len(self.items) == 0

    def size(self):
        """Cantidad de misiones en cola
        
        Returns:
            int: Número de misiones pendientes
        """
        return len(self.items)

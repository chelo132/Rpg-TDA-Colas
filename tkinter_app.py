"""
Interfaz gráfica para el sistema RPG usando Tkinter

Contiene:
- Gestión de personajes (crear, eliminar, seleccionar)
- Gestión de misiones (crear, aceptar, completar)
- Visualización de estado (misión actual, cola FIFO, historial)
- Conexión con API REST para operaciones CRUD
"""

import tkinter as tk
from tkinter import ttk, messagebox
import requests

BASE_URL = "http://127.0.0.1:8000"

class RPGApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema de Misiones RPG")
        
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(padx=10, pady=10, fill='both', expand=True)

        self.tab_personajes = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_personajes, text="Personajes")

        self.list_frame = ttk.Frame(self.tab_personajes)
        self.list_frame.pack(fill='both', expand=True, padx=5, pady=5)

        self.char_listbox = tk.Listbox(self.list_frame)
        self.char_listbox.pack(side='left', fill='both', expand=True)
        self.char_listbox.bind('<<ListboxSelect>>', self.on_character_select)
        
        self.selected_char_id = None
        self.selected_char_name = None
        
        scrollbar = ttk.Scrollbar(self.list_frame, orient='vertical', command=self.char_listbox.yview)
        scrollbar.pack(side='right', fill='y')
        self.char_listbox.config(yscrollcommand=scrollbar.set)

        self.buttons_frame = ttk.Frame(self.tab_personajes)
        self.buttons_frame.pack(fill='x', pady=5)
        
        ttk.Button(self.buttons_frame, text="Actualizar lista", command=self.actualizar_personajes).pack(side='left', padx=5)
        ttk.Button(self.buttons_frame, text="Seleccionar Personaje", command=self.seleccionar_personaje).pack(side='left', padx=5)
        ttk.Button(self.buttons_frame, text="Eliminar Personaje", command=self.eliminar_personaje).pack(side='left', padx=5)

        self.creation_frame = ttk.LabelFrame(self.tab_personajes, text="Crear nuevo personaje")
        self.creation_frame.pack(fill='x', padx=5, pady=5)

        ttk.Label(self.creation_frame, text="Nombre del Personaje").grid(row=0, column=0, padx=5, pady=5)
        self.nombre_entry = ttk.Entry(self.creation_frame)
        self.nombre_entry.grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(self.creation_frame, text="Crear Personaje", command=self.crear_personaje).grid(row=0, column=2, padx=5, pady=5)

        self.tab_misiones = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_misiones, text="Misiones")
        
        self.current_mission_frame = ttk.LabelFrame(self.tab_misiones, text="Misión Actual")
        self.current_mission_frame.pack(fill='x', padx=10, pady=5)
        
        self.current_mission_label = ttk.Label(self.current_mission_frame, text="Ninguna misión activa")
        self.current_mission_label.pack(pady=10)
        
        ttk.Button(self.current_mission_frame, text="Completar Misión", command=self.completar_mision_actual).pack(pady=5)
        
        self.queue_frame = ttk.LabelFrame(self.tab_misiones, text="Misiones en Cola (FIFO)")
        self.queue_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        self.queue_listbox = tk.Listbox(self.queue_frame)
        self.queue_listbox.pack(side='left', fill='both', expand=True)
        
        scrollbar = ttk.Scrollbar(self.queue_frame, orient='vertical', command=self.queue_listbox.yview)
        scrollbar.pack(side='right', fill='y')
        self.queue_listbox.config(yscrollcommand=scrollbar.set)
        
        self.controls_frame = ttk.Frame(self.tab_misiones)
        self.controls_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Button(self.controls_frame, text="Actualizar Misiones", command=self.actualizar_misiones).pack(side='right', padx=5)

        self.creation_frame = ttk.LabelFrame(self.controls_frame, text="Crear/Aceptar Misión")
        self.creation_frame.pack(side='left', fill='x', expand=True, padx=5)
        
        ttk.Label(self.creation_frame, text="Título:").grid(row=0, column=0, padx=5, pady=2)
        self.titulo_entry = ttk.Entry(self.creation_frame)
        self.titulo_entry.grid(row=0, column=1, padx=5, pady=2)
        
        ttk.Label(self.creation_frame, text="XP:").grid(row=1, column=0, padx=5, pady=2)
        self.xp_entry = ttk.Entry(self.creation_frame)
        self.xp_entry.grid(row=1, column=1, padx=5, pady=2)
        
        ttk.Button(self.creation_frame, text="Crear Misión", command=self.crear_mision).grid(row=2, column=0, columnspan=2, pady=5)
        
        self.accept_frame = ttk.LabelFrame(self.controls_frame, text="Aceptar Misión")
        self.accept_frame.pack(side='left', fill='x', expand=True, padx=5)
        
        self.mission_combobox = ttk.Combobox(self.accept_frame)
        self.mission_combobox.pack(padx=5, pady=5)
        
        ttk.Button(self.accept_frame, text="Aceptar Misión", command=self.aceptar_mision).pack(pady=5)
        
        self.history_frame = ttk.LabelFrame(self.tab_misiones, text="Misiones Completadas")
        self.history_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        self.history_listbox = tk.Listbox(self.history_frame)
        self.history_listbox.pack(side='left', fill='both', expand=True)
        
        scrollbar = ttk.Scrollbar(self.history_frame, orient='vertical', command=self.history_listbox.yview)
        scrollbar.pack(side='right', fill='y')
        self.history_listbox.config(yscrollcommand=scrollbar.set)

        self.actualizar_personajes()

    def on_character_select(self, event):
        """Manejador de evento para selección de personaje en la lista
        
        Args:
            event: Evento de selección de Tkinter
            
        Actualiza:
            selected_char_id: ID del personaje seleccionado
            selected_char_name: Nombre del personaje seleccionado
        """
        selection = self.char_listbox.curselection()
        if selection:
            selected_text = self.char_listbox.get(selection[0])
            parts = selected_text.split()
            self.selected_char_id = int(parts[1])
            self.selected_char_name = ' '.join(parts[3:-1]).strip('()')

    def seleccionar_personaje(self):
        """Selecciona el personaje actual para operaciones de misiones
        
        Valida que haya un personaje seleccionado.
        Cambia a la pestaña de misiones.
        Muestra mensaje de confirmación.
        """
        if not self.selected_char_id:
            messagebox.showerror("Error", "Selecciona un personaje primero")
            return
            
        self.notebook.select(1)
        messagebox.showinfo("Personaje seleccionado", f"Personaje {self.selected_char_name} (ID: {self.selected_char_id}) seleccionado")

    def actualizar_personajes(self):
        try:
            res = requests.get(f"{BASE_URL}/personajes", timeout=5)
            res.raise_for_status()
            
            personajes = res.json()
            self.char_listbox.delete(0, tk.END)
            
            for p in personajes:
                self.char_listbox.insert(tk.END, f"ID: {p['id']} - {p['nombre']} (XP: {p['xp']})")
                
        except Exception as e:
            messagebox.showerror("Error", f"Error al obtener personajes: {str(e)}")

    def crear_personaje(self):
        nombre = self.nombre_entry.get()
        if nombre:
            try:
                res = requests.post(
                    f"{BASE_URL}/personajes",
                    json={"nombre": nombre},
                    headers={"Content-Type": "application/json"}
                )
                res.raise_for_status()
                messagebox.showinfo("Éxito", f"Personaje {nombre} creado")
                self.actualizar_personajes()
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo crear el personaje: {str(e)}")

    def eliminar_personaje(self):
        """Elimina el personaje seleccionado
        
        Realiza petición DELETE a la API.
        Valida selección y muestra mensajes de éxito/error.
        Actualiza la lista de personajes.
        """
        selection = self.char_listbox.curselection()
        if not selection:
            messagebox.showerror("Error", "Selecciona un personaje primero")
            return
            
        personaje_id = int(self.char_listbox.get(selection[0]).split()[1])
        
        try:
            response = requests.delete(f"{BASE_URL}/personajes/{personaje_id}")
            if response.status_code == 200:
                messagebox.showinfo("Éxito", "Personaje eliminado")
                self.actualizar_personajes()
            else:
                messagebox.showerror("Error", f"No se pudo eliminar: {response.text}")
        except Exception as e:
            messagebox.showerror("Error", f"Error al eliminar: {str(e)}")

    def actualizar_misiones(self):
        if not self.selected_char_id:
            return

        try:
            res = requests.get(f"{BASE_URL}/personajes/{self.selected_char_id}/misiones")
            data = res.json()

            self.queue_listbox.delete(0, tk.END)
            for m in data.get('misiones_pendientes', []):
                self.queue_listbox.insert(tk.END, f"{m['id']}: {m['titulo']} (XP: {m['xp']})")

            self.history_listbox.delete(0, tk.END)
            for m in data.get('misiones_completadas', []):
                self.history_listbox.insert(tk.END, f"{m['id']}: {m['titulo']} (XP: {m['xp']})")

            misiones_disponibles = [
                f"{m['id']}: {m['titulo']}" 
                for m in data.get('misiones_disponibles', [])
            ]
            self.mission_combobox['values'] = misiones_disponibles
            self.mission_combobox.set('')

            mision_activa = data.get('mision_activa')
            if mision_activa:
                self.current_mission_label.config(text=f"{mision_activa['titulo']} (XP: {mision_activa['xp']})")
            else:
                self.current_mission_label.config(text="Ninguna misión activa")
                
        except Exception as e:
            messagebox.showerror("Error", f"Error al actualizar misiones: {str(e)}")

    def completar_mision_actual(self):
        """Marca la misión actual como completada
        
        Realiza petición POST al endpoint de completar misión.
        Muestra XP ganada y total.
        Actualiza la información de misiones.
        """
        if not self.selected_char_id:
            messagebox.showerror("Error", "Selecciona un personaje primero")
            return
            
        try:
            res = requests.post(f"{BASE_URL}/personajes/{self.selected_char_id}/completar")
            result = res.json()
            messagebox.showinfo("Misión completada", f"XP ganada: {result['xp_ganada']}\nXP total: {result['xp_total']}")
            self.actualizar_misiones()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo completar: {str(e)}")

    def aceptar_mision(self):
        """Acepta una misión del combobox y la añade a la cola
        
        Valida selección de personaje y misión.
        Realiza petición POST para aceptar misión.
        Actualiza la interfaz con los nuevos datos.
        Maneja posibles errores.
        """
        if not self.selected_char_id:
            messagebox.showerror("Error", "Selecciona un personaje primero")
            return
            
        selected = self.mission_combobox.get()
        if not selected or selected == 'No hay misiones disponibles':
            messagebox.showerror("Error", "Selecciona una misión primero")
            return
            
        try:
            mission_id = int(selected.split(':')[0])
            res = requests.post(
                f"{BASE_URL}/personajes/{self.selected_char_id}/misiones/{mission_id}"
            )
            
            if res.status_code == 200:
                messagebox.showinfo("Éxito", "Misión aceptada y añadida a la cola")
                self.actualizar_misiones()
                self.mission_combobox.set('')
                data = requests.get(f"{BASE_URL}/personajes/{self.selected_char_id}/misiones").json()
                
                self.queue_listbox.delete(0, tk.END)
                for m in data.get('misiones_pendientes', []):
                    self.queue_listbox.insert(tk.END, f"{m['id']}: {m['titulo']} (XP: {m['xp']})")
                
                self.mission_combobox['values'] = [
                    f"{m['id']}: {m['titulo']}" 
                    for m in data.get('misiones_disponibles', [])
                ]
                if not self.mission_combobox['values']:
                    self.mission_combobox.set('No hay misiones disponibles')
            else:
                error_detail = res.json().get('detail', res.text)
                messagebox.showerror("Error", f"No se pudo aceptar la misión: {error_detail}")
                
        except ValueError:
            messagebox.showerror("Error", "ID de misión inválido")
        except Exception as e:
            messagebox.showerror("Error", f"Error inesperado: {str(e)}")

    def crear_mision(self):
        """Crea una nueva misión con los datos del formulario
        
        Valida campos de título y XP.
        Realiza petición POST para crear misión.
        Limpia formulario y actualiza lista si tiene éxito.
        Maneja errores de validación.
        """
        titulo = self.titulo_entry.get()
        xp = self.xp_entry.get()
        
        if titulo and xp:
            try:
                xp_int = int(xp)
                res = requests.post(
                    f"{BASE_URL}/misiones",
                    params={"titulo": titulo, "xp": xp_int}
                )
                
                if res.status_code == 200:
                    messagebox.showinfo("Éxito", "Misión creada")
                    self.titulo_entry.delete(0, tk.END)
                    self.xp_entry.delete(0, tk.END)
                    self.actualizar_misiones()
                else:
                    messagebox.showerror("Error", f"No se pudo crear: {res.text}")
                    
            except ValueError:
                messagebox.showerror("Error", "XP debe ser un número")
            except Exception as e:
                messagebox.showerror("Error", f"Error al crear: {str(e)}")
        else:
            messagebox.showerror("Error", "Título y XP son requeridos")

if __name__ == "__main__":
    root = tk.Tk()
    app = RPGApp(root)
    root.mainloop()

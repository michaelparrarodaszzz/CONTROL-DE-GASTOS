#uwu onichan
import sqlite3, hashlib, re, datetime
import tkinter as tk
from tkinter import ttk, messagebox

DB_PATH = "gestiondegastos.db"

# -------------------- Conexión --------------------
def conexion_bd() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

def hash_pw(pw: str) -> str:
    return hashlib.sha256(pw.encode("utf-8")).hexdigest()

def email_valido(email: str) -> bool:
    return EMAIL_RE.match(email or "") is not None

def fecha_valida(yyyy_mm_dd: str) -> bool:
    if not yyyy_mm_dd:
        return True
    try:
        datetime.date.fromisoformat(yyyy_mm_dd)
        return True
    except Exception:
        return False

def lista_usuarios():
    with conexion_bd() as c:
        return c.execute("SELECT id, nombre, email FROM usuarios ORDER BY nombre").fetchall()

def lista_cuentas(id_usuario: int):
    with conexion_bd() as c:
        return c.execute("SELECT id, nombre FROM cuentas WHERE id_usuario=? ORDER BY nombre", (id_usuario,)).fetchall()

def lista_categorias(id_usuario: int):
    with conexion_bd() as c:
        return c.execute("SELECT id, nombre FROM categorias WHERE id_usuario=? ORDER BY nombre", (id_usuario,)).fetchall()

def id_from_combo(texto: str):
    try:
        return int((texto or "").split(" - ")[0])
    except Exception:
        return None

# -------------------- Base CRUD --------------------
class BaseCRUD(ttk.Frame):
    def __init__(self, master):
        super().__init__(master, padding=10)
        self.pack(fill="both", expand=True)
        self.selected_id = None
        self._build_layout()
        self._build_form()
        self.configurar_columnas()
        self.cargar_tabla()

    def _build_layout(self):
        # Buscador
        top = ttk.Frame(self); top.pack(fill="x")
        ttk.Label(top, text="Buscar:").pack(side="left")
        self.ent_buscar = ttk.Entry(top, width=30); self.ent_buscar.pack(side="left", padx=6)
        ttk.Button(top, text="Buscar", command=self.buscar).pack(side="left")
        ttk.Button(top, text="Limpiar", command=self.limpiar_busqueda).pack(side="left", padx=(6,0))

        # Tabla
        mid = ttk.Frame(self); mid.pack(fill="both", expand=True, pady=(8,8))
        self.tree = ttk.Treeview(mid, show="headings", selectmode="browse")
        self.tree.pack(side="left", fill="both", expand=True)
        vsb = ttk.Scrollbar(mid, orient="vertical", command=self.tree.yview)
        vsb.pack(side="left", fill="y")
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        # Formulario
        self.form = ttk.LabelFrame(self, text="Formulario", padding=10)
        self.form.pack(fill="x")

        # Botones
        btns = ttk.Frame(self); btns.pack(fill="x", pady=(8,0))
        ttk.Button(btns, text="Nuevo", command=self.nuevo).pack(side="left")
        ttk.Button(btns, text="Guardar", command=self.guardar).pack(side="left", padx=6)
        ttk.Button(btns, text="Eliminar", command=self.eliminar).pack(side="left")
        ttk.Button(btns, text="Refrescar", command=self.cargar_tabla).pack(side="right")

    # Hooks para sobrescribir
    def configurar_columnas(self): ...
    def _build_form(self): ...
    def cargar_tabla(self, filtro: str = ""): ...
    def on_select(self, _evt): ...
    def nuevo(self): ...
    def guardar(self): ...
    def eliminar(self): ...
    # Comunes
    def buscar(self): self.cargar_tabla(self.ent_buscar.get().strip())
    def limpiar_busqueda(self):
        self.ent_buscar.delete(0, tk.END)
        self.cargar_tabla()
        self.nuevo()

# -------------------- Usuarios --------------------
class UsuariosFrame(BaseCRUD):
    def configurar_columnas(self):
        cols = [("id","ID",60,"e"), ("nombre","Nombre",220,"w"), ("email","Email",260,"w")]
        self.tree["columns"] = [c[0] for c in cols]
        for key, title, w, anchor in cols:
            self.tree.heading(key, text=title)
            self.tree.column(key, width=w, anchor=anchor)

    def _build_form(self):
        f = ttk.Frame(self.form); f.pack(fill="x")

        ttk.Label(f, text="ID:").grid(row=0, column=0, sticky="w")
        self.var_id = tk.StringVar(); ttk.Entry(f, textvariable=self.var_id, width=10, state="readonly").grid(row=0, column=1, sticky="w", pady=3)

        ttk.Label(f, text="Nombre *:").grid(row=1, column=0, sticky="w")
        self.var_nombre = tk.StringVar(); ttk.Entry(f, textvariable=self.var_nombre, width=40).grid(row=1, column=1, sticky="w", pady=3)

        ttk.Label(f, text="Email *:").grid(row=2, column=0, sticky="w")
        self.var_email = tk.StringVar(); ttk.Entry(f, textvariable=self.var_email, width=40).grid(row=2, column=1, sticky="w", pady=3)

        ttk.Label(f, text="Contraseña *:").grid(row=3, column=0, sticky="w")
        self.var_pwd = tk.StringVar(); self.ent_pwd = ttk.Entry(f, textvariable=self.var_pwd, width=40, show="•")
        self.ent_pwd.grid(row=3, column=1, sticky="w", pady=3)

        ttk.Label(f, text="Confirmar *:").grid(row=4, column=0, sticky="w")
        self.var_pwd2 = tk.StringVar(); self.ent_pwd2 = ttk.Entry(f, textvariable=self.var_pwd2, width=40, show="•")
        self.ent_pwd2.grid(row=4, column=1, sticky="w", pady=3)

        self.var_mostrar = tk.BooleanVar(value=False)
        ttk.Checkbutton(f, text="Mostrar contraseñas", variable=self.var_mostrar, command=self._toggle_pw).grid(row=5, column=1, sticky="w")

        f.grid_columnconfigure(1, weight=1)

    def _toggle_pw(self):
        show = "" if self.var_mostrar.get() else "•"
        self.ent_pwd.config(show=show); self.ent_pwd2.config(show=show)

    def cargar_tabla(self, filtro: str = ""):
        for it in self.tree.get_children(): self.tree.delete(it)
        with conexion_bd() as c:
            if filtro:
                like = f"%{filtro}%"
                rows = c.execute("""SELECT id, nombre, email FROM usuarios
                                    WHERE nombre LIKE ? OR email LIKE ?
                                    ORDER BY id DESC""", (like, like)).fetchall()
            else:
                rows = c.execute("SELECT id, nombre, email FROM usuarios ORDER BY id DESC").fetchall()
        for r in rows:
            self.tree.insert("", "end", values=(r["id"], r["nombre"], r["email"]))

    def on_select(self, _evt):
        sel = self.tree.selection()
        if not sel: return
        uid = int(self.tree.item(sel[0], "values")[0])
        with conexion_bd() as c:
            r = c.execute("SELECT id, nombre, email FROM usuarios WHERE id=?", (uid,)).fetchone()
        if r:
            self.selected_id = uid
            self.var_id.set(r["id"]); self.var_nombre.set(r["nombre"]); self.var_email.set(r["email"])
            self.var_pwd.set(""); self.var_pwd2.set("")

    def nuevo(self):
        self.selected_id = None
        self.var_id.set(""); self.var_nombre.set(""); self.var_email.set(""); self.var_pwd.set(""); self.var_pwd2.set("")

    def guardar(self):
        nombre = self.var_nombre.get().strip()
        email  = self.var_email.get().strip().lower()
        pwd    = self.var_pwd.get(); pwd2 = self.var_pwd2.get()
        if not nombre or not email or not email_valido(email):
            messagebox.showwarning("Validación", "Nombre y Email válido son obligatorios."); return
        if self.selected_id is None:
            if not pwd or pwd != pwd2 or len(pwd) < 8:
                messagebox.showwarning("Validación", "Contraseña obligatoria, coincidente y ≥ 8."); return
            try:
                with conexion_bd() as c:
                    c.execute("INSERT INTO usuarios(nombre,email,contrasena) VALUES (?,?,?)",
                              (nombre, email, hash_pw(pwd)))
                messagebox.showinfo("OK", "Usuario creado.")
            except sqlite3.IntegrityError:
                messagebox.showerror("Error", "El email ya está registrado.")
        else:
            if (pwd or pwd2) and (pwd != pwd2 or len(pwd) < 8):
                messagebox.showwarning("Validación", "Si cambias, la contraseña debe coincidir y tener ≥ 8."); return
            with conexion_bd() as c:
                if pwd:
                    c.execute("UPDATE usuarios SET nombre=?, email=?, contrasena=? WHERE id=?",
                              (nombre, email, hash_pw(pwd), self.selected_id))
                else:
                    c.execute("UPDATE usuarios SET nombre=?, email=? WHERE id=?",
                              (nombre, email, self.selected_id))
            messagebox.showinfo("OK", "Usuario actualizado.")
        self.cargar_tabla(); self.nuevo()

    def eliminar(self):
        if not self.selected_id:
            messagebox.showwarning("Eliminar", "Selecciona un usuario."); return
        if not messagebox.askyesno("Confirmar", "¿Eliminar usuario seleccionado?"): return
        try:
            with conexion_bd() as c:
                c.execute("DELETE FROM usuarios WHERE id=?", (self.selected_id,))
            messagebox.showinfo("OK", "Usuario eliminado.")
        except sqlite3.IntegrityError as e:
            messagebox.showerror("Error", f"No se pudo eliminar: {e}")
        self.cargar_tabla(); self.nuevo()

# -------------------- Cuentas --------------------
class CuentasFrame(BaseCRUD):
    TIPOS = ("ahorro","corriente","tarjeta","efectivo","otro")
    ESTADOS = ("activa","inactiva")

    def configurar_columnas(self):
        cols = [
            ("id","ID",60,"e"), ("usuario","Usuario",160,"w"), ("nombre","Nombre",180,"w"),
            ("tipo","Tipo",100,"w"), ("moneda","Moneda",70,"center"), ("saldo","Saldo",100,"e"),
            ("estado","Estado",90,"w"), ("fecha","Creada",100,"w")
        ]
        self.tree["columns"] = [c[0] for c in cols]
        for key, title, w, anchor in cols:
            self.tree.heading(key, text=title)
            self.tree.column(key, width=w, anchor=anchor)

    def _build_form(self):
        f = ttk.Frame(self.form); f.pack(fill="x")

        ttk.Label(f, text="ID:").grid(row=0, column=0, sticky="w")
        self.var_id = tk.StringVar(); ttk.Entry(f, textvariable=self.var_id, width=10, state="readonly").grid(row=0, column=1, sticky="w", pady=3)

        ttk.Label(f, text="Usuario *:").grid(row=1, column=0, sticky="w")
        self.var_user = tk.StringVar(); self.cbo_user = ttk.Combobox(f, textvariable=self.var_user, state="readonly", width=38)
        self.cbo_user.grid(row=1, column=1, sticky="w", pady=3); self._cargar_usuarios_combo()

        ttk.Label(f, text="Nombre *:").grid(row=2, column=0, sticky="w")
        self.var_nombre = tk.StringVar(); ttk.Entry(f, textvariable=self.var_nombre, width=40).grid(row=2, column=1, sticky="w", pady=3)

        ttk.Label(f, text="Tipo *:").grid(row=3, column=0, sticky="w")
        self.var_tipo = tk.StringVar(value=self.TIPOS[0]); ttk.Combobox(f, values=self.TIPOS, textvariable=self.var_tipo, state="readonly", width=38)\
            .grid(row=3, column=1, sticky="w", pady=3)

        ttk.Label(f, text="Moneda *:").grid(row=4, column=0, sticky="w")
        self.var_moneda = tk.StringVar(value="PYG"); ttk.Entry(f, textvariable=self.var_moneda, width=10).grid(row=4, column=1, sticky="w", pady=3)

        ttk.Label(f, text="Saldo inicial *:").grid(row=5, column=0, sticky="w")
        self.var_saldo = tk.StringVar(value="0"); ttk.Entry(f, textvariable=self.var_saldo, width=14).grid(row=5, column=1, sticky="w", pady=3)

        ttk.Label(f, text="Estado *:").grid(row=6, column=0, sticky="w")
        self.var_estado = tk.StringVar(value=self.ESTADOS[0]); ttk.Combobox(f, values=self.ESTADOS, textvariable=self.var_estado, state="readonly", width=38)\
            .grid(row=6, column=1, sticky="w", pady=3)

        ttk.Label(f, text="Fecha (YYYY-MM-DD):").grid(row=7, column=0, sticky="w")
        self.var_fecha = tk.StringVar(value=str(datetime.date.today()))
        ttk.Entry(f, textvariable=self.var_fecha, width=18).grid(row=7, column=1, sticky="w", pady=3)

        f.grid_columnconfigure(1, weight=1)

    def _cargar_usuarios_combo(self):
        items = lista_usuarios()
        self.cbo_user["values"] = [f"{r['id']} - {r['email']}" for r in items]
        if items: self.cbo_user.current(0)

    def cargar_tabla(self, filtro: str = ""):
        for it in self.tree.get_children(): self.tree.delete(it)
        with conexion_bd() as c:
            if filtro:
                like = f"%{filtro}%"
                rows = c.execute("""SELECT cu.id, u.email AS usuario, cu.nombre, cu.tipo_cuenta AS tipo,
                                           cu.moneda, cu.saldo_inicial AS saldo, cu.estado, cu.fecha_creacion AS fecha
                                    FROM cuentas cu JOIN usuarios u ON u.id=cu.id_usuario
                                    WHERE cu.nombre LIKE ? OR u.email LIKE ?
                                    ORDER BY cu.id DESC""", (like, like)).fetchall()
            else:
                rows = c.execute("""SELECT cu.id, u.email AS usuario, cu.nombre, cu.tipo_cuenta AS tipo,
                                           cu.moneda, cu.saldo_inicial AS saldo, cu.estado, cu.fecha_creacion AS fecha
                                    FROM cuentas cu JOIN usuarios u ON u.id=cu.id_usuario
                                    ORDER BY cu.id DESC""").fetchall()
        for r in rows:
            self.tree.insert("", "end", values=(r["id"], r["usuario"], r["nombre"], r["tipo"], r["moneda"],
                                                f"{r['saldo']:.2f}", r["estado"], r["fecha"]))

    def on_select(self, _evt):
        sel = self.tree.selection()
        if not sel: return
        cid = int(self.tree.item(sel[0], "values")[0])
        with conexion_bd() as c:
            r = c.execute("SELECT * FROM cuentas WHERE id=?", (cid,)).fetchone()
            u = c.execute("SELECT email FROM usuarios WHERE id=?", (r["id_usuario"],)).fetchone()
        if r:
            self.selected_id = cid
            self.var_id.set(r["id"])
            self.var_user.set(f"{r['id_usuario']} - {u['email'] if u else ''}")
            self.var_nombre.set(r["nombre"])
            self.var_tipo.set(r["tipo_cuenta"])
            self.var_moneda.set(r["moneda"])
            self.var_saldo.set(str(r["saldo_inicial"]))
            self.var_estado.set(r["estado"])
            self.var_fecha.set(r["fecha_creacion"])

    def nuevo(self):
        self.selected_id = None
        self.var_id.set("")
        self._cargar_usuarios_combo()
        self.var_nombre.set("")
        self.var_tipo.set(self.TIPOS[0])
        self.var_moneda.set("PYG")
        self.var_saldo.set("0")
        self.var_estado.set(self.ESTADOS[0])
        self.var_fecha.set(str(datetime.date.today()))

    def guardar(self):
        usuario_id = id_from_combo(self.var_user.get())
        if not usuario_id: messagebox.showwarning("Validación", "Selecciona un usuario."); return
        nombre = self.var_nombre.get().strip()
        if not nombre: messagebox.showwarning("Validación", "Nombre es obligatorio."); return
        tipo = self.var_tipo.get()
        moneda = self.var_moneda.get().strip() or "PYG"
        try:
            saldo = float(self.var_saldo.get())
        except:
            messagebox.showwarning("Validación", "Saldo inválido."); return
        estado = self.var_estado.get()
        fecha = self.var_fecha.get().strip()
        if not fecha_valida(fecha): messagebox.showwarning("Validación", "Fecha inválida."); return

        try:
            with conexion_bd() as c:
                if self.selected_id is None:
                    c.execute("""INSERT INTO cuentas(id_usuario,nombre,tipo_cuenta,moneda,saldo_inicial,estado,fecha_creacion)
                                 VALUES (?,?,?,?,?,?,?)""",
                              (usuario_id, nombre, tipo, moneda, saldo, estado, fecha))
                    messagebox.showinfo("OK", "Cuenta creada.")
                else:
                    c.execute("""UPDATE cuentas SET id_usuario=?, nombre=?, tipo_cuenta=?, moneda=?, saldo_inicial=?, estado=?, fecha_creacion=?
                                 WHERE id=?""",
                              (usuario_id, nombre, tipo, moneda, saldo, estado, fecha, self.selected_id))
                    messagebox.showinfo("OK", "Cuenta actualizada.")
        except sqlite3.IntegrityError as e:
            messagebox.showerror("Error", f"No se pudo guardar: {e}")
        self.cargar_tabla(); self.nuevo()

    def eliminar(self):
        if not self.selected_id:
            messagebox.showwarning("Eliminar", "Selecciona una cuenta."); return
        if not messagebox.askyesno("Confirmar", "¿Eliminar cuenta?"): return
        try:
            with conexion_bd() as c:
                c.execute("DELETE FROM cuentas WHERE id=?", (self.selected_id,))
            messagebox.showinfo("OK", "Cuenta eliminada.")
        except sqlite3.IntegrityError as e:
            messagebox.showerror("Error", f"No se pudo eliminar: {e}")
        self.cargar_tabla(); self.nuevo()

# -------------------- Categorías --------------------
class CategoriasFrame(BaseCRUD):
    TIPOS = ("ingreso","gasto")

    def configurar_columnas(self):
        cols = [("id","ID",60,"e"), ("usuario","Usuario",160,"w"), ("nombre","Nombre",220,"w"), ("tipo","Tipo",100,"w")]
        self.tree["columns"] = [c[0] for c in cols]
        for key, title, w, anchor in cols:
            self.tree.heading(key, text=title)
            self.tree.column(key, width=w, anchor=anchor)

    def _build_form(self):
        f = ttk.Frame(self.form); f.pack(fill="x")

        ttk.Label(f, text="ID:").grid(row=0, column=0, sticky="w")
        self.var_id = tk.StringVar(); ttk.Entry(f, textvariable=self.var_id, width=10, state="readonly").grid(row=0, column=1, sticky="w", pady=3)

        ttk.Label(f, text="Usuario *:").grid(row=1, column=0, sticky="w")
        self.var_user = tk.StringVar(); self.cbo_user = ttk.Combobox(f, textvariable=self.var_user, state="readonly", width=38)
        self.cbo_user.grid(row=1, column=1, sticky="w", pady=3); self._cargar_usuarios_combo()

        ttk.Label(f, text="Nombre *:").grid(row=2, column=0, sticky="w")
        self.var_nombre = tk.StringVar(); ttk.Entry(f, textvariable=self.var_nombre, width=40).grid(row=2, column=1, sticky="w", pady=3)

        ttk.Label(f, text="Tipo *:").grid(row=3, column=0, sticky="w")
        self.var_tipo = tk.StringVar(value=self.TIPOS[0]); ttk.Combobox(f, values=self.TIPOS, textvariable=self.var_tipo, state="readonly", width=38)\
            .grid(row=3, column=1, sticky="w", pady=3)

        f.grid_columnconfigure(1, weight=1)

    def _cargar_usuarios_combo(self):
        items = lista_usuarios()
        self.cbo_user["values"] = [f"{r['id']} - {r['email']}" for r in items]
        if items: self.cbo_user.current(0)

    def cargar_tabla(self, filtro: str = ""):
        for it in self.tree.get_children(): self.tree.delete(it)
        with conexion_bd() as c:
            if filtro:
                like = f"%{filtro}%"
                rows = c.execute("""SELECT ca.id, u.email AS usuario, ca.nombre, ca.tipo_categoria AS tipo
                                    FROM categorias ca JOIN usuarios u ON u.id=ca.id_usuario
                                    WHERE ca.nombre LIKE ? OR u.email LIKE ?
                                    ORDER BY ca.id DESC""", (like, like)).fetchall()
            else:
                rows = c.execute("""SELECT ca.id, u.email AS usuario, ca.nombre, ca.tipo_categoria AS tipo
                                    FROM categorias ca JOIN usuarios u ON u.id=ca.id_usuario
                                    ORDER BY ca.id DESC""").fetchall()
        for r in rows:
            self.tree.insert("", "end", values=(r["id"], r["usuario"], r["nombre"], r["tipo"]))

    def on_select(self, _evt):
        sel = self.tree.selection()
        if not sel: return
        cid = int(self.tree.item(sel[0], "values")[0])
        with conexion_bd() as c:
            r = c.execute("SELECT * FROM categorias WHERE id=?", (cid,)).fetchone()
            u = c.execute("SELECT email FROM usuarios WHERE id=?", (r["id_usuario"],)).fetchone()
        if r:
            self.selected_id = cid
            self.var_id.set(r["id"])
            self.var_user.set(f"{r['id_usuario']} - {u['email'] if u else ''}")
            self.var_nombre.set(r["nombre"])
            self.var_tipo.set(r["tipo_categoria"])

    def nuevo(self):
        self.selected_id = None
        self.var_id.set(""); self._cargar_usuarios_combo()
        self.var_nombre.set(""); self.var_tipo.set(self.TIPOS[0])

    def guardar(self):
        usuario_id = id_from_combo(self.var_user.get())
        if not usuario_id: messagebox.showwarning("Validación", "Selecciona un usuario."); return
        nombre = self.var_nombre.get().strip()
        if not nombre: messagebox.showwarning("Validación", "Nombre es obligatorio."); return
        tipo = self.var_tipo.get()
        try:
            with conexion_bd() as c:
                if self.selected_id is None:
                    c.execute("INSERT INTO categorias(id_usuario,nombre,tipo_categoria) VALUES (?,?,?)",
                              (usuario_id, nombre, tipo))
                    messagebox.showinfo("OK", "Categoría creada.")
                else:
                    c.execute("UPDATE categorias SET id_usuario=?, nombre=?, tipo_categoria=? WHERE id=?",
                              (usuario_id, nombre, tipo, self.selected_id))
                    messagebox.showinfo("OK", "Categoría actualizada.")
        except sqlite3.IntegrityError as e:
            messagebox.showerror("Error", f"No se pudo guardar: {e}")
        self.cargar_tabla(); self.nuevo()

    def eliminar(self):
        if not self.selected_id:
            messagebox.showwarning("Eliminar", "Selecciona una categoría."); return
        if not messagebox.askyesno("Confirmar", "¿Eliminar categoría?"): return
        try:
            with conexion_bd() as c:
                c.execute("DELETE FROM categorias WHERE id=?", (self.selected_id,))
            messagebox.showinfo("OK", "Categoría eliminada.")
        except sqlite3.IntegrityError as e:
            messagebox.showerror("Error", f"No se pudo eliminar: {e}")
        self.cargar_tabla(); self.nuevo()

# -------------------- Transacciones --------------------
class TransaccionesFrame(BaseCRUD):
    def configurar_columnas(self):
        cols = [
            ("id","ID",60,"e"), ("usuario","Usuario",150,"w"), ("cuenta","Cuenta",150,"w"),
            ("categoria","Categoría",160,"w"), ("monto","Monto",100,"e"), ("fecha","Fecha",100,"w"),
            ("descripcion","Descripción",220,"w")
        ]
        self.tree["columns"] = [c[0] for c in cols]
        for key, title, w, anchor in cols:
            self.tree.heading(key, text=title)
            self.tree.column(key, width=w, anchor=anchor)

    def _build_form(self):
        f = ttk.Frame(self.form); f.pack(fill="x")

        ttk.Label(f, text="ID:").grid(row=0, column=0, sticky="w")
        self.var_id = tk.StringVar()
        ttk.Entry(f, textvariable=self.var_id, width=10, state="readonly").grid(row=0, column=1, sticky="w", pady=3)

        ttk.Label(f, text="Usuario *:").grid(row=1, column=0, sticky="w")
        self.var_user = tk.StringVar()
        self.cbo_user = ttk.Combobox(f, textvariable=self.var_user, state="readonly", width=36)
        self.cbo_user.grid(row=1, column=1, sticky="w", pady=3)
        self.cbo_user.bind("<<ComboboxSelected>>", lambda e: self._recargar_dependientes())

        ttk.Label(f, text="Cuenta *:").grid(row=2, column=0, sticky="w")
        self.var_cuenta = tk.StringVar()
        self.cbo_cuenta = ttk.Combobox(f, textvariable=self.var_cuenta, state="readonly", width=36)
        self.cbo_cuenta.grid(row=2, column=1, sticky="w", pady=3)

        ttk.Label(f, text="Categoría *:").grid(row=3, column=0, sticky="w")
        self.var_categoria = tk.StringVar()
        self.cbo_categoria = ttk.Combobox(f, textvariable=self.var_categoria, state="readonly", width=36)
        self.cbo_categoria.grid(row=3, column=1, sticky="w", pady=3)

        ttk.Label(f, text="Monto *:").grid(row=4, column=0, sticky="w")
        self.var_monto = tk.StringVar()
        ttk.Entry(f, textvariable=self.var_monto, width=18).grid(row=4, column=1, sticky="w", pady=3)

        ttk.Label(f, text="Fecha (YYYY-MM-DD):").grid(row=5, column=0, sticky="w")
        self.var_fecha = tk.StringVar(value=str(datetime.date.today()))
        ttk.Entry(f, textvariable=self.var_fecha, width=18).grid(row=5, column=1, sticky="w", pady=3)

        ttk.Label(f, text="Descripción:").grid(row=6, column=0, sticky="w")
        self.var_desc = tk.StringVar()
        ttk.Entry(f, textvariable=self.var_desc, width=40).grid(row=6, column=1, sticky="w", pady=3)

        f.grid_columnconfigure(1, weight=1)

        # 👇 Cargar usuarios DESPUÉS de crear cuenta/categoría
        self._cargar_usuarios_combo(cargar_dependientes=True)

    def _cargar_usuarios_combo(self, cargar_dependientes: bool = False):
        items = lista_usuarios()
        self.cbo_user["values"] = [f"{r['id']} - {r['email']}" for r in items]
        if items:
            self.cbo_user.current(0)
        # Solo recargar dependientes si los combos YA existen y nos lo piden
        if cargar_dependientes and hasattr(self, "cbo_cuenta") and hasattr(self, "cbo_categoria"):
            self._recargar_dependientes()

    def _recargar_dependientes(self):
        # Baranda extra por si se llama antes de tiempo
        if not hasattr(self, "cbo_cuenta") or not hasattr(self, "cbo_categoria"):
            return
        uid = id_from_combo(self.var_user.get())
        if not uid:
            self.cbo_cuenta["values"] = []
            self.cbo_categoria["values"] = []
            return
        cs = lista_cuentas(uid)
        self.cbo_cuenta["values"] = [f"{r['id']} - {r['nombre']}" for r in cs]
        if cs: self.cbo_cuenta.current(0)

        cats = lista_categorias(uid)
        self.cbo_categoria["values"] = [f"{r['id']} - {r['nombre']}" for r in cats]
        if cats: self.cbo_categoria.current(0)

    def on_select(self, _evt):
        sel = self.tree.selection()
        if not sel: return
        tid = int(self.tree.item(sel[0], "values")[0])
        with conexion_bd() as c:
            r = c.execute("SELECT * FROM transacciones WHERE id=?", (tid,)).fetchone()
            u = c.execute("SELECT email FROM usuarios WHERE id=?", (r["id_usuario"],)).fetchone()
            cu = c.execute("SELECT nombre FROM cuentas WHERE id=?", (r["cuenta_id"],)).fetchone()
            ca = c.execute("SELECT nombre FROM categorias WHERE id=?", (r["categoria_id"],)).fetchone()
        if r:
            self.selected_id = tid
            self.var_id.set(r["id"])
            self.var_user.set(f"{r['id_usuario']} - {u['email'] if u else ''}")
            self._recargar_dependientes()
            self.var_cuenta.set(f"{r['cuenta_id']} - {cu['nombre'] if cu else ''}")
            self.var_categoria.set(f"{r['categoria_id']} - {ca['nombre'] if ca else ''}")
            self.var_monto.set(str(r["monto"]))
            self.var_fecha.set(r["fecha"])
            self.var_desc.set(r["descripcion"] or "")

# -------------------- App --------------------
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Gestión de gastos — Tkinter + SQLite (simple)")
        self.geometry("1120x720")
        self.minsize(980, 640)
        try: ttk.Style(self).configure("Treeview", rowheight=26)
        except Exception: pass

        nb = ttk.Notebook(self); nb.pack(fill="both", expand=True)
        nb.add(UsuariosFrame(nb), text="Usuarios")
        nb.add(CuentasFrame(nb), text="Cuentas")
        nb.add(CategoriasFrame(nb), text="Categorías")
        nb.add(TransaccionesFrame(nb), text="Transacciones")

if __name__ == "__main__":
    App().mainloop()


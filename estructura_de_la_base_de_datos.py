import sqlite3

conn = sqlite3.connect('gestiondegastos.db')
c = conn.cursor()

# Importante en SQLite:
c.execute("PRAGMA foreign_keys = ON;")

c.execute("""
CREATE TABLE IF NOT EXISTS usuarios (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  nombre TEXT NOT NULL,
  email  TEXT NOT NULL UNIQUE,
  contrasena TEXT NOT NULL
);
""")

c.execute("""
CREATE TABLE IF NOT EXISTS cuentas (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  id_usuario INTEGER NOT NULL,
  nombre TEXT NOT NULL,
  tipo_cuenta TEXT NOT NULL CHECK (tipo_cuenta IN ('ahorro','corriente','tarjeta','efectivo','otro')),
  moneda TEXT NOT NULL DEFAULT 'PYG',
  saldo_inicial NUMERIC NOT NULL DEFAULT 0,
  estado TEXT NOT NULL CHECK (estado IN ('activa','inactiva')),
  fecha_creacion DATETIME NOT NULL DEFAULT (datetime('now')),
  UNIQUE (id_usuario, nombre),
  FOREIGN KEY (id_usuario) REFERENCES usuarios(id)
);
""")

c.execute("""
CREATE TABLE IF NOT EXISTS categorias (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  id_usuario INTEGER NOT NULL,
  nombre TEXT NOT NULL,
  tipo_categoria TEXT NOT NULL CHECK (tipo_categoria IN ('ingreso','gasto')),
  UNIQUE (id_usuario, nombre),
  FOREIGN KEY (id_usuario) REFERENCES usuarios(id)
);
""")

c.execute("""
CREATE TABLE IF NOT EXISTS transacciones (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  id_usuario INTEGER NOT NULL,
  categoria_id INTEGER NOT NULL,
  cuenta_id INTEGER NOT NULL,
  monto NUMERIC NOT NULL,
  fecha TEXT NOT NULL,               -- 'YYYY-MM-DD'
  descripcion TEXT,
  creado_en DATETIME NOT NULL DEFAULT (datetime('now')),
  FOREIGN KEY (categoria_id) REFERENCES categorias(id),
  FOREIGN KEY (id_usuario) REFERENCES usuarios(id),
  FOREIGN KEY (cuenta_id) REFERENCES cuentas(id)
);
""")

c.execute("""
CREATE TABLE IF NOT EXISTS presupuestos (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  id_usuario INTEGER NOT NULL,
  categoria_id INTEGER NOT NULL,
  monto_limite NUMERIC NOT NULL,
  periodo TEXT NOT NULL CHECK (periodo IN ('mensual','anual')),
  FOREIGN KEY (categoria_id) REFERENCES categorias(id),
  FOREIGN KEY (id_usuario) REFERENCES usuarios(id)
);
""")

c.execute("""
CREATE TABLE IF NOT EXISTS logs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  id_usuario INTEGER NOT NULL,
  accion TEXT NOT NULL,
  fecha DATETIME NOT NULL DEFAULT (datetime('now')),
  FOREIGN KEY (id_usuario) REFERENCES usuarios(id)
);
""")

# Índices recomendados para rendimiento en reportes
c.execute("CREATE INDEX IF NOT EXISTS idx_tx_usuario_fecha ON transacciones(id_usuario, fecha);")
c.execute("CREATE INDEX IF NOT EXISTS idx_tx_categoria ON transacciones(categoria_id);")

conn.commit()
conn.close()


import mysql.connector
from mysql.connector import errorcode
import os
import platform
from datetime import datetime
import uuid

# Función para limpiar la pantalla
def limpiar_pantalla():
    sistema = platform.system()
    if sistema == "Windows":
        os.system("cls")
    else:
        os.system("clear")

# Función para validar el tipo de producto
def validar_tipo_producto(tipo):
    tipos_validos = {"hardware", "software"}
    tipo = tipo if tipo is not None else ""
    tipo_normalizado = tipo.strip().lower()
    return tipo_normalizado in tipos_validos

# Función para validar la fecha en formato dd/mm/aaaa
def validar_fecha(fecha):
    try:
        datetime.strptime(fecha, "%d/%m/%Y")
        return True
    except ValueError:
        return False

# Clase base Producto
class Producto:
    def __init__(self, nombre, precio, cantidad_en_stock):
        self.id = str(uuid.uuid4())  # Generar un ID único
        if not isinstance(nombre, str) or not nombre.strip():
            raise ValueError("El producto debe contener un nombre. Por favor ingresalo!!")
        if not isinstance(precio, (int, float)) or precio <= 0:
            raise ValueError("El precio debe ser un número positivo.")
        if not isinstance(cantidad_en_stock, int) or cantidad_en_stock < 0:
            raise ValueError("La cantidad en stock debe ser un entero no negativo.")
        self.nombre = nombre
        self.precio = precio
        self.cantidad_en_stock = cantidad_en_stock

    def to_dict(self):
        return {
            "id": self.id,
            "nombre": self.nombre,
            "precio": self.precio,
            "cantidad_en_stock": self.cantidad_en_stock
        }

# Clase derivada ProductoHardware
class ProductoHardware(Producto):
    def __init__(self, nombre, precio, cantidad_en_stock, garantia):
        super().__init__(nombre, precio, cantidad_en_stock)
        if not isinstance(garantia, str) or not garantia.strip():
            raise ValueError("Si el producto no tiene garantía, escriba '0'.")
        self.garantia = garantia

    def to_dict(self):
        data = super().to_dict()
        data["garantia"] = self.garantia
        data["tipo"] = "hardware"
        return data

# Clase derivada ProductoSoftware
class ProductoSoftware(Producto):
    def __init__(self, nombre, precio, cantidad_en_stock, fecha_expiracion):
        super().__init__(nombre, precio, cantidad_en_stock)
        if not isinstance(fecha_expiracion, str) or not fecha_expiracion.strip():
            raise ValueError("La fecha de expiración no debe quedar en blanco. Si no tiene fecha de expiracion use: '31/12/2999'")
        if not validar_fecha(fecha_expiracion):
            raise ValueError("La fecha de expiración debe estar en el formato dd/mm/aaaa.")
        self.fecha_expiracion = fecha_expiracion

    def to_dict(self):
        data = super().to_dict()
        data["fecha_expiracion"] = self.fecha_expiracion
        data["tipo"] = "software"
        return data

# Clase Inventario
class Inventario:
    def __init__(self, host, user, password, database, port=3306):
        try:
            self.conn = mysql.connector.connect(
                host=host,
                user=user,
                password=password,
                database=database,
                port=port
            )
            self.cursor = self.conn.cursor()
            self.crear_tabla()
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                print("Error: Nombre de usuario o contraseña incorrectos.")
            elif err.errno == errorcode.ER_BAD_DB_ERROR:
                print("Error: La base de datos no existe.")
            else:
                print(err)
            exit(1)

    def crear_tabla(self):
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS productos (
            id VARCHAR(36) PRIMARY KEY,
            nombre VARCHAR(255) NOT NULL,
            precio DECIMAL(10, 2) NOT NULL,
            cantidad_en_stock INT NOT NULL,
            garantia VARCHAR(50),
            fecha_expiracion VARCHAR(10),
            tipo VARCHAR(50) NOT NULL
        )
        """)
        self.conn.commit()

    def agregar_producto(self, producto):
        if self.obtener_producto(producto.nombre):
            print("Producto con el mismo nombre ya existe.")
            return
        query = """
        INSERT INTO productos (id, nombre, precio, cantidad_en_stock, garantia, fecha_expiracion, tipo)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        values = (
            producto.id,
            producto.nombre,
            producto.precio,
            producto.cantidad_en_stock,
            getattr(producto, 'garantia', None),
            getattr(producto, 'fecha_expiracion', None),
            'hardware' if isinstance(producto, ProductoHardware) else 'software'
        )
        self.cursor.execute(query, values)
        self.conn.commit()
        print(f"Producto {producto.nombre} agregado exitosamente.")

    def obtener_producto(self, nombre):
        query = "SELECT * FROM productos WHERE nombre = %s"
        self.cursor.execute(query, (nombre,))
        result = self.cursor.fetchone()
        if result:
            try:
                tipo = result[-1]
                if tipo == "hardware":
                    # Verifica que los valores se conviertan correctamente
                    precio = float(result[2])
                    cantidad_en_stock = int(result[3])
                    if precio <= 0:
                        raise ValueError("El precio debe ser un número positivo.")
                    return ProductoHardware(result[1], precio, cantidad_en_stock, result[4])
                elif tipo == "software":
                    # Verifica que los valores se conviertan correctamente
                    precio = float(result[2])
                    cantidad_en_stock = int(result[3])
                    if precio <= 0:
                        raise ValueError("El precio debe ser un número positivo.")
                    return ProductoSoftware(result[1], precio, cantidad_en_stock, result[5])
            except ValueError as e:
                print(f"Error al recuperar el producto: {e}")
        return None

    def actualizar_producto(self, nombre, nuevo_nombre=None, nuevo_precio=None, nueva_cantidad=None, nueva_garantia=None, nueva_fecha=None):
        producto = self.obtener_producto(nombre)
        if producto:
            if isinstance(producto, ProductoHardware):
                query = """
                UPDATE productos
                SET nombre = %s, precio = %s, cantidad_en_stock = %s, garantia = %s
                WHERE nombre = %s
                """
                values = (
                    nuevo_nombre or producto.nombre,
                    nuevo_precio or producto.precio,
                    nueva_cantidad or producto.cantidad_en_stock,
                    nueva_garantia if nueva_garantia is not None else producto.garantia,
                    nombre
                )
            elif isinstance(producto, ProductoSoftware):
                query = """
                UPDATE productos
                SET nombre = %s, precio = %s, cantidad_en_stock = %s, fecha_expiracion = %s
                WHERE nombre = %s
                """
                values = (
                    nuevo_nombre or producto.nombre,
                    nuevo_precio or producto.precio,
                    nueva_cantidad or producto.cantidad_en_stock,
                    nueva_fecha if nueva_fecha is not None else producto.fecha_expiracion,
                    nombre
                )
            
            self.cursor.execute(query, values)
            self.conn.commit()
            print(f"Producto {nombre} actualizado exitosamente.")
        else:
            print("Producto no encontrado.")
            
    def eliminar_producto(self, nombre):
        query = "DELETE FROM productos WHERE nombre = %s"
        self.cursor.execute(query, (nombre,))
        self.conn.commit()
        if self.cursor.rowcount > 0:
            print(f"Producto {nombre} eliminado exitosamente.")
        else:
            print("Producto no encontrado.")

    def listar_productos(self):
        query = "SELECT * FROM productos"
        self.cursor.execute(query)
        productos = self.cursor.fetchall()

        if not productos:
            print("No hay productos en el inventario.")
            return

        for producto in productos:
            print("\n" + "-" * 40)
            print(f"ID: {producto[0]}")
            print(f"Nombre del producto: {producto[1]}")
            print(f"Precio: ${producto[2]:.2f}")
            print(f"Cantidad en stock: {producto[3]}")
            if producto[-1] == "hardware":
                print(f"Garantía: {producto[4]} años")
            elif producto[-1] == "software":
                print(f"Fecha de expiración: {producto[5]}")
            print("-" * 40)

    def cerrar_conexion(self):
        self.cursor.close()
        self.conn.close()

# Función para mostrar el menú
def mostrar_menu():
    print("\n" + "*" * 40)
    print(" " * 10 + "--- Sistema de Gestión de Productos ---")
    print(" " * 10 + "1. Agregar producto")
    print(" " * 10 + "2. Listar productos")
    print(" " * 10 + "3. Actualizar producto")
    print(" " * 10 + "4. Eliminar producto")
    print(" " * 10 + "5. Salir")
    print("*" * 40)

# Función para obtener la opción del usuario
def obtener_opcion():
    try:
        opcion = int(input("Seleccione una opción: "))
        if 1 <= opcion <= 5:
            return opcion
        else:
            print("Opción inválida. Seleccione un número entre 1 y 5.")
            return None
    except ValueError:
        print("Error: Debe ingresar un número entre 1 y 5.")
        return None

# Función para validar el precio
def validar_precio(valor):
    try:
        precio = float(valor)
        if precio <= 0:
            raise ValueError("El precio debe ser un número positivo.")
        return precio
    except ValueError as e:
        print(f"Error: {e}")
        return None

# Función para validar la cantidad en stock
def validar_cantidad(valor):
    try:
        cantidad = int(valor)
        if cantidad < 0:
            raise ValueError("La cantidad en stock debe ser un entero no negativo.")
        return cantidad
    except ValueError as e:
        print(f"Error: {e}")
        return None

# Función principal
def main():
    inventario = Inventario(
        host="localhost",  # Cambiar por la dirección de tu servidor MySQL
        user="root",       # Cambiar por tu usuario MySQL
        password="password",       # Cambiar por tu contraseña MySQL
        database="gestiondeproductos",  # Cambiar por tu base de datos
        port=3306    # Cambia por el puerto de tu base de datos
    )

    while True:
        limpiar_pantalla()
        mostrar_menu()
        opcion = obtener_opcion()

        if opcion == 1:
            tipo_producto = input("Ingrese el tipo de producto ('hardware' o 'software'): ").lower().strip()
            while not validar_tipo_producto(tipo_producto):
                print("Tipo de producto inválido. Por favor, ingrese 'hardware' o 'software'.")
                tipo_producto = input("Ingrese el tipo de producto ('hardware' o 'software'): ").lower().strip()

            nombre = input("Ingrese el nombre del producto: ").strip()
            while not nombre:
                print("El nombre del producto no debe estar vacío.")
                nombre = input("Ingrese el nombre del producto: ").strip()

            precio = None
            while precio is None:
                precio = validar_precio(input("Ingrese el precio del producto: "))

            cantidad = None
            while cantidad is None:
                cantidad = validar_cantidad(input("Ingrese la cantidad en stock: "))

            if tipo_producto == "hardware":
                garantia = input("Ingrese la garantía del producto (en años): ").strip()
                while not garantia:
                    print("La garantía no debe estar vacía.")
                    garantia = input("Ingrese la garantía del producto (en años): ").strip()
                producto = ProductoHardware(nombre, precio, cantidad, garantia)

            elif tipo_producto == "software":
                fecha_expiracion = input("Ingrese la fecha de expiración del producto (dd/mm/aaaa): ").strip()
                while not fecha_expiracion or not validar_fecha(fecha_expiracion):
                    print("Fecha inválida. Debe estar en formato dd/mm/aaaa.")
                    fecha_expiracion = input("Ingrese la fecha de expiración del producto (dd/mm/aaaa): ").strip()
                producto = ProductoSoftware(nombre, precio, cantidad, fecha_expiracion)

            inventario.agregar_producto(producto)

        elif opcion == 2:
            inventario.listar_productos()

        elif opcion == 3:
            nombre = input("Ingrese el nombre del producto que desea actualizar: ").strip()
            producto = inventario.obtener_producto(nombre)
            if producto:
                nuevo_nombre = input(f"Nuevo nombre (presione enter para mantener '{producto.nombre}'): ").strip() or None
                nuevo_precio_str = input(f"Nuevo precio (presione enter para mantener '{producto.precio}'): ").strip()
                nuevo_precio = validar_precio(nuevo_precio_str) if nuevo_precio_str else None
                nueva_cantidad_str = input(f"Nueva cantidad (presione enter para mantener '{producto.cantidad_en_stock}'): ").strip()
                nueva_cantidad = validar_cantidad(nueva_cantidad_str) if nueva_cantidad_str else None

                if isinstance(producto, ProductoHardware):
                    nueva_garantia = input(f"Nueva garantía (presione enter para mantener '{producto.garantia}'): ").strip() or None
                    inventario.actualizar_producto(nombre, nuevo_nombre, nuevo_precio, nueva_cantidad, nueva_garantia)

                elif isinstance(producto, ProductoSoftware):
                    nueva_fecha = input(f"Nueva fecha de expiración (presione enter para mantener '{producto.fecha_expiracion}'): ").strip() or None
                    while nueva_fecha and not validar_fecha(nueva_fecha):
                        print("Fecha inválida. Debe estar en formato dd/mm/aaaa.")
                        nueva_fecha = input(f"Nueva fecha de expiración (presione enter para mantener '{producto.fecha_expiracion}'): ").strip() or None
                    inventario.actualizar_producto(nombre, nuevo_nombre, nuevo_precio, nueva_cantidad, nueva_fecha=nueva_fecha)

            else:
                print("Producto no encontrado.")

        elif opcion == 4:
            nombre = input("Ingrese el nombre del producto que desea eliminar: ").strip()
            inventario.eliminar_producto(nombre)

        elif opcion == 5:
            inventario.cerrar_conexion()
            break

        input("\nPresione enter para continuar...")


if __name__ == "__main__":
    main()

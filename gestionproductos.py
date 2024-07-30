import json
import os
import platform
import re
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

    @staticmethod
    def from_dict(data):
        producto = Producto(
            data["nombre"],
            data["precio"],
            data["cantidad_en_stock"]
        )
        producto.id = data.get("id", str(uuid.uuid4()))
        return producto

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

    @staticmethod
    def from_dict(data):
        return ProductoHardware(
            data["nombre"],
            data["precio"],
            data["cantidad_en_stock"],
            data["garantia"]
        )

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

    @staticmethod
    def from_dict(data):
        return ProductoSoftware(
            data["nombre"],
            data["precio"],
            data["cantidad_en_stock"],
            data["fecha_expiracion"]
        )

# Clase Inventario
class Inventario:
    def __init__(self, archivo):
        self.archivo = archivo
        self.productos = self.cargar_productos()

    def cargar_productos(self):
        try:
            with open(self.archivo, 'r') as f:
                data = json.load(f)
                productos = []
                for item in data:
                    if item["tipo"] == "hardware":
                        productos.append(ProductoHardware.from_dict(item))
                    elif item["tipo"] == "software":
                        productos.append(ProductoSoftware.from_dict(item))
                return productos
        except FileNotFoundError:
            print("Archivo no encontrado. Se creará uno nuevo al guardar.")
            return []
        except json.JSONDecodeError:
            print("Error al decodificar el archivo JSON.")
            return []

    def guardar_productos(self):
        try:
            with open(self.archivo, 'w') as f:
                json.dump([p.to_dict() for p in self.productos], f, indent=4)
        except IOError:
            print("Error al guardar el archivo.")

    def agregar_producto(self, producto):
        if self.obtener_producto(producto.nombre):
            print("Producto con el mismo nombre ya existe.")
            return
        self.productos.append(producto)
        self.guardar_productos()
        print(f"Producto {producto.nombre} agregado exitosamente.")

    def obtener_producto(self, nombre):
        for producto in self.productos:
            if producto.nombre == nombre:
                return producto
        return None

    def actualizar_producto(self, nombre, nuevo_nombre=None, nuevo_precio=None, nueva_cantidad=None, nueva_garantia=None, nueva_fecha=None):
        producto = self.obtener_producto(nombre)
        if producto:
            try:
                if nuevo_nombre is not None:
                    producto.nombre = nuevo_nombre
                if nuevo_precio is not None:
                    producto.precio = nuevo_precio
                if nueva_cantidad is not None:
                    producto.cantidad_en_stock = nueva_cantidad
                if isinstance(producto, ProductoHardware) and nueva_garantia is not None:
                    if not nueva_garantia.strip():
                        nueva_garantia = '0'
                    producto.garantia = nueva_garantia
                if isinstance(producto, ProductoSoftware) and nueva_fecha is not None:
                    if nueva_fecha.strip() == '':
                        nueva_fecha = producto.fecha_expiracion
                    elif validar_fecha(nueva_fecha):
                        producto.fecha_expiracion = nueva_fecha
                    else:
                        raise ValueError("La nueva fecha debe estar en el formato dd/mm/aaaa.")
                self.guardar_productos()
                print(f"Producto {nombre} actualizado exitosamente.")
            except ValueError as e:
                print(f"Error al actualizar el producto: {e}")
        else:
            print("Producto no encontrado.")

    def eliminar_producto(self, nombre):
        producto = self.obtener_producto(nombre)
        if producto:
            self.productos.remove(producto)
            self.guardar_productos()
            print(f"Producto {nombre} eliminado exitosamente.")
        else:
            print("Producto no encontrado.")

    def listar_productos(self):
        if not self.productos:
            print("No hay productos en el inventario.")
            return

        for producto in self.productos:
            print("\n" + "-" * 40)
            print(f"ID: {producto.id}")
            print(f"Nombre del producto: {producto.nombre}")
            print(f"Precio: ${producto.precio:.2f}")
            print(f"Cantidad en stock: {producto.cantidad_en_stock}")

            if isinstance(producto, ProductoHardware):
                print(f"Garantía: {producto.garantia} años")
            elif isinstance(producto, ProductoSoftware):
                print(f"Fecha de expiración: {producto.fecha_expiracion}")

            print("-" * 40)

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
        if opcion < 1 or opcion > 5:
            raise ValueError
        return opcion
    except ValueError:
        print("Por favor, ingrese un número válido entre 1 y 5.")
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
    inventario = Inventario('productos.json')  # Nombre del archivo

    while True:
        limpiar_pantalla()
        mostrar_menu()
        opcion = obtener_opcion()

        if opcion == 1:
            tipo = ""
            while not validar_tipo_producto(tipo):
                tipo = input("Tipo de producto (hardware/software): ").strip().lower()
                if not validar_tipo_producto(tipo):
                    print("Tipo de producto no válido. Por favor, ingrese 'hardware' o 'software'.")

            nombre = input("Nombre del producto: ").strip()
            precio = None
            while precio is None:
                precio = validar_precio(input("Precio: "))

            cantidad = None
            while cantidad is None:
                cantidad = validar_cantidad(input("Cantidad en stock: "))

            if tipo == "hardware":
                garantia = input("Garantía (en años, ingrese 0 si no tiene): ").strip()
                producto = ProductoHardware(nombre, precio, cantidad, garantia)
            elif tipo == "software":
                fecha_expiracion = ""
                while not validar_fecha(fecha_expiracion):
                    fecha_expiracion = input("Fecha de expiración (dd/mm/aaaa): ").strip()
                    if not validar_fecha(fecha_expiracion):
                        print("Fecha de expiración no válida. Por favor, ingrese una fecha en formato dd/mm/aaaa.")
                producto = ProductoSoftware(nombre, precio, cantidad, fecha_expiracion)

            inventario.agregar_producto(producto)

        elif opcion == 2:
            inventario.listar_productos()
            input("\nPresione Enter para continuar...")

        elif opcion == 3:
            nombre = input("Ingrese el nombre del producto a actualizar: ").strip()
            nuevo_nombre = input("Nuevo nombre (o deje en blanco para no cambiar): ").strip() or None
            nuevo_precio = validar_precio(input("Nuevo precio (o deje en blanco para no cambiar): ").strip() or None)
            nueva_cantidad = validar_cantidad(input("Nueva cantidad en stock (o deje en blanco para no cambiar): ").strip() or None)
            nueva_garantia = input("Nueva garantía (o deje en blanco para no cambiar): ").strip() or None
            nueva_fecha = input("Nueva fecha de expiración (dd/mm/aaaa, o deje en blanco para no cambiar): ").strip() or None

            inventario.actualizar_producto(nombre, nuevo_nombre, nuevo_precio, nueva_cantidad, nueva_garantia, nueva_fecha)

        elif opcion == 4:
            nombre = input("Ingrese el nombre del producto a eliminar: ").strip()
            inventario.eliminar_producto(nombre)

        elif opcion == 5:
            print("Saliendo del sistema...")
            break

        input("\nPresione Enter para continuar...")

if __name__ == "__main__":
    main()

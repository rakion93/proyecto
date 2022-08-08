from sqlalchemy.orm import relationship
import db
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text, Float
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

#Usuario hereda de UserMixin, para poder utilizar las funciones de flask_login
class Usuario(UserMixin, db.Base):

    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True)
    email = Column(String(100), unique=True)
    password = Column(String(100))
    name = Column(String(1000))
    cat = Column(Boolean)
    #El producto esta relacionado con el usuario.
    #Cada producto tiene 1 proveedor.
    #One-to-One relation
    productos = relationship('Productos', backref='owner')
    #El pedido esta relacionado con el usuario
    #Cada pedido tiene 1 usuario
    pedidos = relationship('Pedidos', backref="pedidos_realizados")
    mensaje = relationship('Mensajes', backref="emisor")
    dni = Column(String(10))
    direccion = Column(String)
    telefono = Column(Integer())


    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def __repr__(self):
        return '<User {}>'.format(self.email)


class Productos(db.Base):

    __tablename__ ="producto"

    id = Column(Integer, primary_key=True)  # primary keys are required by SQLAlchemy
    name = Column(String(100), unique=True)
    price = Column(Float)
    finalprice = Column(Float)
    iva = Column(Integer)
    #Cada producto tiene un proveedor.
    #Relacionamos las tablas con ForeignKey
    proveedor = Column(Integer, ForeignKey('usuarios.id'))
    description = Column(Text)
    url = Column(String(200))
    stock = Column(Integer)
    stockAlmacen = Column(Integer)
    #Cada pedido tiene un producto, asi, desde pedido, podemos acceder a los datos del producto
    pedidos = relationship('Pedidos', backref="pedidos_incluido")
    #Cada mensaje tiene relacion con un producto, asi, desde los mensajes podremos acceder a los atributos
    #De cada producto
    pedidosmensaje = relationship('Mensajes', backref="mensaje_incluido")

class Pedidos(db.Base):

    __tablename__ = "pedido"

    id = Column(Integer, primary_key=True)
    #Relacion con producto
    id_producto = Column(Integer, ForeignKey('producto.id'))
    #Relacion con cliente
    id_cliente = Column(Integer, ForeignKey('usuarios.id'))
    npedido = Column(Integer)
    cantidad = Column(Integer)
    confirmado = Column(Boolean)

class Mensajes(db.Base):

    __tablename__ ="mensaje"

    id = Column(Integer, primary_key=True)
    id_user = Column(Integer, ForeignKey('usuarios.id'))
    #Relacion con producto
    id_producto = Column(Integer, ForeignKey('producto.id'))
    cantidad = Column(Integer)

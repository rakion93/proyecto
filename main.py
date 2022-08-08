from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
import db
from models import Usuario, Productos, Pedidos, Mensajes
from flask_login import LoginManager, current_user, login_required, logout_user, login_user
import pygal
import time

app = Flask(__name__)
app.config['SECRET_KEY'] = '7110c8ae51a4b5af97be6534caef90e4bb9bdcb3380af008f90b23a5d1616bf319bc298105da20fe'
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.init_app(app)


@app.route('/')
def index():
    return render_template('index.html')

#--------------------------------------------LOGIN------------------------------------------------
@app.route('/login')
def login():
    return render_template('login.html')

#Login
@app.route('/login', methods=['POST'])
def login_post():
    #Recogemos datos
    email = request.form.get('email')
    password = request.form.get('password')

    # Buscamos algun usuario con el mismo email
    user = db.session.query(Usuario).filter_by(email=email).first()

    # Si el correo no esta o el pasword hasheado no es igual en la DB, mensaje de error
    if not user or not check_password_hash(user.password, password):
        flash('Los datos introducidos no son correctos. Vuelva a intentarlo.')
        # Si el usuario no existe, devolvemos a la pagina de login
        return redirect(url_for('login'))

    # Logeamos al usuario
    login_user(user)

    #Si el usuario es un proveedor
    if current_user.cat == 0 :
        #Filtramos los productos para que solo vea los suyos
        todos_los_productos = db.session.query(Productos).filter_by(proveedor=current_user.id)
        return render_template('tienda.html', user=current_user, productos=todos_los_productos, primeravez=True)
    #Si el usuario es un cliente
    else:
        #Recogemos todos los productos
        todos_los_productos = db.session.query(Productos).all()
        return render_template('tienda.html', user=current_user, productos=todos_los_productos, primeravez=True)

#--------------------------------------------SIGNUP------------------------------------------------
@app.route('/signup')
def signup():
    return render_template('signup.html')

#Registro
@app.route('/signup', methods=['POST'])
def signup_post():
    #Recogemos datos
    email = request.form.get('email')
    name = request.form.get('name')
    password = request.form.get('password')
    cat = request.form.get('categoria')
    dni = request.form.get('dni')
    direccion = request.form.get('direccion')
    phone = request.form.get('telefono')
    #Le asignamos una categoria
    if cat == "Cliente":
        categoria = True
    else:
        categoria = False
    #Si existe user, el usuario ya existe en la base de datos
    user = db.session.query(Usuario).filter_by(email=email).first()
    #Mensaje de error
    if user:
        flash('El email ya existe')
        # Cargamos signup
        return redirect(url_for('signup'))
    #Creamos un nuevo usuario
    new_user = Usuario(email=email, name=name, password=generate_password_hash(password, method='sha256'), dni = dni, direccion = direccion, telefono=phone,
                       cat=categoria)
    # Lo añadimos a la base de datos
    db.session.add(new_user)
    db.session.commit()
    return render_template('login.html')

#--------------------------------------REGISTRO PRODUCTO------------------------------------------------
@app.route('/regproducto')
def regproducto():
    return render_template('registroproducto.html', user=current_user)

#Registro producto
@app.route('/registroproducto', methods=['POST'])
def registroproducto_post():
    #Recogemos los datos
    name = request.form.get('name')
    price = request.form.get('price')
    finalprice = float(price) + float(price) * 0.1
    prov = current_user.id
    iva = request.form.get('iva')
    stockAlmacen = request.form.get('stock')
    stock = 0
    description = request.form.get('description')
    url = request.form.get('url')
    #Si no indicamos ninguna URL, rellenaremos el campo con undefined
    if len(url) == 0:
        url = "undefined"
    #Si ya existe un producto con ese nombre, lanzamos un mensaje de advertencia
    producto = db.session.query(Productos).filter_by(name=name).first()
    if producto:
        flash('El producto ya existe')
        return redirect(url_for('regproducto'))

    #Creamos el producto, lo añadimos, y cuardamos los cambios
    producto = Productos(name=name, price=price, finalprice=finalprice, proveedor=prov, iva=iva, url=url, description=description, stockAlmacen=stockAlmacen, stock = stock)
    db.session.add(producto)
    db.session.commit()
    todos_los_productos = db.session.query(Productos).filter_by(proveedor=prov)
    return render_template('tienda.html', user=current_user, productos=todos_los_productos)

#Logout y redireccion a index
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return render_template('index.html')

#Cargador del usuario
@login_manager.user_loader
def load_user(user_id):
    return db.session.query(Usuario).get(int(user_id))

#Tienda donde vemos los productos
@app.route('/tienda')
@login_required
def tienda():
    #Si el usuario es un proveedor, cargaremos solo sus productos
    if current_user.cat == 0:
        todos_los_productos = db.session.query(Productos).filter_by(proveedor=current_user.id)
        return render_template('tienda.html', user=current_user, productos=todos_los_productos, primeravez=False)
    #Sino, cargamos todos los productos
    else:
        todos_los_productos = db.session.query(Productos).all()
        return render_template('tienda.html', user=current_user, productos=todos_los_productos, primeravez=False)

#---------------------------------------ELIMINAR PRODUCTO------------------------------------------------
@app.route('/eliminar-producto/<id>')
def eliminar(id):
    #Eliminamos el producto de la DB a traves de su ID
    producto = db.session.query(Productos).filter_by(id=int(id)).delete()
    db.session.commit()
    #Volvemos a la tienda, segun si seamos proveedor o cliente
    if current_user.cat == 0:
        todos_los_productos = db.session.query(Productos).filter_by(proveedor=current_user.id)
        return render_template('tienda.html', user=current_user, productos=todos_los_productos, primeravez=False)
    # Cliente
    else:
        todos_los_productos = db.session.query(Productos).all()
        return render_template('tienda.html', user=current_user, productos=todos_los_productos, primeravez=False)

#-------------------------------------MODIFICAR PRODUCTO------------------------------------------------
@app.route("/modifyproduct/<int:id>")
def modifyproduct(id):
    producto = db.session.query(Productos).get(int(id))
    return render_template("modifyproduct.html", producto=producto)

@app.route('/modify_post/<int:id>', methods=['POST'])
def modify_post(id):
    #Buscamos el producto
    producto = db.session.query(Productos).filter_by(id=int(id))
    #Recogemos los datos
    name = request.form.get('name')
    price = request.form.get('price')
    stockAlmacen = request.form.get('stock')
    description = request.form.get('description')
    url = request.form.get('url')
    #Comprovamos cuales queremos modificar y los actualizamos
    if name != "":
        producto.update({Productos.name: name})
    if price != "":
        producto.update({Productos.price: price})
    if stockAlmacen != "":
        producto.update({Productos.stockAlmacen: stockAlmacen})
    if description != "":
        producto.update({Productos.description: description})
    if url != "":
        producto.update({Productos.url: url})
    db.session.commit()
    #Devolvemos a la pantalla principal
    todos_los_productos = db.session.query(Productos).filter_by(proveedor=current_user.id)
    return render_template('tienda.html', user=current_user, productos=todos_los_productos)

#--------------------------------------AÑADIR PRODUCTO CARRITO------------------------------------------------
@app.route("/addProduct/<int:id>", methods=['POST'])
@login_required
def addProduct(id):
    #Recogemos los datos
    cantidad = request.form.get('cantidad')
    producto = db.session.query(Productos).filter_by(id = id).first()
    #Si no hay suficiente stock, ponemos una alerta
    if int(cantidad) > producto.stock:
        flash('No hay suficiente stock. Hemos avisado a la empresa. Disculpe las molestias.')
        todos_los_productos = db.session.query(Productos).all()
        mensaje = Mensajes(id_user=current_user.id, id_producto = id, cantidad = 0)
        db.session.add(mensaje)
        db.session.commit()
        return render_template('tienda.html', user=current_user, productos=todos_los_productos, primeravez=False)
    #Sino, creamos un pedido que no este confirmado
    pedido = Pedidos(id_producto=id, id_cliente=current_user.id, cantidad=cantidad, confirmado=False)
    db.session.add(pedido)
    db.session.commit()
    #Mensaje de que ha funcionado correctamente
    flash('Producto añadido al carrito')
    todos_los_productos = db.session.query(Productos).all()
    return render_template('tienda.html', user=current_user, productos=todos_los_productos, primeravez=False)

#---------------------------ELIMINAR PRODUCTO CARRITO------------------------------------------------
@app.route("/deleteElementCarrito/<int:id>")
@login_required
def deleteElementCarrito(id):
    pedido = db.session.query(Pedidos).filter_by(id=int(id)).delete()
    db.session.commit()
    pedidos = db.session.query(Pedidos).all()
    return render_template('carrito.html', pedidos=pedidos)

@app.route("/carrito")
@login_required
def carrito():
    pedidos = db.session.query(Pedidos).all()
    return render_template('carrito.html', pedidos=pedidos)

#---------------------------------CONFIRMAR CARRITO------------------------------------------------
@app.route("/confirmarCarrito")
@login_required
def confirmarCarrito():
    #Filtramos los pedidos por id_cliente y confirmado=False
    pedidos = db.session.query(Pedidos).filter_by(id_cliente=current_user.id).filter_by(confirmado=False)
    #Por cada pedido filtrado
    for pedido in pedidos:
        #Lo confirmamos
        pedido.confirmado = True
        #Le restamos el stock
        pedido.pedidos_incluido.stock -= pedido.cantidad
    #Mensaje de que se ha realizado correctamente
    flash('Pedido realizado correctamente')
    db.session.commit()
    #MEJORA: GENERAR FACTURA CON LIBRERIA
    todos_los_productos = db.session.query(Productos).all()
    return render_template('tienda.html', user=current_user, productos=todos_los_productos, primeravez=False)

#--------------------------------PEDIR PRODUCTO A PROVEEDOR------------------------------------------------
@app.route("/askForProduct/<int:id>", methods = ['POST'])
@login_required
def askForProduct(id):
    #Recogemos la cantidad
    cantidad = request.form.get('cantidad')
    #Generamos un mensaje
    mensaje = Mensajes(id_producto = id, cantidad = cantidad, id_user= current_user.id)
    db.session.add(mensaje)
    db.session.commit()
    #Mensaje ha salido correctamente
    flash('Pedido realizado correctamente al proveedor')
    todos_los_productos = db.session.query(Productos).all()
    return render_template('tienda.html', user=current_user, productos=todos_los_productos, primeravez=False)

#-----------------------------CONFIRMAR SOLICITUD PEDIDO------------------------------------------------
@app.route("/confirmarSolicitud/<int:id>")
def confirmarSolicitud(id):
    #Buscamos el mensaje
    mensaje = db.session.query(Mensajes).filter_by(id=int(id)).first()
    #Buscamos el producto al que hace referencia
    producto = db.session.query(Productos).filter_by(id = int(mensaje.id_producto))
    #Buscamos el id del admin
    id_admin = db.session.query(Usuario).filter_by(name = "admin").first()
    id_admin = id_admin.id
    #Generamos un pedido
    pedido = Pedidos(id_producto=mensaje.id_producto, id_cliente=id_admin, cantidad=mensaje.cantidad, confirmado=True)
    db.session.add(pedido)
    #Actualizamos stock del producto
    producto.update({Productos.stockAlmacen: Productos.stockAlmacen - mensaje.cantidad})
    producto.update({Productos.stock: Productos.stock + mensaje.cantidad})
    #Eliminamos mensaje
    mensaje = db.session.query(Mensajes).filter_by(id=int(id)).delete()
    db.session.commit()
    mensajes = db.session.query(Mensajes).all()
    return render_template('mensajes.html', mensajes=mensajes)

@app.route("/mensajes")
def mensajes():
    mensajes = db.session.query(Mensajes).all()
    return render_template('mensajes.html', mensajes = mensajes)

@app.route("/deletemessage/<int:id>")
def deletemessage(id):
    db.session.query(Mensajes).filter_by(id = int(id)).delete()
    db.session.commit()
    mensajes = db.session.query(Mensajes).all()
    return render_template('mensajes.html', mensajes = mensajes)

#----------------------------- CREACION GRAFICOS ------------------------------------------------
def crearGraficosProductos():
    graf = {}
    graf2 = {}
    #Recogemos los pedidos y los productos
    pedidos = db.session.query(Pedidos).all()
    productos = db.session.query(Productos).all()
    #Creamos la clave de todos los nombres y los ponemos a 0
    for producto in productos:
        graf[producto.name] = 0
        graf2[producto.name] = 0
    for pedido in pedidos:
        #Si el pedido tiene id = id_admin, es un pedido hecho al proveedor
        if pedido.id_cliente == current_user.id:
            graf[pedido.pedidos_incluido.name] += pedido.cantidad
        #Sino, el pedido lo ha hecho un cliente
        else:
            graf2[pedido.pedidos_incluido.name] += pedido.cantidad
    #Generamos graficas
    claves = graf.keys()
    valores = graf.values()
    valores2 = graf2.values()
    chart = pygal.Bar()
    chart.add('Compras al Proveedor', valores)
    chart.add('Ventas al cliente', valores2)
    chart.x_labels = claves
    #Lo renderizamos a svg
    chart.render_to_file('static/images/bar_chart.svg')
    #Guardamos la direccion de la imagen y la retornamos
    img_url = 'static/images/bar_chart.svg?cache=' + str(time.time())
    return img_url

def crearGraficosVentasEuros():
    graf = {}
    graf2 = {}
    # Recogemos los pedidos y los productos
    pedidos = db.session.query(Pedidos).all()
    productos = db.session.query(Productos).all()
    # Creamos la clave de todos los nombres y los ponemos a 0
    for producto in productos:
        graf[producto.name] = 0
        graf2[producto.name] = 0
    for pedido in pedidos:
        #Si es un pedido al proveedor
        if pedido.id_cliente == current_user.id:
            graf[pedido.pedidos_incluido.name] += pedido.cantidad * pedido.pedidos_incluido.price
        #Si es un pedido del cliente
        else:
            graf2[pedido.pedidos_incluido.name] += pedido.cantidad * pedido.pedidos_incluido.finalprice
    #Generamos graficos
    claves = graf.keys()
    valores = graf.values()
    valores2 = graf2.values()
    chart = pygal.Bar()
    chart.add('Compras al Proveedor', valores)
    chart.add('Ventas al cliente', valores2)
    chart.x_labels = claves
    chart.render_to_file('static/images/bar_chart.svg')
    img_url = 'static/images/bar_chart.svg?cache=' + str(time.time())
    return img_url

def crearGraficosStock():
    graf = {}
    graf2 = {}
    #Recogemos los los productos
    productos = db.session.query(Productos).all()
    for producto in productos:
        #En graf guardamos su stock en tienda, en graf2 su stockAlmacen
        graf[producto.name] = producto.stock
        graf2[producto.name] = producto.stockAlmacen
    #Generamos el grafico
    claves = graf.keys()
    valores = graf.values()
    valores2 = graf2.values()
    chart = pygal.Bar()
    chart.add('Stock Tienda', valores)
    chart.add('Stock Almacen Proveedor', valores2)
    chart.x_labels = claves
    #Renderizamos a SVG
    chart.render_to_file('static/images/bar_chart.svg')
    img_url = 'static/images/bar_chart.svg?cache=' + str(time.time())
    return img_url

def crearGraficosBeneficio():
    graf = {}
    #Recogemos todos los pedidos y los productos
    pedidos = db.session.query(Pedidos).all()
    productos = db.session.query(Productos).all()
    #Creamos una clave para cada producto
    for producto in productos:
        graf[producto.name] = 0
    for pedido in pedidos:
        #Si el pedido lo realiza un cliente, calculamos su beneficio (10%)
        if pedido.id_cliente != 1:
            graf[pedido.pedidos_incluido.name] += pedido.pedidos_incluido.price * 0.1 * pedido.cantidad
    #Creamos el grafico
    claves = graf.keys()
    valores = graf.values()
    chart = pygal.Bar()
    chart.add('Beneficio por producto', valores)
    chart.x_labels = claves
    #Renderizamos a svg
    chart.render_to_file('static/images/bar_chart.svg')
    img_url = 'static/images/bar_chart.svg?cache=' + str(time.time())
    return img_url

def crearGraficosCliente():
    graf = {}
    #Recogemos todos los pedidos del cliente
    pedidos = db.session.query(Pedidos).filter_by(id_cliente=current_user.id).all()
    #Recogemos todos los productos
    productos = db.session.query(Productos).all()
    for producto in productos:
        #Ponemos cada producto a 0
        graf[producto.name] = 0
    for pedido in pedidos:
        #Sumamos al cantidad  a la clave del producto
        graf[pedido.pedidos_incluido.name] += pedido.cantidad
    #Generamos grafico
    claves = graf.keys()
    valores = graf.values()
    chart = pygal.Bar()
    chart.add('Compras', valores)
    chart.x_labels = claves
    #Renderizamos a SVG
    chart.render_to_file('static/images/bar_chart.svg')
    img_url = 'static/images/bar_chart.svg?cache=' + str(time.time())
    return img_url

def crearGraficosProveedor():
    graf = {}
    #Recogemos el ID del admin (aunque siempre sera 1)
    id_admin = db.session.query(Usuario).filter_by(name="admin").first()
    id_admin = id_admin.id
    #Filtramos los pedidos hechos por el admin
    pedidos = db.session.query(Pedidos).filter_by(id_cliente=id_admin).all()
    #Filtramos los productos del proveedor
    productos = db.session.query(Productos).filter_by(proveedor=current_user.id).all()
    for producto in productos:
        #Ponemos el valor de cada clave a 0
        graf[producto.name] = 0
    for pedido in pedidos:
        #Por cada pedido, si existe en graf
        if pedido.pedidos_incluido.name in graf:
            #Sumamos la cantidad comprada por el admin
            graf[pedido.pedidos_incluido.name] += pedido.cantidad
    #Generamos grafico
    claves = graf.keys()
    valores = graf.values()
    chart = pygal.Bar()
    chart.add('Ventas', valores)
    chart.x_labels = claves
    #Renderizamos a SVG
    chart.render_to_file('static/images/bar_chart.svg')
    img_url = 'static/images/bar_chart.svg?cache=' + str(time.time())
    return img_url

@app.route('/graficastocks')
def graficastocks():
    return render_template('perfil.html', image_url = crearGraficosStock())

@app.route('/graficasVentasUnidades')
def graficasVentasUnidades():
    return render_template('perfil.html', image_url = crearGraficosProductos())

@app.route('/graficasBeneficio')
def graficasBeneficio():
    return render_template('perfil.html', image_url = crearGraficosBeneficio())

@app.route('/graficasVentasEuros')
def graficasVentasEuros():
    return render_template('perfil.html', image_url = crearGraficosVentasEuros())

#En perfil redireccionamos para ver los graficos
@login_required
@app.route('/perfil')
def perfil():
    if current_user.id == 1:
        return render_template('perfil.html', image_url = crearGraficosProductos())
    elif current_user.cat == True:
        return render_template('perfil.html', image_url=crearGraficosCliente())
    elif current_user.cat == False:
        return render_template('perfil.html', image_url=crearGraficosProveedor())

if __name__ == '__main__':
    db.Base.metadata.create_all(db.engine)
    #Buscamos al admin en la base de datos
    admin = db.session.query(Usuario).filter_by(name = "admin").first()
    #Si no existe, lo creamos
    if not admin:
        user = Usuario(email="admin@admin.com", password=generate_password_hash("admin", method='sha256'), name="admin", dni = "-", direccion = "-", telefono = 0,
                   cat=True)
        db.session.add(user)
        db.session.commit()

    app.run(debug=True)

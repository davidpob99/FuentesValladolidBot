# coding=utf-8
import math, sqlite3, logging, os, time, uuid
from sqlite3 import Error
from Fuente import Fuente
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, RegexHandler, ConversationHandler
from telegram import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove, ParseMode, InlineKeyboardMarkup

TOKEN = os.environ['TELEGRAM_TOKEN']
db = "db/fuentes.db"
USUARIO_NOLOGID = os.environ['USUARIO_NOLOGID']
STR_DIRURL = "https://maps.googleapis.com/maps/api/streetview?size=1050x300&pitch=1&key=AIzaSyBXnWJ28-55-mDm6J8-I7Fs04TFQ7LpwGQ&location="
ACCESO = {u"public": u"Pública", u"restricted": u"Acceso limitado", u"private": u"Privada"}

INCIDENCIA_ID, INCIDENCIA_DESC = range(2)
LOCALIZACION_CERCANAS = 0
TITULO, TIPO, DIR, DESC, HORA, LOCALIZACION = range(6)

updater = Updater(TOKEN)
all_user_data = dict()

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

def error(bot, update, error):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"' % (update, error))

def concectarDB(db_file):
    """ create a database connection to the SQLite database
        specified by db_file
    :param db_file: database file
    :return: Connection object or None
    """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Error as e:
        print(e)
 
    return conn

def consultaDB(consulta):
    """
    Hace una consulta específica a la base de datos puesta como parámetro global

    Parameters
    ----------
    consulta : string
        Orden SQL de la consulta que se quiere realizar

    Returns
    -------
    string
        Datos leídos en la BD de la consulta dada
    """
    conexion = concectarDB(db)
    cur = conexion.cursor()
    cur.execute(consulta)
 
    data = cur.fetchall()
    conexion.close()
    return data

def obtenerFuenteDB(id):
    """
    Dado un identificador de la fuente, la busca en la BD y obtiene todas sus características

    Parameters
    ----------
    id : int
        Identificador de la fuente

    Returns
    -------
    Fuente
        Si el id es válido, devuelve las características de la fuente.
        Si no lo es, devuelve None

    """
    conexion = concectarDB(db)
    cur = conexion.cursor()
    cur.execute("SELECT * FROM fuentes WHERE id=" + str(id))
 
    data = cur.fetchall()
    if data == []:
        return None
    data = data[0]
    conexion.close()
    fuente = Fuente(data[0], data[1], data[2], data[3], data[4], data[5], data[6], data[7], data[8], data[9], data[10], data[11])
    return fuente

def getKeySort(item):
    """
    Sirve para seleccionar el índice al ordenar las distancias desde la ubicación del usuario a la de la fuente

    Parameters
    ----------
    item : Tuple
        Contiene los siguientes campos : 
            - id de la fuente
            - distancia entre el usuario y la fuente
            - titulo de la fuente

    Returns
    -------
    double
        Distancia entre el usuario y la fuente

    """
    return item[1]

def logId(username, id):
    """
    Escribe en una hoja de cálculo de Google:   
        - username
        - fecha
        - hora
        - id de la fuente

    Parameters
    ----------
    username : string
        Nombre de usuario del cliente
    id : int
        id de la fuente 

    Returns
    -------
    None

    """
    conexion = concectarDB(db)
    cur = conexion.cursor()
    insertarLogFuente = '''
    INSERT INTO log_fuentes (id_user, fecha, hora, id_fuente)
    VALUES (?,?,?,?)
    '''
    cur.execute(insertarLogFuente, [username, time.strftime("%d/%m/%Y"), time.strftime("%H:%M:%S"), id])
    conexion.commit()
    cur.close()

def logFuente(fuente, user_id):
    """
    Guarda una nueva fuente en la BD
    """
    conexion = concectarDB(db)
    cur = conexion.cursor()
    insertarNuevaFuente = '''
    INSERT INTO nuevas_fuentes (id, titulo, tipo, dir, dirUrl, imgsc, desc, hora, lat, long, user_id, revisado)
    VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
    '''
    cur.execute(insertarNuevaFuente, [str(fuente.id), fuente.titulo, fuente.tipo, fuente.dir, fuente.dirUrl, fuente.imgsc, fuente.desc, fuente.hora, float(fuente.lat), float(fuente.long), user_id, False])
    conexion.commit()
    cur.close()

def logIncidencia(incidencia_id, incidencia_desc, user_id):
    """
    Guarda una nueva incidencia en la BD
    """
    conexion = concectarDB(db)
    cur = conexion.cursor()
    insertarNuevaFuente = '''
    INSERT INTO incidencias (id_user, fecha, hora, id_fuente, desc)
    VALUES (?,?,?,?,?)
    '''
    cur.execute(insertarNuevaFuente, [user_id, time.strftime("%d/%m/%Y"), time.strftime("%H:%M:%S"), incidencia_id, incidencia_desc])
    conexion.commit()
    cur.close()


def handler_start_help(bot, update):
    """
    Ejecución del mensaje de bienvenida y la ayuda

    /start /help

    Parameters
    ----------
    bot
        Ver python-telegram-bot
    update
        Ver python-telegram-bot

    Returns
    -------
    None

    """
    update.message.reply_text("Soy un bot 🤖 que permite consultar las fuentes de la ciudad de Valladolid 🚰.\n\nLista de los comandos admitidos:\n/cercanas: muestra las 10 fuentes más cercanas dada una ubicación\n/id ID: consulta información acerca de una fuente en concreto\n/nueva_fuente: informa sobre la ubicación de una fuente [BETA]\n/nueva_inc: informa sobre una incidencia de una fuente [BETA]\n/todas: lista de todas las fuentes de la ciudad\n/help: imprime esta ayuda\n\nAyuda detallada: https://telegra.ph/FuentesValladolidBot-09-25")
    
def handler_cercanas(bot,update):
    """
    Pedir al usuario que envíe su ubicación con un botón en el teclado

    /cercanas

    Parameters
    ----------
    bot
        Ver python-telegram-bot
    update
        Ver python-telegram-bot

    Returns
    -------
    None

    """
    location_keyboard = KeyboardButton(text="Enviar ubicación", request_location=True)
    custom_keyboard = [[ location_keyboard]]
    reply_markup = ReplyKeyboardMarkup(custom_keyboard)
    bot.send_message(chat_id=update.message.chat_id,text="Para obtener las fuentes mas cercanas, necesito que me envíes tu ubicación",reply_markup=reply_markup)

    return LOCALIZACION_CERCANAS

def handler_location(bot, update):
    """
    Se ejecuta cuando se le manda una ubicación. Imprime una lista de las 10 fuentes más cercanas a la ubicación dada,
    en orden de cercanía. La lista se compone de id y título.

    Parameters
    ----------
    bot
        Ver python-telegram-bot
    update
        Ver python-telegram-bot

    Returns
    -------
    None

    """
    ubicacion = (update.message.location.latitude, update.message.location.longitude)
    ubicaciones = consultaDB("SELECT id, lat, long, titulo FROM fuentes")
    distancias = []
    for u in ubicaciones:
        # Calcular la distancia euclidea entre cada una de las ubicaciones y la dada
        dist = math.sqrt((u[1] - ubicacion[0]) ** 2 + (u[2] - ubicacion[1]) ** 2)
        distancias.append((u[0], dist, u[3]))
    distanciasOrd = sorted(distancias, key=getKeySort)
    strDiezCercanas = ""
    for i in range(0,9):
        strDiezCercanas = strDiezCercanas + "\n- ID *" + str(distanciasOrd[i][0]) + "*\t_" + distanciasOrd[i][2] + "_"
    bot.send_message(chat_id=update.message.chat_id, text=strDiezCercanas, parse_mode=ParseMode.MARKDOWN)
    bot.send_message(chat_id=update.message.chat_id, text=str("Para obtener más información de cada una de las fuentes, ejecuta /id ID. Por ejemplo: ``` /id " + str(distanciasOrd[0][0]) + "``` para obtener información de la primera de ellas"), parse_mode=ParseMode.MARKDOWN)
    
    return ConversationHandler.END

def handler_id(bot, update):
    """
    Dado un ID, devuelve características de la fuente (título, calle, descripción, acceso y horario) así como una fotografía
    y la ubicación en un mapa
    Si el ID no es válido, imprime un mensaje de error.

    /id ID

    Parameters
    ----------
    bot
        Ver python-telegram-bot
    update
        Ver python-telegram-bot

    Returns
    -------
    None

    """
    if update.message.text == "/id":
        bot.send_message(chat_id=update.message.chat_id, text="Por favor, especifique un ID después de /id. Por ejemplo: ``` /id 6 ```", parse_mode=ParseMode.MARKDOWN)
        return
    id = update.message.text.replace('/id ', '')
    
    fuente = obtenerFuenteDB(id)
    if fuente == None:
        bot.send_message(chat_id=update.message.chat_id, text="No existe ninguna fuente con ese id (" + id + ")")
        return
    strFuente = "*" + fuente.titulo + "*"+ u"\n_" + fuente.dir + u"_\n" + fuente.desc + u"\n" + ACCESO[fuente.tipo] + u" | " + fuente.hora  + u"\nMeses funcionamiento: " + fuente.mes
    # bot.send_message(chat_id=update.message.chat_id, text=strFuente, parse_mode=ParseMode.MARKDOWN)
    if fuente.imgsc == 2:
        bot.send_photo(chat_id=update.message.chat_id, photo=fuente.imgs, caption=strFuente, parse_mode=ParseMode.MARKDOWN)
    else:
        bot.send_photo(chat_id=update.message.chat_id, photo=fuente.dirUrl, caption=strFuente, parse_mode=ParseMode.MARKDOWN)
    bot.send_location(chat_id=update.message.chat_id, latitude=fuente.lat, longitude=fuente.long)
    if update.message.from_user.username != USUARIO_NOLOGID:
        logId(update.message.from_user.id, fuente.id)

def handler_todas(bot,update):
    """
    Ejecución del mensaje de bienvenida y la ayuda

    /todas

    Parameters
    ----------
    bot
        Ver python-telegram-bot
    update
        Ver python-telegram-bot

    Returns
    -------
    None

    """
    todasFuentes = consultaDB("SELECT id, titulo FROM fuentes")
    strTodas = ""
    for f in todasFuentes:
        strTodas = strTodas + "\n" + str(f[0]) + " " + f[1]
    bot.send_message(chat_id=update.message.chat_id, text=strTodas, parse_mode=ParseMode.MARKDOWN)

def handler_licencia(bot,update):
    """
    Imprime la licencia a la que está sujeto el código de este bot 

    /licencia

    Parameters
    ----------
    bot
        Ver python-telegram-bot
    update
        Ver python-telegram-bot

    Returns
    -------
    None

    """
    strLicencia = "Copyright (C) 2019 David Población. Todos los derechos reservados."
    bot.send_message(chat_id=update.message.chat_id, text=strLicencia)

def handler_nueva(bot, update):
    user_id = update.message.from_user.id

    # Create user dict if it doesn't exist
    if user_id not in all_user_data:
        all_user_data[user_id] = dict()

    update.message.reply_text(
        'Gracias por ayudar en el proyecto 🙂'
        'A continuación te voy a pedir datos sobre la fuente, así como la ubicación. Puedes cancelar la operación en cualquier momento con /cancel\n\n'
        'Pon un título a la fuente. Por ejemplo, si te encuentras al lado del río Esgueva, titulalá _ESGUEVA_', parse_mode=ParseMode.MARKDOWN)

    return TITULO

def nueva_titulo(bot, update):
    reply_keyboard = [['public', 'restricted', 'private']]
    
    user_id = update.message.from_user.id
    user_data = all_user_data[user_id]
    user_data["titulo"] = update.message.text

    update.message.reply_text(
        'Selecciona si la fuente es Pública (_public_), de Acceso limitado (_restricted_) o Privada (_private_)',
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True), parse_mode=ParseMode.MARKDOWN)

    return TIPO

def nueva_tipo(bot, update):
    user_id = update.message.from_user.id
    user_data = all_user_data[user_id]

    user_data["tipo"] = update.message.text

    update.message.reply_text(
        'Especifica lo máximo posible su ubicación (calle, plaza, paseo...). Por ejemplo: _Plaza Mayor, 1_', parse_mode=ParseMode.MARKDOWN)

    return DIR

def nueva_dir(bot, update):
    user_id = update.message.from_user.id
    user_data = all_user_data[user_id]
    
    user_data["dir"] = update.message.text

    update.message.reply_text(
        'Añade una descripción sobre el lugar en dónde se encuentra. Por ejemplo: _Al lado de la estatua del conde Ansúrez, la cual data de 1903 y realizada por..._', parse_mode=ParseMode.MARKDOWN)

    return DESC

def nueva_desc(bot, update):
    user_id = update.message.from_user.id
    user_data = all_user_data[user_id]
    
    user_data["desc"] = update.message.text
    update.message.reply_text(
        'Horarios a la que está abierta. Si es un sitio privado decir rango de horas, si es pública escribir _Todo el día_', parse_mode=ParseMode.MARKDOWN)
    return HORA

def nueva_hora(bot, update):
    user_id = update.message.from_user.id
    user_data = all_user_data[user_id]
    
    user_data["hora"] = update.message.text

    update.message.reply_text(
        'Mándame la ubicación dónde se encuentra. Para ello, selecciona un adjunto y ubícala')
    return LOCALIZACION

def nueva_localizacion(bot, update):
    user = update.message.from_user
    user_location = update.message.location
    user_id = update.message.from_user.id
    user_data = all_user_data[user_id]
    
    user_data["localizacion"] = (user_location.latitude, user_location.longitude)
    fuente = Fuente(uuid.uuid4(), user_data["titulo"], user_data["tipo"], user_data["dir"], STR_DIRURL + str(user_data["localizacion"][0]) + "," + str(user_data["localizacion"][1]), None, 1, user_data["desc"], None, user_data["hora"], user_data["localizacion"][0], user_data["localizacion"][1])
    update.message.reply_text(
        '¡Ya está! Muchas gracias por colaborar y se añadirá en cuanto sea posible😊')
    logFuente(fuente, user_id)
    return ConversationHandler.END

def handler_incidencia(bot, update):
    user_id = update.message.from_user.id
    
    # Create user dict if it doesn't exist
    if user_id not in all_user_data:
        all_user_data[user_id] = dict()

    update.message.reply_text(
        'Gracias por ayudar en el proyecto 🙂\nPor favor, dime el id de la fuente de la incidencia (se puede obtener con /cercanas). Puedes cancelar en cualquier momento con /cancel')
    return INCIDENCIA_ID

def incidencia_id(bot, update):
    user_id = update.message.from_user.id
    user_data = all_user_data[user_id]
    
    user_data["incidencia_id"] = update.message.text
    update.message.reply_text(
        'Describe lo máximo posible en un sólo mensaje la incidencia')

    return INCIDENCIA_DESC

def incidencia_desc(bot, update):
    user_id = update.message.from_user.id
    user_data = all_user_data[user_id]
    
    user_data["incidencia_desc"] = update.message.text
    update.message.reply_text(
        'Muchas gracias, se ha registrado la incidencia 😊')

    logIncidencia(user_data["incidencia_id"], user_data["incidencia_desc"], user_id)
    return ConversationHandler.END


def cancel(bot, update):
    
    user = update.message.from_user
    update.message.reply_text('Operación cancelada',
                              reply_markup=ReplyKeyboardRemove())

    return ConversationHandler.END

updater.dispatcher.add_handler(CommandHandler('start', handler_start_help))
updater.dispatcher.add_handler(CommandHandler('help', handler_start_help))
updater.dispatcher.add_handler(CommandHandler('todas', handler_todas))
updater.dispatcher.add_handler(CommandHandler('licencia', handler_licencia))
updater.dispatcher.add_handler(RegexHandler('^(/id [\d]+)$', handler_id))
updater.dispatcher.add_handler(RegexHandler('id', handler_id))

updater.dispatcher.add_error_handler(error)

conv_handler = ConversationHandler(
        entry_points=[CommandHandler('nueva_fuente', handler_nueva)],

        states={
            TITULO: [MessageHandler(Filters.text, nueva_titulo)],
            TIPO: [MessageHandler(Filters.regex('^(public|restricted|private)$'), nueva_tipo)],
            DIR: [MessageHandler(Filters.text, nueva_dir)],
            DESC: [MessageHandler(Filters.text, nueva_desc)],
            HORA: [MessageHandler(Filters.text, nueva_hora)],
            LOCALIZACION: [MessageHandler(Filters.location, nueva_localizacion)]
        },

        fallbacks=[CommandHandler('cancel', cancel)],

        conversation_timeout=1200 # 20 min
    )

conv_handler_incidencia = ConversationHandler(
        entry_points=[CommandHandler('nueva_inc', handler_incidencia)],

        states={
            INCIDENCIA_ID: [MessageHandler(Filters.text, incidencia_id)],
            INCIDENCIA_DESC: [MessageHandler(Filters.text, incidencia_desc)],
        },

        fallbacks=[CommandHandler('cancel', cancel)],

        conversation_timeout=1200 # 20 min
    )

conv_handler_location = ConversationHandler(
        entry_points=[CommandHandler('cercanas', handler_cercanas)],

        states={
            LOCALIZACION_CERCANAS: [MessageHandler(Filters.location, handler_location)],
        },

        fallbacks=[CommandHandler('cancel', cancel)],

        conversation_timeout=120 # 2 min
    )

updater.dispatcher.add_handler(conv_handler_incidencia)
updater.dispatcher.add_handler(conv_handler_location)
updater.dispatcher.add_handler(conv_handler)

updater.start_polling()
updater.idle()

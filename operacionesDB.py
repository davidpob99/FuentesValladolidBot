# coding=utf-8
import sqlite3, json, os
from sqlite3 import Error
from collections import namedtuple 
from Fuente import Fuente
from bs4 import BeautifulSoup
import re
import urllib

strImgFuenteBase = "https://rellena.es/wp-content/uploads/fuente/"
URL = "https://rellena.es/"
db = "db/fuentes.db"
jsonFile = "fuentes.json"

def eliminarDB(db_file):
    os.remove(db_file)

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

def ejecutarSQL(conexion, sqlTabla):
    """ create a table from the create_table_sql statement
    :param conn: Connection object
    :param create_table_sql: a CREATE TABLE statement
    :return:
    """
    try:
        c = conexion.cursor()
        c.execute(sqlTabla)
    except Error as e:
        print(e)

def importarFuentes(data):
    for f in data:
        strImg = None
        if int(f[10]) == 2:
            strImg = strImgFuenteBase + str(f[8]) + ".jpg"
        fuente = Fuente(int(f[8]), f[3], f[2], f[4], f[11], strImg, int(f[10]), f[5], f[6], f[7], float(f[0]), float(f[1]))
        fuente.anadirDB()

def obtenerDatos():
    web = urllib.urlopen(URL)
    soup = BeautifulSoup(web.read(), 'html.parser')
    data  = soup.find_all("script")[17].string
    p = re.compile('    var fuente              = (.*?);')
    m = p.search(data)
    fuentes = json.loads(m.groups()[0])
    return fuentes
 
if __name__ == '__main__':
    sqlTablaFuentes = """ CREATE TABLE fuentes (
                                        id integer PRIMARY KEY,
                                        titulo text NOT NULL,
                                        tipo text,
                                        dir text,
                                        dirUrl text,
                                        imgs text,
                                        imgsc integer,
                                        desc text,
                                        mes text,
                                        hora text,
                                        lat real,
                                        long real
                                    ); """

    sqlTablaLogFuentes = """CREATE TABLE log_fuentes (
                                        id_user integer,
                                        fecha text,
                                        hora text,
                                        id_fuente integer
                                    ); """

    sqlTablaIncidencias = """CREATE TABLE incidencias (
                                        id_user integer,
                                        fecha date,
                                        hora time,
                                        id_fuente integer,
                                        desc text
                                    ); """

    sqlTablaNuevasFuentes = """ CREATE TABLE nuevas_fuentes (
                                        id text PRIMARY KEY,
                                        titulo text,
                                        tipo text,
                                        dir text,
                                        dirUrl text,
                                        imgsc integer,
                                        desc text,
                                        hora text,
                                        lat real,
                                        long real,
                                        user_id integer,
                                        revisado boolean
                                    ); """

    eliminarFuentes = "DROP TABLE fuentes;"
    conexion = concectarDB(db)

    ejecutarSQL(conexion, eliminarFuentes)
    if conexion is not None:
        # create projects table
        ejecutarSQL(conexion, sqlTablaFuentes)
        ejecutarSQL(conexion, sqlTablaLogFuentes)
        ejecutarSQL(conexion, sqlTablaIncidencias)
        ejecutarSQL(conexion, sqlTablaNuevasFuentes)

    else:
        print("Error en la conexión con la DB")

    datos = obtenerDatos()
    importarFuentes(datos)

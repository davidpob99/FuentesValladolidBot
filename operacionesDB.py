# coding=utf-8
'''
    Fuentes Valladolid: bot de Telegram para obtener información sobre las
    fuentes de la ciudad de Valladolid.

    Copyright (C) 2019  David Población

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
'''
import sqlite3, json, os
from sqlite3 import Error
from collections import namedtuple 
from Fuente import Fuente

strImgFuenteBase = "https://rellena.es/wp-content/uploads/fuente/"
db = "db/fuentes.db"
jsonFile = "fuentes.json"

def crearDB(db_file):
    """ create a database connection to a SQLite database """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        print(sqlite3.version)
    except Error as e:
        print(e)
    finally:
        if conn:
            conn.close()

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

def crearTablaFuentes(conexion, sqlTabla):
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

def importarFuentesJSON(jsonFile):
    # os.remove(db)
    with open(jsonFile) as json_file:
        data = json.load(json_file)
        for f in data:
            strImg = None
            if int(f[10]) == 2:
                strImg = strImgFuenteBase + str(f[8]) + ".jpg"
            fuente = Fuente(int(f[8]), f[3], f[2], f[4], f[11], strImg, int(f[10]), f[5], f[6], f[7], float(f[0]), float(f[1]))
            fuente.anadirDB()
 
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

    crearDB(db)
    conexion = concectarDB(db)

    if conexion is not None:
        # create projects table
        crearTablaFuentes(conexion, sqlTablaFuentes)

    else:
        print("Error! cannot create the database connection.")

    importarFuentesJSON(jsonFile)
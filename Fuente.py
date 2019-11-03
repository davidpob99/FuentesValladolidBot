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

import sqlite3
from sqlite3 import Error

class Fuente:
    """
    Representación de una fuente de Valladolid

    Atributos
    ---------
    id : int
        Identificación única de la fuente
    titulo : string
        Nombre de la fuente
    tipo : string
        Tipo de acceso de la fuente. Puede tener los siguientes valores:
            - public: Pública
            - restricted: Acceso limitado
            - private: Privada
    dir : string
        Localización de la fuente (calle, plaza, ...)
    dirUrl : string
        URL de la foto de StreetView de la foto
    imgs : string
        URL de la foto en el servidor rellena.es. No todas las fuentes tienen esta foto.
    imgsc : int
        Número de fotos disponibles. Pueden ser:
            - 1: sólo está disponible la de StreetView
            - 2: están disponibles ambas (StreetView y rellena.es)
    desc : string
        Descripción de la foto
    mes : List<int>
        Meses en los cuales la fuente está operativa
    hora : string
        Horario de apertura o disponibilidad de la fuente
    lat : double
        Latitud de las coordenadas GPS de la fuente
    long : double
        Longitud de las coordenadas GPS de la fuente
    """
    def __init__(self, id, titulo, tipo, dir, dirUrl, imgs, imgsc, desc, mes, hora, lat, long):
        self.id = id
        self.titulo = titulo
        self.tipo = tipo
        self.dir = dir
        self.dirUrl = dirUrl
        self.imgs = imgs
        self.imgsc = imgsc
        self.desc = desc
        self.mes = mes
        self.hora = hora
        self.lat = lat
        self.long = long

    def conectarDB(self, db_file):
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

    def anadirDB(self):
        db = "db/fuentes.db"
        conexion = self.conectarDB(db)

        sql = ''' INSERT INTO fuentes VALUES(?,?,?,?,?,?,?,?,?,?,?,?) '''
        cur = conexion.cursor()
        cur.execute(sql, (self.id, self.titulo, self.tipo, self.dir, self.dirUrl, self.imgs, self.imgsc, self.desc, self.mes, self.hora, self.lat, self.long))
        conexion.commit()
        conexion.close()
        return cur.lastrowid
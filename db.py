#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by 侃豺小哥 on 2019/9/6 14:05

import mysql.connector


class MyDB(object):
    """docstring for MyDB"""

    def __init__(self, host, user, passwd, db):
        self.host = host
        self.user = user
        self.passwd = passwd
        self.db = db

        self.connect = None
        self.cursor = None

    def db_connect(self):
        """数据库连接
        """
        self.connect = mysql.connector.connect(host=self.host, user=self.user, passwd=self.passwd, database=self.db)
        return self

    def db_cursor(self):
        if self.connect is None:
            self.connect = self.db_connect()

        if not self.connect.is_connected():
            self.connect = self.db_connect()
        self.cursor = self.connect.cursor()
        return self

    def get_rows(self, sql):
        """ 查询数据库结果
        :param sql: SQL语句
        :param cursor: 数据库游标
        """

        self.cursor.execute(sql)
        return self.cursor.fetchall()

    def db_execute(self, sql):
        self.cursor.execute(sql)
        self.connect.commit()

    def db_close(self):
        """关闭数据库连接和游标
        :param connect: 数据库连接实例
        :param cursor: 数据库游标
        """
        if self.connect:
            self.connect.close()
        if self.cursor:
            self.cursor.close()
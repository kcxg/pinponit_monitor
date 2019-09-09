#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by 侃豺小哥 on 2019/9/6 14:06

import sys
import requests
import time
import datetime
import json
from influxdb import InfluxDBClient

sys.path.append('../pinpoint')
import db  # db.py

PPURL = "http://10.39.33.36:8079/"

From_Time = datetime.datetime.now() + datetime.timedelta(seconds=-60)
To_Time = datetime.datetime.now()
From_TimeStamp = int(time.mktime(From_Time.timetuple())) * 1000
To_TimeStamp = int(time.mktime(datetime.datetime.now().timetuple())) * 1000


class PinPoint(object):
    """docstring for PinPoint"""

    def __init__(self, db):
        self.db = db
        super(PinPoint, self).__init__()

    """获取pinpoint中应用"""

    def get_applications(self):
        '''return application dict
        '''
        applicationListUrl = PPURL + "/applications.pinpoint"
        res = requests.get(applicationListUrl)
        if res.status_code != 200:
            print("请求异常,请检查")
            return
        applicationLists = []
        for app in res.json():
            applicationLists.append(app)
        applicationListDict = {}
        applicationListDict["applicationList"] = applicationLists
        return applicationListDict

    def getAgentList(self, appname):
        AgentListUrl = PPURL + "/getAgentList.pinpoint"
        param = {
            'application': appname
        }
        res = requests.get(AgentListUrl, params=param)
        if res.status_code != 200:
            print("请求异常,请检查")
            return
        return len(res.json().keys()), json.dumps(list(res.json().keys()))

    def update_servermap(self, appname, from_time=From_TimeStamp,
                         to_time=To_TimeStamp, serviceType='SPRING_BOOT'):
        '''更新app上下游关系
        :param appname: 应用名称
        :param serviceType: 应用类型
        :param from_time: 起始时间
        :param to_time: 终止时间
        :
        '''
        # https://pinpoint.*****.com/getServerMapData.pinpoint?applicationName=test-app&from=1547721493000&to=1547721553000&callerRange=1&calleeRange=1&serviceTypeName=TOMCAT&_=1547720614229
        param = {
            'applicationName': appname,
            'from': from_time,
            'to': to_time,
            'callerRange': 1,
            'calleeRange': 1,
            'serviceTypeName': serviceType
        }

        # serverMapUrl = PPURL + "/getServerMapData.pinpoint"
        serverMapUrl = "{}{}".format(PPURL, "/getServerMapData.pinpoint")
        res = requests.get(serverMapUrl, params=param)
        if res.status_code != 200:
            print("请求异常,请检查")
            return
        update_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
        links = res.json()["applicationMapData"]["linkDataArray"]
        for link in links:
            ###排除test的应用
            if link['sourceInfo']['applicationName'].startswith('test'):
                continue
            # 应用名称、应用类型、下游应用名称、下游应用类型、应用节点数、下游应用节点数、总请求数、 错误请求数、慢请求数(本应用到下一个应用的数量)
            application = link['sourceInfo']['applicationName']
            serviceType = link['sourceInfo']['serviceType']
            to_application = link['targetInfo']['applicationName']
            to_serviceType = link['targetInfo']['serviceType']
            agents = len(link.get('fromAgent', ' '))
            to_agents = len(link.get('toAgent', ' '))
            totalCount = link['totalCount']
            errorCount = link['errorCount']
            slowCount = link['slowCount']

            host = '10.39.46.5'
            port = 8086
            database = 'xinzhiyun'

            json_body = [
                {
                    "measurement": "pinpoint",
                    "tags": {
                        "application": application,
                        "to_application": to_application,
                    },
                    "fields": {
                        "totalCount": int(totalCount),
                        "errorCount": int(errorCount),
                        "slowCount": int(slowCount),

                    }
                }
            ]

            client = InfluxDBClient(host, port, '', '', database)  # 初始化
            client.write_points(json_body)

            sql = """
                REPLACE into application_server_map (application, serviceType, 
                agents, to_application, to_serviceType, to_agents, totalCount, 
                errorCount,slowCount, update_time, from_time, to_time) 
                VALUES ("{}", "{}", {}, "{}", "{}", {}, {}, {}, {},"{}","{}",
                "{}")""".format(
                application, serviceType, agents, to_application,
                to_serviceType, to_agents, totalCount, errorCount,
                slowCount, update_time, From_Time, To_Time)
            self.db.db_execute(sql)

    def update_app(self):
        """更新application
        """
        appdict = self.get_applications()
        apps = appdict.get("applicationList")
        update_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
        for app in apps:
            if app['applicationName'].startswith('test'):
                continue
            agents, agentlists = self.getAgentList(app['applicationName'])
            sql = """
                REPLACE  into application_list( application_name, 
                service_type, code, agents, agentlists, update_time) 
                VALUES ("{}", "{}", {}, {}, '{}', "{}");""".format(
                app['applicationName'], app['serviceType'],
                app['code'], agents, agentlists, update_time)
            self.db.db_execute(sql)
        return True

    def update_all_servermaps(self):
        """更新所有应用数
        """
        appdict = self.get_applications()
        apps = appdict.get("applicationList")
        for app in apps:
            self.update_servermap(app['applicationName'], serviceType=app['serviceType'])
        ###删除7天前数据
        Del_Time = datetime.datetime.now() + datetime.timedelta(days=-7)

        sql = """delete from application_server_map where update_time <= "{}"
        """.format(Del_Time)
        self.db.db_execute(sql)
        return True


def connect_db():
    """ 建立SQL连接
    """
    mydb = db.MyDB(
        host="10.39.46.41",
        user="sys_admin",
        passwd="MANAGER",
        db="pinpoint"
    )
    mydb.db_connect()
    mydb.db_cursor()
    return mydb


def main():
    db = connect_db()
    pp = PinPoint(db)
    pp.update_app()
    pp.update_all_servermaps()
    db.db_close()


if __name__ == '__main__':
    main()
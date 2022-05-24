import httplib2 
import requests 
import telebot
import apiclient.discovery
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from oauth2client import service_account
import xmltodict
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import datetime
import time

#Задаем константы
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
SERVICE_ACCOUNT_FILE = r"C:\Users\Vegard\credentials.json"
sheet_id = '1QkXYPlx527GLKJLz4-uKWR4zA8yqf5dxobtBvrWrGqk'
token = "5312367779:AAGIaVZ12JwDu36FGtrXInYSrfeTkIv7NoI"
bot = telebot.TeleBot(token)

#Получем необходимые данные от пользователя
print("Введите частоту обновления в секундах: ")
sleep_time = int(input())
print("Введите имя пользователя сервера PostgreSQL: ")
username = input()
print("Введите пароль от сервера PostgreSQL: ")
password = input()

#Получаем курс доллара
for i in (xmltodict.parse(requests.get("http://www.cbr.ru/scripts/XML_daily.asp").text)['ValCurs']['Valute']):
    if i["CharCode"] == "USD":
        v = float(i["Value"].replace(',','.'))
        break

#Создаем подключение через Google API
credentials = service_account.ServiceAccountCredentials.from_json_keyfile_name(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
httpAuth = credentials.authorize(httplib2.Http()) # Авторизуемся в системе
service = apiclient.discovery.build('sheets', 'v4', http = httpAuth)

#Создаем базу данных PostgresSQl
try:
    connection = psycopg2.connect(user=username,
                                  password=password,
                                  host="127.0.0.1",
                                  port="5432")
    connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = connection.cursor()
    sql_create_database = 'create database sales_test'
    cursor.execute(sql_create_database)
except Exception as error:
    print("Ошибка при работе с PostgreSQL", error)
finally:
    if connection:
        cursor.close()
        connection.close()

#Создаем таблицу SALES
connection = psycopg2.connect(user=username,
                                  password=password,
                                  host="127.0.0.1",
                                  port="5432",
                             database="sales_test")
cursor = connection.cursor()

sql = """CREATE TABLE SALES
(
    num_of_order VARCHAR(20),
    price_dol VARCHAR(30),
    price_rub VARCHAR(50),
    date_of_delivery VARCHAR(12),
    id integer,
    PRIMARY KEY (id)
);"""
#cursor.execute(sql)
#connection.commit()


#Вечный цикл обновления
while True:
    #Получаем новые данные из Google Sheets
    data = service.spreadsheets().values().get(spreadsheetId=sheet_id, range="Лист1!A1:D999").execute()["values"][1:]
    #Добавляем новый столбец
    list(map(lambda x: x.append(str(int(x[2])*v)),data))
    #Очизаем базу данных
    cursor.execute('TRUNCATE table SALES')
    connection.commit()
    for i in data:
        x = datetime.datetime.now()
        #Вставляем новые данные
        query = ("INSERT INTO SALES (id,num_of_order,price_dol,date_of_delivery,price_rub)"
                 "VALUES (%s,%s,%s,%s,%s)")
        cursor.execute(query,(i[0],i[1],i[2],i[3],i[4]))
        connection.commit()
        #Проверка на истекший срок поставки
        if x > datetime.datetime(*list(map(int,i[3].split('.')[::-1]))):
            try:
                with open("test_number.txt",'r') as file:
                    if not i[1] in file.read().split():
                        with open('test_chat.txt','r') as file:
                            for chat_id in file.readlines():
                                bot.send_message(chat_id,f'Срок доставки заказа номер {i[1]} истёк')
                        with open("test_number.txt",'a') as file:
                            file.write(i[1] + '\n')
            except FileNotFoundError:
              pass

    print("Sleep.....")
    time.sleep(sleep_time)
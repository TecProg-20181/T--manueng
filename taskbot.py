#!/usr/bin/env python3

import json
import requests
import time
import urllib

import sqlalchemy

import db
from db import Task

def lerarq():
    arq=open('TOKEN.txt','r')
    texto=arq.read()
    texto2=texto.strip()
    arq.close()
    return texto2
    
TOKEN = lerarq()
URL = "https://api.telegram.org/bot{}/".format(TOKEN)
print(URL)

HELP = """
 /new NOME
 /todo ID
 /doing ID
 /done ID
 /delete ID
 /list
 /rename ID NOME
 /dependson ID ID...
 /duplicate ID
 /priority ID PRIORITY{low, medium, high}
 /help
"""
def getdata(msg):
    parts=msg.split()
    data="100"  
    if(validadata(parts)):
      return parts
    else:
       return data
def validadata(parts):
    if(int(parts[0])>0  and int(parts[0])<30):
      if(len(parts)>=2):
        if(int(parts[1])>0 and int(parts[1])<=12):
         if(len(parts)>=3):
           if(int(parts[2])>=2018):
              return True
    return False
       
     
def get_url(url):
    response = requests.get(url)
    content = response.content.decode("utf8")
    return content

def get_json_from_url(url):
    content = get_url(url)
    js = json.loads(content)
    return js

def get_updates(offset=None):
    url = URL + "getUpdates?timeout=100"
    if offset:
        url += "&offset={}".format(offset)
    print (url)
    js = get_json_from_url(url)
    print (js)
    return js

def send_message(text, chat_id, reply_markup=None):
    text = urllib.parse.quote_plus(text)
    url = URL + "sendMessage?text={}&chat_id={}&parse_mode=Markdown".format(text, chat_id)
    if reply_markup:
        url += "&reply_markup={}".format(reply_markup)
    get_url(url)

def get_last_update_id(updates):
    update_ids = []
    for update in updates["result"]:
        update_ids.append(int(update["update_id"]))

    return max(update_ids)

def deps_text(task, chat, preceed=''):
    text = ''

    for i in range(len(task.dependencies.split(',')[:-1])):
        line = preceed
        query = db.session.query(Task).filter_by(id=int(task.dependencies.split(',')[:-1][i]), chat=chat)
        dep = query.one()

        icon = '\U0001F195'
        if dep.status == 'DOING':
            icon = '\U000023FA'
        elif dep.status == 'DONE':
            icon = '\U00002611'

        if i + 1 == len(task.dependencies.split(',')[:-1]):
            line += '└── [[{}]] {} {}\n'.format(dep.id, icon, dep.name)
            line += deps_text(dep, chat, preceed + '    ')
        else:
            line += '├── [[{}]] {} {}\n'.format(dep.id, icon, dep.name)
            line += deps_text(dep, chat, preceed + '│   ')

        text += line

    return text
def error(msg,chat):
    task_id=0;
    if not msg.isdigit():
       send_message("You must inform the task id", chat) 
    else:
       task_id = int(msg)
    return task_id;

def lookupbankt(task_id,chat):
      query = db.session.query(Task).filter_by(id=task_id, chat=chat) 
      task = query.one()
      return task  
def lookupbank(task_id,chat):
    try:
      query = db.session.query(Task).filter_by(id=task_id, chat=chat) 
      task = query.one()
      return True  
    except sqlalchemy.orm.exc.NoResultFound:
      send_message("_404_ Task {} not found x.x".format(task_id), chat)
      return False
def isvalid(msg,chat):
    task_id=error(msg,chat)
    if(task_id>0):
      return lookupbank(task_id,chat)     
    else:
      return False    
def status(msg,chat, status, print2):
     if(isvalid(msg,chat)):
       task_id=int(msg)
       query = db.session.query(Task).filter_by(id=task_id, chat=chat)
       task=query.one()     
       task.status = status 
       db.session.commit() 
       send_message(print2.format(task.id, task.name), chat)     
def statusinform(command,msg,chat):
        numbers=msg.split()
        for number in numbers: 
          if command == '/todo':
             status(number,chat,'TODO',"*TODO* task [[{}]] {}")     
          elif command == '/doing':
             status(number,chat,'DOING',"*DOING* task [[{}]] {}")   
          elif command == '/done':
              status(number,chat,'DONE',"*DONE* task [[{}]] {}")    
def printdata(data,id,chat):
    if (id  in data.keys()):
      send_message(data[id],chat) 
# a variavel que armazena informações a serem impressas na tela, chat informa o local as informações serão impressas, data representa a data de netrega , text a palavra usada para filtrar as tasks, text2 o simbolo que sera mostrado no inicio do filtro das palavras. 
def printforstatus(a,chat,data, text,text2):
    a+=text2
    query = db.session.query(Task).filter_by(status=text, chat=chat).order_by(Task.id)
    return printafor(a,query,chat,data)    
def printafor(a,query,chat,data):
    for task in query.all():
                a += '[[{}]] {}\n'.format(task.id, task.name)
                printdata(data,task.id,chat)
    return a
def printforpriority(a,chat,data, text,text2):
    a+=text2
    query = db.session.query(Task).filter_by(priority=text, chat=chat).order_by(Task.id)
    return printafor(a,query,chat,data)                              
def list(chat,msg,data):
            a = ''
            a += '\U0001F4CB Task List\n'
            query = db.session.query(Task).filter_by(parents='', chat=chat).order_by(Task.id)
            for task in query.all():
                icon = '\U0001F195'
                if task.status == 'DOING':
                    icon = '\U000023FA'
                elif task.status == 'DONE':
                    icon = '\U00002611'

                a += '[[{}]] {} {}\n'.format(task.id, icon, task.name)
                a += deps_text(task, chat)

            send_message(a, chat)
            a = ''
            
            a += '\U0001F4DD _Status_\n'
            a= printforstatus(a,chat,data,'TODO','\n\U0001F195 *TODO*\n')
            a= printforstatus(a,chat,data,'DOING','\n\U000023FA *DOING*\n')
            a= printforstatus(a,chat,data,'DONE','\n\U00002611 *DONE*\n')
            a= printforpriority(a,chat,data,'low','\n\U00002611 *LOW*\n') 
            a=printforpriority(a,chat,data,'medium', '\n\U000023FA *MEDIUM*\n')   
            a=printforpriority(a,chat,data,'high','\n\U000023FA *HIGH*\n')
            send_message(a, chat)              
def priority(chat,msg):
            text = ''
            if msg != '':
                if len(msg.split(' ', 1)) > 1:
                    text = msg.split(' ', 1)[1]
                msg = msg.split(' ', 1)[0]

            task_id=error(msg,chat)
            if(isvalid(msg,chat)):
               task_id=int(msg)
               query = db.session.query(Task).filter_by(id=task_id, chat=chat)
               task=query.one()
            else:
               return
            if text == '':
               task.priority = ''
               send_message("_Cleared_ all priorities from task {}".format(task_id), chat)
            else:
               if text.lower() not in ['high', 'medium', 'low']:
                 send_message("The priority *must be* one of the following: high, medium, low", chat)
               else:
                 task.priority = text.lower()
                 send_message("*Task {}* priority has priority *{}*".format(task_id, text.lower()), chat)
                 db.session.commit()
def duplicate(chat,msg):  
             if(isvalid(msg,chat)):
                  task_id=int(msg)
                  query = db.session.query(Task).filter_by(id=task_id, chat=chat)
                  task=query.one()
             else:
                  return
             dtask = Task(chat=task.chat, name=task.name, status=task.status, dependencies=task.dependencies,
                 parents=task.parents, priority=task.priority, duedate=task.duedate)
             db.session.add(dtask)
             for t in task.dependencies.split(',')[:-1]:
                qy = db.session.query(Task).filter_by(id=int(t), chat=chat)
                t = qy.one()
                t.parents += '{},'.format(dtask.id)

             db.session.commit()
             send_message("New task *TODO* [[{}]] {}".format(dtask.id, dtask.name), chat)

def rename(chat,msg):
            text = ''
            if msg != '':
                if len(msg.split(' ', 1)) > 1:
                    text = msg.split(' ', 1)[1]
                msg = msg.split(' ', 1)[0]
            if(isvalid(msg,chat)):
                  task_id=int(msg)
                  query = db.session.query(Task).filter_by(id=task_id, chat=chat)
                  task=query.one()
            else:
                  return  
            if text == '':
               send_message("You want to modify task {}, but you didn't provide any new text".format(task_id), chat)
               return

            old_text = task.name
            task.name = text
            db.session.commit()
            send_message("Task {} redefined from {} to {}".format(task_id, old_text, text), chat)

def delete(chat,msg):
               if(isvalid(msg,chat)):
                  task_id=int(msg)
                  query = db.session.query(Task).filter_by(id=task_id, chat=chat)
                  task=query.one()
               else:
                  return
               for t in task.dependencies.split(',')[:-1]:
                    qy = db.session.query(Task).filter_by(id=int(t), chat=chat)
                    t = qy.one()
                    t.parents = t.parents.replace('{},'.format(task.id), '')
               db.session.delete(task)
               db.session.commit()
               send_message("Task [[{}]] deleted".format(task_id), chat)       
def handle_updates(updates):
    for update in updates["result"]:
        if 'message' in update:
            message = update['message']
        elif 'edited_message' in update:
            message = update['edited_message']
        else:
            print('Can\'t process! {}'.format(update))
            return

        command = message["text"].split(" ", 1)[0]
        msg = ''
        if len(message["text"].split(" ", 1)) > 1:
            msg = message["text"].split(" ", 1)[1].strip()

        chat = message["chat"]["id"]

        print(command, msg, chat)
        data={}
        if command == '/new':
            task = Task(chat=chat, name=msg, status='TODO', dependencies='', parents='', priority='')
            data2=getdata(msg)
            print(data2)
            data[task.id]=data2 
            db.session.add(task)
            db.session.commit()
            send_message("New task *TODO* [[{}]] {}".format(task.id, task.name), chat)

        elif command == '/rename':
            rename(chat,msg)
        elif command == '/duplicate':
            duplicate(chat,msg)
        elif command == '/delete':
              delete(chat,msg)
        elif(command=='/todo' or  command== '/doing' or command== '/done'):
            statusinform(command,msg,chat)
        elif command == '/list':
             list(chat,msg,data)
        elif command == '/dependson':
            text = ''
            if msg != '':
                if len(msg.split(' ', 1)) > 1:
                    text = msg.split(' ', 1)[1]
                msg = msg.split(' ', 1)[0]

            if(isvalid(msg,chat)):
                  task_id=int(msg)  
                  task=lookupbankt(task_id,chat)      
                  if text == '':
                     for i in task.dependencies.split(',')[:-1]:
                         i = int(i)
                         q = db.session.query(Task).filter_by(id=i, chat=chat)
                         t = q.one()
                         t.parents = t.parents.replace('{},'.format(task.id), '')

                     task.dependencies = ''
                     send_message("Dependencies removed from task {}".format(task_id), chat)
                  else:
                     for depid in text.split(' '):
                        if not depid.isdigit():
                            send_message("All dependencies ids must be numeric, and not {}".format(depid), chat)
                        else:
                            depid = int(depid)
                            query = db.session.query(Task).filter_by(id=depid, chat=chat)
                            try:
                                taskdep = query.one()
                                taskdep.parents += str(task.id) + ','
                            except sqlalchemy.orm.exc.NoResultFound:
                                send_message("_404_ Task {} not found x.x".format(depid), chat)
                                continue

                            deplist = task.dependencies.split(',')
                            if str(depid) not in deplist:
                                task.dependencies += str(depid) + ','

                  db.session.commit()
                  send_message("Task {} dependencies up to date".format(task_id), chat)
            else:
              return 
        elif command == '/priority':
           priority(chat,msg)
        elif command == '/start':
            send_message("Welcome! Here is a list of things you can do.", chat)
            send_message(HELP, chat)
        elif command == '/help':
            send_message("Here is a list of things you can do.", chat)
            send_message(HELP, chat)
        else:
            send_message("I'm sorry dave. I'm afraid I can't do that.", chat)

def main():
    last_update_id = None

    while True:
        print("Updates")
        updates = get_updates(last_update_id)

        if len(updates["result"]) > 0:
            last_update_id = get_last_update_id(updates) + 1
            handle_updates(updates)

        time.sleep(0.5)


if __name__ == '__main__':
    main()


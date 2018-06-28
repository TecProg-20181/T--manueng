#!/usr/bin/env python3

import json
import requests
import time
import urllib

import sqlalchemy

import db
from db import Task
class Funcoes():
  def __init__(self,chat,msg):
     self.chat=chat
     self.msg=msg
  def setmsg(self,msg):
   self.msg=msg
  def getdata(self):
    parts=self.msg.split() 
    if(parts!=[]):
      data=parts[0]
    else:
      data="0"
    return data 

  def send_message(self,game,text, reply_markup=None):  
    chat_id=self.chat
    text = urllib.parse.quote_plus(text)
    url = game.URL + "sendMessage?text={}&chat_id={}&parse_mode=Markdown".format(text, chat_id)
    if reply_markup:
        url += "&reply_markup={}".format(reply_markup)
    game.get_url(url)



  def deps_text(self,task, preceed=''):
    text = ''
    chat=self.chat    
    if(len(task.dependencies.split(',')[:-1])>0):
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
  def error(self,game):
    task_id=0;
    msg=self.msg
    if not msg.isdigit():
       self.send_message(game,"You must inform the task id") 
    else:
       task_id = int(msg)
    return task_id;
  def lookupbankt(self,task_id,game):
      if(self.lookupbank(task_id,game)):
           query = db.session.query(Task).filter_by(id=task_id, chat=self.chat) 
           task = query.one()
           return task
  def lookupbank(self,task_id,game):
    chat=self.chat
    try:
      query = db.session.query(Task).filter_by(id=task_id, chat=chat) 
      task = query.one()
      return True  
    except sqlalchemy.orm.exc.NoResultFound:
      self.send_message(game,"_404_ Task {} not found x.x".format(task_id))
      return False
  def isvalid(self,game):
    task_id=self.error(game)
    if(task_id>0):
      return self.lookupbank(task_id,game)     
    else:
      return False    
  def status(self,game, status, print2):
     chat=self.chat
     if(self.isvalid(game)):
       task_id=int(self.msg)
       query = db.session.query(Task).filter_by(id=task_id, chat=chat)
       task=query.one()     
       task.status = status 
       db.session.commit() 
       self.send_message(game,print2.format(task.id, task.name))     
  def statusinform(self,command,game):
        numbers=self.msg.split()
        for number in numbers: 
          if command == '/todo':
             self.status(game,'TODO',"*TODO* task [[{}]] {}")     
          elif command == '/doing':
             self.status(game,'DOING',"*DOING* task [[{}]] {}")   
          elif command == '/done':
             self.status(game,'DONE',"*DONE* task [[{}]] {}")    
  def printdata(self,data,id,game):
    if (id  in data.keys()):
      send_message(data[id],self.chat) 
# a variavel que armazena informações a serem impressas na tela, chat informa o local as informações serão impressas, data representa a data de netrega , text a palavra usada para filtrar as tasks, text2 o simbolo que sera mostrado no inicio do filtro das palavras. 
  def printforstatus(self,a,game,data, text,text2):
    a+=text2
    query = db.session.query(Task).filter_by(status=text, chat=self.chat).order_by(Task.id)
    return self.printafor(a,query,data,game)    
  def printafor(self,a,query,data,game):
    for task in query.all():
                a += '[[{}]] {}\n'.format(task.id, task.name)
                self.printdata(data,task.id,game)
    return a
  def printforpriority(self,a,game,data, text,text2):
    a+=text2
    query = db.session.query(Task).filter_by(priority=text, chat=self.chat).order_by(Task.id)
    return self.printafor(a,query,data,game)                              
  def list(self,game,data):
            chat=self.chat
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
                a += self.deps_text(task)

            self.send_message(a, chat)
            a = ''
            
            a += '\U0001F4DD _Status_\n'
            a= self.printforstatus(a,game,data,'TODO','\n\U0001F195 *TODO*\n')
            a= self.printforstatus(a,game,data,'DOING','\n\U000023FA *DOING*\n')
            a= self.printforstatus(a,game,data,'DONE','\n\U00002611 *DONE*\n')
            a= self.printforpriority(a,game,data,'low','\n\U00002611 *LOW*\n') 
            a=self.printforpriority(a,game,data,'medium', '\n\U000023FA *MEDIUM*\n')   
            a=self.printforpriority(a,game,data,'high','\n\U000023FA *HIGH*\n')
            self.send_message(game,a) 
  def separamsg(self):
       msg=self.msg   
       if len(msg.split(' ', 1)) > 1:
            text = msg.split(' ', 1)[1]
       msg = msg.split(' ', 1)[0]
       self.setmsg(msg)
       return text                 
  def priority(self,game):
            text = ''
            msg=self.msg
            if msg != '':
                text=self.separamsg()
            
            msg=self.msg
            if(self.isvalid(game)):
               task_id=int(msg)
               query = db.session.query(Task).filter_by(id=task_id, chat=self.chat)
               task=query.one()
            else:
               return
            if text == '':
               task.priority = ''
               self.send_message(game,"_Cleared_ all priorities from task {}".format(task_id))
            else:
               if text.lower() not in ['high', 'medium', 'low']:
                 self.send_message("The priority *must be* one of the following: high, medium, low", chat)
               else:
                 task.priority = text.lower()
                 self.send_message(game,"*Task {}* priority has priority *{}*".format(task_id, text.lower()))
                 db.session.commit()
  def duplicate(self,game):  
             if(self.isvalid(game)):
                  task_id=int(self.msg)
                  query = db.session.query(Task).filter_by(id=task_id, chat=self.chat)
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
             self.send_message(game,"New task *TODO* [[{}]] {}".format(dtask.id, dtask.name))
  
  def rename(self,game):
            text = ''
            msg=self.msg
            if msg != '':
                  text=self.separamsg() 
            msg=self.msg      
            if(self.isvalid(game)):
                  task_id=int(msg)
                  query = db.session.query(Task).filter_by(id=task_id, chat=self.chat)
                  task=query.one()
            else:
                  return  
            if text == '':
               send_message(game,"You want to modify task {}, but you didn't provide any new text".format(task_id))
               return

            old_text = task.name
            task.name = text
            db.session.commit()
            self.send_message(game,"Task {} redefined from {} to {}".format(task_id, old_text, text))

  def delete(self,game):
               if(self.isvalid(game)):
                  task_id=int(self.msg)
                  task=self.lookupbankt(task_id,game)
               else:
                  return
               for t in task.dependencies.split(',')[:-1]:
                    t=self.lookupbankt(int(t),game)
                    t.parents = t.parents.replace('{},'.format(task.id), '')
               db.session.delete(task)
               db.session.commit()
               self.send_message(game,"Task [[{}]] deleted".format(task_id))   
class Game():
  
  def lerarq(self):
    arq=open('TOKEN.txt','r')
    texto=arq.read()
    texto2=texto.strip()
    arq.close()
    return texto2
    
  
 

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
  def __init__(self):
      TOKEN = self.lerarq()   
      self.URL = "https://api.telegram.org/bot{}/".format(TOKEN) 
  def get_url(self,url):
    response = requests.get(url)
    content = response.content.decode("utf8")
    return content

  def get_json_from_url(self,url):
    content = self.get_url(url)
    js = json.loads(content)
    return js
  def setmsg(self,msg):
      self.msg=msg
  def get_updates(self,offset=None):
    url = self.URL + "getUpdates?timeout=100"
    if offset:
        url += "&offset={}".format(offset)
    print (url)
    js = self.get_json_from_url(url)
    print (js)
    return js
  def handle_updates(self,updates):
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
        funcao1=Funcoes(chat,msg)
        data={}
        if command == '/new':
            task = Task(chat=chat, name=msg, status='TODO', dependencies='', parents='', priority='')
            data2=funcao1.getdata()
            data[task.id]=data2 
            db.session.add(task)
            db.session.commit()
            funcao1.send_message(self,"New task *TODO* [[{}]] {}".format(task.id, task.name))

        elif command == '/rename':
            funcao1.rename(self)
        elif command == '/duplicate':
            funcao1.duplicate(self)
        elif command == '/delete':
            funcao1.delete(self)
        elif(command=='/todo' or  command== '/doing' or command== '/done'):
            funcao1.statusinform(command,self)
        elif command == '/list':
             funcao1.list(self,data)
        elif command == '/dependson':
            text = ''
            
            if msg != '':
               text=funcao1.separamsg()
            msg=funcao1.msg 
            if(funcao1.isvalid(self)):
                  task_id=int(msg)   
                  task=funcao1.lookupbankt(msg,self)
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
                            self.send_message("All dependencies ids must be numeric, and not {}".format(depid), chat)
                        else:
                            depid = int(depid)
                            query = db.session.query(Task).filter_by(id=depid, chat=chat)
                            try:
                                taskdep = query.one()
                                taskdep.parents += str(taskdep.id) + ','
                            except sqlalchemy.orm.exc.NoResultFound:
                                send_message("_404_ Task {} not found x.x".format(depid), chat)
                                continue

                            deplist = task.dependencies.split(',')
                            if str(depid) not in deplist:
                                task.dependencies += str(depid) + ','

                  db.session.commit()
                  funcao1.send_message(self,"Task {} dependencies up to date".format(task_id))
            else:
              return 
        elif command == '/priority':
            funcao1.priority(self)
        elif command == '/start':
            funcao.send_message(self,"Welcome! Here is a list of things you can do.")
            funcao.send_message(game)
        elif command == '/help':
            funcao.send_message(self,"Here is a list of things you can do.")
            funcao.send_message(HELP, self)
        else:
            funcao1.send_message(self,"I'm sorry dave. I'm afraid I can't do that." )

  def main(self):
    last_update_id = None

    while True:
        print("Updates")
        updates = self.get_updates(last_update_id)

        if len(updates["result"]) > 0:
            last_update_id = self.get_last_update_id(updates) + 1
            self.handle_updates(updates)

        time.sleep(0.5)
  def get_last_update_id(self,updates):
    update_ids = []
    for update in updates["result"]:
        update_ids.append(int(update["update_id"]))

    return max(update_ids)

    


if __name__ == '__main__':
     game1=Game()
     game1.main()


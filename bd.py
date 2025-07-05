import sqlalchemy
from sqlalchemy import create_engine, Column, String, Integer
from sqlalchemy.orm import declarative_base, sessionmaker
import socket
import time

engine = create_engine('sqlite:///bests.db')
create_tables = declarative_base()

class Table(create_tables):
    __tablename__ = 'Bests_List'
    id = Column(Integer, primary_key=1, autoincrement=True)
    name = Column(String)
    score = Column(Integer)

create_tables.metadata.create_all(bind=engine)

create_session = sessionmaker(bind=engine)

local_session = create_session()

#example = Table(id=3, name = 'Full', score = 10)

# local_session.merge(example)
# local_session.commit()

# data = local_session.query(Table).order_by(Table.score.desc()).all()
# for i in data:
#     print(i.id, i.name, i.score)

main_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
main_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
main_socket.bind(('localhost', 4365))
main_socket.setblocking(False)
main_socket.listen(5)

connected = []

while True:
    try:
        client_socket, address = main_socket.accept()
        client_socket.setblocking(False)
        connected.append(client_socket)
        data = local_session.query(Table).order_by(Table.score.desc()).all()
        if len(data) > 5:
            data = data[:5]
        bests_str = ''
        if not data:
            bests_str = 'Вы первый, кто принял участие!'
        for i in data:
            bests_str +=f'{i.name}: {i.score}\n'
        client_socket.send(bests_str.encode())
    except Exception as e:
        #print(e)
        pass
    time.sleep(0.02)
    
    for i in connected:
        try:
            data = i.recv(1024).decode()
            print(data)
            data = data.split('\n')
            example_table = Table(name=data[0], score = data[1])
            local_session.merge(example_table)
            local_session.commit()
        except Exception as e:
            pass
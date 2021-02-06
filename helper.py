def getArrDict(data):
    ret = []
    for item in data:
        ret.append(item.getBlock())
    return ret



class User:
    def __init__(self, username):
        self.name = username

    def disp(self):
        print(f'{self.name}')

    def getBlock(self):
        return self.name

class Admin:
    def __init__(self, block:dict):
        self.sharedUsers:User = []
        self.name = ''
        self.writable = False
        
        if block != None:
            self.name = '' if block.get('name') == None else block.get('name')
            self.writable = False if block.get('writable') != True else True
            for item in block.get('sharedUsers'):
                self.sharedUsers.append(User(item))

            

    def disp(self):
        print(f'_______\nAdmin - {self.name}')
        print(f'_______\nShared Users - ')

        for item in self.sharedUsers:
            item.disp()

    def getBlock(self):
        return {
            "name" : self.name,
            "writable" : self.writable,
            "sharedUsers" : getArrDict(self.sharedUsers)
        }


class Host:
    def __init__(self, block:dict):
        self.name = block.get('name')
        self.path = block.get('path')
        self.writable = block.get('writable')
        self.public = block.get('public')
        self.admin = Admin(block.get('admin'))
        self.validUsers:User = []
        for item in block.get('validUsers'):
            self.validUsers.append(User(item))

    def disp(self):
        print(f'_______\nHost Name - {self.name}')
        print(f'Path - {self.path}')
        print(f'Writable - {self.writable}')
        print(f'Public - {self.public}')
        print(f'Valid user - ')

        for item in self.validUsers:
            item.disp()

    def getBlock(self):
        return {
            "name": self.name,
            "path": self.path,
            "writable": self.writable,
            "public": self.public,
            "admin": self.admin.getBlock(),
            "validUsers": getArrDict(self.validUsers)
        }

    
    


class Server:
    def __init__(self, block:dict):
        self.id = block.get('_id')
        self.name = block.get('name')
        self.address = block.get('address')
        self.autoStart = block.get('autoStart')
        self.hosts:Host = []

        for item in block.get('hosts'):
            self.hosts.append(Host(item))


    def disp(self):
        print(f'\n\n-----\nServer Name - {self.name}')
        print(f'Address - {self.address}')
        print(f'Auto start - {self.autoStart}')
        print(f'Hosts - ')
        for item in self.hosts:
            item.disp()


    def getHost(self, hostName:str):
        for host in self.hosts:
            if host.name == hostName:
                return host
        
        return None

    def getBlock(self):
        return {
            "name": self.name,
            "id": str(self.id),
            "address": self.address,
            "autoStart": self.autoStart,
            "hosts": getArrDict(self.hosts)
        }




class Nas:
    def __init__(self, block):
        self.servers = []
        for item in block:
            self.servers.append(Server(item))


    def disp(self):
        for item in self.servers:
            item.disp()
    


    def getServer(self, serverName:str):
        for server in self.servers:
            if server.name == serverName:
                return server

    
    def getHost(self, serverName:str, hostName:str):
        server:Server = self.getServer(serverName)
        if server == None:
            return None
        else:
            return server.getHost(hostName)


    def getUsers(self, serverName:str, hostName:str):
        server:Server = self.getServer(serverName)
        if server == None:
            return None
        else:
            host:Host = server.getHost(hostName)

        if host == None:
            return None
        else:
            return host.validUsers

    def getBlock(self):
        ret = []
        for s in self.servers:
            ret.append(s.getBlock())

        return getArrDict(self.servers)

        
        


    



    



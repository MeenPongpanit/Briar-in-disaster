"""Node modules"""
import random
import matplotlib.pyplot as plt
from math import hypot, sin, cos, tan, radians, acos, atan2


class NODE:
    def __init__(self, id, posx, posy, field):
        self.id = id
        self.posx = posx
        self.posy = posy
        self.synced_nodes = {id, }
        self.met_nodes = set()
        self.is_on = True
        self.field = field
        self.is_briar_user = random.random() <= self.field.briar_use_rate
        self.assembling_node = None
        self.vision_range = 3
        self.communicate_range = 0.5
        self.has_payload = False
    
    def sync(self, target_node):
        if target_node.is_briar_user:
            sync_nodes = self.synced_nodes|target_node.synced_nodes
            self.synced_nodes = sync_nodes
            target_node.synced_nodes = sync_nodes
            target_node.has_payload = True
        else:
            self.met_nodes.add(target_node.id)
        self.assembling_node = None
        target_node.assembling_node = None
        # print(f'{self.id} sync! {target_node.id} {target_node.has_payload}')
        # print([node for node in target_node.synced_nodes])

    def is_connecting2inet(self):
        for bs in self.field.inetbs_dict.values():
            if distance(self, bs) <= bs.coverage_range:
                # print(bs.coverage_range, distance(self, bs))
                return True
        return False

    def is_in_danger(self):
        return distance(self.field.middle_of_earthquake, self) <= self.field.earthquake_rad

    def lookout(self):
        found_node = []
        for node in self.field.nodes_dict.values():
            if distance(node, self) <= self.vision_range and node.assembling_node == None and node.id not in self.synced_nodes:
                # print(node.assembling_node)
                if not node.id in self.met_nodes:
                    found_node.append(node)
        if found_node:
            self.assembling_node = min(found_node, key=lambda node: distance(node, self))
            # print(f'{self.id} assemble {self.assembling_node.id}')
            node.assembling_node = self
        
    def try2connect_inet(self):
        if self.is_connecting2inet() and self.field.payload_arrive == None:
            # print(self.id, self.posx, self.posy)
            self.field.payload_arrive = self.id

    def walk(self, time_pass):
        walk_distance = 4*time_pass/3600
        if self.is_in_danger():
            walk_distance *= 1 - 0.35
        if self.assembling_node == None:
            direction = radians(random.uniform(0, 360))
            self.posx += cos(direction)*walk_distance
            self.posy += sin(direction)*walk_distance
            self.posx = max(0, min(self.field.width, self.posx))
            self.posy = max(0, min(self.field.height, self.posy))
            if self.has_payload:
                self.lookout()

        else:
            if distance(self, self.assembling_node) <= self.communicate_range:
                self.sync(self.assembling_node)
                return
            direction = atan2(self.assembling_node.posy - self.posy, self.assembling_node.posx-self.posx)
            self.posx += cos(direction)*walk_distance
            self.posy += sin(direction)*walk_distance
        if self.has_payload:
            self.try2connect_inet()
        
  
    # def __str__(self):
    #     return f'Node ID:{self.id} at ({self.posx}, {self.posy}).\n' +\
    #         f'\tSync with {[node.id for node in self.synced_nodes]}'

class INET_BS(NODE):
    def __init__(self, id, posx, posy, field, coverage_range=8.5):
        NODE.__init__(self, id, posx, posy, field)
        self.coverage_range = coverage_range
        self.is_available = True
    
    def broke(self):
        self.is_available = False

class FIELD:
    def __init__(self, height, width, node_density, internet_density, plot, briar_use_rate):
        self.height = height
        self.width = width
        self.node_amount = int(node_density*height*width)
        self.inetbs_amount = int(internet_density*height*width)
        self.briar_use_rate = briar_use_rate
        self.nodes_dict = {id: NODE(id, random.uniform(0, width), random.uniform(0, height), self) for id in range(self.node_amount)}
        self.inetbs_dict = {id: INET_BS(id, random.uniform(0, width), random.uniform(0, height), self) for id in range(self.inetbs_amount)}
        if plot:
            self.figure, self.ax = plt.subplots()
        self.payload_arrive = None
        self.broken_bs_dict = dict()

    def earthquake(self, richter):
        occur_x = random.uniform(0, self.width)
        occur_y = random.uniform(0, self.height)
        self.middle_of_earthquake = NODE(None, occur_x, occur_y, self)
        radius = {3:24, 4:48, 5:112, 6:220, 7:400, 8:720}[richter]
        self.earthquake_rad = radius
        broken_bs = []
        for bs in self.inetbs_dict.values():
            if distance(bs, self.middle_of_earthquake) <= radius:
                broken_bs.append(bs.id)
                bs.broke()
        # print(broken_bs)
        for id in broken_bs:
            self.broken_bs_dict[id] = self.inetbs_dict.pop(id)
        # print([bs.id for bs in self.inetbs_dict.values()])
        

    def create_message(self, node_id=None):
        if node_id == None:
            nodes_in_danger = [node for node in self.nodes_dict.values() if node.is_in_danger()]
            node_id = nodes_in_danger[random.randint(0, len(nodes_in_danger) - 1)].id
        self.nodes_dict[node_id].has_payload = True

    def progress_time(self, time):
        for node in self.nodes_dict.values():
            node.walk(time)

    def show(self, name=''):
        
        plt.xlim(self.width)
        plt.ylim(self.height)
        plt.scatter([node.posx for node in self.nodes_dict.values()], [node.posy for node in self.nodes_dict.values()], color='blue', marker='.')
        plt.scatter([node.posx for node in self.inetbs_dict.values() if node.is_available], [node.posy for node in self.inetbs_dict.values() if node.is_available], color='yellow', marker='.')
        plt.scatter([node.posx for node in self.broken_bs_dict.values() if not node.is_available], [node.posy for node in self.broken_bs_dict.values() if not node.is_available], color='red', marker='.')
        # plt.scatter([node.posx for node in self.nodes_dict.values() if node.assembling_node != None], [node.posy for node in self.nodes_dict.values() if node.assembling_node != None], color='green')
        plt.scatter([node.posx for node in self.nodes_dict.values() if node.has_payload], [node.posy for node in self.nodes_dict.values() if node.has_payload], color='green', marker='.')
        sec = int(name.strip('.png'))

        plt.title(f'Time: {sec//3600} hour(s) {sec%3600//60} minute(s) {sec%60} second(s)')
        plt.scatter(self.middle_of_earthquake.posx, self.middle_of_earthquake.posy, color='black')
        self.ax.add_patch(plt.Circle([self.middle_of_earthquake.posx, self.middle_of_earthquake.posy], self.earthquake_rad, color=(1,0,0, 0.3)))
        # plt.show()
        plt.savefig(name)
        plt.clf()


def distance(node_a, node_b):
    return hypot(node_a.posx-node_b.posx, node_a.posy-node_b.posy)



def simulate(earthquake):
    field =FIELD(FIELD_HEIGHT, FIELD_WIDTH, NODE_DENSITY, TELECOM_BS_DENSITY, PLOT_GRAPH, BRIAR_USE_RATE)
    field.earthquake(earthquake)
    # f.show('00.png')
    time = 0
    SAMPLING_RATE = 300
    field.create_message()
    # field.show('0.png')
    while True:
        field.progress_time(SAMPLING_RATE)
        if PLOT_GRAPH:
            if time%1800 == 0:
                field.show(f'{time}.png')
        # print(time, sum(node.has_payload for node in f.nodes_dict.values()))
        # print(*[node.id for node in f.nodes_dict[0].synced_nodes])
        time += SAMPLING_RATE
        if field.payload_arrive != None or time > 3600*24*30:
            # print(f.payload_arrive)
            # plt.scatter(f.nodes_dict[f.payload_arrive].posx, f.nodes_dict[f.payload_arrive].posx, color='orange')
            break
    # print('Success  !')
    del field
    return time

FIELD_HEIGHT = 100      #km
FIELD_WIDTH = 100       #km
NODE_DENSITY = 1.276    #node per km^2
TELECOM_BS_DENSITY = 0.01  #Basestation per km^2
SAMPLING_RATE = 300     #second
EARTHQUAKE = 3          #RICHTER (integers in range 3 - 8)
PLOT_GRAPH = True      #for testing
SIM_AMOUNT = 1000       #time
BRIAR_USE_RATE = 0.5    #0-1

simulate(EARTHQUAKE)

# for sim in range(5000):
#     result = simulate(EARTHQUAKE)
#     with open(f'result_for_{EARTHQUAKE}_richter.txt', 'a') as result_file:
#         result_file.writelines(str(result)+'\n')
#     print(f'sim {"%3d"%sim}: {"%2d"%(result//3600//24)} d {"%3d"%(result%(3600*24)//3600)} h {"%2d"%(result%3600//60)} m')
    



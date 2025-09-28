from flask import Flask, render_template, request, jsonify
import math
import random

app = Flask(__name__)

class Agent:
    def __init__(self, x=20, y=15):
        self.x = x
        self.y = y
        self.energy = 100
        self.has_key = False
    
    def to_dict(self):
        return {
            'x': self.x,
            'y': self.y,
            'energy': self.energy,
            'has_key': self.has_key
        }
    
    @classmethod
    def from_dict(cls, data):
        agent = cls()
        agent.x = data['x']
        agent.y = data['y']
        agent.energy = data['energy']
        agent.has_key = data['has_key']
        return agent

class WorldObject:
    def __init__(self, x, y, obj_type):
        self.x = x
        self.y = y
        self.type = obj_type
    
    def to_dict(self):
        return {
            'x': self.x,
            'y': self.y,
            'type': self.type
        }
    
    @classmethod
    def from_dict(cls, data):
        return cls(data['x'], data['y'], data['type'])

class WorldState:
    def __init__(self):
        self.agent = Agent()
        self.world_objects = []
    
    def to_dict(self):
        return {
            'agent': self.agent.to_dict(),
            'world_objects': [obj.to_dict() for obj in self.world_objects]
        }
    
    @classmethod
    def from_dict(cls, data):
        state = cls()
        state.agent = Agent.from_dict(data['agent'])
        state.world_objects = [WorldObject.from_dict(obj) for obj in data['world_objects']]
        return state

def distance(x1, y1, x2, y2):
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

def is_adjacent(agent, obj):
    return abs(agent.x - obj.x) <= 1 and abs(agent.y - obj.y) <= 1

def move_towards(agent, target_x, target_y):
    """Move agent one step towards target coordinates"""
    if agent.x < target_x:
        agent.x += 1
    elif agent.x > target_x:
        agent.x -= 1
    elif agent.y < target_y:
        agent.y += 1
    elif agent.y > target_y:
        agent.y -= 1
    
    # Keep agent within bounds (assuming 40x30 grid)
    agent.x = max(0, min(39, agent.x))
    agent.y = max(0, min(29, agent.y))

def find_object_by_type(world_objects, obj_type):
    """Find the first object of a given type"""
    for obj in world_objects:
        if obj.type == obj_type:
            return obj
    return None

def update_world(world_state):
    """Update world state based on rule-based logic and return log message"""
    agent = world_state.agent
    objects = world_state.world_objects
    log_message = ""
    
    # Decrease energy slightly each turn
    agent.energy = max(0, agent.energy - 1)
    
    # Find important objects
    charger = find_object_by_type(objects, 'charger')
    key = find_object_by_type(objects, 'key')
    door = find_object_by_type(objects, 'door')
    
    # Rule 1: Emergency Charging
    if agent.energy < 25 and charger:
        if is_adjacent(agent, charger):
            agent.energy = min(100, agent.energy + 10)
            log_message = "Charging... (Energy: {})".format(agent.energy)
        else:
            move_towards(agent, charger.x, charger.y)
            log_message = "Energy critical (<25). Seeking charging station."
    
    # Rule 2: Unlock Door
    elif agent.has_key and door and is_adjacent(agent, door):
        world_state.world_objects = [obj for obj in objects if obj.type != 'door']
        log_message = "Key presented. Unlocking door."
    
    # Rule 3: Go to Door with Key
    elif agent.has_key and door:
        move_towards(agent, door.x, door.y)
        log_message = "Key acquired. Moving towards door."
    
    # Rule 4: Pickup Key
    elif not agent.has_key and key and is_adjacent(agent, key):
        agent.has_key = True
        world_state.world_objects = [obj for obj in objects if obj.type != 'key']
        log_message = "Arrived at key. Picking it up."
    
    # Rule 5: Seek Key
    elif not agent.has_key and key:
        move_towards(agent, key.x, key.y)
        log_message = "No key. Seeking key."
    
    # Rule 6: Charge if Idle
    elif agent.energy < 80 and charger:
        if is_adjacent(agent, charger):
            agent.energy = min(100, agent.energy + 5)
            log_message = "Charging at station... (Energy: {})".format(agent.energy)
        else:
            move_towards(agent, charger.x, charger.y)
            log_message = "Idle and energy is not full. Moving to charger."
    
    # Rule 7: Wander
    else:
        # Random movement
        direction = random.choice(['up', 'down', 'left', 'right'])
        if direction == 'up':
            agent.y = max(0, agent.y - 1)
        elif direction == 'down':
            agent.y = min(29, agent.y + 1)
        elif direction == 'left':
            agent.x = max(0, agent.x - 1)
        elif direction == 'right':
            agent.x = min(39, agent.x + 1)
        log_message = "All tasks complete. Wandering aimlessly."
    
    return log_message

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/update', methods=['POST'])
def update():
    data = request.get_json()
    world_state = WorldState.from_dict(data)
    
    log_message = update_world(world_state)
    
    return jsonify({
        'world_state': world_state.to_dict(),
        'log_message': log_message
    })

if __name__ == '__main__':
    app.run(debug=True)
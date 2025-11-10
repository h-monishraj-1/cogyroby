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
        self.perception_radius = 5
        # New exploration attributes
        self.exploration_target = {'x': 39, 'y': 0}
        self.moving_direction = 'right'
        self.vertical_sweep_direction = 'down'
    
    def to_dict(self):
        return {
            'x': self.x,
            'y': self.y,
            'energy': self.energy,
            'has_key': self.has_key,
            'perception_radius': self.perception_radius,
            'exploration_target': self.exploration_target,
            'moving_direction': self.moving_direction,
            'vertical_sweep_direction': self.vertical_sweep_direction
        }
    
    @classmethod
    def from_dict(cls, data):
        agent = cls()
        agent.x = data['x']
        agent.y = data['y']
        agent.energy = data['energy']
        agent.has_key = data['has_key']
        agent.perception_radius = data.get('perception_radius', 5)
        agent.exploration_target = data.get('exploration_target', {'x': 39, 'y': 0})
        agent.moving_direction = data.get('moving_direction', 'right')
        agent.vertical_sweep_direction = data.get('vertical_sweep_direction', 'down')
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
    
    # PERCEPTION: Filter objects to only those within perception radius
    visible_objects = []
    for obj in objects:
        # Calculate Manhattan distance
        distance = abs(obj.x - agent.x) + abs(obj.y - agent.y)
        if distance <= agent.perception_radius:
            visible_objects.append(obj)
    
    # Find important objects from VISIBLE objects only
    charger = find_object_by_type(visible_objects, 'charger')
    key = find_object_by_type(visible_objects, 'key')
    door = find_object_by_type(visible_objects, 'door')
    
    # Log visible objects for debugging
    visible_types = [obj.type for obj in visible_objects]
    if visible_types:
        visibility_info = f" [Visible: {', '.join(visible_types)}]"
    else:
        visibility_info = " [No objects in sight]"
    
    # Rule 1: Emergency Charging
    if agent.energy < 25 and charger:
        if is_adjacent(agent, charger):
            agent.energy = min(100, agent.energy + 10)
            log_message = "Charging... (Energy: {})".format(agent.energy)
        else:
            move_towards(agent, charger.x, charger.y)
            log_message = "Energy critical (<25). Seeking charging station." + visibility_info
    
    # Rule 2: Unlock Door
    elif agent.has_key and door and is_adjacent(agent, door):
        world_state.world_objects = [obj for obj in objects if obj.type != 'door']
        log_message = "Key presented. Unlocking door."
    
    # Rule 3: Go to Door with Key
    elif agent.has_key and door:
        move_towards(agent, door.x, door.y)
        log_message = "Key acquired. Moving towards visible door." + visibility_info
    
    # Rule 4: Pickup Key
    elif not agent.has_key and key and is_adjacent(agent, key):
        agent.has_key = True
        world_state.world_objects = [obj for obj in objects if obj.type != 'key']
        log_message = "Arrived at key. Picking it up."
    
    # Rule 5: Seek Key
    elif not agent.has_key and key:
        move_towards(agent, key.x, key.y)
        log_message = "No key. Seeking visible key." + visibility_info
    
    # Rule 6: Charge if Idle
    elif agent.energy < 25 and charger:
        if is_adjacent(agent, charger):
            agent.energy = min(100, agent.energy + 5)
            log_message = "Charging at station... (Energy: {})".format(agent.energy)
        else:
            move_towards(agent, charger.x, charger.y)
            log_message = "Idle and energy is not full. Moving to visible charger." + visibility_info
    
    # Rule 7: Systematic Exploration (replacing random wander)
    else:
        log_message = "No immediate tasks. Systematically exploring environment." + visibility_info
        
        # Check if agent has reached the current exploration target
        if agent.x == agent.exploration_target['x'] and agent.y == agent.exploration_target['y']:
            # Agent has reached target, calculate next target
            
            if agent.vertical_sweep_direction == 'down':
                # Check if moving further down would go off the map
                if agent.y + 5 >= 30:
                    # Reached the bottom, reverse vertical sweep
                    agent.vertical_sweep_direction = 'up'
                    # Don't change y, just reverse horizontal direction
                else:
                    # Continue downward
                    agent.exploration_target['y'] += 5
            else:  # vertical_sweep_direction == 'up'
                # Check if moving further up would go off the map
                if agent.y - 5 < 0:
                    # Reached the top, reverse vertical sweep
                    agent.vertical_sweep_direction = 'down'
                    # Don't change y, just reverse horizontal direction
                else:
                    # Continue upward
                    agent.exploration_target['y'] -= 5
            
            # After determining the next vertical level, flip horizontal direction and target
            if agent.moving_direction == 'right':
                agent.exploration_target['x'] = 0
                agent.moving_direction = 'left'
            else:  # moving_direction == 'left'
                agent.exploration_target['x'] = 39
                agent.moving_direction = 'right'
        else:
            # Haven't reached target yet, move one step towards it
            move_towards(agent, agent.exploration_target['x'], agent.exploration_target['y'])
    
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
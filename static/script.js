// Canvas and context setup
const canvas = document.getElementById('world-canvas');
const ctx = canvas.getContext('2d');
const reasoningPanel = document.getElementById('reasoning-panel');

// World configuration
const GRID_WIDTH = 40;
const GRID_HEIGHT = 30;
const CELL_SIZE = 20;

// Set canvas size
canvas.width = GRID_WIDTH * CELL_SIZE;
canvas.height = GRID_HEIGHT * CELL_SIZE;

// World state
let worldState = {
    agent: {
        x: 20,
        y: 15,
        energy: 100,
        has_key: false
    },
    world_objects: []
};

// Interaction state
let placingObjectType = null;

// Colors for different objects
const COLORS = {
    agent: '#4A90E2',
    key: '#FFD700',
    door: '#8B4513',
    charger: '#00FF00',
    obstacle: '#666666',
    grid: '#DDDDDD'
};

// Drawing functions
function drawGrid() {
    ctx.strokeStyle = COLORS.grid;
    ctx.lineWidth = 0.5;
    
    // Draw vertical lines
    for (let x = 0; x <= GRID_WIDTH; x++) {
        ctx.beginPath();
        ctx.moveTo(x * CELL_SIZE, 0);
        ctx.lineTo(x * CELL_SIZE, canvas.height);
        ctx.stroke();
    }
    
    // Draw horizontal lines
    for (let y = 0; y <= GRID_HEIGHT; y++) {
        ctx.beginPath();
        ctx.moveTo(0, y * CELL_SIZE);
        ctx.lineTo(canvas.width, y * CELL_SIZE);
        ctx.stroke();
    }
}

function drawAgent(agent) {
    const x = agent.x * CELL_SIZE + CELL_SIZE / 2;
    const y = agent.y * CELL_SIZE + CELL_SIZE / 2;
    
    // Draw agent as a circle
    ctx.fillStyle = COLORS.agent;
    ctx.beginPath();
    ctx.arc(x, y, CELL_SIZE * 0.4, 0, Math.PI * 2);
    ctx.fill();
    
    // Draw energy bar above agent
    const barWidth = CELL_SIZE * 0.8;
    const barHeight = 4;
    const barX = x - barWidth / 2;
    const barY = y - CELL_SIZE * 0.6;
    
    // Background
    ctx.fillStyle = '#FF0000';
    ctx.fillRect(barX, barY, barWidth, barHeight);
    
    // Energy level
    const energyColor = agent.energy > 50 ? '#00FF00' : agent.energy > 25 ? '#FFFF00' : '#FF0000';
    ctx.fillStyle = energyColor;
    ctx.fillRect(barX, barY, barWidth * (agent.energy / 100), barHeight);
    
    // Draw key indicator if agent has key
    if (agent.has_key) {
        ctx.fillStyle = COLORS.key;
        ctx.beginPath();
        ctx.arc(x + CELL_SIZE * 0.3, y - CELL_SIZE * 0.3, 3, 0, Math.PI * 2);
        ctx.fill();
    }
}

function drawObjects(objects) {
    objects.forEach(obj => {
        const x = obj.x * CELL_SIZE;
        const y = obj.y * CELL_SIZE;
        
        ctx.save();
        
        switch (obj.type) {
            case 'key':
                // Draw key as a golden square with a handle
                ctx.fillStyle = COLORS.key;
                ctx.fillRect(x + 5, y + 5, CELL_SIZE - 10, CELL_SIZE - 10);
                ctx.strokeStyle = '#B8860B';
                ctx.lineWidth = 2;
                ctx.strokeRect(x + 5, y + 5, CELL_SIZE - 10, CELL_SIZE - 10);
                
                // Key teeth
                ctx.fillStyle = COLORS.key;
                ctx.fillRect(x + 8, y + 2, 4, 5);
                ctx.fillRect(x + 12, y + 2, 4, 5);
                break;
                
            case 'door':
                // Draw door as a brown rectangle
                ctx.fillStyle = COLORS.door;
                ctx.fillRect(x + 2, y + 2, CELL_SIZE - 4, CELL_SIZE - 4);
                
                // Door handle
                ctx.fillStyle = '#FFD700';
                ctx.beginPath();
                ctx.arc(x + CELL_SIZE * 0.75, y + CELL_SIZE * 0.5, 2, 0, Math.PI * 2);
                ctx.fill();
                break;
                
            case 'charger':
                // Draw charger as a green circle with lightning bolt
                ctx.fillStyle = COLORS.charger;
                ctx.beginPath();
                ctx.arc(x + CELL_SIZE / 2, y + CELL_SIZE / 2, CELL_SIZE * 0.35, 0, Math.PI * 2);
                ctx.fill();
                
                // Lightning bolt
                ctx.strokeStyle = '#FFFFFF';
                ctx.lineWidth = 2;
                ctx.beginPath();
                ctx.moveTo(x + CELL_SIZE * 0.5, y + CELL_SIZE * 0.3);
                ctx.lineTo(x + CELL_SIZE * 0.45, y + CELL_SIZE * 0.5);
                ctx.lineTo(x + CELL_SIZE * 0.55, y + CELL_SIZE * 0.5);
                ctx.lineTo(x + CELL_SIZE * 0.5, y + CELL_SIZE * 0.7);
                ctx.stroke();
                break;
                
            case 'obstacle':
                // Draw obstacle as a gray square
                ctx.fillStyle = COLORS.obstacle;
                ctx.fillRect(x + 3, y + 3, CELL_SIZE - 6, CELL_SIZE - 6);
                break;
        }
        
        ctx.restore();
    });
}

function draw() {
    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    // Draw everything
    drawGrid();
    drawObjects(worldState.world_objects);
    drawAgent(worldState.agent);
    
    // Update status panel
    updateStatusPanel();
}

function updateStatusPanel() {
    document.getElementById('energy-level').textContent = Math.round(worldState.agent.energy);
    document.getElementById('key-status').textContent = worldState.agent.has_key ? 'Yes' : 'No';
    document.getElementById('agent-position').textContent = `${worldState.agent.x}, ${worldState.agent.y}`;
}

// API communication
async function updateState() {
    try {
        const response = await fetch('/update', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(worldState)
        });
        
        if (!response.ok) {
            console.error('Server response not OK');
            return;
        }
        
        const data = await response.json();
        worldState = data.world_state;
        
        // Update reasoning panel
        if (data.log_message) {
            addLogEntry(data.log_message);
        }
    } catch (error) {
        console.error('Error updating state:', error);
    }
}

function addLogEntry(message) {
    const timestamp = new Date().toLocaleTimeString();
    const entry = document.createElement('div');
    entry.className = 'log-entry';
    entry.innerHTML = `
        <div class="timestamp">[${timestamp}]</div>
        <div class="message">${message}</div>
    `;
    
    // Prepend to reasoning panel (newest first)
    reasoningPanel.insertBefore(entry, reasoningPanel.firstChild);
    
    // Keep only last 50 entries
    while (reasoningPanel.children.length > 50) {
        reasoningPanel.removeChild(reasoningPanel.lastChild);
    }
}

// Main loop
function mainLoop() {
    updateState().then(() => {
        draw();
    });
}

// Control button event listeners
document.getElementById('add-key').addEventListener('click', () => {
    setPlacingMode('key');
});

document.getElementById('add-door').addEventListener('click', () => {
    setPlacingMode('door');
});

document.getElementById('add-charger').addEventListener('click', () => {
    setPlacingMode('charger');
});

document.getElementById('add-obstacle').addEventListener('click', () => {
    setPlacingMode('obstacle');
});

document.getElementById('reset-agent').addEventListener('click', () => {
    worldState.agent = {
        x: 20,
        y: 15,
        energy: 100,
        has_key: false
    };
    addLogEntry('Agent reset to starting position');
    draw();
});

function setPlacingMode(type) {
    // Remove active class from all buttons
    document.querySelectorAll('.controls button').forEach(btn => {
        btn.classList.remove('active');
    });
    
    if (placingObjectType === type) {
        placingObjectType = null;
    } else {
        placingObjectType = type;
        // Add active class to current button
        document.getElementById(`add-${type}`).classList.add('active');
        addLogEntry(`Click on the grid to place a ${type}`);
    }
}

// Canvas click event listener
canvas.addEventListener('click', (event) => {
    if (!placingObjectType) return;
    
    const rect = canvas.getBoundingClientRect();
    const x = Math.floor((event.clientX - rect.left) / CELL_SIZE);
    const y = Math.floor((event.clientY - rect.top) / CELL_SIZE);
    
    // Check if position is valid and not occupied
    if (x >= 0 && x < GRID_WIDTH && y >= 0 && y < GRID_HEIGHT) {
        // Check if position is occupied by agent
        if (x === worldState.agent.x && y === worldState.agent.y) {
            addLogEntry('Cannot place object on agent position');
            return;
        }
        
        // Check if position is already occupied by another object
        const existing = worldState.world_objects.find(obj => obj.x === x && obj.y === y);
        if (existing) {
            addLogEntry('Position already occupied');
            return;
        }
        
        // Add new object
        worldState.world_objects.push({
            x: x,
            y: y,
            type: placingObjectType
        });
        
        addLogEntry(`Placed ${placingObjectType} at (${x}, ${y})`);
        
        // Reset placing mode
        document.querySelectorAll('.controls button').forEach(btn => {
            btn.classList.remove('active');
        });
        placingObjectType = null;
        
        // Redraw immediately
        draw();
    }
});

// Show cursor position on hover
canvas.addEventListener('mousemove', (event) => {
    if (placingObjectType) {
        const rect = canvas.getBoundingClientRect();
        const x = Math.floor((event.clientX - rect.left) / CELL_SIZE);
        const y = Math.floor((event.clientY - rect.top) / CELL_SIZE);
        
        // Redraw and highlight current cell
        draw();
        
        if (x >= 0 && x < GRID_WIDTH && y >= 0 && y < GRID_HEIGHT) {
            ctx.fillStyle = 'rgba(100, 126, 234, 0.3)';
            ctx.fillRect(x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE);
        }
    }
});

// Initialize
addLogEntry('System initialized. Agent starting at position (20, 15)');
draw();

// Start simulation loop
setInterval(mainLoop, 500); // Update every 500ms for smoother visualization
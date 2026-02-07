# Financial Network Systemic Risk Platform

A comprehensive web-based platform for modeling and analyzing systemic risk in financial networks using game-theoretic approaches. Built for Rasmalai Datathon 2026.

## 🎯 Overview

This platform simulates financial infrastructure networks consisting of banks, exchanges, and clearing houses. It models contagion effects, equilibrium analysis, and stress testing scenarios to understand systemic risk propagation in interconnected financial systems.

---

## ✨ Features Implemented

### 🎨 **Frontend (React + Vite)**

#### **Visual Canvas Editor (Canva-Style Light Theme)**
- ✅ Professional white board interface with dot grid pattern
- ✅ Real-time network visualization with HTML5 Canvas
- ✅ Drag-and-drop institution positioning
- ✅ Ctrl+drag to create connections between institutions
- ✅ Zoom controls (50% - 200%)
- ✅ Collapsible side panels for controls and metrics
- ✅ Floating toolbar with tool selection (Select, Pan, Connect)

#### **Institution Management**
- ✅ Three institution types with custom SVG-style icons:
  - **Banks** 🏛️ - Building icon with columns
  - **Exchanges** 📈 - Stock chart line graph
  - **Clearing Houses** ⚖️ - Balance scale
- ✅ Add/remove institutions dynamically
- ✅ Edit properties: capital, liquidity, risk, strategy
- ✅ Visual risk indicators with pulse animations
- ✅ Institution details panel with full editing capabilities

#### **Connection System**
- ✅ Three connection types:
  - Credit Exposure (blue)
  - Settlement Obligation (green)
  - Margin Requirement (yellow/dashed)
- ✅ Animated dollar signs ($) during transfers
- ✅ Connection labels showing exposure amounts
- ✅ Directional arrows indicating flow
- ✅ Visual feedback during connection creation

#### **Simulation Engine**
- ✅ Real-time contagion simulation
- ✅ Play/Pause/Reset controls
- ✅ Adjustable simulation speed
- ✅ Step counter display
- ✅ Live metrics updates during simulation
- ✅ Animated particle flows on connections

#### **Stress Testing Scenarios**
- ✅ Financial Crisis (severe market crash)
- ✅ Credit Crunch (reduced credit availability)
- ✅ Regulatory Stress Test
- ✅ Institution Failure simulation
- ✅ One-click scenario application

#### **System Metrics Dashboard**
- ✅ Real-time metrics with visual progress bars:
  - Systemic Risk
  - Liquidity Flow
  - Network Congestion
  - Stability Index
  - Cascade Risk
  - Interconnectedness
- ✅ Color-coded severity indicators

#### **Simulation Parameters**
- ✅ Shock Magnitude (0-100%)
- ✅ Shock Type (Liquidity, Capital, Operational, Market)
- ✅ Contagion Threshold
- ✅ Information Asymmetry
- ✅ Recovery Rate
- ✅ Regulatory Intervention toggle

#### **Authentication & User Management**
- ✅ Clerk-based authentication
- ✅ Sign up / Sign in / Sign out
- ✅ User profile integration
- ✅ Protected routes
- ✅ Persistent user sessions

#### **UI/UX Enhancements**
- ✅ Canva-style professional light theme
- ✅ Glassmorphism effects with backdrop blur
- ✅ Smooth animations (60 FPS canvas rendering)
- ✅ Responsive design
- ✅ Gradient buttons with hover effects
- ✅ Shadow and depth effects
- ✅ Custom scrollbar styling
- ✅ Alert notifications system

### 🔧 **Backend (FastAPI + MongoDB)**

#### **Core APIs**
- ✅ `/api/networks` - Network CRUD operations
- ✅ `/api/contagion` - Contagion simulation engine
- ✅ `/api/equilibrium` - Game-theoretic equilibrium analysis
- ✅ `/api/users` - User management and data persistence
- ✅ `/api/simulation/run` - Advanced simulation v2 with ML policy
- ✅ **NEW: Per-node parameters** - Custom configuration for each bank in simulation

#### **Network Management**
- ✅ Create/Read/Update/Delete networks
- ✅ Add/remove institutions and connections
- ✅ Network topology analysis
- ✅ User-specific network isolation

#### **Contagion Engine**
- ✅ Step-by-step contagion propagation
- ✅ Shock scenarios (liquidity, capital, operational, market)
- ✅ Cascading failure modeling
- ✅ Risk metrics calculation
- ✅ Alert generation system

#### **Equilibrium Analysis**
- ✅ Nash equilibrium computation
- ✅ Strategy optimization
- ✅ Stability analysis
- ✅ Network equilibrium metrics

#### **Database Layer**
- ✅ MongoDB integration with Motor (async)
- ✅ User data persistence
- ✅ Network state storage
- ✅ Simulation history tracking

#### **API Features**
- ✅ CORS configuration for frontend integration
- ✅ Environment-based configuration
- ✅ Health check endpoints
- ✅ Auto-generated API documentation (Swagger/OpenAPI)
- ✅ Async request handling

---

## 📁 Folder Structure

```
Rasmalai_Datathon2026/
│
├── frontend/                          # React + Vite Frontend
│   ├── public/                        # Static assets
│   ├── src/
│   │   ├── assets/                    # Images, icons, etc.
│   │   ├── components/                # React components
│   │   │   ├── CanvasToolbar.jsx      # Floating toolbar with tools/controls
│   │   │   ├── ControlPanel.jsx       # Institution/connection add panel
│   │   │   ├── FinancialNetworkPlayground.jsx  # Main app container
│   │   │   ├── InstitutionPanel.jsx   # Institution details/edit panel
│   │   │   ├── MetricsPanel.jsx       # System metrics display
│   │   │   ├── NetworkCanvas.jsx      # HTML5 Canvas visualization
│   │   │   ├── ScenarioPanel.jsx      # Stress test scenarios
│   │   │   ├── SimulationControls.jsx # Simulation buttons
│   │   │   └── UserSyncWrapper.jsx    # User data sync component
│   │   ├── hooks/
│   │   │   └── useUserSync.js         # Custom hook for user sync
│   │   ├── pages/
│   │   │   ├── HeroPage.jsx           # Landing page
│   │   │   ├── LoginPage.jsx          # Login page
│   │   │   └── SignupPage.jsx         # Signup page
│   │   ├── App.jsx                    # Root component with routing
│   │   ├── main.jsx                   # Application entry point
│   │   └── index.css                  # Global styles (Tailwind)
│   ├── .env                           # Environment variables (Clerk keys)
│   ├── package.json                   # Dependencies & scripts
│   ├── vite.config.js                 # Vite configuration
│   ├── tailwind.config.js             # Tailwind CSS config
│   └── index.html                     # HTML entry point
│
├── backend/                           # FastAPI Backend
│   ├── app/
│   │   ├── config/
│   │   │   └── database.py            # MongoDB connection setup
│   │   ├── middleware/                # Custom middleware (if any)
│   │   ├── routers/                   # API route handlers
│   │   │   ├── contagion.py           # Contagion simulation endpoints
│   │   │   ├── equilibrium.py         # Equilibrium analysis endpoints
│   │   │   ├── networks.py            # Network CRUD endpoints
│   │   │   └── users.py               # User management endpoints
│   │   ├── schemas/                   # Pydantic models
│   │   │   ├── contagion.py           # Contagion request/response schemas
│   │   │   ├── equilibrium.py         # Equilibrium schemas
│   │   │   └── network.py             # Network data schemas
│   │   ├── services/                  # Business logic layer
│   │   │   ├── contagion_service.py   # Contagion simulation logic
│   │   │   ├── equilibrium_service.py # Equilibrium computation logic
│   │   │   └── network_service.py     # Network operations logic
│   │   └── main.py                    # FastAPI app initialization
│   ├── requirements.txt               # Python dependencies
│   └── .env                           # Backend environment variables
│
├── core_implementation.py             # Core mathematical models
├── AUTHENTICATION.md                  # Auth setup documentation
├── USER_STORAGE_GUIDE.md              # User data storage guide
├── FIXED_USER_STORAGE.md              # User storage fixes
└── README.md                          # This file

```

---

## 🛠️ Tech Stack

### **Frontend**
- **React 19.2.0** - UI framework
- **Vite 7.2.4** - Build tool & dev server
- **Tailwind CSS 4.1.18** - Utility-first CSS framework
- **Lucide React 0.563.0** - Icon library
- **React Router DOM 7.13.0** - Client-side routing
- **Clerk 5.60.0** - Authentication & user management
- **HTML5 Canvas API** - Network visualization

### **Backend**
- **FastAPI 0.104+** - Modern Python web framework
- **Uvicorn** - ASGI server
- **Pydantic 2.5+** - Data validation
- **MongoDB + Motor** - Database & async driver
- **NumPy 1.24+** - Numerical computations
- **SciPy 1.11+** - Scientific computing
- **NetworkX 3.2+** - Graph algorithms
- **Python-dotenv** - Environment management

---

## 🚀 Getting Started

### **Prerequisites**
- Node.js 20+ and npm
- Python 3.10+
- MongoDB instance (local or cloud)
- Clerk account for authentication

### **Frontend Setup**

1. **Navigate to frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Configure environment variables:**
   Create `.env` file:
   ```env
   VITE_CLERK_PUBLISHABLE_KEY=your_clerk_key_here
   ```

4. **Start development server:**
   ```bash
   npm run dev
   ```
   Frontend runs at: `http://localhost:5173`

### **Backend Setup**

1. **Navigate to backend directory:**
   ```bash
   cd backend
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables:**
   Create `.env` file:
   ```env
   MONGODB_URL=mongodb://localhost:27017
   MONGODB_DB=financial_network
   CORS_ORIGINS=http://localhost:5173,http://localhost:5174
   ```

5. **Start backend server:**
   ```bash
   python -m uvicorn app.main:app --reload --port 8000
   ```
   Backend runs at: `http://localhost:8000`
   API docs at: `http://localhost:8000/docs`

---

## 📡 API Endpoints

### **Networks**
- `POST /api/networks` - Create new network
- `GET /api/networks/{network_id}` - Get network details
- `PUT /api/networks/{network_id}` - Update network
- `DELETE /api/networks/{network_id}` - Delete network
- `POST /api/networks/{network_id}/institutions` - Add institution
- `POST /api/networks/{network_id}/connections` - Add connection

### **Contagion**
- `POST /api/contagion/simulate` - Run contagion simulation
- `POST /api/contagion/step` - Execute single simulation step
- `GET /api/contagion/metrics` - Get current metrics

### **Equilibrium**
- `POST /api/equilibrium/analyze` - Analyze network equilibrium
- `GET /api/equilibrium/nash` - Compute Nash equilibrium
- `POST /api/equilibrium/optimize` - Optimize strategies

### **Users**
- `POST /api/users` - Create/sync user
- `GET /api/users/{user_id}` - Get user data
- `GET /api/users/{user_id}/networks` - Get user's networks

### **Simulation (v2)**
- `POST /api/simulation/run` - Run advanced simulation with ML policy
  - Supports per-node parameters for custom bank configurations
  - See [NODE_PARAMETERS.md](./NODE_PARAMETERS.md) for detailed documentation

---

## 🎨 UI Features

### **Canvas Interactions**
- **Left Click + Drag**: Move institutions
- **Ctrl + Drag**: Create connection between nodes
- **Click Node**: Select and view details
- **Click Connection**: Select connection
- **Zoom**: Use toolbar buttons or mouse wheel

### **Panel Controls**
- **Left Panel**: Add institutions, connections, adjust parameters, apply scenarios
- **Right Panel**: View metrics, edit selected institution
- **Floating Toolbar**: Tool selection, simulation controls, zoom

### **Visual Indicators**
- **Node Colors**: Blue (bank), Green (exchange), Yellow (clearing house)
- **Risk Ring**: Circular progress showing risk level
- **Pulse Animation**: Active institutions pulse during simulation
- **Connection Colors**: Credit (blue), Settlement (green), Margin (yellow)
- **Dollar Signs**: Animated $ symbols flow during transfers

---

## 🧪 Simulation Features

### **Backend Simulation v2 (NEW)**
The platform now supports advanced backend simulations with customizable node parameters:

#### **Using Playground Nodes**
1. Create institutions in the playground canvas
2. Configure each institution's properties (capital, liquidity, risk, strategy)
3. In the Backend Simulation panel, toggle "Use Playground Nodes" ON
4. Click "Run simulation" - backend will use your exact playground configuration

#### **Node Parameters Support**
- **Initial Capital**: Starting capital for each bank
- **Initial Liquidity**: Starting cash/liquidity reserves
- **Risk Level**: Risk tolerance (0-1 scale)
- **Strategy**: Conservative, Balanced, or Aggressive
- **Custom Amounts**: Per-node lending and investment amounts

For detailed documentation, see [NODE_PARAMETERS.md](./NODE_PARAMETERS.md)

### **Shock Types**
1. **Liquidity Shock** - Sudden loss of liquid assets
2. **Capital Shock** - Reduction in capital reserves
3. **Operational Shock** - Internal system failures
4. **Market Shock** - External market disruptions

### **Stress Scenarios**
1. **Financial Crisis** - Severe market crash with liquidity freeze
2. **Credit Crunch** - Reduced credit availability
3. **Regulatory Stress** - Stricter regulatory requirements
4. **Institution Failure** - Random critical failure

### **Real-Time Metrics**
- Systemic Risk indicator
- Liquidity Flow measurement
- Network Congestion level
- Overall Stability Index
- Cascade Risk assessment
- Interconnectedness score

---

## 📝 Key Algorithms

### **Contagion Model**
- Cascading failure propagation
- Liquidity spirals
- Fire-sale externalities
- Capital depletion dynamics

### **Equilibrium Analysis**
- Nash equilibrium computation
- Best response dynamics
- Strategy optimization
- Stability analysis

### **Network Metrics**
- Centrality measures (degree, betweenness, eigenvector)
- Clustering coefficients
- Path lengths and connectivity
- Risk contribution scores

---

## 🔐 Authentication

Uses **Clerk** for secure authentication:
- Email/password authentication
- Social login support
- Session management
- User profile handling
- Protected routes

See `AUTHENTICATION.md` for detailed setup.

---

## 📊 Data Persistence

- User networks stored in MongoDB
- Simulation states saved automatically
- Network configurations retrievable
- Historical simulation data tracked

See `USER_STORAGE_GUIDE.md` for database schema.

---

## 🎯 Future Enhancements

- [ ] Multi-agent reinforcement learning
- [ ] Advanced visualization options (3D network)
- [ ] Historical simulation playback
- [ ] Export simulation results (PDF/CSV)
- [ ] Custom shock scenario builder
- [ ] Network comparison tools
- [ ] Real-time collaboration features
- [ ] Mobile responsive design
- [ ] Dark theme toggle
- [ ] Keyboard shortcuts

---

## 👥 Contributing

This project was developed for the Rasmalai Datathon 2026. For contributions or questions, please refer to the project repository.

---

## 📄 License

[Specify license here]

---

## 🙏 Acknowledgments

Built for **Rasmalai Datathon 2026** - Financial Network Systemic Risk Analysis Platform

---

## 📞 Support

For issues or questions:
- Check API documentation at `/docs`
- Review authentication guide in `AUTHENTICATION.md`
- See user storage guide in `USER_STORAGE_GUIDE.md`

---

**Last Updated:** February 7, 2026

# Poker MTT Helper

Real-time poker table analyzer with GTO recommendations for PokerOK MTT tournaments.

## Features

- **Screen Capture**: Capture poker table directly from browser using Screen Share API
- **Computer Vision**: Automatic detection of cards, stacks, pot, and button position
- **GTO Recommendations**: Preflop and postflop action suggestions based on GTO strategy
- **Push/Fold Charts**: Optimized short stack play with Nash equilibrium solutions
- **ICM Calculator**: Tournament equity calculations for bubble and final table play
- **Real-time Analysis**: Continuous table monitoring at configurable FPS
- **HUD Statistics**: Track opponent VPIP, PFR, 3-bet and other stats
- **Equity Calculator**: Monte Carlo equity calculations
- **In-Browser Training**: Train card recognition model directly from browser

## Tech Stack

### Frontend
- React 18 + TypeScript
- TailwindCSS
- Vite
- React Router
- Screen Capture API
- WebSocket

### Backend
- Python 3.11+ / FastAPI
- OpenCV + EasyOCR
- YOLOv8 (custom trained)
- PostgreSQL
- Redis

## Quick Start

### Using Docker (Recommended)

```bash
# Clone the repository
git clone <repository-url>
cd pokerhelper

# Start development environment
./deploy.sh dev

# Or manually:
docker compose up -d
```

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Training Module: http://localhost:5173/training

### Manual Setup

#### Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

---

## Production Deployment

### Server Requirements

- **OS**: Ubuntu 22.04 LTS (recommended)
- **CPU**: 2+ cores
- **RAM**: 4GB+ (8GB for GPU)
- **SSD**: 40GB+
- **GPU**: NVIDIA (optional, for faster YOLO inference)

### Quick Deploy

```bash
# 1. Setup server (run once)
sudo ./scripts/server-setup.sh

# 2. Configure environment
cp env.example .env.production
nano .env.production  # Fill in your values

# 3. Setup SSL (optional but recommended)
sudo ./scripts/ssl-setup.sh your-domain.com admin@your-domain.com

# 4. Deploy
./deploy.sh prod
```

### Deployment Commands

```bash
./deploy.sh dev      # Start development environment
./deploy.sh prod     # Deploy production
./deploy.sh status   # Show service status
./deploy.sh logs     # View logs
./deploy.sh backup   # Create database backup
./deploy.sh stop     # Stop all services
./deploy.sh restart  # Restart services
./deploy.sh update   # Pull updates and redeploy
```

### Configuration

Edit `.env.production` with your settings:

```env
# Domain
DOMAIN=poker.yourdomain.com
SSL_EMAIL=admin@yourdomain.com

# Database (change password!)
DB_PASSWORD=your_secure_password

# Application
CORS_ORIGINS=https://poker.yourdomain.com
SECRET_KEY=generate_with_openssl_rand_hex_32

# Performance
WORKERS=2
USE_GPU=false
```

### SSL Certificates

SSL certificates are obtained automatically via Let's Encrypt:

```bash
sudo ./scripts/ssl-setup.sh your-domain.com
```

Certificates auto-renew via cron.

### Backups

Database backups run automatically:

```bash
# Manual backup
./deploy.sh backup

# Setup daily backup (cron)
0 2 * * * /path/to/pokerhelper/scripts/backup.sh
```

Backups are stored in `/var/backups/pokerhelper/` with 7-day retention.

---

## Training Card Detection Model

### Browser-Based Training (Recommended)

1. Start the application
2. Navigate to `/training`
3. Select PokerOK window for capture
4. Use **Calibrate** tab to adjust card positions
5. Use **Label Data** tab to collect and label images
6. Start training when you have 100+ images

### Keyboard Shortcuts for Labeling

- **Rank keys**: `A`, `K`, `Q`, `J`, `T`, `9`-`2`
- **Suit keys**: `S` (spades), `H` (hearts), `D` (diamonds), `C` (clubs)
- **Example**: Press `A` then `S` for Ace of Spades

### CLI Training

```bash
cd training

# Create sample dataset structure
python train_cards.py --create-sample

# Validate dataset
python train_cards.py --validate-only

# Train model
python train_cards.py --epochs 100 --model n
```

---

## Project Structure

```
pokerhelper/
├── frontend/                 # React application
│   ├── src/
│   │   ├── components/       # UI components
│   │   │   └── training/     # Training module components
│   │   ├── pages/            # Page components
│   │   ├── hooks/            # React hooks
│   │   └── types/            # TypeScript types
│   └── package.json
│
├── backend/                  # FastAPI server
│   ├── app/
│   │   ├── api/              # WebSocket & REST endpoints
│   │   ├── cv/               # Computer vision pipeline
│   │   ├── poker/            # Poker logic & GTO engine
│   │   ├── training/         # Training module
│   │   └── db/               # Database models
│   ├── data/                 # Training dataset
│   ├── models/               # Trained models
│   └── requirements.txt
│
├── training/                 # CLI training tools
│   ├── card_dataset/         # Training data
│   └── train_cards.py        # YOLO training script
│
├── nginx/                    # Nginx configurations
│   ├── nginx.conf            # Development config
│   └── nginx.prod.conf       # Production config (HTTPS)
│
├── scripts/                  # Deployment scripts
│   ├── server-setup.sh       # Server initialization
│   ├── ssl-setup.sh          # SSL certificate setup
│   └── backup.sh             # Database backup
│
├── docker-compose.yml        # Development
├── docker-compose.prod.yml   # Production
├── deploy.sh                 # Deployment script
└── env.example               # Environment template
```

## Usage

1. Open the web application
2. Click "Start Capture" and select the PokerOK window
3. The system will automatically analyze the table
4. View recommendations in the right panel
5. Use "Train Model" button to improve card recognition

### Main Features

- **Auto-analyze**: Continuous frame analysis at configured FPS
- **Push/Fold Mode**: Automatically activates for short stacks (<15BB)
- **Hand Range Matrix**: Visual display of opening/pushing ranges
- **ICM Awareness**: Adjusts recommendations for bubble/FT play
- **HUD Overlay**: Display opponent statistics

## API Endpoints

### WebSocket

- `ws://localhost:8000/ws/analyze` - Real-time frame analysis

### REST

- `GET /health` - Health check
- `GET /api/status` - System status
- `GET /api/training/dataset/stats` - Dataset statistics
- `POST /api/training/detect` - Auto-detect cards
- `POST /api/training/start` - Start model training
- `GET /api/training/status` - Training progress

## Development

### Running Tests

```bash
# Backend
cd backend
pytest

# Frontend
cd frontend
npm run test
```

### Linting

```bash
# Backend
cd backend
ruff check .

# Frontend
cd frontend
npm run lint
```

## Disclaimer

This tool is intended for educational purposes and offline analysis only.
Using real-time assistance during actual poker play may violate the Terms of Service
of poker platforms and could result in account suspension.

## License

MIT License - See LICENSE file for details

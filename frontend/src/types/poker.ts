// Card representation
export interface Card {
  rank: string; // 2-9, T, J, Q, K, A
  suit: string; // c, d, h, s
}

// Player state
export interface PlayerState {
  seat: number;
  stack: number;
  currentBet: number;
  isActive: boolean;
  isHero: boolean;
  isTurn: boolean;
  position: string;
  name: string;
}

// Full game state from CV analysis
export interface GameState {
  heroCards: string[];
  boardCards: string[];
  potSize: number;
  potBb: number;
  players: PlayerState[];
  buttonSeat: number | null;
  smallBlind: number;
  bigBlind: number;
  ante: number;
  street: 'preflop' | 'flop' | 'turn' | 'river';
  tableFormat: '6max' | '9max' | 'headsup';
  heroPosition: string;
  heroStackBb: number;
  effectiveStackBb: number;
  heroHand: string | null;
  numActivePlayers: number;
}

// Single action recommendation
export interface ActionRecommendation {
  action: 'fold' | 'check' | 'call' | 'bet' | 'raise' | 'allin';
  size?: number;
  frequency: number;
  reason: string;
}

// Complete recommendation response
export interface Recommendation {
  primary: ActionRecommendation;
  alternatives: ActionRecommendation[];
  hand: string;
  position: string;
  stackBb: number;
  street?: string;
  isPushFold: boolean;
  icmAdjusted: boolean;
  rangeStrength: number;
  notes: string[];
}

// WebSocket message types
export interface WSMessage {
  type: 'frame' | 'ping' | 'settings';
  data?: string;
}

// Server response
export interface WSResponse {
  status: 'success' | 'no_table_detected' | 'error';
  gameState?: GameState;
  recommendations?: Recommendation;
  error?: string;
}

// Capture settings
export interface CaptureSettings {
  fps: number;
  quality: number;
  autoCapture: boolean;
}

// Connection status
export type ConnectionStatus = 'disconnected' | 'connecting' | 'connected' | 'error';

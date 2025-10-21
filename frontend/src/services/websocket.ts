// --- TYPESCRIPT INTERFACES ---

export type ConnectionState = 'connecting' | 'connected' | 'disconnected' | 'error';

export interface WebSocketMessage {
  type: string;
  data: any;
}

export type MessageCallback = (message: WebSocketMessage) => void;

const MAX_RETRIES = 5;
const RETRY_INTERVAL_MS = 1000;

// --- WEBSOCKET MANAGER CLASS ---

class WebSocketManager {
  private ws: WebSocket | null = null;
  private url: string | null = null;
  private token: string | null = null;
  private retries = 0;
  private connectionState: ConnectionState = 'disconnected';
  private onMessageCallback: MessageCallback | null = null;

  private setState(state: ConnectionState) {
    this.connectionState = state;
    // Optional: Add a state change callback if needed
  }

  public connect(dashboardId: number, token: string) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      console.log('WebSocket is already connected.');
      return;
    }

    this.url = `ws://localhost:8000/api/v1/ws/dashboard/${dashboardId}`;
    this.token = token;
    this.retries = 0;
    this.setState('connecting');
    this._doConnect();
  }

  private _doConnect() {
    if (!this.url || !this.token) {
      console.error('URL or token not set for WebSocket connection.');
      this.setState('error');
      return;
    }

    const fullUrl = `${this.url}?token=${this.token}`;
    this.ws = new WebSocket(fullUrl);

    this.ws.onopen = () => {
      console.log('WebSocket connected');
      this.setState('connected');
      this.retries = 0;
    };

    this.ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        if (this.onMessageCallback) {
          this.onMessageCallback(message);
        }
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };

    this.ws.onclose = (event) => {
      console.log(`WebSocket closed with code: ${event.code}`);
      if (event.code !== 1000 && this.retries < MAX_RETRIES) {
        this.retries++;
        const delay = Math.pow(2, this.retries) * RETRY_INTERVAL_MS;
        console.log(`Attempting to reconnect in ${delay}ms...`);
        setTimeout(() => this._doConnect(), delay);
        this.setState('connecting');
      } else {
        this.setState('disconnected');
      }
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      this.setState('error');
    };
  }

  public disconnect() {
    if (this.ws) {
      this.retries = MAX_RETRIES; // Prevent reconnection
      this.ws.close(1000, 'User disconnected');
      this.ws = null;
    }
    this.setState('disconnected');
  }

  public onMessage(callback: MessageCallback) {
    this.onMessageCallback = callback;
  }

  public getConnectionState(): ConnectionState {
    return this.connectionState;
  }
}

const webSocketManager = new WebSocketManager();
export default webSocketManager;

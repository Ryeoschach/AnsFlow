/**
 * 实时日志WebSocket客户端
 * 处理WebSocket连接、重连、消息处理等
 */

export interface LogEntry {
  id?: string;
  timestamp: string;
  level: 'DEBUG' | 'INFO' | 'WARNING' | 'ERROR' | 'CRITICAL';
  service: 'django' | 'fastapi' | 'system';
  module?: string;
  logger?: string;
  message: string;
  extra_data?: any;
  labels?: string[];
  file?: string;
  line_number?: number;
  raw?: boolean;
  trace_id?: string;
  user_id?: number;
  extra?: Record<string, any>;
}

export interface LogFilter {
  levels?: string[];
  services?: string[];
  keywords?: string[];
  start_time?: string;
  end_time?: string;
  user_id?: number;
}

export interface WebSocketMessage {
  type: string;
  message?: string;
  timestamp?: string;
  log?: LogEntry;
  logs?: LogEntry[];
  total?: number;
  filter?: LogFilter;
}

// 简单的事件发射器类型
type EventListener = (...args: any[]) => void;

export class RealTimeLogClient {
  private ws: WebSocket | null = null;
  private reconnectTimer: number | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 10;
  private reconnectDelay = 1000; // 1秒
  private pingTimer: number | null = null;
  private pingInterval = 30000; // 30秒
  private eventListeners: Map<string, EventListener[]> = new Map();
  
  public isConnected = false;
  public isConnecting = false;
  
  constructor(private wsUrl: string) {
    // 初始化事件监听器映射
  }
  
  /**
   * 添加事件监听器
   */
  public on(event: string, listener: EventListener): void {
    if (!this.eventListeners.has(event)) {
      this.eventListeners.set(event, []);
    }
    this.eventListeners.get(event)!.push(listener);
  }
  
  /**
   * 移除事件监听器
   */
  public off(event: string, listener: EventListener): void {
    const listeners = this.eventListeners.get(event);
    if (listeners) {
      const index = listeners.indexOf(listener);
      if (index > -1) {
        listeners.splice(index, 1);
      }
    }
  }
  
  /**
   * 触发事件
   */
  private emit(event: string, ...args: any[]): void {
    const listeners = this.eventListeners.get(event);
    if (listeners) {
      listeners.forEach(listener => {
        try {
          listener(...args);
        } catch (error) {
          console.error(`事件监听器执行失败 (${event}):`, error);
        }
      });
    }
  }
  
  /**
   * 连接WebSocket
   */
  public connect(): void {
    if (this.isConnected || this.isConnecting) {
      return;
    }
    
    this.isConnecting = true;
    
    try {
      // 构建WebSocket URL
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${protocol}//${window.location.host}${this.wsUrl}`;
      
      this.ws = new WebSocket(wsUrl);
      
      this.ws.onopen = this.handleOpen.bind(this);
      this.ws.onmessage = this.handleMessage.bind(this);
      this.ws.onclose = this.handleClose.bind(this);
      this.ws.onerror = this.handleError.bind(this);
      
    } catch (error) {
      console.error('WebSocket连接失败:', error);
      this.emit('error', error);
      this.isConnecting = false;
      this.scheduleReconnect();
    }
  }
  
  /**
   * 断开连接
   */
  public disconnect(): void {
    this.clearTimers();
    
    if (this.ws) {
      this.ws.close(1000, '用户主动断开');
      this.ws = null;
    }
    
    this.isConnected = false;
    this.isConnecting = false;
    this.reconnectAttempts = 0;
  }
  
  /**
   * 发送消息
   */
  public send(data: any): void {
    if (!this.isConnected || !this.ws) {
      console.warn('WebSocket未连接，无法发送消息');
      return;
    }
    
    try {
      this.ws.send(JSON.stringify(data));
    } catch (error) {
      console.error('发送WebSocket消息失败:', error);
      this.emit('error', error);
    }
  }
  
  /**
   * 更新日志过滤器
   */
  public updateFilter(filter: LogFilter): void {
    this.send({
      type: 'update_filter',
      filter
    });
  }
  
  /**
   * 获取最近的日志
   */
  public getRecentLogs(count: number = 50): void {
    this.send({
      type: 'get_recent_logs',
      count
    });
  }
  
  /**
   * 发送ping
   */
  public ping(): void {
    this.send({
      type: 'ping'
    });
  }
  
  private handleOpen(): void {
    console.log('WebSocket连接已建立');
    
    this.isConnected = true;
    this.isConnecting = false;
    this.reconnectAttempts = 0;
    
    // 开始心跳
    this.startPing();
    
    this.emit('connected');
  }
  
  private handleMessage(event: MessageEvent): void {
    try {
      const data: WebSocketMessage = JSON.parse(event.data);
      
      switch (data.type) {
        case 'connection_established':
          console.log('实时日志连接建立:', data.message);
          break;
          
        case 'new_log':
          if (data.log) {
            this.emit('log', data.log);
          }
          break;
          
        case 'recent_logs':
          if (data.logs) {
            this.emit('recent_logs', data.logs, data.total);
          }
          break;
          
        case 'filter_updated':
          console.log('过滤器已更新:', data.message);
          this.emit('filter_updated', data.filter);
          break;
          
        case 'pong':
          // 心跳响应
          break;
          
        case 'error':
          console.error('WebSocket错误:', data.message);
          this.emit('error', new Error(data.message));
          break;
          
        default:
          console.warn('未知消息类型:', data.type);
      }
      
    } catch (error) {
      console.error('解析WebSocket消息失败:', error);
      this.emit('error', error);
    }
  }
  
  private handleClose(event: CloseEvent): void {
    console.log(`WebSocket连接关闭: ${event.code} - ${event.reason}`);
    
    this.isConnected = false;
    this.isConnecting = false;
    this.clearTimers();
    
    this.emit('disconnected', event.code, event.reason);
    
    // 如果不是正常关闭，尝试重连
    if (event.code !== 1000 && this.reconnectAttempts < this.maxReconnectAttempts) {
      this.scheduleReconnect();
    }
  }
  
  private handleError(event: Event): void {
    console.error('WebSocket错误:', event);
    this.emit('error', event);
    this.isConnecting = false;
  }
  
  private scheduleReconnect(): void {
    if (this.reconnectTimer) {
      return;
    }
    
    this.reconnectAttempts++;
    const delay = Math.min(this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1), 30000);
    
    console.log(`${delay / 1000}秒后尝试重连 (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
    
    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null;
      this.connect();
    }, delay);
  }
  
  private startPing(): void {
    this.pingTimer = setInterval(() => {
      if (this.isConnected) {
        this.ping();
      }
    }, this.pingInterval);
  }
  
  private clearTimers(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    
    if (this.pingTimer) {
      clearInterval(this.pingTimer);
      this.pingTimer = null;
    }
  }
}

/**
 * 创建实时日志客户端实例
 */
export function createRealTimeLogClient(): RealTimeLogClient {
  return new RealTimeLogClient('/ws/logs/realtime/');
}

export default RealTimeLogClient;

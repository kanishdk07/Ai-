import React, { createContext, useContext, useEffect, useRef, useState, useCallback } from 'react';
import { WebSocketMessage, WebSocketEventType } from '../types';
import { useAuth } from './AuthContext';

type ConnectionState = 'connected' | 'connecting' | 'disconnected' | 'reconnecting';

interface WebSocketContextType {
  connectionState: ConnectionState;
  lastMessage: WebSocketMessage | null;
  sendMessage: (msg: string | object) => void;
  simulateEvent: (type: WebSocketEventType, data: any) => void;
  reconnect: () => void;
}

const WebSocketContext = createContext<WebSocketContextType | undefined>(undefined);

export const WebSocketProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user } = useAuth();
  const [connectionState, setConnectionState] = useState<ConnectionState>('disconnected');
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const backoffRef = useRef<number>(1000);
  const pingIntervalRef = useRef<NodeJS.Timeout | null>(null);

  const connect = useCallback(() => {
    const token = localStorage.getItem('safeway_access_token') || 'demo-token';
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    
    // In dev, use proxy or direct to 8000
    const wsUrl = `${protocol}//${host}/ws/dashboard?token=${encodeURIComponent(token)}`;

    setConnectionState('connecting');

    try {
      const socket = new WebSocket(wsUrl);
      wsRef.current = socket;

      socket.onopen = () => {
        setConnectionState('connected');
        backoffRef.current = 1000;

        // Start 30s ping heartbeat
        if (pingIntervalRef.current) clearInterval(pingIntervalRef.current);
        pingIntervalRef.current = setInterval(() => {
          if (socket.readyState === WebSocket.OPEN) {
            socket.send('ping');
          }
        }, 30000);
      };

      socket.onmessage = (event) => {
        try {
          const parsed: WebSocketMessage = JSON.parse(event.data);
          if (parsed.type === 'pong') return;
          setLastMessage(parsed);
          window.dispatchEvent(new CustomEvent('safeway:ws_event', { detail: parsed }));
        } catch {
          // Plain text message
        }
      };

      socket.onclose = () => {
        setConnectionState('disconnected');
        if (pingIntervalRef.current) clearInterval(pingIntervalRef.current);
        
        // Auto reconnect with backoff
        if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
        reconnectTimeoutRef.current = setTimeout(() => {
          setConnectionState('reconnecting');
          backoffRef.current = Math.min(backoffRef.current * 2, 30000);
          connect();
        }, backoffRef.current);
      };

      socket.onerror = () => {
        socket.close();
      };
    } catch {
      setConnectionState('disconnected');
    }
  }, []);

  useEffect(() => {
    connect();

    return () => {
      if (wsRef.current) wsRef.current.close();
      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
      if (pingIntervalRef.current) clearInterval(pingIntervalRef.current);
    };
  }, [connect, user]);

  const sendMessage = (msg: string | object) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(typeof msg === 'string' ? msg : JSON.stringify(msg));
    }
  };

  // Helper for simulating real-time AI & backend events in isolated / demo UI
  const simulateEvent = (type: WebSocketEventType, data: any) => {
    const simulatedMsg: WebSocketMessage = {
      type,
      data,
      timestamp: new Date().toISOString(),
    };
    setLastMessage(simulatedMsg);
    window.dispatchEvent(new CustomEvent('safeway:ws_event', { detail: simulatedMsg }));
  };

  return (
    <WebSocketContext.Provider
      value={{
        connectionState,
        lastMessage,
        sendMessage,
        simulateEvent,
        reconnect: connect,
      }}
    >
      {children}
    </WebSocketContext.Provider>
  );
};

export const useWebSocket = () => {
  const context = useContext(WebSocketContext);
  if (!context) throw new Error('useWebSocket must be used within a WebSocketProvider');
  return context;
};

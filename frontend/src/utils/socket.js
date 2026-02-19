import { io } from "socket.io-client";

const SOCKET_URL = "http://localhost:8000";

export function createSocket(token) {
  return io(SOCKET_URL, {
    auth: { token },
    autoConnect: false,
  });
}

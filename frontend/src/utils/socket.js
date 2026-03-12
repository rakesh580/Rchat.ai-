import { io } from "socket.io-client";
import { API_HOST } from "../api";

export function createSocket(token) {
  // In production (same origin), pass undefined so socket.io uses window.location
  const target = API_HOST || undefined;
  return io(target, {
    auth: { token },
    autoConnect: false,
  });
}

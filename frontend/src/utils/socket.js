import { io } from "socket.io-client";
import { API_HOST } from "../api";

export function createSocket(token) {
  return io(API_HOST, {
    auth: { token },
    autoConnect: false,
  });
}

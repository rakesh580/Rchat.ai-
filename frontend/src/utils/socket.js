import { io } from "socket.io-client";
import { API_HOST } from "../api";

export function createSocket(tokenOrGetter) {
  const target = API_HOST || undefined;
  return io(target, {
    auth: (cb) => {
      const token = typeof tokenOrGetter === "function" ? tokenOrGetter() : tokenOrGetter;
      cb({ token });
    },
    autoConnect: false,
  });
}

import { defineStore } from "pinia";
import axios from "axios";


export interface UserInfo {
  id: number;
  username: string;
  role: "student" | "teacher" | "admin";
  display_name: string;
  must_change_password?: boolean;
}


interface AuthState {
  token: string | null;
  user: UserInfo | null;
}


export const useAuthStore = defineStore("auth", {
  state: (): AuthState => ({
    token: localStorage.getItem("token"),
    user: localStorage.getItem("user") ? JSON.parse(localStorage.getItem("user") as string) : null
  }),
  getters: {
    isAuthenticated: state => !!state.token && !!state.user
  },
  actions: {
    async login(username: string, password: string, role: string) {
      const resp = await axios.post("/api/auth/login", { username, password, role });
      const token = resp.data.access_token as string;
      const user = resp.data.user as UserInfo;
      this.token = token;
      this.user = user;
      axios.defaults.headers.common["Authorization"] = "Bearer " + token;
      localStorage.setItem("token", token);
      localStorage.setItem("user", JSON.stringify(user));
      return user;
    },
    logout() {
      this.token = null;
      this.user = null;
      delete axios.defaults.headers.common["Authorization"];
      localStorage.removeItem("token");
      localStorage.removeItem("user");
    },
    initFromStorage() {
      if (this.token) {
        axios.defaults.headers.common["Authorization"] = "Bearer " + this.token;
      }
    }
  }
});

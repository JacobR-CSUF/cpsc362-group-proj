"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { mockUsers, User } from "../mockAPI/mockAPI";

export default function LoginPage() {
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

  const handleLogin = (e: React.FormEvent) => {
  e.preventDefault();

  const user = mockUsers.find(
  (u: User) => u.loginUsername === username && u.password === password
);

  if (user) {
    
    localStorage.setItem("currentUserId", user.id);
    router.push("/home"); 
  } else {
    alert("Invalid credentials. Try again");
  }
};

  return (
    <div className="login-container">
      <form onSubmit={handleLogin} className="login-form">
        <h2>Login</h2>
        <input
          type="text"
          placeholder="Username"
          className="login-input"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
        />
        <input
          type="password"
          placeholder="Password"
          className="login-input"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
        <button type="submit" className="login-button">
          Log In
        </button>
        <div>Test account</div>
        <div>username:bruce123 | password:batman</div>
        <div>username:clark123 | password:superman</div>
        <div>username:joker123 | password:joker</div>
      </form>
    </div>
  );
}

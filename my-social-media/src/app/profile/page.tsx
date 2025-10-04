"use client";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { fetchCurrentUser, User } from "../mockAPI/mockAPI"; 

export default function ProfilePage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
  const getUser = async () => {
    const userId = localStorage.getItem("currentUserId") || "1";
    const data = await fetchCurrentUser(userId);
    setUser(data);
  };
  getUser();
}, []);

  const handleEdit = () => alert("Edit fucntion under construction!");
  const handleLogout = () => router.push("/login");
  const goToProfile = () => router.push("/profile");

  if (!user) return <p>Loading...</p>;

  return (
    <>
      <nav className="navbar">
        <h2>Photon</h2>
        <div className="nav-buttons">
          <button onClick={() => router.push("/home")}>Home</button>
          <button onClick={goToProfile}>Profile</button>
          <button className="logout-button" onClick={handleLogout}>
            Logout
          </button>
        </div>
      </nav>

      <div className="profile-page">
        <div className="profile-header">
          <img src={user.avatar} alt="Profile" className="profile-pic" />
          <div className="profile-info">
            <h2>{user.displayName}</h2>
            <p>Bio: {user.bio}</p>
            <button className="edit-button" onClick={handleEdit}>
              Edit Profile
            </button>
          </div>
        </div>

        <div className="profile-posts">
          <h3>Posts</h3>
          <div className="posts-grid">
            {user.posts.map((src, index) => (
              <img key={index} src={src} alt={`Post ${index}`} />
            ))}
          </div>
        </div>
      </div>
    </>
  );
}

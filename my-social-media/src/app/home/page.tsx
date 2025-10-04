"use client";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import Slider from "react-slick";
import "slick-carousel/slick/slick.css";
import "slick-carousel/slick/slick-theme.css";
import { fetchCurrentUser, User } from "../mockAPI/mockAPI"; // adjust path

export default function HomePage() {
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

  const handleLogout = () => {
    localStorage.removeItem("currentUserId");
    router.push("/login");
  };

  const goToProfile = () => {
    router.push("/profile");
  };

  const images = [
    "/images/cat1.webp",
    "/images/cat2.webp",
    "/images/cat3.jpg",
    "/images/cat4.avif",
  ];

  const settings = {
    dots: true,
    infinite: true,
    speed: 500,
    slidesToShow: 1,
    slidesToScroll: 1,
    autoplay: false,
    centerMode: true,
    centerPadding: "0px",
    arrows: true,
  };

  if (!user) return <p>Loading...</p>;

  return (
    <div>
      <nav className="navbar">
        <h2 className="app-title">
          Photon
          <img
            src={user.avatar}
            alt="Profile"
            className="navbar-profile-pic"
            onClick={goToProfile}
          />
        </h2>
        <div className="nav-buttons">
          <button onClick={() => router.push("/home")}>Home</button>
          <button onClick={goToProfile}>Profile</button>
          <button className="logout-button" onClick={handleLogout}>
            Logout
          </button>
        </div>
      </nav>

      <div className="feed">
        <h3>FEED</h3>
        <Slider {...settings}>
          {images.map((src, index) => (
            <div key={index} className="carousel-slide">
              <img src={src} alt={`Slide ${index}`} />
            </div>
          ))}
        </Slider>

        <h3>FUNCTIONS</h3>
        <ul>
          <li><a href="/summarize">Video Summarizer</a></li>
          <li><a href="/optimize">Photo Optimizer</a></li>
          <li><a href="/reels">Recommended Reels</a></li>
          <li><a href="/chatbot">AI Chatbot</a></li>
        </ul>
      </div>
    </div>
  );
}

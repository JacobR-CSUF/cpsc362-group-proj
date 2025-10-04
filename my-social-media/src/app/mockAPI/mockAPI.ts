export interface User {
  id: string;
  loginUsername: string; 
  password: string;      
  displayName: string;   
  bio: string;
  avatar: string;
  posts: string[];
}

export const mockUsers: User[] = [
  {
    id: "1",
    loginUsername: "bruce123",
    password: "batman",          
    displayName: "Bruce Wayne",
    bio: "I have money",
    avatar: "/images/BruceWayne.webp",
    posts: [
      "/images/image1.jpg",
      "/images/image2.jpg",
      "/images/image3.jpg",
      "/images/image4.jpg",
    ],
  },
  {
    id: "2",
    loginUsername: "clark123",
    password: "superman",        
    displayName: "Clark Kent",
    bio: "I am strong",
    avatar: "/images/ClarkKent.webp",
    posts: [
      "/images/image5.jpg",
      "/images/image6.jpg",
      "/images/image7.jpg",
    ],
  },
  {
    id: "3",
    loginUsername: "joker123",
    password: "joker",          
    displayName: "Joker",
    bio: "BOO!",
    avatar: "/images/joker.webp",
    posts: [
      "/images/image8.jpg",
      "/images/image9.jpg",
      "/images/image10.jpg",
    ],
  },
];

export const fetchCurrentUser = async (userId: string = "1"): Promise<User> => {
  return new Promise((resolve) => {
    const user = mockUsers.find((u: User) => u.id === userId) || mockUsers[0];
    setTimeout(() => resolve(user), 500); 
  });
};
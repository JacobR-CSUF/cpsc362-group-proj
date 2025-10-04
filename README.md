# cpsc362-group-proj
Group assignment that takes the Social Media subject for our project.
### Enhancing a global photo & video sharing platform with AI-powered experiences.

---

## Table of Contents
- [Project Description](#project-description)
- [Installation Instructions](#installation-instructions)
- [Diagram / Visual Explanation](#diagram--visual-explanation)
- [Known Issues](#known-issues)
- [To-Do Items](#to-do-items)

---

## Project Description

Our team has been tasked with integrating **AI-based features** into an existing large-scale social media platform.  
The goal is to enhance user engagement and experience through intelligent features such as:
- AI-generated captions for photos/videos  
- Smart content recommendations  
- Automated moderation and safety filters  
- Personalized feed ranking  

This project will:
- Define our **software development philosophy**  
- Establish a **custom software development framework** aligned with the core team's release cycle  
- Prototype, develop, and deploy new **AI-powered features**  
- Maintain long-term compatibility with the existing infrastructure  

---

## Installation Instructions

> For Developers

1. Create and activate a virtual environment:
    
    ```bash
    python -m venv venv
    source venv/bin/activate  # for Mac/Linux
    venv\Scripts\activate     # for Windows
    ```
    
2. Install dependencies:
    
    ```bash
    pip install -r requirements.txt
    ```
    
3. Run the development server:
    
    ```bash
    uvicorn app.main:app --reload
    ```

> 💡 **For Non-developers (Users)**  
> 
> - The application will be available at [**https://app.yourdomain.com**](https://app.yourdomain.com/).  
> - Log in using your existing social media credentials.  
> - Access **AI Feed**, **Smart Caption**, and **Auto Edit** features from the main dashboard.

---

## Diagram / Visual Explanation

> Below is a conceptual flow of the AI feature integration.

[ User Uploads Photo/Video ]
↓
[ AI Caption Generator ]
↓
[ AI Moderation Filter ]
↓
[ Personalized Feed Recommendation ]
↓
[ Display in App Feed ]

*(You can replace this with an image or demo video later.)*

---

## Known Issues

- AI caption generator may occasionally produce irrelevant or inaccurate text 
- Image moderation latency increases under heavy load 
- Limited GPU resources in the staging environment


## To-Do Items

- [ ] Finalize feature backlog and sprint plan  
- [ ] Implement initial AI ca
- [ ] Integrate recommendation model with feed service  
- [ ] Conduct user testing and collect feedback  
- [ ] Align deployment cycle with core development team  
- [ ] Write unit and integration tests  
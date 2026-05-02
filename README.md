## Project Name ##: ARC

AI-Driven Video Game Review Content Generator

## Team

- Yifan Luo  
- Matt Gu
- Samuel Buck

## Description

This is an undergrates final group project for class MATH-395 Creating AI in the Loop. this program will fetch game info from Steam webpage and generate a game review together with images. User can also provides their own gaming experience and screenshots, that will also be merged in to the final review. 

## Setup(Execute the following code in terminal to run)

1. Clone the repo
2. Create a virtual environment and install dependencies:

```bash
.\.venv\Scripts\Activate.ps1
python -m streamlit run app.py
```

3. Copy `.env.example` to `.env` and add your API key:

```bash
cp .env.example .env
```
## Input
1. Steam page game URL
2. Rating
3. User Description(Optional)
4. Screen Shot(Optional)

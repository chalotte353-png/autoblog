"""
NetWorth Profile Generator
- 1000+ celebrities/influencers list
- Wikipedia se data fetch karta hai
- Claude API se full profile page likhta hai
- /networth/ folder mein HTML save karta hai
- Autoblog system ke saath fully integrated
"""

import os
import json
import time
import requests
import re
from datetime import datetime, timezone
from pathlib import Path
from jinja2 import Template

# ─── CONFIG ────────────────────────────────────────────────────────────────────
CLAUDE_API_KEY = os.environ.get("CLAUDE_API_KEY", "")
SITE_URL       = os.environ.get("SITE_URL", "https://yoursite.com")
SITE_NAME      = os.environ.get("SITE_NAME", "YourBlog")
OUTPUT_DIR     = Path("output")
NETWORTH_DIR   = OUTPUT_DIR / "networth"
PROFILES_PER_RUN = int(os.environ.get("PROFILES_PER_RUN", "50"))

# ─── 500+ CELEBRITIES / INFLUENCERS LIST ───────────────────────────────────────
CELEBRITIES = [
    {
        "name": "MrBeast",
        "category": "YouTuber",
        "real_name": "Jimmy Donaldson"
    },
    {
        "name": "PewDiePie",
        "category": "YouTuber",
        "real_name": "Felix Kjellberg"
    },
    {
        "name": "Logan Paul",
        "category": "YouTuber/Boxer",
        "real_name": "Logan Paul"
    },
    {
        "name": "Jake Paul",
        "category": "YouTuber/Boxer",
        "real_name": "Jake Paul"
    },
    {
        "name": "David Dobrik",
        "category": "YouTuber",
        "real_name": "David Dobrik"
    },
    {
        "name": "Markiplier",
        "category": "YouTuber",
        "real_name": "Mark Fischbach"
    },
    {
        "name": "Jacksepticeye",
        "category": "YouTuber",
        "real_name": "Sean McLoughlin"
    },
    {
        "name": "Ninja",
        "category": "Gamer/Streamer",
        "real_name": "Tyler Blevins"
    },
    {
        "name": "Pokimane",
        "category": "Streamer",
        "real_name": "Imane Anys"
    },
    {
        "name": "Valkyrae",
        "category": "Streamer",
        "real_name": "Rachel Hofstetter"
    },
    {
        "name": "Lilly Singh",
        "category": "YouTuber",
        "real_name": "Lilly Singh"
    },
    {
        "name": "Casey Neistat",
        "category": "YouTuber",
        "real_name": "Casey Neistat"
    },
    {
        "name": "Emma Chamberlain",
        "category": "YouTuber",
        "real_name": "Emma Chamberlain"
    },
    {
        "name": "Jeffree Star",
        "category": "Beauty YouTuber",
        "real_name": "Jeffree Star"
    },
    {
        "name": "James Charles",
        "category": "Beauty YouTuber",
        "real_name": "James Charles"
    },
    {
        "name": "Dude Perfect",
        "category": "YouTuber",
        "real_name": "Dude Perfect"
    },
    {
        "name": "Rhett and Link",
        "category": "YouTuber",
        "real_name": "Rhett McLaughlin and Link Neal"
    },
    {
        "name": "Smosh",
        "category": "YouTuber",
        "real_name": "Ian Hecox and Anthony Padilla"
    },
    {
        "name": "Vsauce",
        "category": "YouTuber",
        "real_name": "Michael Stevens"
    },
    {
        "name": "Veritasium",
        "category": "YouTuber",
        "real_name": "Derek Muller"
    },
    {
        "name": "Kurzgesagt",
        "category": "YouTuber",
        "real_name": "Kurzgesagt Team"
    },
    {
        "name": "Mark Rober",
        "category": "YouTuber",
        "real_name": "Mark Rober"
    },
    {
        "name": "Linus Tech Tips",
        "category": "Tech YouTuber",
        "real_name": "Linus Sebastian"
    },
    {
        "name": "MKBHD",
        "category": "Tech YouTuber",
        "real_name": "Marques Brownlee"
    },
    {
        "name": "Unbox Therapy",
        "category": "Tech YouTuber",
        "real_name": "Lewis Hilsenteger"
    },
    {
        "name": "Shane Dawson",
        "category": "YouTuber",
        "real_name": "Shane Dawson"
    },
    {
        "name": "Trisha Paytas",
        "category": "YouTuber",
        "real_name": "Trisha Paytas"
    },
    {
        "name": "Tana Mongeau",
        "category": "YouTuber",
        "real_name": "Tana Mongeau"
    },
    {
        "name": "KSI",
        "category": "YouTuber/Boxer",
        "real_name": "Olajide Olatunji"
    },
    {
        "name": "Sidemen",
        "category": "YouTuber",
        "real_name": "Sidemen Group"
    },
    {
        "name": "W2S",
        "category": "YouTuber",
        "real_name": "Harry Lewis"
    },
    {
        "name": "Miniminter",
        "category": "YouTuber",
        "real_name": "Simon Minter"
    },
    {
        "name": "Vikkstar123",
        "category": "YouTuber",
        "real_name": "Vikram Barn"
    },
    {
        "name": "Behzinga",
        "category": "YouTuber",
        "real_name": "Ethan Payne"
    },
    {
        "name": "Zerkaa",
        "category": "YouTuber",
        "real_name": "Josh Bradley"
    },
    {
        "name": "Tobi Brown",
        "category": "YouTuber",
        "real_name": "Tobi Brown"
    },
    {
        "name": "Calfreezy",
        "category": "YouTuber",
        "real_name": "Callum Leighton"
    },
    {
        "name": "Jacksfilms",
        "category": "YouTuber",
        "real_name": "John Douglass"
    },
    {
        "name": "Phillip DeFranco",
        "category": "YouTuber",
        "real_name": "Philip DeFranco"
    },
    {
        "name": "iJustine",
        "category": "YouTuber",
        "real_name": "Justine Ezarik"
    },
    {
        "name": "Hannah Hart",
        "category": "YouTuber",
        "real_name": "Hannah Hart"
    },
    {
        "name": "Grace Helbig",
        "category": "YouTuber",
        "real_name": "Grace Helbig"
    },
    {
        "name": "Tyler Oakley",
        "category": "YouTuber",
        "real_name": "Tyler Oakley"
    },
    {
        "name": "Troye Sivan",
        "category": "Singer/YouTuber",
        "real_name": "Troye Sivan Mellet"
    },
    {
        "name": "Connor Franta",
        "category": "YouTuber",
        "real_name": "Connor Franta"
    },
    {
        "name": "Joey Graceffa",
        "category": "YouTuber",
        "real_name": "Joseph Graceffa"
    },
    {
        "name": "Zoella",
        "category": "Lifestyle YouTuber",
        "real_name": "Zoe Sugg"
    },
    {
        "name": "Alfie Deyes",
        "category": "YouTuber",
        "real_name": "Alfie Deyes"
    },
    {
        "name": "Jim Chapman",
        "category": "YouTuber",
        "real_name": "James Chapman"
    },
    {
        "name": "Sprinkleofglitter",
        "category": "YouTuber",
        "real_name": "Louise Pentland"
    },
    {
        "name": "Charli D'Amelio",
        "category": "TikToker",
        "real_name": "Charli D'Amelio"
    },
    {
        "name": "Dixie D'Amelio",
        "category": "TikToker",
        "real_name": "Dixie D'Amelio"
    },
    {
        "name": "Addison Rae",
        "category": "TikToker",
        "real_name": "Addison Rae Easterling"
    },
    {
        "name": "Bella Poarch",
        "category": "TikToker",
        "real_name": "Bella Poarch"
    },
    {
        "name": "Khaby Lame",
        "category": "TikToker",
        "real_name": "Khabane Lame"
    },
    {
        "name": "Zach King",
        "category": "TikToker",
        "real_name": "Zach King"
    },
    {
        "name": "Loren Gray",
        "category": "TikToker",
        "real_name": "Loren Gray"
    },
    {
        "name": "Josh Richards",
        "category": "TikToker",
        "real_name": "Josh Richards"
    },
    {
        "name": "Avani Gregg",
        "category": "TikToker",
        "real_name": "Avani Gregg"
    },
    {
        "name": "Bryce Hall",
        "category": "TikToker",
        "real_name": "Bryce Hall"
    },
    {
        "name": "Noah Beck",
        "category": "TikToker",
        "real_name": "Noah Beck"
    },
    {
        "name": "Chase Hudson",
        "category": "TikToker",
        "real_name": "Chase Hudson"
    },
    {
        "name": "Nessa Barrett",
        "category": "TikToker",
        "real_name": "Nessa Barrett"
    },
    {
        "name": "Riyaz Aly",
        "category": "TikToker",
        "real_name": "Riyaz Aly"
    },
    {
        "name": "Jannat Zubair",
        "category": "TikToker/Actress",
        "real_name": "Jannat Zubair"
    },
    {
        "name": "Arishfa Khan",
        "category": "TikToker",
        "real_name": "Arishfa Khan"
    },
    {
        "name": "Mr Faisu",
        "category": "TikToker",
        "real_name": "Faisal Shaikh"
    },
    {
        "name": "Hasnain Khan",
        "category": "TikToker",
        "real_name": "Hasnain Khan"
    },
    {
        "name": "Dwayne Johnson",
        "category": "Actor",
        "real_name": "Dwayne Johnson"
    },
    {
        "name": "Ryan Reynolds",
        "category": "Actor",
        "real_name": "Ryan Reynolds"
    },
    {
        "name": "Jennifer Aniston",
        "category": "Actress",
        "real_name": "Jennifer Aniston"
    },
    {
        "name": "Tom Hanks",
        "category": "Actor",
        "real_name": "Tom Hanks"
    },
    {
        "name": "Leonardo DiCaprio",
        "category": "Actor",
        "real_name": "Leonardo DiCaprio"
    },
    {
        "name": "Scarlett Johansson",
        "category": "Actress",
        "real_name": "Scarlett Johansson"
    },
    {
        "name": "Robert Downey Jr",
        "category": "Actor",
        "real_name": "Robert Downey Jr"
    },
    {
        "name": "Will Smith",
        "category": "Actor",
        "real_name": "Willard Carroll Smith II"
    },
    {
        "name": "Oprah Winfrey",
        "category": "TV Host/Media",
        "real_name": "Oprah Winfrey"
    },
    {
        "name": "Kim Kardashian",
        "category": "TV Personality",
        "real_name": "Kimberly Noel Kardashian"
    },
    {
        "name": "Kylie Jenner",
        "category": "Influencer/Business",
        "real_name": "Kylie Kristen Jenner"
    },
    {
        "name": "Kendall Jenner",
        "category": "Model",
        "real_name": "Kendall Nicole Jenner"
    },
    {
        "name": "Ellen DeGeneres",
        "category": "TV Host",
        "real_name": "Ellen Lee DeGeneres"
    },
    {
        "name": "Brad Pitt",
        "category": "Actor",
        "real_name": "William Bradley Pitt"
    },
    {
        "name": "Angelina Jolie",
        "category": "Actress",
        "real_name": "Angelina Jolie Voight"
    },
    {
        "name": "Johnny Depp",
        "category": "Actor",
        "real_name": "John Christopher Depp II"
    },
    {
        "name": "Tom Cruise",
        "category": "Actor",
        "real_name": "Thomas Cruise Mapother IV"
    },
    {
        "name": "Denzel Washington",
        "category": "Actor",
        "real_name": "Denzel Hayes Washington Jr"
    },
    {
        "name": "Morgan Freeman",
        "category": "Actor",
        "real_name": "Morgan Porterfield Freeman Jr"
    },
    {
        "name": "Samuel L Jackson",
        "category": "Actor",
        "real_name": "Samuel Leroy Jackson"
    },
    {
        "name": "Chris Hemsworth",
        "category": "Actor",
        "real_name": "Christopher Liam Hemsworth"
    },
    {
        "name": "Chris Evans",
        "category": "Actor",
        "real_name": "Christopher Robert Evans"
    },
    {
        "name": "Chris Pratt",
        "category": "Actor",
        "real_name": "Christopher Michael Pratt"
    },
    {
        "name": "Zendaya",
        "category": "Actress/Singer",
        "real_name": "Zendaya Maree Stoermer Coleman"
    },
    {
        "name": "Timothee Chalamet",
        "category": "Actor",
        "real_name": "Timothee Hal Chalamet"
    },
    {
        "name": "Sydney Sweeney",
        "category": "Actress",
        "real_name": "Sydney Bernice Sweeney"
    },
    {
        "name": "Ana de Armas",
        "category": "Actress",
        "real_name": "Ana Celia de Armas Caso"
    },
    {
        "name": "Margot Robbie",
        "category": "Actress",
        "real_name": "Margot Elise Robbie"
    },
    {
        "name": "Florence Pugh",
        "category": "Actress",
        "real_name": "Florence Rose Pugh"
    },
    {
        "name": "Anya Taylor-Joy",
        "category": "Actress",
        "real_name": "Anya-Josephine Marie Taylor-Joy"
    },
    {
        "name": "Julia Roberts",
        "category": "Actress",
        "real_name": "Julia Fiona Roberts"
    },
    {
        "name": "Sandra Bullock",
        "category": "Actress",
        "real_name": "Sandra Annette Bullock"
    },
    {
        "name": "Reese Witherspoon",
        "category": "Actress",
        "real_name": "Laura Jeanne Reese Witherspoon"
    },
    {
        "name": "Meryl Streep",
        "category": "Actress",
        "real_name": "Mary Louise Streep"
    },
    {
        "name": "Cate Blanchett",
        "category": "Actress",
        "real_name": "Catherine Elise Blanchett"
    },
    {
        "name": "Nicole Kidman",
        "category": "Actress",
        "real_name": "Nicole Mary Kidman"
    },
    {
        "name": "Charlize Theron",
        "category": "Actress",
        "real_name": "Charlize Theron"
    },
    {
        "name": "Halle Berry",
        "category": "Actress",
        "real_name": "Maria Halle Berry"
    },
    {
        "name": "Natalie Portman",
        "category": "Actress",
        "real_name": "Neta-Lee Hershlag"
    },
    {
        "name": "Anne Hathaway",
        "category": "Actress",
        "real_name": "Anne Jacqueline Hathaway"
    },
    {
        "name": "Gwyneth Paltrow",
        "category": "Actress/Business",
        "real_name": "Gwyneth Kate Paltrow"
    },
    {
        "name": "Demi Moore",
        "category": "Actress",
        "real_name": "Demi Gene Guynes"
    },
    {
        "name": "Keanu Reeves",
        "category": "Actor",
        "real_name": "Keanu Charles Reeves"
    },
    {
        "name": "Harrison Ford",
        "category": "Actor",
        "real_name": "Harrison Ford"
    },
    {
        "name": "Sylvester Stallone",
        "category": "Actor",
        "real_name": "Sylvester Gardenzio Stallone"
    },
    {
        "name": "Arnold Schwarzenegger",
        "category": "Actor/Politician",
        "real_name": "Arnold Alois Schwarzenegger"
    },
    {
        "name": "Bruce Willis",
        "category": "Actor",
        "real_name": "Walter Bruce Willis"
    },
    {
        "name": "Mel Gibson",
        "category": "Actor/Director",
        "real_name": "Mel Columcille Gerard Gibson"
    },
    {
        "name": "Clint Eastwood",
        "category": "Actor/Director",
        "real_name": "Clinton Eastwood Jr"
    },
    {
        "name": "Al Pacino",
        "category": "Actor",
        "real_name": "Alfredo James Pacino"
    },
    {
        "name": "Robert De Niro",
        "category": "Actor",
        "real_name": "Robert Anthony De Niro Jr"
    },
    {
        "name": "Jack Nicholson",
        "category": "Actor",
        "real_name": "John Joseph Nicholson"
    },
    {
        "name": "Dustin Hoffman",
        "category": "Actor",
        "real_name": "Dustin Lee Hoffman"
    },
    {
        "name": "Robin Williams",
        "category": "Actor/Comedian",
        "real_name": "Robin McLaurin Williams"
    },
    {
        "name": "Jim Carrey",
        "category": "Actor/Comedian",
        "real_name": "James Eugene Carrey"
    },
    {
        "name": "Eddie Murphy",
        "category": "Actor/Comedian",
        "real_name": "Edward Regan Murphy"
    },
    {
        "name": "Adam Sandler",
        "category": "Actor/Comedian",
        "real_name": "Adam Richard Sandler"
    },
    {
        "name": "Will Ferrell",
        "category": "Actor/Comedian",
        "real_name": "John William Ferrell"
    },
    {
        "name": "Ben Stiller",
        "category": "Actor/Comedian",
        "real_name": "Benjamin Edward Meara Stiller"
    },
    {
        "name": "Owen Wilson",
        "category": "Actor",
        "real_name": "Owen Cunningham Wilson"
    },
    {
        "name": "Vince Vaughn",
        "category": "Actor",
        "real_name": "Vincent Anthony Vaughn"
    },
    {
        "name": "Steve Carell",
        "category": "Actor/Comedian",
        "real_name": "Steven John Carell"
    },
    {
        "name": "Kevin Hart",
        "category": "Actor/Comedian",
        "real_name": "Kevin Darnell Hart"
    },
    {
        "name": "Dave Chappelle",
        "category": "Comedian",
        "real_name": "David Khari Webber Chappelle"
    },
    {
        "name": "Chris Rock",
        "category": "Comedian/Actor",
        "real_name": "Christopher Julius Rock III"
    },
    {
        "name": "Jerry Seinfeld",
        "category": "Comedian/Actor",
        "real_name": "Jerome Allen Seinfeld"
    },
    {
        "name": "Ellen Pompeo",
        "category": "Actress",
        "real_name": "Ellen Kathleen Pompeo"
    },
    {
        "name": "Megan Fox",
        "category": "Actress",
        "real_name": "Megan Denise Fox"
    },
    {
        "name": "Jennifer Lawrence",
        "category": "Actress",
        "real_name": "Jennifer Shrader Lawrence"
    },
    {
        "name": "Emma Watson",
        "category": "Actress",
        "real_name": "Emma Charlotte Duerre Watson"
    },
    {
        "name": "Emma Stone",
        "category": "Actress",
        "real_name": "Emily Jean Stone"
    },
    {
        "name": "Jessica Alba",
        "category": "Actress/Business",
        "real_name": "Jessica Marie Alba"
    },
    {
        "name": "Eva Longoria",
        "category": "Actress",
        "real_name": "Eva Jacqueline Longoria"
    },
    {
        "name": "Sofia Vergara",
        "category": "Actress",
        "real_name": "Sofia Margarita Vergara"
    },
    {
        "name": "Penelope Cruz",
        "category": "Actress",
        "real_name": "Penelope Cruz Sanchez"
    },
    {
        "name": "Salma Hayek",
        "category": "Actress/Producer",
        "real_name": "Salma Hayek Pinault"
    },
    {
        "name": "Cameron Diaz",
        "category": "Actress",
        "real_name": "Cameron Michelle Diaz"
    },
    {
        "name": "Drew Barrymore",
        "category": "Actress",
        "real_name": "Drew Blyth Barrymore"
    },
    {
        "name": "Winona Ryder",
        "category": "Actress",
        "real_name": "Winona Laura Horowitz"
    },
    {
        "name": "Hilary Duff",
        "category": "Actress/Singer",
        "real_name": "Hilary Erhard Duff"
    },
    {
        "name": "Lindsay Lohan",
        "category": "Actress",
        "real_name": "Lindsay Dee Lohan"
    },
    {
        "name": "Paris Hilton",
        "category": "TV Personality/Business",
        "real_name": "Paris Whitney Hilton"
    },
    {
        "name": "Taylor Swift",
        "category": "Singer",
        "real_name": "Taylor Alison Swift"
    },
    {
        "name": "Beyonce",
        "category": "Singer",
        "real_name": "Beyonce Giselle Knowles-Carter"
    },
    {
        "name": "Rihanna",
        "category": "Singer/Business",
        "real_name": "Robyn Rihanna Fenty"
    },
    {
        "name": "Ariana Grande",
        "category": "Singer",
        "real_name": "Ariana Grande-Butera"
    },
    {
        "name": "Selena Gomez",
        "category": "Singer/Actress",
        "real_name": "Selena Marie Gomez"
    },
    {
        "name": "Lady Gaga",
        "category": "Singer",
        "real_name": "Stefani Joanne Angelina Germanotta"
    },
    {
        "name": "Katy Perry",
        "category": "Singer",
        "real_name": "Katheryn Elizabeth Hudson"
    },
    {
        "name": "Justin Bieber",
        "category": "Singer",
        "real_name": "Justin Drew Bieber"
    },
    {
        "name": "Ed Sheeran",
        "category": "Singer",
        "real_name": "Edward Christopher Sheeran"
    },
    {
        "name": "Bruno Mars",
        "category": "Singer",
        "real_name": "Peter Gene Hernandez"
    },
    {
        "name": "The Weeknd",
        "category": "Singer",
        "real_name": "Abel Makkonen Tesfaye"
    },
    {
        "name": "Dua Lipa",
        "category": "Singer",
        "real_name": "Dua Lipa"
    },
    {
        "name": "Billie Eilish",
        "category": "Singer",
        "real_name": "Billie Eilish Pirate Baird O'Connell"
    },
    {
        "name": "Olivia Rodrigo",
        "category": "Singer",
        "real_name": "Olivia Isabel Rodrigo"
    },
    {
        "name": "Harry Styles",
        "category": "Singer",
        "real_name": "Harry Edward Styles"
    },
    {
        "name": "Shawn Mendes",
        "category": "Singer",
        "real_name": "Shawn Peter Raul Mendes"
    },
    {
        "name": "Camila Cabello",
        "category": "Singer",
        "real_name": "Karla Camila Cabello Estrabao"
    },
    {
        "name": "Miley Cyrus",
        "category": "Singer/Actress",
        "real_name": "Destiny Hope Cyrus"
    },
    {
        "name": "Demi Lovato",
        "category": "Singer/Actress",
        "real_name": "Demetria Devonne Lovato"
    },
    {
        "name": "Nick Jonas",
        "category": "Singer/Actor",
        "real_name": "Nicholas Jerry Jonas"
    },
    {
        "name": "Joe Jonas",
        "category": "Singer",
        "real_name": "Joseph Adam Jonas"
    },
    {
        "name": "Jonas Brothers",
        "category": "Music Group",
        "real_name": "Jonas Brothers"
    },
    {
        "name": "One Direction",
        "category": "Music Group",
        "real_name": "One Direction"
    },
    {
        "name": "Niall Horan",
        "category": "Singer",
        "real_name": "Niall James Horan"
    },
    {
        "name": "Liam Payne",
        "category": "Singer",
        "real_name": "Liam James Payne"
    },
    {
        "name": "Louis Tomlinson",
        "category": "Singer",
        "real_name": "Louis William Tomlinson"
    },
    {
        "name": "Zayn Malik",
        "category": "Singer",
        "real_name": "Zain Javadd Malik"
    },
    {
        "name": "Bad Bunny",
        "category": "Reggaeton",
        "real_name": "Benito Antonio Martinez Ocasio"
    },
    {
        "name": "J Balvin",
        "category": "Reggaeton",
        "real_name": "Jose Alvaro Osorio Balvin"
    },
    {
        "name": "Maluma",
        "category": "Reggaeton",
        "real_name": "Juan Luis Londono Arias"
    },
    {
        "name": "Ozuna",
        "category": "Reggaeton",
        "real_name": "Juan Carlos Ozuna Rosado"
    },
    {
        "name": "Daddy Yankee",
        "category": "Reggaeton",
        "real_name": "Ramon Luis Ayala Rodriguez"
    },
    {
        "name": "Shakira",
        "category": "Singer",
        "real_name": "Shakira Isabel Mebarak Ripoll"
    },
    {
        "name": "Jennifer Lopez",
        "category": "Singer/Actress",
        "real_name": "Jennifer Lynn Lopez"
    },
    {
        "name": "Madonna",
        "category": "Singer",
        "real_name": "Madonna Louise Ciccone"
    },
    {
        "name": "Mariah Carey",
        "category": "Singer",
        "real_name": "Mariah Carey"
    },
    {
        "name": "Whitney Houston",
        "category": "Singer",
        "real_name": "Whitney Elizabeth Houston"
    },
    {
        "name": "Celine Dion",
        "category": "Singer",
        "real_name": "Celine Marie Claudette Dion"
    },
    {
        "name": "Adele",
        "category": "Singer",
        "real_name": "Adele Laurie Blue Adkins"
    },
    {
        "name": "Sam Smith",
        "category": "Singer",
        "real_name": "Samuel Frederick Smith"
    },
    {
        "name": "Jay-Z",
        "category": "Rapper/Business",
        "real_name": "Shawn Corey Carter"
    },
    {
        "name": "Kanye West",
        "category": "Rapper/Designer",
        "real_name": "Ye"
    },
    {
        "name": "Drake",
        "category": "Rapper",
        "real_name": "Aubrey Drake Graham"
    },
    {
        "name": "Eminem",
        "category": "Rapper",
        "real_name": "Marshall Bruce Mathers III"
    },
    {
        "name": "Nicki Minaj",
        "category": "Rapper",
        "real_name": "Onika Tanya Maraj-Petty"
    },
    {
        "name": "Cardi B",
        "category": "Rapper",
        "real_name": "Belcalis Marlenis Almanzar"
    },
    {
        "name": "Post Malone",
        "category": "Rapper",
        "real_name": "Austin Richard Post"
    },
    {
        "name": "Lil Wayne",
        "category": "Rapper",
        "real_name": "Dwayne Michael Carter Jr"
    },
    {
        "name": "Lil Uzi Vert",
        "category": "Rapper",
        "real_name": "Symere Bysil Woods"
    },
    {
        "name": "Juice WRLD",
        "category": "Rapper",
        "real_name": "Jarad Higgins"
    },
    {
        "name": "XXXTentacion",
        "category": "Rapper",
        "real_name": "Jahseh Dwayne Ricardo Onfroy"
    },
    {
        "name": "Lil Baby",
        "category": "Rapper",
        "real_name": "Dominique Armani Jones"
    },
    {
        "name": "DaBaby",
        "category": "Rapper",
        "real_name": "Jonathan Lyndale Kirk"
    },
    {
        "name": "Roddy Ricch",
        "category": "Rapper",
        "real_name": "Rodrick Lavon Moore"
    },
    {
        "name": "Travis Scott",
        "category": "Rapper",
        "real_name": "Jacques Bermon Webster II"
    },
    {
        "name": "Future",
        "category": "Rapper",
        "real_name": "Nayvadius DeMun Wilburn"
    },
    {
        "name": "Young Thug",
        "category": "Rapper",
        "real_name": "Jeffery Lamar Williams"
    },
    {
        "name": "Gunna",
        "category": "Rapper",
        "real_name": "Sergio Giavanni Kitchens"
    },
    {
        "name": "Polo G",
        "category": "Rapper",
        "real_name": "Taurus Tremani Bartlett"
    },
    {
        "name": "NBA YoungBoy",
        "category": "Rapper",
        "real_name": "Kentrell DeSean Gaulden"
    },
    {
        "name": "Kendrick Lamar",
        "category": "Rapper",
        "real_name": "Kendrick Lamar Duckworth"
    },
    {
        "name": "J Cole",
        "category": "Rapper",
        "real_name": "Jermaine Lamarr Cole"
    },
    {
        "name": "Big Sean",
        "category": "Rapper",
        "real_name": "Sean Michael Leonard Anderson"
    },
    {
        "name": "Wale",
        "category": "Rapper",
        "real_name": "Olubowale Victor Akintimehin"
    },
    {
        "name": "Rick Ross",
        "category": "Rapper",
        "real_name": "William Leonard Roberts II"
    },
    {
        "name": "Meek Mill",
        "category": "Rapper",
        "real_name": "Robert Rahmeek Williams"
    },
    {
        "name": "2 Chainz",
        "category": "Rapper",
        "real_name": "Tauheed Epps"
    },
    {
        "name": "Ludacris",
        "category": "Rapper/Actor",
        "real_name": "Christopher Brian Bridges"
    },
    {
        "name": "Snoop Dogg",
        "category": "Rapper/Media",
        "real_name": "Calvin Cordozar Broadus Jr"
    },
    {
        "name": "Ice Cube",
        "category": "Rapper/Actor",
        "real_name": "O'Shea Jackson"
    },
    {
        "name": "Dr Dre",
        "category": "Rapper/Producer",
        "real_name": "Andre Romelle Young"
    },
    {
        "name": "50 Cent",
        "category": "Rapper/Business",
        "real_name": "Curtis James Jackson III"
    },
    {
        "name": "Diddy",
        "category": "Rapper/Business",
        "real_name": "Sean John Combs"
    },
    {
        "name": "Missy Elliott",
        "category": "Rapper",
        "real_name": "Melissa Arnette Elliott"
    },
    {
        "name": "Eve",
        "category": "Rapper/Actress",
        "real_name": "Eve Jihan Jeffers-Cooper"
    },
    {
        "name": "Busta Rhymes",
        "category": "Rapper",
        "real_name": "Trevor George Smith Jr"
    },
    {
        "name": "Nas",
        "category": "Rapper",
        "real_name": "Nasir Bin Olu Dara Jones"
    },
    {
        "name": "Rakim",
        "category": "Rapper",
        "real_name": "William Michael Griffin Jr"
    },
    {
        "name": "LL Cool J",
        "category": "Rapper/Actor",
        "real_name": "James Todd Smith"
    },
    {
        "name": "Run DMC",
        "category": "Rap Group",
        "real_name": "Joseph Simmons and Darryl McDaniels"
    },
    {
        "name": "Cristiano Ronaldo",
        "category": "Footballer",
        "real_name": "Cristiano Ronaldo dos Santos Aveiro"
    },
    {
        "name": "Lionel Messi",
        "category": "Footballer",
        "real_name": "Lionel Andres Messi Cuccittini"
    },
    {
        "name": "Neymar Jr",
        "category": "Footballer",
        "real_name": "Neymar da Silva Santos Junior"
    },
    {
        "name": "Kylian Mbappe",
        "category": "Footballer",
        "real_name": "Kylian Mbappe Lottin"
    },
    {
        "name": "Erling Haaland",
        "category": "Footballer",
        "real_name": "Erling Braut Haaland"
    },
    {
        "name": "Vinicius Junior",
        "category": "Footballer",
        "real_name": "Vinicius Jose Paiva Oliveira Junior"
    },
    {
        "name": "Mohamed Salah",
        "category": "Footballer",
        "real_name": "Mohamed Salah Ghaly"
    },
    {
        "name": "Kevin De Bruyne",
        "category": "Footballer",
        "real_name": "Kevin De Bruyne"
    },
    {
        "name": "Luka Modric",
        "category": "Footballer",
        "real_name": "Luka Modric"
    },
    {
        "name": "Robert Lewandowski",
        "category": "Footballer",
        "real_name": "Robert Lewandowski"
    },
    {
        "name": "Harry Kane",
        "category": "Footballer",
        "real_name": "Harry Edward Kane"
    },
    {
        "name": "Virgil van Dijk",
        "category": "Footballer",
        "real_name": "Virgil van Dijk"
    },
    {
        "name": "Marcus Rashford",
        "category": "Footballer",
        "real_name": "Marcus Rashford"
    },
    {
        "name": "Jude Bellingham",
        "category": "Footballer",
        "real_name": "Jude Victor William Bellingham"
    },
    {
        "name": "Bukayo Saka",
        "category": "Footballer",
        "real_name": "Bukayo Ayoyinka Saka"
    },
    {
        "name": "Phil Foden",
        "category": "Footballer",
        "real_name": "Philip Walter Foden"
    },
    {
        "name": "Jack Grealish",
        "category": "Footballer",
        "real_name": "Jack Peter Grealish"
    },
    {
        "name": "Trent Alexander-Arnold",
        "category": "Footballer",
        "real_name": "Trent Alexander-Arnold"
    },
    {
        "name": "David Beckham",
        "category": "Footballer/Business",
        "real_name": "David Robert Joseph Beckham"
    },
    {
        "name": "Zinedine Zidane",
        "category": "Footballer/Manager",
        "real_name": "Zinedine Yazid Zidane"
    },
    {
        "name": "Ronaldinho",
        "category": "Footballer",
        "real_name": "Ronaldo de Assis Moreira"
    },
    {
        "name": "Pele",
        "category": "Footballer",
        "real_name": "Edson Arantes do Nascimento"
    },
    {
        "name": "Zlatan Ibrahimovic",
        "category": "Footballer",
        "real_name": "Zlatan Ibrahimovic"
    },
    {
        "name": "Wayne Rooney",
        "category": "Footballer",
        "real_name": "Wayne Mark Rooney"
    },
    {
        "name": "Frank Lampard",
        "category": "Footballer/Manager",
        "real_name": "Frank James Lampard"
    },
    {
        "name": "Steven Gerrard",
        "category": "Footballer/Manager",
        "real_name": "Steven George Gerrard"
    },
    {
        "name": "Thierry Henry",
        "category": "Footballer",
        "real_name": "Thierry Daniel Henry"
    },
    {
        "name": "Didier Drogba",
        "category": "Footballer",
        "real_name": "Didier Yves Drogba Tebily"
    },
    {
        "name": "Samuel Eto'o",
        "category": "Footballer",
        "real_name": "Samuel Eto'o Fils"
    },
    {
        "name": "LeBron James",
        "category": "Basketball",
        "real_name": "LeBron Raymone James"
    },
    {
        "name": "Stephen Curry",
        "category": "Basketball",
        "real_name": "Wardell Stephen Curry II"
    },
    {
        "name": "Kevin Durant",
        "category": "Basketball",
        "real_name": "Kevin Wayne Durant"
    },
    {
        "name": "Giannis Antetokounmpo",
        "category": "Basketball",
        "real_name": "Giannis Sina Ugo Antetokounmpo"
    },
    {
        "name": "Kobe Bryant",
        "category": "Basketball",
        "real_name": "Kobe Bean Bryant"
    },
    {
        "name": "Michael Jordan",
        "category": "Basketball/Business",
        "real_name": "Michael Jeffrey Jordan"
    },
    {
        "name": "Shaquille O'Neal",
        "category": "Basketball/Media",
        "real_name": "Shaquille Rashaun O'Neal"
    },
    {
        "name": "Magic Johnson",
        "category": "Basketball/Business",
        "real_name": "Earvin Johnson Jr"
    },
    {
        "name": "Charles Barkley",
        "category": "Basketball/Media",
        "real_name": "Charles Wade Barkley"
    },
    {
        "name": "Scottie Pippen",
        "category": "Basketball",
        "real_name": "Scottie Maurice Pippen"
    },
    {
        "name": "Dennis Rodman",
        "category": "Basketball",
        "real_name": "Dennis Keith Rodman"
    },
    {
        "name": "Tiger Woods",
        "category": "Golf",
        "real_name": "Eldrick Tont Woods"
    },
    {
        "name": "Rory McIlroy",
        "category": "Golf",
        "real_name": "Rory McIlroy"
    },
    {
        "name": "Phil Mickelson",
        "category": "Golf",
        "real_name": "Philip Alfred Mickelson"
    },
    {
        "name": "Roger Federer",
        "category": "Tennis",
        "real_name": "Roger Federer"
    },
    {
        "name": "Serena Williams",
        "category": "Tennis",
        "real_name": "Serena Jameka Williams"
    },
    {
        "name": "Novak Djokovic",
        "category": "Tennis",
        "real_name": "Novak Djokovic"
    },
    {
        "name": "Rafael Nadal",
        "category": "Tennis",
        "real_name": "Rafael Nadal Parera"
    },
    {
        "name": "Carlos Alcaraz",
        "category": "Tennis",
        "real_name": "Carlos Alcaraz Garfia"
    },
    {
        "name": "Iga Swiatek",
        "category": "Tennis",
        "real_name": "Iga Swiatek"
    },
    {
        "name": "Naomi Osaka",
        "category": "Tennis",
        "real_name": "Naomi Osaka"
    },
    {
        "name": "Conor McGregor",
        "category": "MMA Fighter",
        "real_name": "Conor Anthony McGregor"
    },
    {
        "name": "Floyd Mayweather",
        "category": "Boxer",
        "real_name": "Floyd Joy Mayweather Jr"
    },
    {
        "name": "Tyson Fury",
        "category": "Boxer",
        "real_name": "Tyson Luke Fury"
    },
    {
        "name": "Canelo Alvarez",
        "category": "Boxer",
        "real_name": "Santos Saul Alvarez Barragan"
    },
    {
        "name": "Anthony Joshua",
        "category": "Boxer",
        "real_name": "Anthony Oluwafemi Olaseni Joshua"
    },
    {
        "name": "Oleksandr Usyk",
        "category": "Boxer",
        "real_name": "Oleksandr Oleksandrovych Usyk"
    },
    {
        "name": "Ryan Garcia",
        "category": "Boxer",
        "real_name": "Ryan Garcia"
    },
    {
        "name": "Gervonta Davis",
        "category": "Boxer",
        "real_name": "Gervonta Jamal Davis"
    },
    {
        "name": "Israel Adesanya",
        "category": "MMA Fighter",
        "real_name": "Israel Adesanya"
    },
    {
        "name": "Jon Jones",
        "category": "MMA Fighter",
        "real_name": "Jonathan Dwight Jones"
    },
    {
        "name": "Khabib Nurmagomedov",
        "category": "MMA Fighter",
        "real_name": "Khabib Abdulmanapovich Nurmagomedov"
    },
    {
        "name": "Francis Ngannou",
        "category": "MMA Fighter",
        "real_name": "Francis Ngannou"
    },
    {
        "name": "Virat Kohli",
        "category": "Cricket",
        "real_name": "Virat Kohli"
    },
    {
        "name": "MS Dhoni",
        "category": "Cricket",
        "real_name": "Mahendra Singh Dhoni"
    },
    {
        "name": "Sachin Tendulkar",
        "category": "Cricket",
        "real_name": "Sachin Ramesh Tendulkar"
    },
    {
        "name": "Rohit Sharma",
        "category": "Cricket",
        "real_name": "Rohit Gurunath Sharma"
    },
    {
        "name": "Babar Azam",
        "category": "Cricket",
        "real_name": "Babar Azam"
    },
    {
        "name": "Shaheen Afridi",
        "category": "Cricket",
        "real_name": "Shaheen Shah Afridi"
    },
    {
        "name": "Ben Stokes",
        "category": "Cricket",
        "real_name": "Ben Stokes"
    },
    {
        "name": "Joe Root",
        "category": "Cricket",
        "real_name": "Joseph Edward Root"
    },
    {
        "name": "Pat Cummins",
        "category": "Cricket",
        "real_name": "Patrick James Cummins"
    },
    {
        "name": "Steve Smith",
        "category": "Cricket",
        "real_name": "Steven Peter Devereux Smith"
    },
    {
        "name": "David Warner",
        "category": "Cricket",
        "real_name": "David Andrew Warner"
    },
    {
        "name": "Kane Williamson",
        "category": "Cricket",
        "real_name": "Kane Stuart Williamson"
    },
    {
        "name": "Usain Bolt",
        "category": "Sprinter",
        "real_name": "Usain St Leo Bolt"
    },
    {
        "name": "Carl Lewis",
        "category": "Sprinter",
        "real_name": "Frederick Carlton Lewis"
    },
    {
        "name": "Michael Phelps",
        "category": "Swimmer",
        "real_name": "Michael Fred Phelps II"
    },
    {
        "name": "Simone Biles",
        "category": "Gymnast",
        "real_name": "Simone Arianne Biles"
    },
    {
        "name": "Nadia Comaneci",
        "category": "Gymnast",
        "real_name": "Nadia Elena Comaneci"
    },
    {
        "name": "Lewis Hamilton",
        "category": "Formula 1",
        "real_name": "Lewis Carl Davidson Hamilton"
    },
    {
        "name": "Max Verstappen",
        "category": "Formula 1",
        "real_name": "Max Emilian Verstappen"
    },
    {
        "name": "Sebastian Vettel",
        "category": "Formula 1",
        "real_name": "Sebastian Vettel"
    },
    {
        "name": "Fernando Alonso",
        "category": "Formula 1",
        "real_name": "Fernando Alonso Diaz"
    },
    {
        "name": "Tom Brady",
        "category": "NFL",
        "real_name": "Thomas Edward Patrick Brady Jr"
    },
    {
        "name": "Patrick Mahomes",
        "category": "NFL",
        "real_name": "Patrick Lavon Mahomes II"
    },
    {
        "name": "Aaron Rodgers",
        "category": "NFL",
        "real_name": "Aaron Charles Rodgers"
    },
    {
        "name": "Peyton Manning",
        "category": "NFL",
        "real_name": "Peyton Williams Manning"
    },
    {
        "name": "Elon Musk",
        "category": "Billionaire/Tech",
        "real_name": "Elon Reeve Musk"
    },
    {
        "name": "Jeff Bezos",
        "category": "Billionaire/Tech",
        "real_name": "Jeffrey Preston Bezos"
    },
    {
        "name": "Bill Gates",
        "category": "Billionaire/Tech",
        "real_name": "William Henry Gates III"
    },
    {
        "name": "Mark Zuckerberg",
        "category": "Billionaire/Tech",
        "real_name": "Mark Elliot Zuckerberg"
    },
    {
        "name": "Warren Buffett",
        "category": "Billionaire/Investor",
        "real_name": "Warren Edward Buffett"
    },
    {
        "name": "Larry Ellison",
        "category": "Billionaire/Tech",
        "real_name": "Lawrence Joseph Ellison"
    },
    {
        "name": "Larry Page",
        "category": "Billionaire/Tech",
        "real_name": "Lawrence Edward Page"
    },
    {
        "name": "Sergey Brin",
        "category": "Billionaire/Tech",
        "real_name": "Sergey Mikhaylovich Brin"
    },
    {
        "name": "Steve Ballmer",
        "category": "Billionaire/Tech",
        "real_name": "Steven Anthony Ballmer"
    },
    {
        "name": "Bernard Arnault",
        "category": "Billionaire/Luxury",
        "real_name": "Bernard Jean Etienne Arnault"
    },
    {
        "name": "Mukesh Ambani",
        "category": "Billionaire",
        "real_name": "Mukesh Dhirubhai Ambani"
    },
    {
        "name": "Gautam Adani",
        "category": "Billionaire",
        "real_name": "Gautam Shantilal Adani"
    },
    {
        "name": "Carlos Slim",
        "category": "Billionaire",
        "real_name": "Carlos Slim Helu"
    },
    {
        "name": "Jack Ma",
        "category": "Billionaire/Tech",
        "real_name": "Ma Yun"
    },
    {
        "name": "Michael Bloomberg",
        "category": "Billionaire/Politician",
        "real_name": "Michael Rubens Bloomberg"
    },
    {
        "name": "George Soros",
        "category": "Billionaire/Investor",
        "real_name": "Gyorgy Schwartz"
    },
    {
        "name": "Koch Brothers",
        "category": "Billionaire/Business",
        "real_name": "Charles and David Koch"
    },
    {
        "name": "Rupert Murdoch",
        "category": "Billionaire/Media",
        "real_name": "Keith Rupert Murdoch"
    },
    {
        "name": "Ken Griffin",
        "category": "Billionaire/Finance",
        "real_name": "Kenneth Cordele Griffin"
    },
    {
        "name": "Ray Dalio",
        "category": "Billionaire/Investor",
        "real_name": "Raymond Thomas Dalio"
    },
    {
        "name": "Chamath Palihapitiya",
        "category": "Investor/VC",
        "real_name": "Chamath Palihapitiya"
    },
    {
        "name": "Peter Thiel",
        "category": "Billionaire/VC",
        "real_name": "Peter Andreas Thiel"
    },
    {
        "name": "Marc Andreessen",
        "category": "VC/Investor",
        "real_name": "Marc Lowell Andreessen"
    },
    {
        "name": "Sam Altman",
        "category": "Tech CEO",
        "real_name": "Samuel Harris Altman"
    },
    {
        "name": "Jensen Huang",
        "category": "Tech CEO",
        "real_name": "Jen-Hsun Huang"
    },
    {
        "name": "Tim Cook",
        "category": "Tech CEO",
        "real_name": "Timothy Donald Cook"
    },
    {
        "name": "Satya Nadella",
        "category": "Tech CEO",
        "real_name": "Satya Narayana Nadella"
    },
    {
        "name": "Sundar Pichai",
        "category": "Tech CEO",
        "real_name": "Pichai Sundararajan"
    },
    {
        "name": "Reed Hastings",
        "category": "Tech CEO",
        "real_name": "Wilmot Reed Hastings Jr"
    },
    {
        "name": "Bob Iger",
        "category": "Media CEO",
        "real_name": "Robert Allen Iger"
    },
    {
        "name": "Oprah Winfrey",
        "category": "Media/Business",
        "real_name": "Oprah Gail Winfrey"
    },
    {
        "name": "Martha Stewart",
        "category": "Business/Media",
        "real_name": "Martha Helen Kostyra"
    },
    {
        "name": "Shah Rukh Khan",
        "category": "Bollywood Actor",
        "real_name": "Shah Rukh Khan"
    },
    {
        "name": "Salman Khan",
        "category": "Bollywood Actor",
        "real_name": "Abdul Rashid Salim Salman Khan"
    },
    {
        "name": "Amitabh Bachchan",
        "category": "Bollywood Actor",
        "real_name": "Amitabh Harivansh Rai Srivastava"
    },
    {
        "name": "Aamir Khan",
        "category": "Bollywood Actor",
        "real_name": "Mohammed Aamir Hussain Khan"
    },
    {
        "name": "Hrithik Roshan",
        "category": "Bollywood Actor",
        "real_name": "Hrithik Roshan"
    },
    {
        "name": "Ranbir Kapoor",
        "category": "Bollywood Actor",
        "real_name": "Ranbir Raj Kapoor"
    },
    {
        "name": "Ranveer Singh",
        "category": "Bollywood Actor",
        "real_name": "Ranveer Singh Bhavnani"
    },
    {
        "name": "Akshay Kumar",
        "category": "Bollywood Actor",
        "real_name": "Rajiv Hari Om Bhatia"
    },
    {
        "name": "Tiger Shroff",
        "category": "Bollywood Actor",
        "real_name": "Jai Hemant Shroff"
    },
    {
        "name": "Varun Dhawan",
        "category": "Bollywood Actor",
        "real_name": "Varun Dhawan"
    },
    {
        "name": "Siddharth Malhotra",
        "category": "Bollywood Actor",
        "real_name": "Sidharth Malhotra"
    },
    {
        "name": "Deepika Padukone",
        "category": "Bollywood Actress",
        "real_name": "Deepika Padukone"
    },
    {
        "name": "Priyanka Chopra",
        "category": "Bollywood Actress",
        "real_name": "Priyanka Chopra Jonas"
    },
    {
        "name": "Kareena Kapoor",
        "category": "Bollywood Actress",
        "real_name": "Kareena Kapoor Khan"
    },
    {
        "name": "Katrina Kaif",
        "category": "Bollywood Actress",
        "real_name": "Katrina Kaif"
    },
    {
        "name": "Alia Bhatt",
        "category": "Bollywood Actress",
        "real_name": "Alia Bhatt"
    },
    {
        "name": "Anushka Sharma",
        "category": "Bollywood Actress",
        "real_name": "Anushka Sharma"
    },
    {
        "name": "Aishwarya Rai",
        "category": "Bollywood Actress",
        "real_name": "Aishwarya Rai Bachchan"
    },
    {
        "name": "Madhuri Dixit",
        "category": "Bollywood Actress",
        "real_name": "Madhuri Dixit Nene"
    },
    {
        "name": "Kajol",
        "category": "Bollywood Actress",
        "real_name": "Kajol Devgn"
    },
    {
        "name": "Vidya Balan",
        "category": "Bollywood Actress",
        "real_name": "Vidya Balan"
    },
    {
        "name": "Taapsee Pannu",
        "category": "Bollywood Actress",
        "real_name": "Taapsee Pannu"
    },
    {
        "name": "AR Rahman",
        "category": "Music Composer",
        "real_name": "Allah Rakha Rahman"
    },
    {
        "name": "Pritam Chakraborty",
        "category": "Music Composer",
        "real_name": "Pritam Chakraborty"
    },
    {
        "name": "Vishal-Shekhar",
        "category": "Music Composers",
        "real_name": "Vishal Dadlani and Shekhar Ravjiani"
    },
    {
        "name": "Arijit Singh",
        "category": "Singer",
        "real_name": "Arijit Singh"
    },
    {
        "name": "Sonu Nigam",
        "category": "Singer",
        "real_name": "Sonu Nigam"
    },
    {
        "name": "Kumar Sanu",
        "category": "Singer",
        "real_name": "Kedarnath Bhattacharya"
    },
    {
        "name": "Lata Mangeshkar",
        "category": "Singer",
        "real_name": "Lata Deenanath Mangeshkar"
    },
    {
        "name": "Shreya Ghoshal",
        "category": "Singer",
        "real_name": "Shreya Ghoshal"
    },
    {
        "name": "Gordon Ramsay",
        "category": "Chef/TV Host",
        "real_name": "Gordon James Ramsay"
    },
    {
        "name": "Jamie Oliver",
        "category": "Chef/TV Host",
        "real_name": "James Trevor Oliver"
    },
    {
        "name": "Guy Fieri",
        "category": "Chef/TV Host",
        "real_name": "Guy Ramsay Fieri"
    },
    {
        "name": "Rachael Ray",
        "category": "Chef/TV Host",
        "real_name": "Rachael Domenica Ray"
    },
    {
        "name": "Ryan Seacrest",
        "category": "TV Host",
        "real_name": "Ryan John Seacrest"
    },
    {
        "name": "Jimmy Fallon",
        "category": "TV Host",
        "real_name": "James Thomas Fallon"
    },
    {
        "name": "Jimmy Kimmel",
        "category": "TV Host",
        "real_name": "James Christian Kimmel"
    },
    {
        "name": "Stephen Colbert",
        "category": "TV Host",
        "real_name": "Stephen Tyrone Colbert"
    },
    {
        "name": "John Oliver",
        "category": "TV Host/Comedian",
        "real_name": "John William Oliver"
    },
    {
        "name": "Trevor Noah",
        "category": "TV Host/Comedian",
        "real_name": "Trevor Noah"
    },
    {
        "name": "Conan O'Brien",
        "category": "TV Host/Comedian",
        "real_name": "Conan Christopher O'Brien"
    },
    {
        "name": "Jay Leno",
        "category": "TV Host/Comedian",
        "real_name": "James Douglas Muir Leno"
    },
    {
        "name": "David Letterman",
        "category": "TV Host",
        "real_name": "David Michael Letterman"
    },
    {
        "name": "Howard Stern",
        "category": "Radio/TV Host",
        "real_name": "Howard Allan Stern"
    },
    {
        "name": "Joe Rogan",
        "category": "Podcaster/Comedian",
        "real_name": "Joseph James Rogan"
    },
    {
        "name": "Tucker Carlson",
        "category": "TV Anchor",
        "real_name": "Tucker Swanson McNear Carlson"
    },
    {
        "name": "Anderson Cooper",
        "category": "TV Journalist",
        "real_name": "Anderson Hays Cooper"
    },
    {
        "name": "Wolf Blitzer",
        "category": "TV Journalist",
        "real_name": "Wolf Isaac Blitzer"
    },
    {
        "name": "Megyn Kelly",
        "category": "TV Anchor",
        "real_name": "Megyn Marie Kelly"
    },
    {
        "name": "Gigi Hadid",
        "category": "Model",
        "real_name": "Jelena Noura Hadid"
    },
    {
        "name": "Bella Hadid",
        "category": "Model",
        "real_name": "Isabella Khair Hadid"
    },
    {
        "name": "Cara Delevingne",
        "category": "Model/Actress",
        "real_name": "Cara Jocelyn Delevingne"
    },
    {
        "name": "Adriana Lima",
        "category": "Model",
        "real_name": "Adriana Lima"
    },
    {
        "name": "Alessandra Ambrosio",
        "category": "Model",
        "real_name": "Alessandra Corine Ambrosio"
    },
    {
        "name": "Candice Swanepoel",
        "category": "Model",
        "real_name": "Candice Susan Swanepoel"
    },
    {
        "name": "Karlie Kloss",
        "category": "Model/Business",
        "real_name": "Karlie Elizabeth Kloss"
    },
    {
        "name": "Miranda Kerr",
        "category": "Model/Business",
        "real_name": "Miranda May Kerr"
    },
    {
        "name": "Naomi Campbell",
        "category": "Model",
        "real_name": "Naomi Elaine Campbell"
    },
    {
        "name": "Tyra Banks",
        "category": "Model/TV Host",
        "real_name": "Tyra Lynne Banks"
    },
    {
        "name": "Kate Moss",
        "category": "Model",
        "real_name": "Katherine Ann Moss"
    },
    {
        "name": "Cindy Crawford",
        "category": "Model/Business",
        "real_name": "Cynthia Ann Crawford"
    },
    {
        "name": "Heidi Klum",
        "category": "Model/TV Host",
        "real_name": "Heidi Samuel"
    },
    {
        "name": "Elle Macpherson",
        "category": "Model/Business",
        "real_name": "Eleanor Nancy Gow"
    },
    {
        "name": "Huda Kattan",
        "category": "Beauty Influencer",
        "real_name": "Huda Kattan"
    },
    {
        "name": "Chiara Ferragni",
        "category": "Fashion Influencer",
        "real_name": "Chiara Ferragni"
    },
    {
        "name": "Kayla Itsines",
        "category": "Fitness Influencer",
        "real_name": "Kayla Itsines"
    },
    {
        "name": "Donald Trump",
        "category": "Politician/Business",
        "real_name": "Donald John Trump"
    },
    {
        "name": "Barack Obama",
        "category": "Politician/Author",
        "real_name": "Barack Hussein Obama II"
    },
    {
        "name": "Hillary Clinton",
        "category": "Politician",
        "real_name": "Hillary Diane Rodham Clinton"
    },
    {
        "name": "Bill Clinton",
        "category": "Politician",
        "real_name": "William Jefferson Clinton"
    },
    {
        "name": "George W Bush",
        "category": "Politician",
        "real_name": "George Walker Bush"
    },
    {
        "name": "George HW Bush",
        "category": "Politician",
        "real_name": "George Herbert Walker Bush"
    },
    {
        "name": "Joe Biden",
        "category": "Politician",
        "real_name": "Joseph Robinette Biden Jr"
    },
    {
        "name": "Kamala Harris",
        "category": "Politician",
        "real_name": "Kamala Devi Harris"
    },
    {
        "name": "Bernie Sanders",
        "category": "Politician",
        "real_name": "Bernard Sanders"
    },
    {
        "name": "AOC",
        "category": "Politician",
        "real_name": "Alexandria Ocasio-Cortez"
    },
    {
        "name": "Nancy Pelosi",
        "category": "Politician",
        "real_name": "Nancy Patricia D'Alesandro Pelosi"
    },
    {
        "name": "Mitt Romney",
        "category": "Politician/Business",
        "real_name": "Willard Mitt Romney"
    },
    {
        "name": "Boris Johnson",
        "category": "Politician",
        "real_name": "Alexander Boris de Pfeffel Johnson"
    },
    {
        "name": "Tony Blair",
        "category": "Politician",
        "real_name": "Anthony Charles Lynton Blair"
    },
    {
        "name": "Margaret Thatcher",
        "category": "Politician",
        "real_name": "Margaret Hilda Roberts"
    },
    {
        "name": "Vladimir Putin",
        "category": "Politician",
        "real_name": "Vladimir Vladimirovich Putin"
    },
    {
        "name": "Narendra Modi",
        "category": "Politician",
        "real_name": "Narendra Damodardas Modi"
    },
    {
        "name": "Imran Khan",
        "category": "Politician/Cricket",
        "real_name": "Imran Ahmed Khan Niazi"
    },
    {
        "name": "Justin Trudeau",
        "category": "Politician",
        "real_name": "Justin Pierre James Trudeau"
    },
    {
        "name": "Emmanuel Macron",
        "category": "Politician",
        "real_name": "Emmanuel Jean-Michel Macron"
    },
    {
        "name": "King Charles III",
        "category": "Royal",
        "real_name": "Charles Philip Arthur George"
    },
    {
        "name": "Prince William",
        "category": "Royal",
        "real_name": "William Arthur Philip Louis"
    },
    {
        "name": "Kate Middleton",
        "category": "Royal",
        "real_name": "Catherine Elizabeth Middleton"
    },
    {
        "name": "Prince Harry",
        "category": "Royal",
        "real_name": "Henry Charles Albert David"
    },
    {
        "name": "Meghan Markle",
        "category": "Royal/Actress",
        "real_name": "Rachel Meghan Markle"
    },
    {
        "name": "Queen Elizabeth II",
        "category": "Royal",
        "real_name": "Elizabeth Alexandra Mary Windsor"
    },
    {
        "name": "Princess Diana",
        "category": "Royal",
        "real_name": "Diana Frances Spencer"
    },
    {
        "name": "BTS",
        "category": "K-Pop Group",
        "real_name": "BTS"
    },
    {
        "name": "Blackpink",
        "category": "K-Pop Group",
        "real_name": "Blackpink"
    },
    {
        "name": "Lisa Blackpink",
        "category": "K-Pop Artist",
        "real_name": "Lalisa Manobal"
    },
    {
        "name": "Jennie Blackpink",
        "category": "K-Pop Artist",
        "real_name": "Kim Jennie"
    },
    {
        "name": "Rose Blackpink",
        "category": "K-Pop Artist",
        "real_name": "Park Chaeyoung"
    },
    {
        "name": "Jisoo Blackpink",
        "category": "K-Pop Artist",
        "real_name": "Kim Jisoo"
    },
    {
        "name": "BTS Jungkook",
        "category": "K-Pop Artist",
        "real_name": "Jeon Jungkook"
    },
    {
        "name": "BTS V",
        "category": "K-Pop Artist",
        "real_name": "Kim Taehyung"
    },
    {
        "name": "BTS Jin",
        "category": "K-Pop Artist",
        "real_name": "Kim Seokjin"
    },
    {
        "name": "BTS RM",
        "category": "K-Pop Artist",
        "real_name": "Kim Namjoon"
    },
    {
        "name": "BTS Suga",
        "category": "K-Pop Artist",
        "real_name": "Min Yoongi"
    },
    {
        "name": "BTS J-Hope",
        "category": "K-Pop Artist",
        "real_name": "Jung Hoseok"
    },
    {
        "name": "BTS Jimin",
        "category": "K-Pop Artist",
        "real_name": "Park Jimin"
    },
    {
        "name": "PSY",
        "category": "K-Pop Artist",
        "real_name": "Park Jae-sang"
    },
    {
        "name": "EXO",
        "category": "K-Pop Group",
        "real_name": "EXO"
    },
    {
        "name": "Twice",
        "category": "K-Pop Group",
        "real_name": "Twice"
    },
    {
        "name": "Stray Kids",
        "category": "K-Pop Group",
        "real_name": "Stray Kids"
    },
    {
        "name": "NewJeans",
        "category": "K-Pop Group",
        "real_name": "NewJeans"
    },
    {
        "name": "aespa",
        "category": "K-Pop Group",
        "real_name": "aespa"
    },
    {
        "name": "Shohei Ohtani",
        "category": "Baseball",
        "real_name": "Shohei Ohtani"
    },
    {
        "name": "Mike Trout",
        "category": "Baseball",
        "real_name": "Michael Nelson Trout"
    },
    {
        "name": "Bryce Harper",
        "category": "Baseball",
        "real_name": "Bryce Aron Max Harper"
    },
    {
        "name": "Cody Bellinger",
        "category": "Baseball",
        "real_name": "Cody James Bellinger"
    },
    {
        "name": "LeBron James Jr",
        "category": "Basketball",
        "real_name": "Bronny James"
    },
    {
        "name": "Zion Williamson",
        "category": "Basketball",
        "real_name": "Zion Williamson"
    },
    {
        "name": "Ja Morant",
        "category": "Basketball",
        "real_name": "Temetrius Jamel Morant"
    },
    {
        "name": "Luka Doncic",
        "category": "Basketball",
        "real_name": "Luka Doncic"
    },
    {
        "name": "Devin Booker",
        "category": "Basketball",
        "real_name": "Devin Armani Booker"
    },
    {
        "name": "Jayson Tatum",
        "category": "Basketball",
        "real_name": "Jayson Christopher Tatum"
    },
    {
        "name": "Joel Embiid",
        "category": "Basketball",
        "real_name": "Joel Hans Embiid"
    },
    {
        "name": "Nikola Jokic",
        "category": "Basketball",
        "real_name": "Nikola Jokic"
    },
    {
        "name": "Victor Wembanyama",
        "category": "Basketball",
        "real_name": "Victor Wembanyama"
    },
    {
        "name": "Lionel Messi Jr",
        "category": "Football",
        "real_name": "Thiago Messi"
    },
    {
        "name": "Kylian Mbappe Jr",
        "category": "Football",
        "real_name": "Kylian Mbappe"
    },
    {
        "name": "Pedri",
        "category": "Footballer",
        "real_name": "Pedro Gonzalez Lopez"
    },
    {
        "name": "Gavi",
        "category": "Footballer",
        "real_name": "Pablo Martin Paez Gavira"
    },
    {
        "name": "Aitana Bonmati",
        "category": "Footballer",
        "real_name": "Aitana Bonmati Conca"
    },
    {
        "name": "Sam Kerr",
        "category": "Footballer",
        "real_name": "Samantha May Kerr"
    },
    {
        "name": "Alex Morgan",
        "category": "Footballer",
        "real_name": "Alexandra Patricia Morgan Carrasco"
    },
    {
        "name": "Megan Rapinoe",
        "category": "Footballer",
        "real_name": "Megan Anna Rapinoe"
    },
    {
        "name": "Caitlin Clark",
        "category": "Basketball",
        "real_name": "Caitlin Clark"
    },
    {
        "name": "Angel Reese",
        "category": "Basketball",
        "real_name": "Angel Reese"
    },
    {
        "name": "Brock Purdy",
        "category": "NFL",
        "real_name": "Brock Purdy"
    },
    {
        "name": "Lamar Jackson",
        "category": "NFL",
        "real_name": "Lamar Demeatrice Jackson Jr"
    },
    {
        "name": "Josh Allen",
        "category": "NFL",
        "real_name": "Joshua Patrick Allen"
    },
    {
        "name": "Jalen Hurts",
        "category": "NFL",
        "real_name": "Jalen Alexander Hurts"
    },
    {
        "name": "Travis Kelce",
        "category": "NFL",
        "real_name": "Travis Michael Kelce"
    },
    {
        "name": "Andrew Huberman",
        "category": "Podcaster/Scientist",
        "real_name": "Andrew David Huberman"
    },
    {
        "name": "Lex Fridman",
        "category": "Podcaster/AI Researcher",
        "real_name": "Alexei Fridman"
    },
    {
        "name": "Tim Ferriss",
        "category": "Author/Podcaster",
        "real_name": "Timothy Ferriss"
    },
    {
        "name": "Gary Vaynerchuk",
        "category": "Business/Influencer",
        "real_name": "Gary Vaynerchuk"
    },
    {
        "name": "Tony Robbins",
        "category": "Motivational Speaker",
        "real_name": "Anthony Jay Robbins"
    },
    {
        "name": "Grant Cardone",
        "category": "Business Author",
        "real_name": "Grant Cardone"
    },
    {
        "name": "Robert Kiyosaki",
        "category": "Author/Business",
        "real_name": "Robert Toru Kiyosaki"
    },
    {
        "name": "Dave Ramsey",
        "category": "Finance Author",
        "real_name": "David Lawrence Ramsey III"
    },
    {
        "name": "Suze Orman",
        "category": "Finance Author/TV",
        "real_name": "Susan Lynn Orman"
    },
    {
        "name": "Jordan Peterson",
        "category": "Author/Psychologist",
        "real_name": "Jordan Bernt Peterson"
    },
    {
        "name": "Malcolm Gladwell",
        "category": "Author",
        "real_name": "Malcolm Timothy Gladwell"
    },
    {
        "name": "Brene Brown",
        "category": "Author/Speaker",
        "real_name": "Brene Brown"
    },
    {
        "name": "Michelle Obama",
        "category": "Author/Former First Lady",
        "real_name": "Michelle LaVaughn Robinson Obama"
    },
    {
        "name": "Barack Obama",
        "category": "Author/Politician",
        "real_name": "Barack Hussein Obama II"
    },
    {
        "name": "Mel Robbins",
        "category": "Author/Speaker",
        "real_name": "Melanie Robbins"
    },
    {
        "name": "Shroud",
        "category": "Gamer/Streamer",
        "real_name": "Michael Grzesiek"
    },
    {
        "name": "TimTheTatman",
        "category": "Gamer/Streamer",
        "real_name": "Timothy Betar"
    },
    {
        "name": "Tfue",
        "category": "Gamer/Streamer",
        "real_name": "Turner Tenney"
    },
    {
        "name": "DrLupo",
        "category": "Gamer/Streamer",
        "real_name": "Benjamin Lupo"
    },
    {
        "name": "NICKMERCS",
        "category": "Gamer/Streamer",
        "real_name": "Nick Kolcheff"
    },
    {
        "name": "SypherPK",
        "category": "Gamer/Streamer",
        "real_name": "Ali Hassan"
    },
    {
        "name": "Bugha",
        "category": "Esports Player",
        "real_name": "Kyle Giersdorf"
    },
    {
        "name": "s1mple",
        "category": "Esports Player",
        "real_name": "Oleksandr Kostyliev"
    },
    {
        "name": "ZywOo",
        "category": "Esports Player",
        "real_name": "Mathieu Herbaut"
    },
    {
        "name": "NiKo",
        "category": "Esports Player",
        "real_name": "Nikola Kovac"
    },
    {
        "name": "dev1ce",
        "category": "Esports Player",
        "real_name": "Nicolai Reedtz"
    },
    {
        "name": "Faker",
        "category": "Esports Player",
        "real_name": "Lee Sang-hyeok"
    },
    {
        "name": "Doublelift",
        "category": "Esports Player",
        "real_name": "Yiliang Peng"
    },
    {
        "name": "xQc",
        "category": "Gamer/Streamer",
        "real_name": "Felix Lengyel"
    },
    {
        "name": "HasanAbi",
        "category": "Political Streamer",
        "real_name": "Hasan Dogan Piker"
    },
    {
        "name": "Mizkif",
        "category": "Streamer",
        "real_name": "Matthew Rinaudo"
    },
    {
        "name": "Ludwig",
        "category": "Streamer",
        "real_name": "Ludwig Anders Ahgren"
    },
    {
        "name": "Moistcritikal",
        "category": "Streamer/Comedian",
        "real_name": "Charles White Jr"
    },
    {
        "name": "Asmongold",
        "category": "Gamer/Streamer",
        "real_name": "Zack"
    },
    {
        "name": "Amouranth",
        "category": "Streamer",
        "real_name": "Kaitlyn Siragusa"
    },
    {
        "name": "Demi Lovato",
        "category": "Singer/Actress",
        "real_name": "Demetria Devonne Lovato"
    },
    {
        "name": "Vanessa Hudgens",
        "category": "Actress/Singer",
        "real_name": "Vanessa Anne Hudgens"
    },
    {
        "name": "Zac Efron",
        "category": "Actor/Singer",
        "real_name": "Zachary David Alexander Efron"
    },
    {
        "name": "Ashley Tisdale",
        "category": "Actress/Singer",
        "real_name": "Ashley Michelle Tisdale"
    },
    {
        "name": "Selena Gomez",
        "category": "Singer/Actress",
        "real_name": "Selena Marie Gomez"
    },
    {
        "name": "Bella Thorne",
        "category": "Actress",
        "real_name": "Annabella Avery Thorne"
    },
    {
        "name": "Dove Cameron",
        "category": "Actress/Singer",
        "real_name": "Chloe Celeste Hosterman"
    },
    {
        "name": "Sabrina Carpenter",
        "category": "Singer/Actress",
        "real_name": "Sabrina Annlynn Carpenter"
    },
    {
        "name": "Jenna Ortega",
        "category": "Actress",
        "real_name": "Jenna Marie Ortega"
    },
    {
        "name": "Millie Bobby Brown",
        "category": "Actress",
        "real_name": "Millie Bobby Brown"
    },
    {
        "name": "Noah Schnapp",
        "category": "Actor",
        "real_name": "Noah Cameron Schnapp"
    },
    {
        "name": "Finn Wolfhard",
        "category": "Actor/Musician",
        "real_name": "Finn Wolfhard"
    },
    {
        "name": "Gaten Matarazzo",
        "category": "Actor",
        "real_name": "Gaten John Matarazzo III"
    },
    {
        "name": "Caleb McLaughlin",
        "category": "Actor",
        "real_name": "Caleb McLaughlin"
    },
    {
        "name": "Sadie Sink",
        "category": "Actress",
        "real_name": "Sadie Elizabeth Sink"
    },
    {
        "name": "Pedro Pascal",
        "category": "Actor",
        "real_name": "Jose Pedro Balmaceda Pascal"
    },
    {
        "name": "Oscar Isaac",
        "category": "Actor",
        "real_name": "Oscar Isaac Hernandez Estrada"
    },
    {
        "name": "Lupita Nyong'o",
        "category": "Actress",
        "real_name": "Lupita Amondi Nyong'o"
    },
    {
        "name": "Chadwick Boseman",
        "category": "Actor",
        "real_name": "Chadwick Aaron Boseman"
    },
    {
        "name": "Michael B Jordan",
        "category": "Actor",
        "real_name": "Michael Bakari Jordan"
    },
    {
        "name": "Idris Elba",
        "category": "Actor",
        "real_name": "Idrissa Akuna Elba"
    },
    {
        "name": "Jamie Foxx",
        "category": "Actor/Singer",
        "real_name": "Eric Marlon Bishop"
    },
    {
        "name": "Taraji P Henson",
        "category": "Actress",
        "real_name": "Taraji Penda Henson"
    },
    {
        "name": "Kerry Washington",
        "category": "Actress",
        "real_name": "Kerry Marisa Washington"
    },
    {
        "name": "Viola Davis",
        "category": "Actress",
        "real_name": "Viola Davis"
    },
    {
        "name": "Regina King",
        "category": "Actress/Director",
        "real_name": "Regina Rene King"
    },
    {
        "name": "Halle Bailey",
        "category": "Actress/Singer",
        "real_name": "Halle Lynn Bailey"
    },
    {
        "name": "Chloe Bailey",
        "category": "Singer/Actress",
        "real_name": "Chloe Elizabeth Bailey"
    },
    {
        "name": "Marshmello",
        "category": "DJ/Producer",
        "real_name": "Christopher Comstock"
    },
    {
        "name": "DJ Khaled",
        "category": "DJ/Producer",
        "real_name": "Khaled Mohammed Khaled"
    },
    {
        "name": "Calvin Harris",
        "category": "DJ/Producer",
        "real_name": "Adam Richard Wiles"
    },
    {
        "name": "David Guetta",
        "category": "DJ/Producer",
        "real_name": "Pierre David Guetta"
    },
    {
        "name": "Tiesto",
        "category": "DJ/Producer",
        "real_name": "Tijs Michiel Verwest"
    },
    {
        "name": "Martin Garrix",
        "category": "DJ/Producer",
        "real_name": "Martijn Gerard Garritsen"
    },
    {
        "name": "Diplo",
        "category": "DJ/Producer",
        "real_name": "Thomas Wesley Pentz"
    },
    {
        "name": "Skrillex",
        "category": "DJ/Producer",
        "real_name": "Sonny John Moore"
    },
    {
        "name": "Deadmau5",
        "category": "DJ/Producer",
        "real_name": "Joel Thomas Zimmerman"
    },
    {
        "name": "Avicii",
        "category": "DJ/Producer",
        "real_name": "Tim Bergling"
    },
    {
        "name": "Zedd",
        "category": "DJ/Producer",
        "real_name": "Anton Zaslavski"
    },
    {
        "name": "Kygo",
        "category": "DJ/Producer",
        "real_name": "Kyrre Gorvell-Dahll"
    },
    {
        "name": "Lizzo",
        "category": "Singer",
        "real_name": "Melissa Viviane Jefferson"
    },
    {
        "name": "Megan Thee Stallion",
        "category": "Rapper",
        "real_name": "Megan Jovon Ruth Pete"
    },
    {
        "name": "Doja Cat",
        "category": "Singer/Rapper",
        "real_name": "Amala Ratna Zandile Dlamini"
    },
    {
        "name": "SZA",
        "category": "Singer",
        "real_name": "Solana Imani Rowe"
    },
    {
        "name": "H.E.R",
        "category": "Singer",
        "real_name": "Gabriella Sarmiento Wilson"
    },
    {
        "name": "Summer Walker",
        "category": "Singer",
        "real_name": "Summer Marjani Walker"
    },
    {
        "name": "Jazmine Sullivan",
        "category": "Singer",
        "real_name": "Jazmine Sullivan"
    },
    {
        "name": "Jhene Aiko",
        "category": "Singer",
        "real_name": "Jhene Aiko Efuru Chilombo"
    },
    {
        "name": "Kehlani",
        "category": "Singer",
        "real_name": "Kehlani Ashley Parrish"
    },
    {
        "name": "Normani",
        "category": "Singer",
        "real_name": "Normani Kordei Hamilton"
    },
    {
        "name": "Fifth Harmony",
        "category": "Music Group",
        "real_name": "Fifth Harmony"
    },
    {
        "name": "Little Mix",
        "category": "Music Group",
        "real_name": "Little Mix"
    },
    {
        "name": "Spice Girls",
        "category": "Music Group",
        "real_name": "Spice Girls"
    },
    {
        "name": "Destiny's Child",
        "category": "Music Group",
        "real_name": "Destiny's Child"
    },
    {
        "name": "TLC",
        "category": "Music Group",
        "real_name": "TLC"
    },
    {
        "name": "Backstreet Boys",
        "category": "Music Group",
        "real_name": "Backstreet Boys"
    },
    {
        "name": "NSYNC",
        "category": "Music Group",
        "real_name": "NSYNC"
    },
    {
        "name": "Justin Timberlake",
        "category": "Singer/Actor",
        "real_name": "Justin Randall Timberlake"
    },
    {
        "name": "Usher",
        "category": "Singer",
        "real_name": "Usher Raymond IV"
    },
    {
        "name": "Chris Brown",
        "category": "Singer",
        "real_name": "Christopher Maurice Brown"
    },
    {
        "name": "Trey Songz",
        "category": "Singer",
        "real_name": "Tremaine Aldon Neverson"
    },
    {
        "name": "Ne-Yo",
        "category": "Singer",
        "real_name": "Shaffer Chimere Smith"
    },
    {
        "name": "John Legend",
        "category": "Singer",
        "real_name": "John Roger Stephens"
    },
    {
        "name": "Alicia Keys",
        "category": "Singer",
        "real_name": "Alicia Augello Cook"
    },
    {
        "name": "Mary J Blige",
        "category": "Singer",
        "real_name": "Mary Jane Blige"
    },
    {
        "name": "Janet Jackson",
        "category": "Singer/Actress",
        "real_name": "Janet Damita Jo Jackson"
    },
    {
        "name": "Michael Jackson",
        "category": "Singer",
        "real_name": "Michael Joseph Jackson"
    },
    {
        "name": "Prince",
        "category": "Singer",
        "real_name": "Prince Rogers Nelson"
    },
    {
        "name": "Elvis Presley",
        "category": "Singer/Actor",
        "real_name": "Elvis Aaron Presley"
    },
    {
        "name": "David Bowie",
        "category": "Singer",
        "real_name": "David Robert Jones"
    },
    {
        "name": "Freddie Mercury",
        "category": "Singer",
        "real_name": "Farrokh Bulsara"
    },
    {
        "name": "John Lennon",
        "category": "Singer",
        "real_name": "John Winston Lennon"
    },
    {
        "name": "Paul McCartney",
        "category": "Singer",
        "real_name": "James Paul McCartney"
    },
    {
        "name": "Mick Jagger",
        "category": "Singer",
        "real_name": "Michael Philip Jagger"
    },
    {
        "name": "Keith Richards",
        "category": "Guitarist",
        "real_name": "Keith Richards"
    },
    {
        "name": "Bob Dylan",
        "category": "Singer",
        "real_name": "Robert Allen Zimmerman"
    },
    {
        "name": "Bruce Springsteen",
        "category": "Singer",
        "real_name": "Bruce Frederick Springsteen"
    },
    {
        "name": "Bon Jovi",
        "category": "Singer",
        "real_name": "John Francis Bongiovi Jr"
    },
    {
        "name": "Elton John",
        "category": "Singer",
        "real_name": "Reginald Kenneth Dwight"
    },
    {
        "name": "Rod Stewart",
        "category": "Singer",
        "real_name": "Roderick David Stewart"
    },
    {
        "name": "Phil Collins",
        "category": "Singer/Drummer",
        "real_name": "Philip David Charles Collins"
    },
    {
        "name": "Lionel Richie",
        "category": "Singer",
        "real_name": "Lionel Brockman Richie Jr"
    },
    {
        "name": "Stevie Wonder",
        "category": "Singer",
        "real_name": "Stevland Hardaway Morris"
    },
    {
        "name": "Billy Joel",
        "category": "Singer",
        "real_name": "William Martin Joel"
    },
    {
        "name": "Lebron James",
        "category": "Basketball/Business",
        "real_name": "LeBron Raymone James Sr"
    },
    {
        "name": "Dak Prescott",
        "category": "NFL",
        "real_name": "Rayne Dakota Prescott"
    },
    {
        "name": "Joe Burrow",
        "category": "NFL",
        "real_name": "Joseph Lee Burrow"
    },
    {
        "name": "Justin Herbert",
        "category": "NFL",
        "real_name": "Justin Lawrence Herbert"
    },
    {
        "name": "Tua Tagovailoa",
        "category": "NFL",
        "real_name": "Tua Tagovailoa"
    },
    {
        "name": "Davante Adams",
        "category": "NFL",
        "real_name": "Davante Lavell Adams"
    },
    {
        "name": "Tyreek Hill",
        "category": "NFL",
        "real_name": "Tyreek Hill"
    },
    {
        "name": "Stefon Diggs",
        "category": "NFL",
        "real_name": "Stefon Diggs"
    },
    {
        "name": "Ja'Marr Chase",
        "category": "NFL",
        "real_name": "Ja'Marr Chase"
    },
    {
        "name": "Julio Jones",
        "category": "NFL",
        "real_name": "Quintorris Lopez Jones"
    },
    {
        "name": "Odell Beckham Jr",
        "category": "NFL",
        "real_name": "Odell Cornelious Beckham Jr"
    },
    {
        "name": "Antonio Brown",
        "category": "NFL",
        "real_name": "Antonio Tavaris Brown"
    },
    {
        "name": "Barry Sanders",
        "category": "NFL",
        "real_name": "Barry David Sanders"
    },
    {
        "name": "Jerry Rice",
        "category": "NFL",
        "real_name": "Jerry Lee Rice"
    },
    {
        "name": "Walter Payton",
        "category": "NFL",
        "real_name": "Walter Jerry Payton"
    },
    {
        "name": "Jim Brown",
        "category": "NFL/Actor",
        "real_name": "James Nathaniel Brown"
    },
    {
        "name": "Deion Sanders",
        "category": "NFL/Baseball",
        "real_name": "Deion Luwynn Sanders"
    },
    {
        "name": "Bo Jackson",
        "category": "NFL/Baseball",
        "real_name": "Vincent Edward Jackson"
    },
    {
        "name": "Mike Tyson",
        "category": "Boxer",
        "real_name": "Michael Gerard Tyson"
    },
    {
        "name": "Muhammad Ali",
        "category": "Boxer",
        "real_name": "Cassius Marcellus Clay Jr"
    },
    {
        "name": "Oscar De La Hoya",
        "category": "Boxer",
        "real_name": "Oscar De La Hoya"
    },
    {
        "name": "Manny Pacquiao",
        "category": "Boxer/Politician",
        "real_name": "Emmanuel Dapidran Pacquiao"
    },
    {
        "name": "George Foreman",
        "category": "Boxer/Business",
        "real_name": "George Edward Foreman"
    },
    {
        "name": "Evander Holyfield",
        "category": "Boxer",
        "real_name": "Evander Holyfield"
    },
    {
        "name": "Lennox Lewis",
        "category": "Boxer",
        "real_name": "Lennox Claudius Lewis"
    },
    {
        "name": "Ronda Rousey",
        "category": "MMA Fighter/Actress",
        "real_name": "Ronda Jean Rousey"
    },
    {
        "name": "Amanda Nunes",
        "category": "MMA Fighter",
        "real_name": "Amanda Lourenco Nunes"
    },
    {
        "name": "Valentina Shevchenko",
        "category": "MMA Fighter",
        "real_name": "Valentina Shevchenko"
    },
    {
        "name": "Charles Oliveira",
        "category": "MMA Fighter",
        "real_name": "Charles do Bronx Oliveira"
    },
    {
        "name": "Islam Makhachev",
        "category": "MMA Fighter",
        "real_name": "Islam Makhachev"
    },
    {
        "name": "Alex Pereira",
        "category": "MMA Fighter",
        "real_name": "Alex Pereira"
    },
    {
        "name": "Sean O'Malley",
        "category": "MMA Fighter",
        "real_name": "Sean O'Malley"
    },
    {
        "name": "Wayne Gretzky",
        "category": "Hockey",
        "real_name": "Wayne Douglas Gretzky"
    },
    {
        "name": "Sidney Crosby",
        "category": "Hockey",
        "real_name": "Sidney Patrick Crosby"
    },
    {
        "name": "Alexander Ovechkin",
        "category": "Hockey",
        "real_name": "Alexander Mikhailovich Ovechkin"
    },
    {
        "name": "Connor McDavid",
        "category": "Hockey",
        "real_name": "Connor McDavid"
    },
    {
        "name": "Auston Matthews",
        "category": "Hockey",
        "real_name": "Auston Matthews"
    },
    {
        "name": "Nathan MacKinnon",
        "category": "Hockey",
        "real_name": "Nathan MacKinnon"
    },
    {
        "name": "Mike Trout",
        "category": "Baseball",
        "real_name": "Michael Nelson Trout"
    },
    {
        "name": "Derek Jeter",
        "category": "Baseball/Business",
        "real_name": "Derek Sanderson Jeter"
    },
    {
        "name": "Alex Rodriguez",
        "category": "Baseball/Business",
        "real_name": "Alexander Emmanuel Rodriguez"
    },
    {
        "name": "David Ortiz",
        "category": "Baseball",
        "real_name": "David Americo Ortiz Arias"
    },
    {
        "name": "Ken Griffey Jr",
        "category": "Baseball",
        "real_name": "George Kenneth Griffey Jr"
    },
    {
        "name": "Cal Ripken Jr",
        "category": "Baseball",
        "real_name": "Calvin Edwin Ripken Jr"
    },
    {
        "name": "Babe Ruth",
        "category": "Baseball",
        "real_name": "George Herman Ruth Jr"
    },
    {
        "name": "Venus Williams",
        "category": "Tennis",
        "real_name": "Venus Ebony Starr Williams"
    },
    {
        "name": "Maria Sharapova",
        "category": "Tennis",
        "real_name": "Maria Yuryevna Sharapova"
    },
    {
        "name": "Andy Murray",
        "category": "Tennis",
        "real_name": "Andrew Barron Murray"
    },
    {
        "name": "Pete Sampras",
        "category": "Tennis",
        "real_name": "Peter Sampras"
    },
    {
        "name": "Andre Agassi",
        "category": "Tennis/Business",
        "real_name": "Andre Kirk Agassi"
    },
    {
        "name": "Jimmy Connors",
        "category": "Tennis",
        "real_name": "James Scott Connors"
    },
    {
        "name": "John McEnroe",
        "category": "Tennis/Media",
        "real_name": "John Patrick McEnroe Jr"
    },
    {
        "name": "Billie Jean King",
        "category": "Tennis",
        "real_name": "Billie Jean Moffitt King"
    },
    {
        "name": "Steffi Graf",
        "category": "Tennis",
        "real_name": "Stephanie Maria Graf"
    },
    {
        "name": "Nole Djokovic",
        "category": "Tennis",
        "real_name": "Novak Djokovic"
    },
    {
        "name": "David Dobrik",
        "category": "YouTuber/Podcaster",
        "real_name": "David Julian Dobrik"
    },
    {
        "name": "Trisha Paytas",
        "category": "YouTuber/Podcaster",
        "real_name": "Trisha Kay Paytas"
    },
    {
        "name": "H3H3 Productions",
        "category": "YouTuber/Podcaster",
        "real_name": "Ethan and Hila Klein"
    },
    {
        "name": "Ethan Klein",
        "category": "YouTuber/Podcaster",
        "real_name": "Ethan Edward Klein"
    },
    {
        "name": "Hila Klein",
        "category": "Business/YouTuber",
        "real_name": "Hila Klein"
    },
    {
        "name": "Gabbie Hanna",
        "category": "YouTuber/Singer",
        "real_name": "Gabrielle Hanna"
    },
    {
        "name": "Amber Scholl",
        "category": "YouTuber",
        "real_name": "Amber Scholl"
    },
    {
        "name": "Bestdressed",
        "category": "YouTuber/Fashion",
        "real_name": "Ashley Rous"
    },
    {
        "name": "Safiya Nygaard",
        "category": "YouTuber",
        "real_name": "Safiya Nygaard"
    },
    {
        "name": "NikkieTutorials",
        "category": "Beauty YouTuber",
        "real_name": "Nikkie de Jager"
    },
    {
        "name": "MannyMUA",
        "category": "Beauty Influencer",
        "real_name": "Manuel Gutierrez"
    },
    {
        "name": "Wayne Goss",
        "category": "Beauty YouTuber",
        "real_name": "Wayne Goss"
    },
    {
        "name": "RawBeautyKristi",
        "category": "Beauty YouTuber",
        "real_name": "Kristi"
    },
    {
        "name": "Hindash",
        "category": "Beauty YouTuber",
        "real_name": "Hindash"
    },
    {
        "name": "Jackie Aina",
        "category": "Beauty Influencer",
        "real_name": "Jackie Aina"
    },
    {
        "name": "Patrick Starrr",
        "category": "Beauty Influencer",
        "real_name": "Patrick Simondac"
    },
    {
        "name": "Robert Welsh",
        "category": "Beauty YouTuber",
        "real_name": "Robert Welsh"
    },
    {
        "name": "Bailey Sarian",
        "category": "YouTuber",
        "real_name": "Bailey Sarian"
    },
    {
        "name": "Trixie Mattel",
        "category": "Drag Queen/YouTuber",
        "real_name": "Brian Michael Firkus"
    },
    {
        "name": "RuPaul",
        "category": "TV Host/Drag Queen",
        "real_name": "RuPaul Andre Charles"
    },
    {
        "name": "Steve Jobs",
        "category": "Tech Billionaire",
        "real_name": "Steven Paul Jobs"
    },
    {
        "name": "Paul Allen",
        "category": "Tech Billionaire",
        "real_name": "Paul Gardner Allen"
    },
    {
        "name": "Michael Dell",
        "category": "Tech Billionaire",
        "real_name": "Michael Saul Dell"
    },
    {
        "name": "Andy Grove",
        "category": "Tech Executive",
        "real_name": "Andras Grof"
    },
    {
        "name": "Gordon Moore",
        "category": "Tech Pioneer",
        "real_name": "Gordon Earle Moore"
    },
    {
        "name": "Bob Noyce",
        "category": "Tech Pioneer",
        "real_name": "Robert Norton Noyce"
    },
    {
        "name": "Travis Kalanick",
        "category": "Tech Entrepreneur",
        "real_name": "Travis Cordell Kalanick"
    },
    {
        "name": "Garrett Camp",
        "category": "Tech Entrepreneur",
        "real_name": "Garrett Camp"
    },
    {
        "name": "Brian Chesky",
        "category": "Tech CEO",
        "real_name": "Brian Joseph Chesky"
    },
    {
        "name": "Joe Gebbia",
        "category": "Tech Entrepreneur",
        "real_name": "Joe Gebbia"
    },
    {
        "name": "Nathan Blecharczyk",
        "category": "Tech Entrepreneur",
        "real_name": "Nathan Blecharczyk"
    },
    {
        "name": "Drew Houston",
        "category": "Tech CEO",
        "real_name": "Andrew W Houston"
    },
    {
        "name": "Arash Ferdowsi",
        "category": "Tech Entrepreneur",
        "real_name": "Arash Ferdowsi"
    },
    {
        "name": "Kevin Systrom",
        "category": "Tech Entrepreneur",
        "real_name": "Kevin Systrom"
    },
    {
        "name": "Mike Krieger",
        "category": "Tech Entrepreneur",
        "real_name": "Mike Krieger"
    },
    {
        "name": "Evan Spiegel",
        "category": "Tech CEO",
        "real_name": "Evan Thomas Spiegel"
    },
    {
        "name": "Bobby Murphy",
        "category": "Tech Entrepreneur",
        "real_name": "Bobby Murphy"
    },
    {
        "name": "Jan Koum",
        "category": "Tech Entrepreneur",
        "real_name": "Jan Koum"
    },
    {
        "name": "Brian Acton",
        "category": "Tech Entrepreneur",
        "real_name": "Brian Acton"
    },
    {
        "name": "Jack Dorsey",
        "category": "Tech CEO",
        "real_name": "Jack Patrick Dorsey"
    },
    {
        "name": "Parag Agrawal",
        "category": "Tech CEO",
        "real_name": "Parag Agrawal"
    },
    {
        "name": "Eric Schmidt",
        "category": "Tech Executive",
        "real_name": "Eric Emerson Schmidt"
    },
    {
        "name": "Sheryl Sandberg",
        "category": "Tech Executive",
        "real_name": "Sheryl Kara Sandberg"
    },
    {
        "name": "Ginni Rometty",
        "category": "Tech CEO",
        "real_name": "Virginia Marie Rometty"
    },
    {
        "name": "Marissa Mayer",
        "category": "Tech CEO",
        "real_name": "Marissa Ann Mayer"
    },
    {
        "name": "Meg Whitman",
        "category": "Tech CEO",
        "real_name": "Margaret Cushing Whitman"
    },
    {
        "name": "Carly Fiorina",
        "category": "Tech CEO/Politician",
        "real_name": "Cara Carleton Sneed"
    },
    {
        "name": "Pat Gelsinger",
        "category": "Tech CEO",
        "real_name": "Pat Paul Gelsinger"
    },
    {
        "name": "Lisa Su",
        "category": "Tech CEO",
        "real_name": "Lisa Tzwu-Fang Su"
    },
    {
        "name": "Andy Jassy",
        "category": "Tech CEO",
        "real_name": "Andrew R Jassy"
    },
    {
        "name": "Dara Khosrowshahi",
        "category": "Tech CEO",
        "real_name": "Dara Khosrowshahi"
    },
    {
        "name": "Airbnb Founders",
        "category": "Tech Entrepreneurs",
        "real_name": "Brian Chesky Joe Gebbia Nathan Blecharczyk"
    },
    {
        "name": "Volodymyr Zelensky",
        "category": "Politician",
        "real_name": "Volodymyr Oleksandrovych Zelensky"
    },
    {
        "name": "Angela Merkel",
        "category": "Politician",
        "real_name": "Angela Dorothea Merkel"
    },
    {
        "name": "Nicolas Sarkozy",
        "category": "Politician",
        "real_name": "Nicolas Paul Stephane Sarkozy de Nagy-Bocsa"
    },
    {
        "name": "Recep Tayyip Erdogan",
        "category": "Politician",
        "real_name": "Recep Tayyip Erdogan"
    },
    {
        "name": "Xi Jinping",
        "category": "Politician",
        "real_name": "Xi Jinping"
    },
    {
        "name": "Kim Jong-un",
        "category": "Politician",
        "real_name": "Kim Jong-un"
    },
    {
        "name": "Jair Bolsonaro",
        "category": "Politician",
        "real_name": "Jair Messias Bolsonaro"
    },
    {
        "name": "Luiz Inacio Lula da Silva",
        "category": "Politician",
        "real_name": "Luiz Inacio Lula da Silva"
    },
    {
        "name": "Pedro Sanchez",
        "category": "Politician",
        "real_name": "Pedro Sanchez Perez-Castejon"
    },
    {
        "name": "Rishi Sunak",
        "category": "Politician",
        "real_name": "Rishi Sunak"
    },
    {
        "name": "Keir Starmer",
        "category": "Politician",
        "real_name": "Keir Rodney Starmer"
    },
    {
        "name": "Scott Morrison",
        "category": "Politician",
        "real_name": "Scott John Morrison"
    },
    {
        "name": "Jacinda Ardern",
        "category": "Politician",
        "real_name": "Jacinda Kate Laurell Ardern"
    },
    {
        "name": "Giorgia Meloni",
        "category": "Politician",
        "real_name": "Giorgia Meloni"
    },
    {
        "name": "Marine Le Pen",
        "category": "Politician",
        "real_name": "Marion Anne Perrine Le Pen"
    },
    {
        "name": "Princess Beatrice",
        "category": "Royal",
        "real_name": "Beatrice Elizabeth Mary"
    },
    {
        "name": "Princess Eugenie",
        "category": "Royal",
        "real_name": "Eugenie Victoria Helena"
    },
    {
        "name": "Zara Tindall",
        "category": "Royal/Equestrian",
        "real_name": "Zara Anne Elizabeth Tindall"
    },
    {
        "name": "Mike Tindall",
        "category": "Royal/Rugby",
        "real_name": "Michael James Tindall"
    },
    {
        "name": "Crown Prince Mohammed bin Salman",
        "category": "Royal/Politician",
        "real_name": "Mohammed bin Salman Al Saud"
    },
    {
        "name": "Queen Rania",
        "category": "Royal",
        "real_name": "Rania Al-Yassin"
    },
    {
        "name": "Sheikh Mohammed Al Maktoum",
        "category": "Royal/Business",
        "real_name": "Mohammed bin Rashid Al Maktoum"
    },
    {
        "name": "Ajay Devgn",
        "category": "Bollywood Actor",
        "real_name": "Vishal Veeru Devgan"
    },
    {
        "name": "John Abraham",
        "category": "Bollywood Actor",
        "real_name": "Farhan Irani"
    },
    {
        "name": "Abhishek Bachchan",
        "category": "Bollywood Actor",
        "real_name": "Abhishek Amitabh Bachchan"
    },
    {
        "name": "Sunny Deol",
        "category": "Bollywood Actor",
        "real_name": "Ajay Singh Deol"
    },
    {
        "name": "Bobby Deol",
        "category": "Bollywood Actor",
        "real_name": "Vijay Singh Deol"
    },
    {
        "name": "Arjun Kapoor",
        "category": "Bollywood Actor",
        "real_name": "Arjun Kapoor"
    },
    {
        "name": "Ayushmann Khurrana",
        "category": "Bollywood Actor",
        "real_name": "Ayushmann Khurrana"
    },
    {
        "name": "Rajkummar Rao",
        "category": "Bollywood Actor",
        "real_name": "Rajkummar Rao"
    },
    {
        "name": "Kartik Aaryan",
        "category": "Bollywood Actor",
        "real_name": "Kartik Tiwari"
    },
    {
        "name": "Vicky Kaushal",
        "category": "Bollywood Actor",
        "real_name": "Vicky Kaushal"
    },
    {
        "name": "Sunny Leone",
        "category": "Actress",
        "real_name": "Karenjit Kaur Vohra"
    },
    {
        "name": "Nora Fatehi",
        "category": "Actress/Dancer",
        "real_name": "Nora Fatehi"
    },
    {
        "name": "Kiara Advani",
        "category": "Bollywood Actress",
        "real_name": "Alia Advani"
    },
    {
        "name": "Kriti Sanon",
        "category": "Bollywood Actress",
        "real_name": "Kriti Sanon"
    },
    {
        "name": "Shraddha Kapoor",
        "category": "Bollywood Actress",
        "real_name": "Shraddha Kapoor"
    },
    {
        "name": "Sara Ali Khan",
        "category": "Bollywood Actress",
        "real_name": "Sara Ali Khan"
    },
    {
        "name": "Janhvi Kapoor",
        "category": "Bollywood Actress",
        "real_name": "Janhvi Kapoor"
    },
    {
        "name": "Sonam Kapoor",
        "category": "Bollywood Actress",
        "real_name": "Sonam Kapoor Ahuja"
    },
    {
        "name": "Karan Johar",
        "category": "Director/Producer",
        "real_name": "Karan Johar"
    },
    {
        "name": "Rohit Shetty",
        "category": "Director",
        "real_name": "Rohit Shetty"
    },
    {
        "name": "Sanjay Leela Bhansali",
        "category": "Director",
        "real_name": "Sanjay Leela Bhansali"
    },
    {
        "name": "Anurag Kashyap",
        "category": "Director",
        "real_name": "Anurag Kashyap"
    },
    {
        "name": "Farhan Akhtar",
        "category": "Actor/Director",
        "real_name": "Farhan Akhtar"
    },
    {
        "name": "Zoya Akhtar",
        "category": "Director",
        "real_name": "Zoya Akhtar"
    },
    {
        "name": "Imtiaz Ali",
        "category": "Director",
        "real_name": "Imtiaz Ali"
    },
    {
        "name": "Davido",
        "category": "Afrobeats Singer",
        "real_name": "David Adedeji Adeleke"
    },
    {
        "name": "Wizkid",
        "category": "Afrobeats Singer",
        "real_name": "Ayodeji Ibrahim Balogun"
    },
    {
        "name": "Burna Boy",
        "category": "Afrobeats Singer",
        "real_name": "Damini Ebunoluwa Ogulu"
    },
    {
        "name": "Tiwa Savage",
        "category": "Afrobeats Singer",
        "real_name": "Tiwatope Savage"
    },
    {
        "name": "Tems",
        "category": "Afrobeats Singer",
        "real_name": "Temilade Openiyi"
    },
    {
        "name": "Rema",
        "category": "Afrobeats Singer",
        "real_name": "Divine Ikubor"
    },
    {
        "name": "Asake",
        "category": "Afrobeats Singer",
        "real_name": "Ahmed Ololade"
    },
    {
        "name": "Fireboy DML",
        "category": "Afrobeats Singer",
        "real_name": "Adedamola Adefolahan"
    },
    {
        "name": "Naira Marley",
        "category": "Afrobeats Singer",
        "real_name": "Azeez Fashola"
    },
    {
        "name": "Fela Kuti",
        "category": "Musician",
        "real_name": "Fela Anikulapo Kuti"
    },
    {
        "name": "Vin Diesel",
        "category": "Actor",
        "real_name": "Mark Sinclair"
    },
    {
        "name": "Gael Garcia Bernal",
        "category": "Actor",
        "real_name": "Gael Garcia Bernal"
    },
    {
        "name": "Diego Luna",
        "category": "Actor",
        "real_name": "Diego Luna Alexander"
    },
    {
        "name": "Benicio del Toro",
        "category": "Actor",
        "real_name": "Benicio Monserrate Rafael del Toro Sanchez"
    },
    {
        "name": "Antonio Banderas",
        "category": "Actor",
        "real_name": "Jose Antonio Dominguez Banderas"
    },
    {
        "name": "Javier Bardem",
        "category": "Actor",
        "real_name": "Javier Angel Encinas Bardem"
    },
    {
        "name": "Alejandro Gonzalez Inarritu",
        "category": "Director",
        "real_name": "Alejandro Gonzalez Inarritu"
    },
    {
        "name": "Alfonso Cuaron",
        "category": "Director",
        "real_name": "Alfonso Cuaron Orozco"
    },
    {
        "name": "Guillermo del Toro",
        "category": "Director",
        "real_name": "Guillermo del Toro Gomez"
    },
    {
        "name": "Steven Spielberg",
        "category": "Director/Producer",
        "real_name": "Steven Allan Spielberg"
    },
    {
        "name": "Christopher Nolan",
        "category": "Director",
        "real_name": "Christopher Edward Nolan"
    },
    {
        "name": "James Cameron",
        "category": "Director",
        "real_name": "James Francis Cameron"
    },
    {
        "name": "Martin Scorsese",
        "category": "Director",
        "real_name": "Martin Charles Scorsese"
    },
    {
        "name": "Quentin Tarantino",
        "category": "Director",
        "real_name": "Quentin Jerome Tarantino"
    },
    {
        "name": "Ridley Scott",
        "category": "Director",
        "real_name": "Ridley Scott"
    },
    {
        "name": "Denis Villeneuve",
        "category": "Director",
        "real_name": "Denis Villeneuve"
    },
    {
        "name": "Coen Brothers",
        "category": "Directors",
        "real_name": "Joel and Ethan Coen"
    },
    {
        "name": "Ron Howard",
        "category": "Director",
        "real_name": "Ronald William Howard"
    },
    {
        "name": "Peter Jackson",
        "category": "Director",
        "real_name": "Peter Robert Jackson"
    },
    {
        "name": "George Lucas",
        "category": "Director/Producer",
        "real_name": "George Walton Lucas Jr"
    },
    {
        "name": "Francis Ford Coppola",
        "category": "Director",
        "real_name": "Francis Ford Coppola"
    },
    {
        "name": "Spike Lee",
        "category": "Director",
        "real_name": "Shelton Jackson Lee"
    },
    {
        "name": "Tyler Perry",
        "category": "Director/Actor",
        "real_name": "Emmitt Perry Jr"
    },
    {
        "name": "Jordan Peele",
        "category": "Director/Actor",
        "real_name": "Jordan Haworth Peele"
    },
    {
        "name": "Ryan Coogler",
        "category": "Director",
        "real_name": "Ryan Kyle Coogler"
    },
    {
        "name": "Ava DuVernay",
        "category": "Director",
        "real_name": "Ava Marie DuVernay"
    },
    {
        "name": "Greta Gerwig",
        "category": "Director/Actress",
        "real_name": "Greta Celeste Gerwig"
    },
    {
        "name": "Noah Baumbach",
        "category": "Director",
        "real_name": "Noah Baumbach"
    },
    {
        "name": "Wes Anderson",
        "category": "Director",
        "real_name": "Wesley Wales Anderson"
    },
    {
        "name": "Dream",
        "category": "YouTuber/Gamer",
        "real_name": "Clay"
    },
    {
        "name": "GeorgeNotFound",
        "category": "YouTuber/Gamer",
        "real_name": "George Davidson"
    },
    {
        "name": "Sapnap",
        "category": "YouTuber/Gamer",
        "real_name": "Nicholas Armstrong"
    },
    {
        "name": "Technoblade",
        "category": "YouTuber/Gamer",
        "real_name": "Alex"
    },
    {
        "name": "TommyInnit",
        "category": "YouTuber/Gamer",
        "real_name": "Thomas Simons"
    },
    {
        "name": "Wilbur Soot",
        "category": "YouTuber/Musician",
        "real_name": "William Patrick Spencer Gold"
    },
    {
        "name": "Quackity",
        "category": "YouTuber/Streamer",
        "real_name": "Alexis"
    },
    {
        "name": "Karl Jacobs",
        "category": "YouTuber/Streamer",
        "real_name": "Karl Jacobs"
    },
    {
        "name": "Tubbo",
        "category": "YouTuber/Streamer",
        "real_name": "Toby Smith"
    },
    {
        "name": "Ranboo",
        "category": "YouTuber/Streamer",
        "real_name": "Ranboo"
    },
    {
        "name": "Callahan",
        "category": "Streamer",
        "real_name": "Callahan"
    },
    {
        "name": "Fundy",
        "category": "YouTuber/Gamer",
        "real_name": "Floris Damen"
    },
    {
        "name": "CriticalRole",
        "category": "Streaming Group",
        "real_name": "Critical Role"
    },
    {
        "name": "Matthew Mercer",
        "category": "Voice Actor/Streamer",
        "real_name": "Matthew Christopher Miller"
    },
    {
        "name": "Sodapoppin",
        "category": "Streamer",
        "real_name": "Thomas Jefferson Chance Morris IV"
    },
    {
        "name": "Lirik",
        "category": "Streamer",
        "real_name": "Saqib Ali Zahid"
    },
    {
        "name": "Summit1g",
        "category": "Streamer",
        "real_name": "Jaryd Russell Lazar"
    },
    {
        "name": "DrDisrespect",
        "category": "Streamer",
        "real_name": "Guy Beahm"
    },
    {
        "name": "CourageJD",
        "category": "Streamer/Content Creator",
        "real_name": "Jack Dunlop"
    },
    {
        "name": "Cloak",
        "category": "Streamer",
        "real_name": "Cody Ko"
    },
    {
        "name": "Gianmarco Tamberi",
        "category": "High Jump",
        "real_name": "Gianmarco Tamberi"
    },
    {
        "name": "Mondo Duplantis",
        "category": "Pole Vault",
        "real_name": "Armand Duplantis"
    },
    {
        "name": "Noah Lyles",
        "category": "Sprinter",
        "real_name": "Noah Lyles"
    },
    {
        "name": "Sha'Carri Richardson",
        "category": "Sprinter",
        "real_name": "Sha'Carri Richardson"
    },
    {
        "name": "Marcell Jacobs",
        "category": "Sprinter",
        "real_name": "Lamont Marcell Jacobs"
    },
    {
        "name": "Katie Ledecky",
        "category": "Swimmer",
        "real_name": "Kathleen Genevieve Ledecky"
    },
    {
        "name": "Caeleb Dressel",
        "category": "Swimmer",
        "real_name": "Caeleb Remel Dressel"
    },
    {
        "name": "Leon Marchand",
        "category": "Swimmer",
        "real_name": "Leon Marchand"
    },
    {
        "name": "Neeraj Chopra",
        "category": "Javelin",
        "real_name": "Neeraj Chopra"
    },
    {
        "name": "PV Sindhu",
        "category": "Badminton",
        "real_name": "Pusarla Venkata Sindhu"
    },
    {
        "name": "Lin Dan",
        "category": "Badminton",
        "real_name": "Lin Dan"
    },
    {
        "name": "Lee Chong Wei",
        "category": "Badminton",
        "real_name": "Dato Lee Chong Wei"
    },
    {
        "name": "Viktor Axelsen",
        "category": "Badminton",
        "real_name": "Viktor Axelsen"
    },
    {
        "name": "Kento Momota",
        "category": "Badminton",
        "real_name": "Kento Momota"
    },
    {
        "name": "Chen Long",
        "category": "Badminton",
        "real_name": "Chen Long"
    },
    {
        "name": "Son Heung-min",
        "category": "Footballer",
        "real_name": "Son Heung-min"
    },
    {
        "name": "Sadio Mane",
        "category": "Footballer",
        "real_name": "Sadio Mane"
    },
    {
        "name": "Romelu Lukaku",
        "category": "Footballer",
        "real_name": "Romelu Menama Lukaku Bolingoli"
    },
    {
        "name": "Antoine Griezmann",
        "category": "Footballer",
        "real_name": "Antoine Griezmann"
    },
    {
        "name": "Paul Pogba",
        "category": "Footballer",
        "real_name": "Paul Labile Pogba"
    },
    {
        "name": "Gareth Bale",
        "category": "Footballer",
        "real_name": "Gareth Frank Bale"
    },
    {
        "name": "Sergio Ramos",
        "category": "Footballer",
        "real_name": "Sergio Ramos Garcia"
    },
    {
        "name": "Gerard Pique",
        "category": "Footballer/Business",
        "real_name": "Gerard Pique Bernabeu"
    },
    {
        "name": "Andres Iniesta",
        "category": "Footballer",
        "real_name": "Andres Iniesta Lujan"
    },
    {
        "name": "Xavi Hernandez",
        "category": "Footballer/Manager",
        "real_name": "Xavier Hernandez Creus"
    },
    {
        "name": "Carlo Ancelotti",
        "category": "Football Manager",
        "real_name": "Carlo Ancelotti"
    },
    {
        "name": "Pep Guardiola",
        "category": "Football Manager",
        "real_name": "Josep Guardiola Sala"
    },
    {
        "name": "Jurgen Klopp",
        "category": "Football Manager",
        "real_name": "Jurgen Norbert Klopp"
    },
    {
        "name": "Jose Mourinho",
        "category": "Football Manager",
        "real_name": "Jose Mario dos Santos Mourinho Felix"
    },
    {
        "name": "Alex Ferguson",
        "category": "Football Manager",
        "real_name": "Alexander Chapman Ferguson"
    },
    {
        "name": "Jeffree Star",
        "category": "Beauty YouTuber/Business",
        "real_name": "Jeffrey Lynn Steininger Jr"
    },
    {
        "name": "Tati Westbrook",
        "category": "Beauty YouTuber",
        "real_name": "Tatiana Aleksandra Westbrook"
    },
    {
        "name": "Lisa Eldridge",
        "category": "Beauty Expert/YouTuber",
        "real_name": "Lisa Eldridge"
    },
    {
        "name": "Wayne Goss",
        "category": "Beauty YouTuber",
        "real_name": "Wayne Goss"
    },
    {
        "name": "Kate Gleason",
        "category": "Beauty Influencer",
        "real_name": "Kate Gleason"
    },
    {
        "name": "Bretman Rock",
        "category": "Beauty Influencer",
        "real_name": "Bretman Sacayanan"
    },
    {
        "name": "NikkieTutorials",
        "category": "Beauty YouTuber",
        "real_name": "Nikkie de Jager"
    },
    {
        "name": "Lucie Fink",
        "category": "Lifestyle YouTuber",
        "real_name": "Lucie Fink"
    },
    {
        "name": "Gaby Ugarte",
        "category": "Lifestyle Influencer",
        "real_name": "Gaby Ugarte"
    },
    {
        "name": "Dulce Candy",
        "category": "Beauty/Lifestyle YouTuber",
        "real_name": "Dulce Candy Ruiz"
    },
    {
        "name": "Claudia Sulewski",
        "category": "Lifestyle YouTuber",
        "real_name": "Claudia Sulewski"
    },
    {
        "name": "Ingrid Nilsen",
        "category": "Beauty YouTuber",
        "real_name": "Ingrid Nilsen"
    },
    {
        "name": "Louise Pentland",
        "category": "Lifestyle YouTuber",
        "real_name": "Louise Michelle Pentland"
    },
    {
        "name": "Marcus Butler",
        "category": "YouTuber",
        "real_name": "Marcus Butler"
    },
    {
        "name": "Oli White",
        "category": "YouTuber",
        "real_name": "Oliver William White"
    },
    {
        "name": "Dan and Phil",
        "category": "YouTubers",
        "real_name": "Daniel Howell and Phil Lester"
    },
    {
        "name": "Dan Howell",
        "category": "YouTuber",
        "real_name": "Daniel James Howell"
    },
    {
        "name": "AmazingPhil",
        "category": "YouTuber",
        "real_name": "Philip Michael Lester"
    },
    {
        "name": "Dodie Clark",
        "category": "YouTuber/Musician",
        "real_name": "Dorothy Miranda Clark"
    },
    {
        "name": "Jack Howard",
        "category": "YouTuber",
        "real_name": "Jack Howard"
    },
    {
        "name": "Indra Nooyi",
        "category": "Business Executive",
        "real_name": "Indra Krishnamurthy Nooyi"
    },
    {
        "name": "Mary Barra",
        "category": "Auto CEO",
        "real_name": "Mary Teresa Barra"
    },
    {
        "name": "Elon Musk Tesla",
        "category": "Electric Vehicles CEO",
        "real_name": "Elon Reeve Musk"
    },
    {
        "name": "Herbert Diess",
        "category": "Auto CEO",
        "real_name": "Herbert Diess"
    },
    {
        "name": "Jim Farley",
        "category": "Auto CEO",
        "real_name": "James D Farley Jr"
    },
    {
        "name": "Carlos Tavares",
        "category": "Auto CEO",
        "real_name": "Carlos Manuel da Silva Tavares"
    },
    {
        "name": "Ola Kallenius",
        "category": "Auto CEO",
        "real_name": "Ola Kallenius"
    },
    {
        "name": "Daniel Ek",
        "category": "Tech CEO",
        "real_name": "Daniel Gustav Ek"
    },
    {
        "name": "Whitney Wolfe Herd",
        "category": "Tech CEO",
        "real_name": "Whitney Wolfe Herd"
    },
    {
        "name": "Anne Wojcicki",
        "category": "Biotech CEO",
        "real_name": "Anne E Wojcicki"
    },
    {
        "name": "Elizabeth Holmes",
        "category": "Tech Entrepreneur",
        "real_name": "Elizabeth Anne Holmes"
    },
    {
        "name": "Adam Neumann",
        "category": "Tech Entrepreneur",
        "real_name": "Adam Neumann"
    },
    {
        "name": "Masayoshi Son",
        "category": "Billionaire/Investor",
        "real_name": "Masayoshi Son"
    },
    {
        "name": "Softbank",
        "category": "Investment Group",
        "real_name": "Softbank Group Corp"
    },
    {
        "name": "Jamie Dimon",
        "category": "Banking CEO",
        "real_name": "James Dimon"
    },
    {
        "name": "Lloyd Blankfein",
        "category": "Banking CEO",
        "real_name": "Lloyd Craig Blankfein"
    },
    {
        "name": "David Solomon",
        "category": "Banking CEO",
        "real_name": "David Marcus Solomon"
    },
    {
        "name": "James Gorman",
        "category": "Banking CEO",
        "real_name": "James Patrick Gorman"
    },
    {
        "name": "Stephen Schwarzman",
        "category": "Billionaire/Finance",
        "real_name": "Stephen Allen Schwarzman"
    },
    {
        "name": "Henry Kravis",
        "category": "Billionaire/Finance",
        "real_name": "Henry Roberts Kravis"
    },
    {
        "name": "Coldplay",
        "category": "Music Group",
        "real_name": "Chris Martin Band"
    },
    {
        "name": "Chris Martin",
        "category": "Singer",
        "real_name": "Christopher Anthony John Martin"
    },
    {
        "name": "U2",
        "category": "Music Group",
        "real_name": "U2"
    },
    {
        "name": "Bono",
        "category": "Singer/Activist",
        "real_name": "Paul David Hewson"
    },
    {
        "name": "Radiohead",
        "category": "Music Group",
        "real_name": "Radiohead"
    },
    {
        "name": "Thom Yorke",
        "category": "Singer",
        "real_name": "Thomas Edward Yorke"
    },
    {
        "name": "Linkin Park",
        "category": "Music Group",
        "real_name": "Linkin Park"
    },
    {
        "name": "Chester Bennington",
        "category": "Singer",
        "real_name": "Chester Charles Bennington"
    },
    {
        "name": "Green Day",
        "category": "Music Group",
        "real_name": "Green Day"
    },
    {
        "name": "Billy Joe Armstrong",
        "category": "Singer",
        "real_name": "Billie Joe Armstrong"
    },
    {
        "name": "Red Hot Chili Peppers",
        "category": "Music Group",
        "real_name": "Red Hot Chili Peppers"
    },
    {
        "name": "Anthony Kiedis",
        "category": "Singer",
        "real_name": "Anthony Kiedis"
    },
    {
        "name": "Metallica",
        "category": "Music Group",
        "real_name": "Metallica"
    },
    {
        "name": "James Hetfield",
        "category": "Singer/Guitarist",
        "real_name": "James Alan Hetfield"
    },
    {
        "name": "AC DC",
        "category": "Music Group",
        "real_name": "ACDC"
    },
    {
        "name": "Angus Young",
        "category": "Guitarist",
        "real_name": "Angus McKinnon Young"
    },
    {
        "name": "Led Zeppelin",
        "category": "Music Group",
        "real_name": "Led Zeppelin"
    },
    {
        "name": "Jimmy Page",
        "category": "Guitarist",
        "real_name": "James Patrick Page"
    },
    {
        "name": "Robert Plant",
        "category": "Singer",
        "real_name": "Robert Anthony Plant"
    },
    {
        "name": "Pink Floyd",
        "category": "Music Group",
        "real_name": "Pink Floyd"
    },
    {
        "name": "Roger Waters",
        "category": "Singer/Musician",
        "real_name": "George Roger Waters"
    },
    {
        "name": "David Gilmour",
        "category": "Guitarist",
        "real_name": "David Jon Gilmour"
    },
    {
        "name": "Nirvana",
        "category": "Music Group",
        "real_name": "Nirvana"
    },
    {
        "name": "Kurt Cobain",
        "category": "Singer",
        "real_name": "Kurt Donald Cobain"
    },
    {
        "name": "Pearl Jam",
        "category": "Music Group",
        "real_name": "Pearl Jam"
    },
    {
        "name": "Eddie Vedder",
        "category": "Singer",
        "real_name": "Edward Louis Severson III"
    },
    {
        "name": "Soundgarden",
        "category": "Music Group",
        "real_name": "Soundgarden"
    },
    {
        "name": "Chris Cornell",
        "category": "Singer",
        "real_name": "Christopher John Cornell"
    },
    {
        "name": "Alice in Chains",
        "category": "Music Group",
        "real_name": "Alice in Chains"
    },
    {
        "name": "Layne Staley",
        "category": "Singer",
        "real_name": "Layne Thomas Staley"
    },
    {
        "name": "Foo Fighters",
        "category": "Music Group",
        "real_name": "Foo Fighters"
    },
    {
        "name": "Dave Grohl",
        "category": "Singer/Musician",
        "real_name": "David Eric Grohl"
    },
    {
        "name": "The Beatles",
        "category": "Music Group",
        "real_name": "The Beatles"
    },
    {
        "name": "Ringo Starr",
        "category": "Drummer",
        "real_name": "Richard Starkey"
    },
    {
        "name": "George Harrison",
        "category": "Guitarist/Singer",
        "real_name": "George Harrison"
    },
    {
        "name": "Jimi Hendrix",
        "category": "Guitarist",
        "real_name": "James Marshall Hendrix"
    },
    {
        "name": "Eric Clapton",
        "category": "Guitarist",
        "real_name": "Eric Patrick Clapton"
    },
    {
        "name": "Bob Marley",
        "category": "Reggae Singer",
        "real_name": "Nesta Robert Marley"
    },
    {
        "name": "Ziggy Marley",
        "category": "Reggae Singer",
        "real_name": "David Nesta Marley"
    },
    {
        "name": "Damian Marley",
        "category": "Reggae Singer",
        "real_name": "Damian Robert Nesta Marley"
    },
    {
        "name": "Sean Paul",
        "category": "Reggae Singer",
        "real_name": "Sean Paul Francis Henriques"
    },
    {
        "name": "Wyclef Jean",
        "category": "Singer/Musician",
        "real_name": "Wyclef Jean"
    },
    {
        "name": "Lauryn Hill",
        "category": "Singer/Rapper",
        "real_name": "Lauryn Noelle Hill"
    },
    {
        "name": "Fugees",
        "category": "Music Group",
        "real_name": "Fugees"
    },
    {
        "name": "Pras Michel",
        "category": "Rapper",
        "real_name": "Samuel Prakazrel Michel"
    },
    {
        "name": "Lil Nas X",
        "category": "Singer/Rapper",
        "real_name": "Montero Lamar Hill"
    },
    {
        "name": "Jack Harlow",
        "category": "Rapper",
        "real_name": "Jack Thomas Harlow"
    },
    {
        "name": "Morgan Wallen",
        "category": "Country Singer",
        "real_name": "Morgan Cole Wallen"
    },
    {
        "name": "Luke Bryan",
        "category": "Country Singer",
        "real_name": "Thomas Luther Bryan"
    },
    {
        "name": "Blake Shelton",
        "category": "Country Singer",
        "real_name": "Blake Tollison Shelton"
    },
    {
        "name": "Carrie Underwood",
        "category": "Country Singer",
        "real_name": "Carrie Marie Underwood"
    },
    {
        "name": "Miranda Lambert",
        "category": "Country Singer",
        "real_name": "Miranda Leigh Lambert"
    },
    {
        "name": "Keith Urban",
        "category": "Country Singer",
        "real_name": "Keith Lionel Urban"
    },
    {
        "name": "Tim McGraw",
        "category": "Country Singer",
        "real_name": "Samuel Timothy McGraw"
    },
    {
        "name": "Faith Hill",
        "category": "Country Singer",
        "real_name": "Audrey Faith Perry"
    },
    {
        "name": "Dolly Parton",
        "category": "Country Singer",
        "real_name": "Dolly Rebecca Parton"
    },
    {
        "name": "Willie Nelson",
        "category": "Country Singer",
        "real_name": "Willie Hugh Nelson"
    },
    {
        "name": "Johnny Cash",
        "category": "Country Singer",
        "real_name": "John R Cash"
    },
    {
        "name": "Kenny Rogers",
        "category": "Country Singer",
        "real_name": "Kenneth Donald Rogers"
    },
    {
        "name": "Garth Brooks",
        "category": "Country Singer",
        "real_name": "Troyal Garth Brooks"
    },
    {
        "name": "Shania Twain",
        "category": "Country Singer",
        "real_name": "Eilleen Regina Edwards"
    },
    {
        "name": "Reba McEntire",
        "category": "Country Singer/Actress",
        "real_name": "Reba Nell McEntire"
    },
    {
        "name": "Charlie Puth",
        "category": "Singer/Songwriter",
        "real_name": "Charles Otto Puth Jr"
    },
    {
        "name": "Halsey",
        "category": "Singer",
        "real_name": "Ashley Nicolette Frangipane"
    },
    {
        "name": "Lorde",
        "category": "Singer",
        "real_name": "Ella Marija Lani Yelich-O'Connor"
    },
    {
        "name": "Lana Del Rey",
        "category": "Singer",
        "real_name": "Elizabeth Woolridge Grant"
    },
    {
        "name": "Sia",
        "category": "Singer",
        "real_name": "Sia Kate Isobelle Furler"
    },
    {
        "name": "P!nk",
        "category": "Singer",
        "real_name": "Alecia Beth Moore"
    },
    {
        "name": "Alanis Morissette",
        "category": "Singer",
        "real_name": "Alanis Nadine Morissette"
    },
    {
        "name": "Sheryl Crow",
        "category": "Singer",
        "real_name": "Sheryl Suzanne Crow"
    },
    {
        "name": "Gwen Stefani",
        "category": "Singer/Designer",
        "real_name": "Gwen Renee Stefani"
    },
    {
        "name": "No Doubt",
        "category": "Music Group",
        "real_name": "No Doubt"
    },
    {
        "name": "Amy Winehouse",
        "category": "Singer",
        "real_name": "Amy Jade Winehouse"
    },
    {
        "name": "Amy Lee",
        "category": "Singer",
        "real_name": "Amy Lynn Hartzler"
    },
    {
        "name": "Evanescence",
        "category": "Music Group",
        "real_name": "Evanescence"
    },
    {
        "name": "Paramore",
        "category": "Music Group",
        "real_name": "Paramore"
    },
    {
        "name": "Hayley Williams",
        "category": "Singer",
        "real_name": "Hayley Nichole Williams"
    },
    {
        "name": "Fall Out Boy",
        "category": "Music Group",
        "real_name": "Fall Out Boy"
    },
    {
        "name": "Pete Wentz",
        "category": "Musician",
        "real_name": "Peter Lewis Kingston Wentz III"
    },
    {
        "name": "Panic at the Disco",
        "category": "Music Group",
        "real_name": "Panic at the Disco"
    },
    {
        "name": "Brendon Urie",
        "category": "Singer",
        "real_name": "Brendon Boyd Urie"
    },
    {
        "name": "My Chemical Romance",
        "category": "Music Group",
        "real_name": "My Chemical Romance"
    },
    {
        "name": "Gerard Way",
        "category": "Singer",
        "real_name": "Gerard Arthur Way"
    },
    {
        "name": "Twenty One Pilots",
        "category": "Music Duo",
        "real_name": "Tyler Joseph and Josh Dun"
    },
    {
        "name": "Tyler Joseph",
        "category": "Singer",
        "real_name": "Tyler Robert Joseph"
    },
    {
        "name": "Imagine Dragons",
        "category": "Music Group",
        "real_name": "Imagine Dragons"
    },
    {
        "name": "Dan Reynolds",
        "category": "Singer",
        "real_name": "Daniel Coulter Reynolds"
    },
    {
        "name": "Maroon 5",
        "category": "Music Group",
        "real_name": "Maroon 5"
    },
    {
        "name": "Adam Levine",
        "category": "Singer",
        "real_name": "Adam Noah Levine"
    },
    {
        "name": "OneRepublic",
        "category": "Music Group",
        "real_name": "OneRepublic"
    },
    {
        "name": "Ryan Tedder",
        "category": "Singer/Songwriter",
        "real_name": "Ryan Benjamin Tedder"
    },
    {
        "name": "Train",
        "category": "Music Group",
        "real_name": "Train"
    },
    {
        "name": "Pat Monahan",
        "category": "Singer",
        "real_name": "Patrick Monahan"
    },
    {
        "name": "Matchbox Twenty",
        "category": "Music Group",
        "real_name": "Matchbox Twenty"
    },
    {
        "name": "Rob Thomas",
        "category": "Singer",
        "real_name": "Robert Thomas Velline"
    },
    {
        "name": "Counting Crows",
        "category": "Music Group",
        "real_name": "Counting Crows"
    },
    {
        "name": "Third Eye Blind",
        "category": "Music Group",
        "real_name": "Third Eye Blind"
    },
    {
        "name": "Gin Blossoms",
        "category": "Music Group",
        "real_name": "Gin Blossoms"
    },
    {
        "name": "Hootie Blowfish",
        "category": "Music Group",
        "real_name": "Hootie and the Blowfish"
    },
    {
        "name": "Darius Rucker",
        "category": "Singer",
        "real_name": "Darius Carlos Rucker"
    },
    {
        "name": "Jason Mraz",
        "category": "Singer",
        "real_name": "Jason Thomas Mraz"
    },
    {
        "name": "John Mayer",
        "category": "Singer/Guitarist",
        "real_name": "John Clayton Mayer"
    },
    {
        "name": "Jack Johnson",
        "category": "Singer",
        "real_name": "Jack Hody Johnson"
    },
    {
        "name": "Ben Harper",
        "category": "Singer/Guitarist",
        "real_name": "Ben Chase Harper"
    },
    {
        "name": "Dave Matthews",
        "category": "Singer/Musician",
        "real_name": "David John Matthews"
    },
    {
        "name": "Phish",
        "category": "Music Group",
        "real_name": "Phish"
    },
    {
        "name": "Trey Anastasio",
        "category": "Musician",
        "real_name": "Ernest Joseph Anastasio III"
    },
    {
        "name": "Jack White",
        "category": "Singer/Guitarist",
        "real_name": "John Anthony Gillis"
    },
    {
        "name": "The White Stripes",
        "category": "Music Duo",
        "real_name": "The White Stripes"
    },
    {
        "name": "Meg White",
        "category": "Drummer",
        "real_name": "Megan Martha White"
    },
    {
        "name": "The Strokes",
        "category": "Music Group",
        "real_name": "The Strokes"
    },
    {
        "name": "Julian Casablancas",
        "category": "Singer",
        "real_name": "Julian Fernando Casablancas"
    }
]


# ─── HELPERS ───────────────────────────────────────────────────────────────────

def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text[:80]


def load_done() -> set:
    p = OUTPUT_DIR / "networth_done.json"
    if p.exists():
        return set(json.loads(p.read_text()))
    return set()


def save_done(slugs: set):
    p = OUTPUT_DIR / "networth_done.json"
    p.write_text(json.dumps(list(slugs), indent=2))


def load_profiles_index() -> list:
    p = OUTPUT_DIR / "networth_index.json"
    if p.exists():
        return json.loads(p.read_text())
    return []


def save_profiles_index(profiles: list):
    p = OUTPUT_DIR / "networth_index.json"
    p.write_text(json.dumps(profiles, indent=2))


# ─── WIKIPEDIA FETCH ───────────────────────────────────────────────────────────

def fetch_wiki(name: str) -> str:
    try:
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{name.replace(' ', '_')}"
        r = requests.get(url, timeout=10)
        data = r.json()
        return data.get("extract", "")[:1200]
    except Exception:
        return ""


# ─── CLAUDE PROFILE WRITER ─────────────────────────────────────────────────────

def generate_profile(celeb: dict, wiki_text: str) -> dict | None:
    name     = celeb["name"]
    category = celeb["category"]
    real     = celeb.get("real_name", name)

    prompt = f"""Write a detailed net worth profile page for: {name} ({real})
Category: {category}

Wikipedia background info (use as reference only, do NOT copy):
{wiki_text}

Return ONLY valid JSON (no markdown fences) with these exact keys:
{{
  "name": "{name}",
  "real_name": "{real}",
  "category": "{category}",
  "slug": "{slugify(name)}",
  "meta_description": "SEO meta description 150-160 chars about {name} net worth",
  "estimated_net_worth": "e.g. $500 Million",
  "net_worth_rank": "e.g. Top 10 YouTubers",
  "age": "estimated age or birth year",
  "nationality": "country",
  "known_for": "1 sentence what they are famous for",
  "income_sources": ["source1", "source2", "source3", "source4"],
  "career_highlights": ["highlight1", "highlight2", "highlight3"],
  "brand_deals": ["brand1", "brand2", "brand3"],
  "social_following": "e.g. 300M+ across all platforms",
  "biography_html": "<full biography as HTML — minimum 600 words — use <h2>, <h3>, <p>, <ul> tags>",
  "tags": ["tag1", "tag2", "tag3"]
}}

Rules:
- Net worth should be well-researched estimate based on public knowledge
- Biography must be original, engaging, detailed
- Income sources must be realistic and specific
- All data based on publicly available information"""

    try:
        r = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": CLAUDE_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-haiku-4-5-20251001",
                "max_tokens": 2500,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=60,
        )
        raw = r.json()["content"][0]["text"].strip()
        raw = re.sub(r"^```json\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
        return json.loads(raw)
    except Exception as e:
        print(f"  ✗ Claude error for {name}: {e}")
        return None


# ─── HTML TEMPLATES ────────────────────────────────────────────────────────────

PROFILE_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{{ name }} Net Worth {{ year }} | {{ site_name }}</title>
<meta name="description" content="{{ meta_description }}">
<meta name="keywords" content="{{ name }} net worth, {{ name }} earnings, {{ name }} salary, {{ category }} net worth {{ year }}">
<meta name="robots" content="index,follow">
<link rel="canonical" href="{{ site_url }}/networth/{{ slug }}.html">
<meta property="og:title" content="{{ name }} Net Worth {{ year }}">
<meta property="og:description" content="{{ meta_description }}">
<meta property="og:image" content="{{ site_url }}/celeb-images/{{ slug }}.jpg">
<meta property="og:type" content="profile">
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Person",
  "name": "{{ name }}",
  "description": "{{ meta_description }}",
  "url": "{{ site_url }}/networth/{{ slug }}.html",
  "image": "{{ site_url }}/celeb-images/{{ slug }}.jpg"
}
</script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="../style.css">
<style>
.nw-profile-hero{position:relative;background:var(--dark);color:#fff;padding:48px 0;overflow:hidden;border-bottom:3px solid var(--red)}
.nw-hero-bg{position:absolute;inset:0;background-image:url('/celeb-images/{{ slug }}.jpg');background-size:cover;background-position:top center;filter:blur(12px) brightness(0.18);transform:scale(1.1)}
.nw-hero-inner{position:relative;z-index:2;display:grid;grid-template-columns:180px 1fr;gap:32px;align-items:center}
.nw-hero-photo{width:180px;height:180px;border-radius:50%;object-fit:cover;object-position:top center;border:4px solid rgba(255,255,255,0.2);box-shadow:0 8px 32px rgba(0,0,0,0.5);display:block}
.nw-hero-name{font-family:var(--serif);font-size:clamp(2rem,5vw,3rem);font-weight:900;line-height:1.1;margin-bottom:4px}
.nw-hero-real{font-size:14px;color:rgba(255,255,255,0.5);margin-bottom:12px}
.nw-hero-cat{display:inline-block;background:var(--red);color:#fff;font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:1.5px;padding:4px 12px;margin-bottom:20px}
.nw-hero-worth{display:inline-flex;flex-direction:column;background:rgba(255,255,255,0.08);border:1px solid rgba(255,255,255,0.15);padding:14px 24px;backdrop-filter:blur(10px)}
.nw-hero-worth-label{font-size:9px;text-transform:uppercase;letter-spacing:2px;color:rgba(255,255,255,0.5);margin-bottom:4px}
.nw-hero-worth-val{font-family:var(--serif);font-size:2rem;font-weight:900;color:#fff;line-height:1}
.nw-stats-bar{background:var(--gray);border-bottom:1px solid var(--border);padding:20px 0}
.nw-stats-inner{display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:16px}
.nw-stat-item{text-align:center}
.nw-stat-label{font-size:9px;font-weight:700;text-transform:uppercase;letter-spacing:1.5px;color:var(--muted);margin-bottom:4px}
.nw-stat-value{font-family:var(--serif);font-size:15px;font-weight:700;color:var(--dark)}
.nw-body{padding:40px 0 60px}
.nw-layout{display:grid;grid-template-columns:1fr 300px;gap:40px}
.nw-section{margin-bottom:32px}
.nw-section-title{font-family:var(--serif);font-size:18px;font-weight:700;color:var(--dark);border-left:4px solid var(--red);padding-left:12px;margin-bottom:16px}
.nw-list{list-style:none;padding:0}
.nw-list li{display:flex;align-items:flex-start;gap:10px;padding:10px 0;border-bottom:1px solid var(--border);font-size:14px;color:var(--text);line-height:1.5}
.nw-list li:last-child{border-bottom:none}
.nw-list li::before{content:"✓";color:var(--red);font-weight:700;flex-shrink:0}
.nw-bio{font-size:15px;line-height:1.85;color:#222}
.nw-bio p{margin-bottom:1rem}
.nw-sidebar-card{background:var(--gray);border:1px solid var(--border);border-top:3px solid var(--dark);padding:20px;margin-bottom:20px}
.nw-sidebar-title{font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:2px;color:var(--dark);margin-bottom:14px}
.nw-similar{margin-top:40px;padding-top:32px;border-top:2px solid var(--border)}
.nw-similar-title{font-family:var(--serif);font-size:22px;font-weight:700;color:var(--dark);margin-bottom:20px}
.nw-similar-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:16px}
.nw-similar-card{border:1px solid var(--border);overflow:hidden;text-decoration:none;color:inherit;transition:transform 0.2s,box-shadow 0.2s;display:block;background:#fff}
.nw-similar-card:hover{transform:translateY(-2px);box-shadow:0 6px 20px rgba(0,0,0,0.1)}
.nw-similar-img{width:100%;aspect-ratio:1/1;object-fit:cover;object-position:top center;display:block;background:var(--dark)}
.nw-similar-body{padding:12px}
.nw-similar-name{font-weight:700;font-size:14px;color:var(--dark);margin-bottom:4px}
.nw-similar-worth{font-size:13px;color:var(--red);font-weight:700}
@media(max-width:768px){
  .nw-hero-inner{grid-template-columns:1fr;text-align:center}
  .nw-hero-photo{margin:0 auto;width:140px;height:140px}
  .nw-layout{grid-template-columns:1fr}
  .nw-similar-grid{grid-template-columns:repeat(2,1fr)}
}
</style>
</head>
<body>
{{ nav_html }}

<div class="nw-profile-hero">
  <div class="nw-hero-bg"></div>
  <div class="container">
    <div class="nw-hero-inner">
      <img src="/celeb-images/{{ slug }}.jpg" alt="{{ name }}" class="nw-hero-photo" onerror="this.style.display='none'">
      <div>
        <div class="nw-hero-name">{{ name }}</div>
        <div class="nw-hero-real">{{ real_name }}</div>
        <div class="nw-hero-cat">{{ category }}</div>
        <div class="nw-hero-worth">
          <span class="nw-hero-worth-label">Est. Net Worth {{ year }}</span>
          <span class="nw-hero-worth-val">{{ estimated_net_worth }}</span>
        </div>
      </div>
    </div>
  </div>
</div>

<div class="nw-stats-bar">
  <div class="container">
    <div class="nw-stats-inner">
      <div class="nw-stat-item"><div class="nw-stat-label">Nationality</div><div class="nw-stat-value">{{ nationality }}</div></div>
      <div class="nw-stat-item"><div class="nw-stat-label">Age</div><div class="nw-stat-value">{{ age }}</div></div>
      <div class="nw-stat-item"><div class="nw-stat-label">Social Following</div><div class="nw-stat-value">{{ social_following }}</div></div>
      <div class="nw-stat-item"><div class="nw-stat-label">Ranking</div><div class="nw-stat-value">{{ net_worth_rank }}</div></div>
    </div>
  </div>
</div>

<div class="nw-body">
  <div class="container">
    <div class="nw-layout">
      <main>
        <div class="nw-section">
          <div class="nw-section-title">About {{ name }}</div>
          <div class="nw-bio">{{ biography_html }}</div>
        </div>
        <div class="nw-section">
          <div class="nw-section-title">Income Sources</div>
          <ul class="nw-list">{% for s in income_sources %}<li>{{ s }}</li>{% endfor %}</ul>
        </div>
        <div class="nw-section">
          <div class="nw-section-title">Career Highlights</div>
          <ul class="nw-list">{% for h in career_highlights %}<li>{{ h }}</li>{% endfor %}</ul>
        </div>
        {% if similar_profiles %}
        <div class="nw-similar">
          <div class="nw-similar-title">Similar Profiles</div>
          <div class="nw-similar-grid">
            {% for p in similar_profiles %}
            <a href="{{ p.slug }}.html" class="nw-similar-card">
              <img src="/celeb-images/{{ p.slug }}.jpg" alt="{{ p.name }}" class="nw-similar-img" onerror="this.style.display='none'">
              <div class="nw-similar-body">
                <div class="nw-similar-name">{{ p.name }}</div>
                <div class="nw-similar-worth">{{ p.estimated_net_worth }}</div>
              </div>
            </a>
            {% endfor %}
          </div>
        </div>
        {% endif %}
      </main>
      <aside>
        <div class="nw-sidebar-card">
          <div class="nw-sidebar-title">Quick Facts</div>
          <ul class="nw-list">
            <li>Net Worth: {{ estimated_net_worth }}</li>
            <li>Category: {{ category }}</li>
            <li>Nationality: {{ nationality }}</li>
            <li>{{ age }}</li>
            <li>Following: {{ social_following }}</li>
          </ul>
        </div>
        <div class="nw-sidebar-card">
          <div class="nw-sidebar-title">Brand Deals</div>
          <ul class="nw-list">{% for b in brand_deals %}<li>{{ b }}</li>{% endfor %}</ul>
        </div>
        <div class="post-tags" style="margin-top:8px">
          {% for tag in tags %}<span class="tag">{{ tag }}</span>{% endfor %}
        </div>
      </aside>
    </div>
  </div>
</div>
{{ foot_html }}
</body>
</html>"""


NETWORTH_INDEX_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Celebrity Net Worth {{ year }} | {{ site_name }}</title>
<meta name="description" content="Complete list of celebrity, influencer and billionaire net worth estimates for {{ year }}. YouTubers, athletes, actors, musicians and more.">
<meta name="robots" content="index,follow">
<link rel="canonical" href="{{ site_url }}/networth/">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="../style.css">
<style>
.nw-index-hero {
  background: var(--dark);
  color: #fff;
  padding: 56px 0;
  text-align: center;
  border-bottom: 3px solid var(--red);
}
.nw-index-hero h1 {
  font-family: var(--serif);
  font-size: clamp(2rem, 5vw, 3.5rem);
  font-weight: 900;
  margin-bottom: 10px;
}
.nw-index-hero p { font-size: 16px; color: rgba(255,255,255,0.6); }
.nw-index-body { padding: 36px 0 60px; }
.nw-filter {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 28px;
  justify-content: center;
}
.nw-filter-btn {
  padding: 6px 16px;
  border: 1.5px solid var(--border);
  cursor: pointer;
  font-size: 11px;
  font-weight: 700;
  background: #fff;
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  transition: all 0.15s;
  font-family: var(--sans);
}
.nw-filter-btn.active,
.nw-filter-btn:hover { background: var(--red); color: #fff; border-color: var(--red); }
.nw-count { text-align: center; color: var(--muted); font-size: 13px; margin-bottom: 24px; }
.nw-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 16px;
}
.nw-card {
  display: flex;
  flex-direction: column;
  border: 1px solid var(--border);
  overflow: hidden;
  transition: box-shadow 0.2s, transform 0.2s;
  background: #fff;
  text-decoration: none;
  color: inherit;
}
.nw-card-img {
  width: 100%;
  aspect-ratio: 1;
  object-fit: cover;
  object-position: top center;
  display: block;
}
.nw-card:hover { box-shadow: 0 6px 24px rgba(0,0,0,0.1); transform: translateY(-2px); }
.nw-card-img {
  width: 100%;
  aspect-ratio: 1;
  object-fit: cover;
  object-position: top;
  background: var(--gray);
}
.nw-card-body { padding: 14px; flex: 1; display: flex; flex-direction: column; }
.nw-card-cat {
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 1px;
  color: var(--red);
  margin-bottom: 5px;
}
.nw-card-name {
  font-family: var(--serif);
  font-size: 15px;
  font-weight: 700;
  color: var(--dark);
  margin-bottom: 6px;
  line-height: 1.3;
  transition: color 0.2s;
}
.nw-card:hover .nw-card-name { color: var(--red); }
.nw-card-worth {
  font-size: 16px;
  font-weight: 800;
  color: var(--dark);
  margin-top: auto;
  padding-top: 8px;
  border-top: 1px solid var(--border);
}
.nw-card-meta { font-size: 11px; color: var(--muted); margin-top: 4px; }
@media (max-width: 640px) {
  .nw-grid { grid-template-columns: repeat(2, 1fr); }
}
</style>
</head>
<body>
{{ nav_html }}
<div class="nw-index-hero">
  <div class="container">
    <h1>Celebrity Net Worth {{ year }}</h1>
    <p>Estimated net worth of {{ total }} celebrities, influencers &amp; billionaires</p>
  </div>
</div>
<div class="nw-index-body">
  <div class="container">
    <div class="nw-filter" id="filters">
      <button class="nw-filter-btn active" onclick="filter('all',this)">All</button>
      {% for cat in categories %}
      <button class="nw-filter-btn" onclick="filter('{{ cat|lower|replace(' ','-') }}',this)">{{ cat }}</button>
      {% endfor %}
    </div>
    <div class="nw-count" id="count">Showing {{ total }} profiles</div>
    <div class="nw-grid" id="grid">
      {% for p in profiles %}
      <a href="{{ p.slug }}.html" class="nw-card" data-cat="{{ p.category|lower|replace(' ','-') }}">
        <img src="/celeb-images/{{ p.slug }}.jpg" class="nw-card-img" onerror="this.style.display='none'">
        <div class="nw-card-body">
          <div class="nw-card-cat">{{ p.category }}</div>
          <div class="nw-card-name">{{ p.name }}</div>
          <div class="nw-card-worth">{{ p.estimated_net_worth }}</div>
          <div class="nw-card-meta">{{ p.nationality }}</div>
        </div>
      </a>
      {% endfor %}
    </div>
  </div>
</div>
{{ foot_html }}
<script>
function filter(cat, btn) {
  document.querySelectorAll('.nw-filter-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  const cards = document.querySelectorAll('.nw-card');
  let v = 0;
  cards.forEach(c => {
    const show = cat === 'all' || c.dataset.cat === cat;
    c.style.display = show ? '' : 'none';
    if (show) v++;
  });
  document.getElementById('count').textContent = 'Showing ' + v + ' profiles';
}
</script>
</body>
</html>"""


def get_nw_nav():
    return """<div class="topbar"><div class="topbar-inner">
  <span class="topbar-left"></span>
  <a href="../" class="topbar-logo">Markets <span class="accent">News</span> Today</a>
  <span class="topbar-right">Business &middot; Finance &middot; Technology</span>
</div></div>
<nav class="navbar"><div class="navbar-inner">
  <a href="../">Home</a>
  <a href="../category-business.html">Business</a>
  <a href="../category-technology.html">Technology</a>
  <a href="../category-finance.html">Finance</a>
  <a href="../category-world.html">World</a>
  <a href="../category-sports.html">Sports</a>
  <a href="../category-health.html">Health</a>
  <a href="../category-politics.html">Politics</a>
  <a href="index.html">Net Worth</a>
</div></nav>"""

def get_nw_footer(year):
    return f"""<footer class="footer"><div class="footer-top"><div class="container"><div class="footer-grid">
  <div class="footer-brand">
    <div class="footer-logo">Markets <span class="accent">News</span> Today</div>
    <p>Your trusted source for breaking news and expert analysis.</p>
  </div>
  <div class="footer-col"><h4>Business</h4>
    <a href="../category-business.html">Business</a>
    <a href="../category-finance.html">Finance</a>
    <a href="../category-technology.html">Technology</a>
    <a href="index.html">Net Worth</a></div>
  <div class="footer-col"><h4>World</h4>
    <a href="../category-world.html">World</a>
    <a href="../category-politics.html">Politics</a>
    <a href="../category-sports.html">Sports</a>
    <a href="../category-entertainment.html">Entertainment</a></div>
  <div class="footer-col"><h4>More</h4>
    <a href="../category-health.html">Health</a>
    <a href="../category-science.html">Science</a>
    <a href="../category-travel.html">Travel</a>
    <a href="../sitemap.xml">Sitemap</a></div>
</div></div></div>
<div class="footer-btm"><div class="container">&copy; {year} Markets News Today. All rights reserved.</div></div>
</footer>"""

def get_celeb_image(name, slug):
    """Get celebrity image from Unsplash or fallback to avatar"""
    unsplash_key = os.environ.get("UNSPLASH_KEY", "")
    if unsplash_key:
        try:
            r = requests.get("https://api.unsplash.com/photos/random",
                params={"query": name + " celebrity portrait", "orientation": "squarish"},
                headers={"Authorization": "Client-ID " + unsplash_key}, timeout=8)
            if r.status_code == 200:
                return r.json()["urls"]["regular"]
        except Exception:
            pass
    seed = abs(hash(slug)) % 1000
    return f"https://picsum.photos/seed/{seed}/400/400"

def build_profile_html(data: dict, all_profiles: list = None) -> str:
    now = datetime.now(timezone.utc)
    tpl = Template(PROFILE_TEMPLATE)
    # Get similar profiles (same category, exclude self)
    similar = []
    if all_profiles:
        cat = data.get("category", "")
        slug = data.get("slug", "")
        similar = [p for p in all_profiles if p.get("category") == cat and p.get("slug") != slug][:4]
    return tpl.render(**data, site_name=SITE_NAME, site_url=SITE_URL, year=now.year,
                      nav_html=get_nw_nav(), foot_html=get_nw_footer(now.year),
                      similar_profiles=similar)


def rebuild_networth_index(profiles: list):
    now = datetime.now()
    categories = sorted(set(p["category"] for p in profiles))
    tpl = Template(NETWORTH_INDEX_TEMPLATE)
    html = tpl.render(
        profiles=sorted(profiles, key=lambda x: x["name"]),
        categories=categories,
        total=len(profiles),
        site_name=SITE_NAME,
        site_url=SITE_URL,
        year=now.year,
        nav_html=get_nw_nav(),
        foot_html=get_nw_footer(now.year),
    )
    (NETWORTH_DIR / "index.html").write_text(html)


# ─── MAIN ──────────────────────────────────────────────────────────────────────

def main():
    OUTPUT_DIR.mkdir(exist_ok=True)
    NETWORTH_DIR.mkdir(exist_ok=True)

    done     = load_done()
    profiles = load_profiles_index()
    todo     = [c for c in CELEBRITIES if slugify(c["name"]) not in done]

    print(f"👤 {len(todo)} profiles remaining | Running {PROFILES_PER_RUN} this run")

    new_count = 0
    for i, celeb in enumerate(todo[:PROFILES_PER_RUN]):
        name = celeb["name"]
        slug = slugify(name)
        print(f"  ✍  [{i+1}/{min(PROFILES_PER_RUN, len(todo))}] {name}")

        wiki = fetch_wiki(celeb.get("real_name", name))
        time.sleep(0.3)

        profile = generate_profile(celeb, wiki)
        if not profile:
            continue

        profile["slug"] = slug

        # Get celebrity image
        image_url = get_celeb_image(name, slug)
        profile["image_url"] = image_url

        # Save profile HTML
        html = build_profile_html(profile, profiles)
        (NETWORTH_DIR / f"{slug}.html").write_text(html)

        # Update index
        profiles.append({
            "name":              profile["name"],
            "slug":              slug,
            "category":          profile.get("category", celeb["category"]),
            "estimated_net_worth": profile.get("estimated_net_worth", "N/A"),
            "nationality":       profile.get("nationality", ""),
            "age":               profile.get("age", ""),
            "image_url":         image_url,
            "meta_description":  profile.get("meta_description", ""),
        })
        done.add(slug)
        new_count += 1
        time.sleep(1.5)

    print(f"\n✅ Generated {new_count} new profiles")
    print("📋 Rebuilding net worth index page...")
    rebuild_networth_index(profiles)
    save_profiles_index(profiles)
    save_done(done)
    print("🎉 Done!")


if __name__ == "__main__":
    main()

import os
import zipfile

base_dir = r"C:\Users\gimbe\OneDrive\Desktop\lol_project\dataset\champion"

champions = [
"Aatrox","Ahri","Akali","Akshan","Alistar","Ambessa","Amumu","Annie","Ashe",
"Aurelion Sol","Aurora","Bard","Blitzcrank","Brand","Braum","Caitlyn","Camille",
"Corki","Darius","Diana","Dr. Mundo","Draven","Ekko","Evelynn","Ezreal",
"Fiddlesticks","Fiora","Fizz","Galio","Garen","Gnar","Gragas","Graves","Gwen",
"Hecarim","Heimerdinger","Irelia","Janna","Jarvan IV","Jax","Jayce","Jhin",
"Jinx","Kai'Sa","Kalista","Karma","Kassadin","Katarina","Kayle","Kayn","Kennen",
"Kha'Zix","Kindred","Kog'Maw","Lee Sin","Leona","Lillia","Lissandra","Lucian",
"Lulu","Lux","Malphite","Maokai","Master Yi","Mel","Milio","Miss Fortune",
"Mordekaiser","Morgana","Nami","Nasus","Nautilus","Nidalee","Nilah","Nocturne",
"Norra","Nunu & Willump","Olaf","Orianna","Ornn","Pantheon","Poppy","Pyke",
"Rakan","Rammus","Rell","Renekton","Rengar","Riven","Rumble","Ryze","Samira",
"Senna","Seraphine","Sett","Shen","Shyvana","Singed","Sion","Sivir","Smolder",
"Sona","Soraka","Swain","Syndra","Talon","Teemo","Thresh","Tristana",
"Tryndamere","Twisted Fate","Twitch","Urgot","Varus","Vayne","Veigar","Vel'Koz",
"Vex","Vi","Viego","Viktor","Vladimir","Volibear","Warwick","Wukong","Xayah",
"Xin Zhao","Yasuo","Yone","Yuumi","Zed","Zeri","Ziggs","Zilean","Zoe","Zyra"
]

# 폴더 생성
os.makedirs(base_dir, exist_ok=True)

for champ in champions:
    path = os.path.join(base_dir, champ)
    os.makedirs(path, exist_ok=True)

print("폴더 생성 완료")

# zip 생성
zip_path = base_dir + ".zip"

with zipfile.ZipFile(zip_path, 'w') as z:
    for root, dirs, files in os.walk(base_dir):
        for d in dirs:
            folder_path = os.path.join(root, d)
            z.write(folder_path, os.path.relpath(folder_path, base_dir))

print("ZIP 생성 완료:", zip_path)
import instaloader
import re
import time

usernames = [
    "ugo_legozzi", "francescogottuso", "edoceladon", "ilsignorfans", "laragazzatascabile",
    "ettorean", "uybavolley", "navdeep.lubani", "sonoalessiorusso", "rtpiccolo",
    "gabriele_benatti_art", "yasserbenjillali", "michele.97_", "itsme.rina",
    "emiliopitrelli", "andrea_pirrera", "diegomicheli", "cicalone", "franchinomipare",
    "luigialoisi", "ruben_bondi", "nonnodigitale", "ilbaffogram", "the_regoli",
    "eleazaro", "luca_ravenna", "karmab_official", "vincenzo_comunale", "yoko_yamada_",
    "salvobygita", "gianlucatripete", "andrea_rosa_", "gabrieleruffo", "danielefabbri",
    "saverioraimondo", "dado_comedy", "paolocamilli", "angelodurolog", "michelemacaluso_",
    "pierlucamariti", "filosottile", "giuliopugliese_", "fabio_celenza", "alessandropaio",
    "matteomacallisto", "the_cerebros", "enricoluparello", "claudio_colica", "emanuele_fasano",
    "alessio_mina", "leonardobocci", "federicopalamo", "francesco_zardo", "dado_canterini",
    "lorenzo_biagiarelli", "luigidi_lorenzo", "nicolocarmine", "marcolingua", "andrealarosa",
    "tommy_kuti", "alberto.marzetti", "lorenzo.balducci", "gianmarco.tognazzi", 
    "francesco_aversa", "christian_musella", "lorenzo_baglioni", "stefano_chianucci",
    "nekucciola", "tizianolabella", "fabiana__official", "jacopoaquila_", "exulansismood",
    "nicolo.de.devitiis", "danieledacconiano"
]

L = instaloader.Instaloader(max_connection_attempts=1)
results = []

print(f"Starting email extraction for {len(usernames)} creators...")

# Initialize Micro Dork Results markdown
with open('micro_dork_results.md', 'w') as f:
    f.write("# Instaloader Results - Micro Creators\n\n")
    f.write("| Creator Username | Profile Link | Email | Followers | Bio Snippet |\n")
    f.write("| :--- | :--- | :--- | :--- | :--- |\n")

for uname in usernames:
    try:
        profile = instaloader.Profile.from_username(L.context, uname)
        bio = profile.biography
        followers = profile.followers
        
        # Only consider 10k - 300k as per user's earlier general guidance
        if not (10000 <= followers <= 300000):
            continue
            
        email_match = None
        if bio:
            email_match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', bio)
            
        if email_match:
            email = email_match.group(0)
            print(f"[{uname}] Followers: {followers} | Email: {email}")
            with open('micro_dork_results.md', 'a') as f:
                f.write(f"| **{uname}** | [Link](https://instagram.com/{uname}) | {email} | {followers} | {bio.replace(chr(10), ' ')[:100]}... |\n")
            results.append(uname)
        
        # Be nice to Instagram
        time.sleep(1)
            
    except Exception as e:
        print(f"Error fetching {uname}: {e}")

print(f"\nSaved {len(results)} creators to micro_dork_results.md")

"""
Seed script to populate the database with test users, genres and books.
Run from project root: python scripts/seed_data.py
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import User, Genre, Book
from werkzeug.security import generate_password_hash
from decimal import Decimal

USERS = [
    {"username": "padma", "city": "Mumbai", "email": "paddyy2003@gmail.com", "password": "test123", "about": "Book lover from Mumbai. Fantasy & Sci-Fi enthusiast."},
    {"username": "swapnil", "city": "Pune", "email": "padmaiyer1123@gmail.com", "password": "test123", "about": "Software engineer who reads thrillers on weekends."},
    {"username": "rahul", "city": "Delhi", "email": "rahul@example.com", "password": "test123", "about": "History buff and classic literature collector."},
    {"username": "priya", "city": "Bangalore", "email": "priya@example.com", "password": "test123", "about": "Manga addict. Currently collecting One Piece."},
    {"username": "arjun", "city": "Chennai", "email": "arjun@example.com", "password": "test123", "about": "Horror & mystery writer. Books are my research."},
]

GENRES = [
    {"name": "Fantasy", "emoji": "🧙", "quote": "Not all those who wander are lost.", "mood": "Escape into magical worlds."},
    {"name": "Romance", "emoji": "💕", "quote": "Whatever our souls are made of, his and mine are the same.", "mood": "Fall in love, one page at a time."},
    {"name": "Thriller", "emoji": "🔪", "quote": "The suspense is terrible. I hope it will last.", "mood": "Heart-racing, page-turning, edge-of-your-seat."},
    {"name": "Horror", "emoji": "👻", "quote": "Monsters are real, and ghosts are real too.", "mood": "Sleep with the lights on."},
    {"name": "Manga", "emoji": "📘", "quote": "I'll become the king of the pirates!", "mood": "Epic sagas, stunning art, unforgettable characters."},
    {"name": "Classics", "emoji": "📜", "quote": "It is a truth universally acknowledged...", "mood": "Timeless stories that shaped literature."},
    {"name": "Sci-Fi", "emoji": "🚀", "quote": "The answer to the ultimate question of life, the universe, and everything is 42.", "mood": "Explore distant galaxies and future worlds."},
    {"name": "Mystery", "emoji": "🔍", "quote": "The world is full of obvious things which nobody by any chance ever observes.", "mood": "Every page is a clue."},
    {"name": "Biography", "emoji": "👤", "quote": "The story of a life worth telling.", "mood": "Walk in someone else's shoes."},
    {"name": "Self-Help", "emoji": "🌱", "quote": "The only person you are destined to become is the person you decide to be.", "mood": "Grow. Learn. Become better."},
]

BOOKS = [
    # Fantasy (genre 1)
    {"title": "The Hobbit", "author": "J.R.R. Tolkien", "isbn": "9780547928227", "genre": "Fantasy", "description": "Bilbo Baggins is a hobbit who enjoys a comfortable, unambitious life, rarely traveling any farther than his pantry or cellar. But his contentment is disturbed when the wizard Gandalf and a company of dwarves arrive and whisk him away on an adventure.", "security_deposit": 250, "rating": 4.7},
    {"title": "A Game of Thrones", "author": "George R.R. Martin", "isbn": "9780553593716", "genre": "Fantasy", "description": "Summers span decades. Winter can last a lifetime. And the struggle for the Iron Throne has begun. From the citadel of Dragonstone to the frozen wastes beyond the Wall, powerful forces are gathering.", "security_deposit": 350, "rating": 4.5},
    {"title": "The Name of the Wind", "author": "Patrick Rothfuss", "isbn": "9780756404741", "genre": "Fantasy", "description": "Told in Kvothe's own voice, this is the tale of the magically gifted young man who grows to be the most notorious wizard his world has ever seen.", "security_deposit": 300, "rating": 4.6},
    {"title": "The Alchemist", "author": "Paulo Coelho", "isbn": "9780062315007", "genre": "Fantasy", "description": "The story of Santiago, an Andalusian shepherd boy who yearns to travel in search of a worldly treasure as extravagant as any ever found.", "security_deposit": 150, "rating": 4.2},

    # Romance (genre 2)
    {"title": "Pride and Prejudice", "author": "Jane Austen", "isbn": "9780141439518", "genre": "Classics", "description": "When Elizabeth Bennet first meets eligible bachelor Fitzwilliam Darcy, she thinks him arrogant and conceited; he is indifferent to her good looks and lively mind.", "security_deposit": 200, "rating": 4.6},
    {"title": "The Notebook", "author": "Nicholas Sparks", "isbn": "9781455582880", "genre": "Romance", "description": "Every so often a love story so captures our hearts that it becomes more than a story—it becomes an experience to remember forever.", "security_deposit": 150, "rating": 4.3},
    {"title": "Me Before You", "author": "Jojo Moyes", "isbn": "9780143124542", "genre": "Romance", "description": "Louisa Clark is an ordinary girl living an exceedingly ordinary life—steady boyfriend, close family—who has barely been farther afield than their tiny village.", "security_deposit": 180, "rating": 4.4},

    # Thriller (genre 3)
    {"title": "The Girl with the Dragon Tattoo", "author": "Stieg Larsson", "isbn": "9780307454546", "genre": "Thriller", "description": "Harriet Vanger, a scion of one of Sweden's wealthiest families, disappeared over forty years ago. Now her aged uncle wants to know what happened.", "security_deposit": 280, "rating": 4.2},
    {"title": "Gone Girl", "author": "Gillian Flynn", "isbn": "9780307588371", "genre": "Thriller", "description": "On a warm summer morning in North Carthage, Missouri, it is Nick and Amy Dunne's fifth wedding anniversary. Presents are being wrapped and reservations are being made when Nick's clever and beautiful wife disappears.", "security_deposit": 220, "rating": 4.3},
    {"title": "The Silent Patient", "author": "Alex Michaelides", "isbn": "9781250301697", "genre": "Thriller", "description": "Alicia Berenson's life is seemingly perfect. A famous painter married to an in-demand fashion photographer, she lives in a grand house. One evening her husband Gabriel returns home late and Alicia shoots him five times.", "security_deposit": 200, "rating": 4.4},

    # Horror (genre 4)
    {"title": "The Shining", "author": "Stephen King", "isbn": "9780307743657", "genre": "Horror", "description": "Jack Torrance's new job at the Overlook Hotel is the perfect chance for a fresh start. As the off-season caretaker, he'll have plenty of time to spend reconnecting with his family and working on his writing.", "security_deposit": 230, "rating": 4.4},
    {"title": "It", "author": "Stephen King", "isbn": "9781501142970", "genre": "Horror", "description": "Seven adults who first encountered the horror as children return to Derry, Maine, to face the nightmare without end—a nightmare that has haunted each of them since the summer of 1958.", "security_deposit": 280, "rating": 4.5},

    # Manga (genre 5)
    {"title": "One Piece Vol. 1", "author": "Eiichiro Oda", "isbn": "9781569319017", "genre": "Manga", "description": "As a child, Monkey D. Luffy dreamed of becoming King of the Pirates. But his life changed when he accidentally ate the Gum-Gum Fruit, an enchanted Devil Fruit that gave him the ability to stretch like rubber.", "security_deposit": 120, "rating": 4.8},
    {"title": "Death Note Vol. 1", "author": "Tsugumi Ohba", "isbn": "9781421501680", "genre": "Manga", "description": "Light Yagami is an ace student with great prospects—and he's bored out of his mind. But all that changes when he finds the Death Note, a notebook dropped by a rogue Shinigami death god.", "security_deposit": 120, "rating": 4.7},
    {"title": "Attack on Titan Vol. 1", "author": "Hajime Isayama", "isbn": "9781612620244", "genre": "Manga", "description": "In this post-apocalyptic sci-fi story, humanity has been devastated by the bizarre, giant humanoids known as the Titans. Little is known about where they came from or why they are bent on consuming mankind.", "security_deposit": 130, "rating": 4.6},

    # Classics (genre 6)
    {"title": "1984", "author": "George Orwell", "isbn": "9780451524935", "genre": "Sci-Fi", "description": "Among the seminal texts of the 20th century. A dystopian vision of a totalitarian future where Big Brother is always watching and nothing the protagonist does goes unnoticed.", "security_deposit": 180, "rating": 4.6},
    {"title": "To Kill a Mockingbird", "author": "Harper Lee", "isbn": "9780060935467", "genre": "Classics", "description": "The unforgettable novel of a childhood in a sleepy Southern town and the crisis of conscience that rocked it.", "security_deposit": 170, "rating": 4.7},
    {"title": "The Great Gatsby", "author": "F. Scott Fitzgerald", "isbn": "9780743273565", "genre": "Classics", "description": "The story of the mysteriously wealthy Jay Gatsby and his love for the beautiful Daisy Buchanan, of lavish parties on Long Island.", "security_deposit": 160, "rating": 4.3},

    # Sci-Fi (genre 7)
    {"title": "Dune", "author": "Frank Herbert", "isbn": "9780441013593", "genre": "Sci-Fi", "description": "Set on the desert planet Arrakis, Dune is the story of the boy Paul Atreides, heir to a noble family tasked with ruling an inhospitable world.", "security_deposit": 320, "rating": 4.7},
    {"title": "The Hitchhiker's Guide to the Galaxy", "author": "Douglas Adams", "isbn": "9780345391803", "genre": "Sci-Fi", "description": "Seconds before the Earth is demolished to make way for a galactic freeway, Arthur Dent is plucked off the planet by his friend Ford Prefect.", "security_deposit": 140, "rating": 4.5},
    {"title": "Ender's Game", "author": "Orson Scott Card", "isbn": "9780812550702", "genre": "Sci-Fi", "description": "Andrew 'Ender' Wiggin thinks he is playing computer-simulated war games; he is, in fact, engaged in something far more desperate. The result of genetic experimentation, Ender may be the military genius Earth desperately needs.", "security_deposit": 190, "rating": 4.5},

    # Mystery (genre 8)
    {"title": "The Da Vinci Code", "author": "Dan Brown", "isbn": "9780307474278", "genre": "Mystery", "description": "While in Paris on business, Harvard symbologist Robert Langdon receives an urgent late-night phone call: the elderly curator of the Louvre has been murdered inside the museum.", "security_deposit": 210, "rating": 4.1},
    {"title": "Sherlock Holmes: The Complete Collection", "author": "Arthur Conan Doyle", "isbn": "9780553212419", "genre": "Mystery", "description": "The complete adventures of the world's most famous detective, Sherlock Holmes, and his loyal companion Dr. John Watson.", "security_deposit": 350, "rating": 4.6},
    {"title": "And Then There Were None", "author": "Agatha Christie", "isbn": "9780062073488", "genre": "Mystery", "description": "Ten strangers are lured to an isolated island mansion off the Devon coast. Over dinner, a recorded message accuses each person of hiding a guilty secret.", "security_deposit": 150, "rating": 4.4},

    # Biography (genre 9)
    {"title": "Steve Jobs", "author": "Walter Isaacson", "isbn": "9781451648539", "genre": "Biography", "description": "Based on more than forty interviews with Jobs conducted over two years, as well as interviews with more than a hundred family members, friends, adversaries, competitors, and colleagues.", "security_deposit": 300, "rating": 4.5},
    {"title": "The Diary of a Young Girl", "author": "Anne Frank", "isbn": "9780553296983", "genre": "Biography", "description": "Discovered in the attic in which she spent the last years of her life, Anne Frank's remarkable diary has become a world classic.", "security_deposit": 130, "rating": 4.6},

    # Self-Help (genre 10)
    {"title": "Atomic Habits", "author": "James Clear", "isbn": "9780735211292", "genre": "Self-Help", "description": "No matter your goals, Atomic Habits offers a proven framework for improving—every day. James Clear reveals practical strategies that will teach you exactly how to form good habits, break bad ones.", "security_deposit": 200, "rating": 4.7},
    {"title": "The 7 Habits of Highly Effective People", "author": "Stephen R. Covey", "isbn": "9781982137274", "genre": "Self-Help", "description": "One of the most inspiring and impactful books ever written. This beloved classic presents a principle-centered approach for solving personal and professional problems.", "security_deposit": 190, "rating": 4.3},
]


def seed():
    with app.app_context():
        # --- Genres ---
        for g in GENRES:
            if not Genre.query.filter_by(name=g["name"]).first():
                db.session.add(Genre(**g))
        db.session.commit()

        # Resolve genre name -> id lookup
        genre_map = {g.name: g.id for g in Genre.query.all()}
        print(f"Genres: {len(genre_map)} ready")

        # --- Users ---
        owner_ids = {}
        for u in USERS:
            user = User.query.filter_by(username=u["username"]).first()
            if user:
                # Update password if user exists (so login works)
                user.password = generate_password_hash(u["password"])
                user.city = u["city"]
                user.about = u["about"]
                owner_ids[u["username"]] = user.id
            else:
                user = User(
                    username=u["username"],
                    city=u["city"],
                    email=u["email"],
                    password=generate_password_hash(u["password"]),
                    about=u["about"],
                )
                db.session.add(user)
                db.session.flush()
                owner_ids[u["username"]] = user.id
        db.session.commit()
        print(f"Users: {owner_ids}")

        # --- Books ---
        # Assign books to users in a round-robin way
        owner_usernames = list(owner_ids.keys())
        book_count = 0
        for i, b in enumerate(BOOKS):
            existing = Book.query.filter_by(title=b["title"], author=b["author"]).first()
            isbn = b.get("isbn", "")
            image_url = f"https://covers.openlibrary.org/b/isbn/{isbn}-L.jpg" if isbn else b.get("image", "")
            if existing:
                if isbn:
                    existing.image = image_url
                existing.security_deposit = Decimal(str(b["security_deposit"]))
                existing.rating = b["rating"]
            else:
                owner = owner_usernames[i % len(owner_usernames)]
                book = Book(
                    title=b["title"],
                    author=b["author"],
                    description=b["description"],
                    security_deposit=Decimal(str(b["security_deposit"])),
                    rating=b["rating"],
                    image=image_url,
                    owner_id=owner_ids[owner],
                    genre_id=genre_map[b["genre"]],
                )
                db.session.add(book)
                book_count += 1
        db.session.commit()
        print(f"Books added: {book_count}")

        print("\n--- SEED COMPLETE ---")
        print("Default password for all users: test123")


if __name__ == "__main__":
    seed()

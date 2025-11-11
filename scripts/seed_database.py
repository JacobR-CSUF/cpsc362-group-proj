"""
Database Seeding Script
Creates test users for development and testing
Includes Faker support for realistic data generation
"""
import asyncio
from datetime import datetime
from pathlib import Path
import sys
import random
from dotenv import load_dotenv

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
dotenv_path = project_root / ".env" 
load_dotenv(dotenv_path)

from apps.api.app.services.supabase_client import get_supabase_client

# Try to import Faker (optional)
try:
    from faker import Faker
    FAKER_AVAILABLE = True
except ImportError:
    FAKER_AVAILABLE = False

# Global verbose flag
VERBOSE = False


async def seed_users():
    """Create hardcoded test users"""
    print("\n" + "="*60)
    print("  Creating Hardcoded Test Users")
    print("="*60 + "\n")
    
    client = get_supabase_client()
    
    test_users = [
        {"username": "john_doe", "email": "john@example.com", "profile_pic": "https://i.pravatar.cc/150?img=1"},
        {"username": "jane_smith", "email": "jane@example.com", "profile_pic": "https://i.pravatar.cc/150?img=2"},
        {"username": "bob_wilson", "email": "bob@example.com", "profile_pic": "https://i.pravatar.cc/150?img=3"},
        {"username": "alice_johnson", "email": "alice@example.com", "profile_pic": "https://i.pravatar.cc/150?img=4"},
        {"username": "charlie_brown", "email": "charlie@example.com", "profile_pic": "https://i.pravatar.cc/150?img=5"}
    ]
    
    created_users = []
    
    for user_data in test_users:
        try:
            existing = client.table("users").select("*").eq("email", user_data["email"]).execute()
            
            if existing.data and len(existing.data) > 0:
                print(f"⚠️  {user_data['username']} already exists")
                created_users.append(existing.data[0])
                continue
            
            response = client.table("users").insert(user_data).execute()
            
            if response.data and len(response.data) > 0:
                user = response.data[0]
                created_users.append(user)
                print(f"✅ Created: {user['username']}")
                
        except Exception as e:
            print(f"❌ Error: {user_data['username']}")
    
    print(f"\n✅ {len(created_users)} users ready\n{'='*60}\n")
    return created_users


async def seed_realistic_users(count=20):
    """Create realistic users using Faker with multiple languages"""
    if not FAKER_AVAILABLE:
        print("\n❌ Faker not installed! Run: pip install faker")
        return []
    
    print("\n" + "="*60)
    print(f"  Generating {count} Realistic Users 🌍")
    print("="*60 + "\n")
    
    client = get_supabase_client()
    
    # Multiple locales for variety!
    locales = ['en_US', 'ja_JP', 'es_ES', 'fr_FR', 'de_DE', 'ko_KR', 'it_IT', 'pt_BR']
    fakers = {locale: Faker(locale) for locale in locales}
    
    created_users = []
    
    for i in range(count):
        try:
            locale = random.choice(locales)
            fake = fakers[locale]
            
            username = fake.user_name() + str(random.randint(100, 999))
            email = fake.email()
            profile_pic = f"https://i.pravatar.cc/150?u={fake.uuid4()}"
            
            user_data = {"username": username, "email": email, "profile_pic": profile_pic}
            
            response = client.table("users").insert(user_data).execute()
            
            if response.data:
                user = response.data[0]
                created_users.append(user)
                flag = {'en_US': '🇺🇸', 'ja_JP': '🇯🇵', 'es_ES': '🇪🇸', 'fr_FR': '🇫🇷', 
                        'de_DE': '🇩🇪', 'ko_KR': '🇰🇷', 'it_IT': '🇮🇹', 'pt_BR': '🇧🇷'}
                print(f"{flag.get(locale, '🌍')} [{i+1}/{count}] {username}")
            
        except:
            continue
    
    print(f"\n✅ Created {len(created_users)} users\n{'='*60}\n")
    return created_users


async def seed_realistic_media(users, count=40):
    """Generate realistic media with Faker"""
    if not FAKER_AVAILABLE or len(users) == 0:
        return []
    
    print("\n" + "="*60)
    print(f"  Generating {count} Realistic Media 📸")
    print("="*60 + "\n")
    
    client = get_supabase_client()
    fake = Faker()
    
    media_types = ["image", "image", "image", "video"]  # More images than videos
    
    # Fun media descriptions
    image_descriptions = [
        "Captured this amazing moment! 📷✨",
        "Nature at its finest 🌿",
        "Can't believe I got this shot! 😍",
        "Golden hour hits different 🌅",
        "Aesthetic vibes only ✨",
        "Picture perfect day 📸",
        "This view though! 😱",
        "Making memories 💫",
    ]
    
    video_descriptions = [
        "Behind the scenes 🎬",
        "Watch till the end! 🎥",
        "This was wild! 😂",
        "Epic moment captured 🎞️",
        "Can't stop watching this 🔁",
        "POV: Living my best life 🎥",
    ]
    
    created_media = []
    
    for i in range(count):
        try:
            user = random.choice(users)
            media_type = random.choice(media_types)
            
            if media_type == "image":
                description = random.choice(image_descriptions) + " " + fake.sentence(nb_words=random.randint(3, 8))
            else:
                description = random.choice(video_descriptions) + " " + fake.sentence(nb_words=random.randint(3, 8))
            
            media_data = {
                "user_id": user["id"],
                "url": fake.image_url(width=random.choice([640, 800, 1024]), height=random.choice([480, 600, 768])),
                "type": media_type,
                "description": description
            }
            
            response = client.table("media").insert(media_data).execute()
            
            if response.data:
                created_media.append(response.data[0])
                emoji = "📷" if media_type == "image" else "🎥"
                print(f"{emoji} [{i+1}/{count}] {user['username']}: {description[:50]}...")
            
        except:
            continue
    
    print(f"\n✅ Created {len(created_media)} media items\n{'='*60}\n")
    return created_media


async def seed_realistic_posts(users, media_list, count=50):
    """Generate realistic posts with Faker, some with media attachments"""
    if not FAKER_AVAILABLE or len(users) == 0:
        return []
    
    print("\n" + "="*60)
    print(f"  Generating {count} Realistic Posts 📝")
    print("="*60 + "\n")
    
    client = get_supabase_client()
    
    # Multiple fakers for different languages
    fakers = [Faker('en_US'), Faker('ja_JP'), Faker('es_ES'), Faker('fr_FR')]
    visibilities = ['public', 'public', 'public', 'followers', 'private']  # More public posts
    
    created_posts = []
    
    for i in range(count):
        try:
            user = random.choice(users)
            fake = random.choice(fakers)
            
            # 50% chance to attach media if available
            media_id = None
            if media_list and random.random() > 0.5:
                # Try to find media from this user
                user_media = [m for m in media_list if m["user_id"] == user["id"]]
                if user_media:
                    media_id = random.choice(user_media)["id"]
            
            # Generate realistic captions
            caption_types = [
                fake.sentence(nb_words=random.randint(5, 15)),
                fake.catch_phrase() + " ✨",
                fake.text(max_nb_chars=random.randint(50, 200)),
            ]
            
            post_data = {
                "user_id": user["id"],
                "media_id": media_id,
                "caption": random.choice(caption_types),
                "visibility": random.choice(visibilities)
            }
            
            response = client.table("posts").insert(post_data).execute()
            
            if response.data:
                created_posts.append(response.data[0])
                media_indicator = "🖼️ " if media_id else ""
                print(f"{media_indicator}📝 [{i+1}/{count}] {user['username']}: {post_data['caption'][:40]}...")
            
        except:
            continue
    
    print(f"\n✅ Created {len(created_posts)} posts\n{'='*60}\n")
    return created_posts


async def seed_realistic_follows(users):
    """Create realistic follow relationships"""
    if len(users) < 2:
        return
    
    print("\n" + "="*60)
    print("  Generating Realistic Follows 👥")
    print("="*60 + "\n")
    
    client = get_supabase_client()
    created = 0
    connections = []
    
    for user in users:
        # Each user follows 3-8 random others
        num_follows = random.randint(3, min(8, len(users)-1))
        potential = [u for u in users if u["id"] != user["id"]]
        
        if not potential:
            continue
        
        to_follow = random.sample(potential, min(num_follows, len(potential)))
        
        for followed in to_follow:
            try:
                client.table("follows").insert({
                    "following_user_id": user["id"],
                    "followed_user_id": followed["id"]
                }).execute()
                created += 1
                
                if VERBOSE:
                    print(f"  👤 {user['username']} → {followed['username']}")
                else:
                    connections.append((user['username'], followed['username']))
                    
            except:
                continue
    
    if not VERBOSE and connections:
        # Show sample of connections
        sample_size = min(10, len(connections))
        print(f"Sample of {sample_size} connections (use --verbose for all):")
        for follower, followed in random.sample(connections, sample_size):
            print(f"  👤 {follower} → {followed}")
        print(f"  ... and {len(connections) - sample_size} more")
    
    print(f"\n✅ Created {created} follow relationships\n{'='*60}\n")


async def seed_realistic_likes(users, posts):
    """Generate realistic likes on posts"""
    if len(users) == 0 or len(posts) == 0:
        return
    
    print("\n" + "="*60)
    print("  Generating Realistic Likes ❤️")
    print("="*60 + "\n")
    
    client = get_supabase_client()
    created = 0
    like_records = []
    
    for post in posts:
        # Each post gets 0-15 likes (more realistic distribution)
        num_likes = random.choices([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 15], 
                                   weights=[5, 10, 15, 15, 12, 10, 8, 7, 5, 4, 3, 3, 2])[0]
        
        potential_likers = [u for u in users if u["id"] != post["user_id"]]
        
        if not potential_likers or num_likes == 0:
            continue
        
        likers = random.sample(potential_likers, min(num_likes, len(potential_likers)))
        
        # Get post owner username
        post_owner = next((u for u in users if u["id"] == post["user_id"]), None)
        
        for user in likers:
            try:
                client.table("likes").insert({
                    "post_id": post["id"],
                    "user_id": user["id"]
                }).execute()
                created += 1
                
                if VERBOSE and post_owner:
                    post_caption = post.get('caption', 'a post')[:30]
                    print(f"  ❤️  {user['username']} liked {post_owner['username']}'s post: \"{post_caption}...\"")
                else:
                    like_records.append((user['username'], post_owner['username'] if post_owner else 'unknown'))
                    
            except:
                continue
    
    if not VERBOSE and like_records:
        # Show sample of likes
        sample_size = min(15, len(like_records))
        print(f"Sample of {sample_size} likes (use --verbose for all):")
        for liker, post_owner in random.sample(like_records, sample_size):
            print(f"  ❤️  {liker} → {post_owner}'s post")
        print(f"  ... and {len(like_records) - sample_size} more")
    
    print(f"\n✅ Created {created} likes\n{'='*60}\n")


async def clear_test_data():
    """Clear all test data from database"""
    print("\n⚠️  WARNING: This will delete ALL data!")
    confirm = input("Type 'yes' to confirm: ")
    
    if confirm.lower() != 'yes':
        print("❌ Cancelled")
        return
    
    client = get_supabase_client()
    print("\nClearing data...")
    
    tables = [
        ("comments", "id"), ("likes", "id"), ("posts", "id"),
        ("media", "id"), ("messages", "id"), ("friend_suggestions", "id"),
    ]
    
    for table, id_col in tables:
        try:
            client.table(table).delete().neq(id_col, "00000000-0000-0000-0000-000000000000").execute()
            print(f"✅ Cleared {table}")
        except:
            pass
    
    try:
        client.table("follows").delete().neq("following_user_id", "00000000-0000-0000-0000-000000000000").execute()
        print(f"✅ Cleared follows")
    except:
        pass
    
    try:
        client.table("users").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
        print(f"✅ Cleared users")
    except:
        pass
    
    print("\n✅ All data cleared!\n")


async def main():
    """Main menu"""
    global VERBOSE
    
    # Check for verbose flag
    if len(sys.argv) > 1 and (sys.argv[1] == '--verbose' or sys.argv[1] == '-v'):
        VERBOSE = True
        print("\n🔊 Verbose mode enabled - showing all connections!")
    
    print("\n" + "="*60)
    print("  Database Seeding Menu")
    if VERBOSE:
        print("  (Verbose Mode Active 🔊)")
    print("="*60)
    print("\n1. Seed 5 hardcoded test users")
    print("2. Seed 20 realistic users (Faker) 🌍")
    print("3. Seed EVERYTHING realistic (users, media, posts, follows, likes) 🎭")
    print("4. Clear all test data")
    print("5. Exit")
    
    if not VERBOSE:
        print("\nTip: Use --verbose or -v flag to see all connections!")
        print("Example: python scripts/seed_database.py --verbose")
    
    choice = input("\nSelect (1-5): ").strip()
    
    if choice == "1":
        await seed_users()
    
    elif choice == "2":
        if not FAKER_AVAILABLE:
            print("\n❌ Install Faker: pip install faker")
        else:
            await seed_realistic_users(20)
    
    elif choice == "3":
        if not FAKER_AVAILABLE:
            print("\n❌ Install Faker: pip install faker")
        else:
            users = await seed_realistic_users(20)
            if users:
                media = await seed_realistic_media(users, 40)
                posts = await seed_realistic_posts(users, media, 50)
                await seed_realistic_follows(users)
                if posts:
                    await seed_realistic_likes(users, posts)
    
    elif choice == "4":
        await clear_test_data()
    
    elif choice == "5":
        print("\n👋 Goodbye!")
        return
    
    else:
        print("\n❌ Invalid option")
    
    print("\n✅ Complete! Test at: http://localhost:8001/api/v1/users/")


if __name__ == "__main__":
    asyncio.run(main())

"""
Database Setup Script
Runs the setup-supabase.sql file to create tables
"""
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv(project_root / ".env")

from apps.api.app.services.supabase_client import get_supabase_client

def setup_database():
    """Run the SQL setup script"""
    print("\n" + "="*60)
    print("  Database Setup Script")
    print("="*60 + "\n")
    
    # Read the SQL file
    sql_file = project_root / "scripts" / "setup-supabase.sql"
    
    if not sql_file.exists():
        print(f"❌ SQL file not found: {sql_file}")
        return False
    
    with open(sql_file, 'r') as f:
        sql_content = f.read()
    
    print(f"📄 Reading SQL from: {sql_file}\n")
    
    # Get Supabase client
    try:
        client = get_supabase_client()
        print("✅ Connected to Supabase\n")
    except Exception as e:
        print(f"❌ Failed to connect to Supabase: {e}")
        return False
    
    # Split SQL into individual statements
    statements = [s.strip() for s in sql_content.split(';') if s.strip() and not s.strip().startswith('--')]
    
    print(f"Found {len(statements)} SQL statements to execute\n")
    print("="*60)
    
    success_count = 0
    error_count = 0
    
    for i, statement in enumerate(statements, 1):
        # Skip comments and empty statements
        if not statement or statement.startswith('/*'):
            continue
            
        # Get table name for display
        table_name = "unknown"
        if "CREATE TABLE" in statement.upper():
            parts = statement.upper().split("CREATE TABLE")
            if len(parts) > 1:
                table_name = parts[1].split()[0].replace("IF", "").replace("NOT", "").replace("EXISTS", "").strip()
        
        try:
            # Execute via Supabase RPC (this is a workaround since Supabase client doesn't have direct SQL execution)
            # Note: This might not work for all statements. If it fails, use psql or Studio instead.
            print(f"[{i}/{len(statements)}] Executing: {table_name}...", end=" ")
            
            # For CREATE TABLE statements, we'll use a workaround
            # The proper way is to use psql or Supabase Studio
            print("⚠️  SKIPPED (use Supabase Studio or psql)")
            
        except Exception as e:
            error_count += 1
            print(f"❌ ERROR: {str(e)[:100]}")
    
    print("\n" + "="*60)
    print(f"\n⚠️  This script cannot execute raw SQL directly.")
    print("\nPlease use one of these methods instead:\n")
    print("1. **Supabase Studio** (EASIEST):")
    print("   - Open http://100.92.51.75:3100")
    print("   - Go to SQL Editor")
    print("   - Copy/paste scripts/setup-supabase.sql")
    print("   - Click 'Run'\n")
    
    print("2. **psql command line**:")
    print("   psql \"postgresql://postgres:postgres@100.92.51.75:5432/postgres\" \\")
    print("       -f scripts/setup-supabase.sql\n")
    
    print("3. **Using Python with psycopg2**:")
    print("   pip install psycopg2-binary")
    print("   # Then use psycopg2 to execute the SQL\n")
    
    return False


if __name__ == "__main__":
    setup_database()

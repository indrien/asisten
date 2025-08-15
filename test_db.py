import asyncio
from config.database import test_connection

async def main():
    """Test database connection"""
    print("🔗 Testing database connection...")
    try:
        await test_connection()
        print("✅ Database connection successful!")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False
    return True

if __name__ == "__main__":
    asyncio.run(main())

from app import create_app
from app.database import initialize_database, seed_database


if __name__ == "__main__":
    application = create_app()

    database_path = initialize_database(
        application
    )

    counts = seed_database(
        application
    )

    print(
        f"Database initialized: {database_path}"
    )

    print("Seed data summary:")

    for table_name, count in counts.items():
        print(
            f"  {table_name}: {count}"
        )
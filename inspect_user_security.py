import argparse

from app import create_app
from app.extensions import db
from app.models import User


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Inspect password-storage properties of a local user."
    )

    parser.add_argument(
        "--username",
        required=True,
        help="Username to inspect.",
    )

    return parser.parse_args()


def main():
    args = parse_arguments()

    application = create_app()

    with application.app_context():

        user = db.session.execute(
            db.select(User).where(
                User.username == args.username
            )
        ).scalar_one_or_none()

        if user is None:
            raise SystemExit(
                f"User not found: {args.username}"
            )

        password_hash = user.password_hash

        print(
            f"Username: {user.username}"
        )

        print(
            f"Role: {user.role}"
        )

        print(
            f"Password hash present: {bool(password_hash)}"
        )

        if password_hash:
            print(
                f"Hash length: {len(password_hash)}"
            )

            scheme = password_hash.split(
                "$",
                1,
            )[0]

            print(
                f"Hash scheme prefix: {scheme}"
            )

            print(
                "Full password hash: [not displayed]"
            )

            print(
                "Plaintext password: [not stored/displayed]"
            )

        else:
            print(
                "Password hash is currently empty."
            )


if __name__ == "__main__":
    main()
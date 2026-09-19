import argparse
import getpass

from werkzeug.security import generate_password_hash

from app import create_app
from app.database import initialize_database
from app.extensions import db
from app.models import User


MIN_PASSWORD_LENGTH = 8

VALID_ROLES = {
    "admin",
    "assessor",
}


def parse_arguments():
    parser = argparse.ArgumentParser(
        description=(
            "Create or update a local development user "
            "for the Cybersecurity Risk Assessment Framework."
        )
    )

    parser.add_argument(
        "--username",
        required=True,
        help="Username for the development account.",
    )

    parser.add_argument(
        "--role",
        required=True,
        choices=sorted(VALID_ROLES),
        help="Role for the account.",
    )

    return parser.parse_args()


def main():
    args = parse_arguments()

    username = args.username.strip()

    if not username:
        raise SystemExit(
            "Error: username cannot be empty."
        )

    application = create_app()

    initialize_database(
        application
    )

    with application.app_context():

        password = getpass.getpass(
            "Development password (not shown): "
        )

        confirmation = getpass.getpass(
            "Confirm password: "
        )

        if len(password) < MIN_PASSWORD_LENGTH:
            raise SystemExit(
                (
                    "Error: password must contain at least "
                    f"{MIN_PASSWORD_LENGTH} characters."
                )
            )

        if password != confirmation:
            raise SystemExit(
                "Error: passwords do not match."
            )

        user = db.session.execute(
            db.select(User).where(
                User.username == username
            )
        ).scalar_one_or_none()

        if user is None:

            user = User(
                username=username,
                role=args.role,
            )

            db.session.add(user)

        else:

            user.role = args.role

        user.password_hash = generate_password_hash(
            password
        )

        db.session.commit()

        print()
        print(
            f"Development user ready: {user.username}"
        )
        print(
            f"Role: {user.role}"
        )
        print(
            "Password stored as a hash; "
            "the password itself is not stored."
        )


if __name__ == "__main__":
    main()
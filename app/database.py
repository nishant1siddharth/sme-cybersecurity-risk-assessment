from pathlib import Path

from .extensions import db


def initialize_database(app) -> Path:
    """Create the configured database and all registered tables."""
    from . import models  # noqa: F401

    Path(app.instance_path).mkdir(
        parents=True,
        exist_ok=True,
    )

    with app.app_context():
        db.create_all()
        database_path = app.config["DATABASE_PATH"]

    return Path(database_path)


def seed_database(app) -> dict[str, int]:
    """Insert idempotent fictional demonstration data."""
    from .models import (
        Assessment,
        Asset,
        Mitigation,
        Organization,
        RiskItem,
        User,
    )

    with app.app_context():

        assessor = db.session.execute(
            db.select(User).where(
                User.username == "demo_assessor"
            )
        ).scalar_one_or_none()

        if assessor is None:
            assessor = User(
                username="demo_assessor",
                password_hash=None,
                role="assessor",
            )

            db.session.add(assessor)
            db.session.flush()

        organizations_data = [
            {
                "name": "Small Retail Business",
                "business_type": "Retail",
                "description": (
                    "A fictional small retail store used for "
                    "cybersecurity assessment demonstrations."
                ),
            },
            {
                "name": "Educational Institute",
                "business_type": "Education",
                "description": (
                    "A fictional educational institute used for "
                    "cybersecurity assessment demonstrations."
                ),
            },
            {
                "name": "Small IT Company",
                "business_type": "Information Technology",
                "description": (
                    "A fictional small IT services company used for "
                    "cybersecurity assessment demonstrations."
                ),
            },
        ]

        organizations = []

        for item in organizations_data:
            organization = db.session.execute(
                db.select(Organization).where(
                    Organization.name == item["name"]
                )
            ).scalar_one_or_none()

            if organization is None:
                organization = Organization(**item)
                db.session.add(organization)
                db.session.flush()

            organizations.append(organization)

        assets_by_org = {
            "Small Retail Business": [
                (
                    "Point-of-Sale System",
                    "Business System",
                    "Fictional POS terminal used for sales transactions.",
                ),
                (
                    "Customer Records",
                    "Data",
                    "Fictional customer information stored for business operations.",
                ),
                (
                    "Business Wi-Fi",
                    "Network",
                    "Fictional wireless network used by staff devices.",
                ),
            ],
            "Educational Institute": [
                (
                    "Student Database",
                    "Data",
                    "Fictional student records stored by the institute.",
                ),
                (
                    "Faculty Computers",
                    "Endpoint",
                    "Fictional computers used by teaching staff.",
                ),
                (
                    "Institute Wi-Fi",
                    "Network",
                    "Fictional wireless network serving staff and students.",
                ),
            ],
            "Small IT Company": [
                (
                    "Source Code Repository",
                    "Application Data",
                    "Fictional repository containing company software source code.",
                ),
                (
                    "Developer Workstations",
                    "Endpoint",
                    "Fictional workstations used by developers.",
                ),
                (
                    "Cloud Storage",
                    "Cloud Service",
                    "Fictional cloud storage used for business documents and project files.",
                ),
            ],
        }

        assets = {}

        for organization in organizations:
            for name, asset_type, description in assets_by_org[
                organization.name
            ]:
                asset = db.session.execute(
                    db.select(Asset).where(
                        Asset.organization_id == organization.id,
                        Asset.name == name,
                    )
                ).scalar_one_or_none()

                if asset is None:
                    asset = Asset(
                        organization=organization,
                        name=name,
                        asset_type=asset_type,
                        description=description,
                    )

                    db.session.add(asset)
                    db.session.flush()

                assets[(organization.name, name)] = asset

        mitigations_data = [
            (
                "Phishing",
                "Multi-Factor Authentication",
                (
                    "Require a second authentication factor for "
                    "accounts that support it."
                ),
                "High",
            ),
            (
                "Phishing",
                "Employee Awareness Training",
                (
                    "Train staff to identify suspicious messages, "
                    "links, attachments, and impersonation attempts."
                ),
                "High",
            ),
            (
                "Ransomware",
                "Offline or Immutable Backups",
                (
                    "Maintain tested backups protected from unauthorized "
                    "modification or deletion."
                ),
                "Critical",
            ),
            (
                "Insider Threat",
                "Role-Based Access Control",
                (
                    "Give users only the permissions required for "
                    "their assigned responsibilities."
                ),
                "High",
            ),
            (
                "Unpatched Software",
                "Regular Patch Management",
                (
                    "Track software updates and apply security patches "
                    "within defined maintenance windows."
                ),
                "High",
            ),
        ]

        mitigations = {}

        for (
            threat_type,
            name,
            description,
            priority,
        ) in mitigations_data:

            mitigation = db.session.execute(
                db.select(Mitigation).where(
                    Mitigation.threat_type == threat_type,
                    Mitigation.mitigation_name == name,
                )
            ).scalar_one_or_none()

            if mitigation is None:
                mitigation = Mitigation(
                    threat_type=threat_type,
                    mitigation_name=name,
                    description=description,
                    priority=priority,
                )

                db.session.add(mitigation)
                db.session.flush()

            mitigations[(threat_type, name)] = mitigation

        retail = organizations[0]

        retail_assessment = db.session.execute(
            db.select(Assessment).where(
                Assessment.organization_id == retail.id,
                Assessment.assessor_id == assessor.id,
            )
        ).scalar_one_or_none()

        if retail_assessment is None:
            retail_assessment = Assessment(
                organization=retail,
                assessor=assessor,
            )

            db.session.add(retail_assessment)
            db.session.flush()

        existing_risk_count = db.session.scalar(
            db.select(
                db.func.count(RiskItem.id)
            ).where(
                RiskItem.assessment_id == retail_assessment.id
            )
        )

        if existing_risk_count == 0:

            phishing_risk = RiskItem(
                assessment=retail_assessment,
                asset=assets[
                    (
                        "Small Retail Business",
                        "Customer Records",
                    )
                ],
                threat="Phishing",
                vulnerability=(
                    "Employees may follow fraudulent links "
                    "and disclose account credentials."
                ),
                likelihood=4,
                impact=5,
                risk_score=20,
                risk_level="Critical",
                recommendation=(
                    "Enable MFA and provide recurring "
                    "phishing-awareness training."
                ),
            )

            ransomware_risk = RiskItem(
                assessment=retail_assessment,
                asset=assets[
                    (
                        "Small Retail Business",
                        "Point-of-Sale System",
                    )
                ],
                threat="Ransomware",
                vulnerability=(
                    "A compromised endpoint could disrupt "
                    "business operations and encrypt important files."
                ),
                likelihood=3,
                impact=5,
                risk_score=15,
                risk_level="High",
                recommendation=(
                    "Maintain protected backups and keep endpoint "
                    "and operating-system patches current."
                ),
            )

            db.session.add_all(
                [
                    phishing_risk,
                    ransomware_risk,
                ]
            )

            db.session.flush()

            phishing_risk.mitigations.extend(
                [
                    mitigations[
                        (
                            "Phishing",
                            "Multi-Factor Authentication",
                        )
                    ],
                    mitigations[
                        (
                            "Phishing",
                            "Employee Awareness Training",
                        )
                    ],
                ]
            )

            ransomware_risk.mitigations.append(
                mitigations[
                    (
                        "Ransomware",
                        "Offline or Immutable Backups",
                    )
                ]
            )

        db.session.commit()

        return {
            "users": db.session.scalar(
                db.select(db.func.count(User.id))
            )
            or 0,
            "organizations": db.session.scalar(
                db.select(db.func.count(Organization.id))
            )
            or 0,
            "assets": db.session.scalar(
                db.select(db.func.count(Asset.id))
            )
            or 0,
            "assessments": db.session.scalar(
                db.select(db.func.count(Assessment.id))
            )
            or 0,
            "risk_items": db.session.scalar(
                db.select(db.func.count(RiskItem.id))
            )
            or 0,
            "mitigations": db.session.scalar(
                db.select(db.func.count(Mitigation.id))
            )
            or 0,
        }
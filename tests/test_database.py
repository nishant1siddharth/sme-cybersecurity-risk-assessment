import pytest

from app import create_app
from app.extensions import db
from app.models import (
    Assessment,
    Asset,
    Mitigation,
    Organization,
    RiskItem,
    User,
)


@pytest.fixture
def app():
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite://",
            "DATABASE_PATH": ":memory:",
        }
    )

    with application.app_context():
        db.create_all()

        yield application

        db.session.remove()
        db.drop_all()


def test_database_tables_are_created(app):
    expected_tables = {
        "users",
        "organizations",
        "assessments",
        "assets",
        "risk_items",
        "mitigations",
        "risk_item_mitigations",
    }

    assert expected_tables.issubset(
        set(db.metadata.tables)
    )


def test_seed_data_is_inserted_and_idempotent(app):
    from app.database import seed_database

    first_counts = seed_database(app)
    second_counts = seed_database(app)

    assert first_counts == second_counts

    assert first_counts["users"] == 1
    assert first_counts["organizations"] == 3
    assert first_counts["assets"] == 9
    assert first_counts["assessments"] == 1
    assert first_counts["risk_items"] == 2
    assert first_counts["mitigations"] == 5

    with app.app_context():

        seeded_assessment = db.session.execute(
            db.select(Assessment).where(
                Assessment.id == 1
            )
        ).scalar_one()

        assert len(
            seeded_assessment.risk_items
        ) == 2

        assert len(
            seeded_assessment.risk_items[0].mitigations
        ) >= 1


def test_create_user_and_organization(app):
    with app.app_context():

        user = User(
            username="test_assessor",
            password_hash="test-hash",
            role="assessor",
        )

        organization = Organization(
            name="Test Retail Store",
            business_type="Retail",
            description=(
                "Fictional organization used only "
                "by the test suite."
            ),
        )

        db.session.add_all(
            [
                user,
                organization,
            ]
        )

        db.session.commit()

        assert user.id is not None
        assert organization.id is not None
        assert organization.created_at is not None


def test_create_assets_assessment_and_risk_relationships(app):
    with app.app_context():

        user = User(
            username="relationship_tester",
            password_hash="test-hash",
            role="assessor",
        )

        organization = Organization(
            name="Relationship Test Business",
            business_type="Retail",
        )

        db.session.add_all(
            [
                user,
                organization,
            ]
        )

        db.session.flush()

        asset = Asset(
            organization=organization,
            name="Customer Database",
            asset_type="Data",
            description="Fictional customer data asset.",
        )

        assessment = Assessment(
            organization=organization,
            assessor=user,
        )

        db.session.add_all(
            [
                asset,
                assessment,
            ]
        )

        db.session.flush()

        risk = RiskItem(
            assessment=assessment,
            asset=asset,
            threat="Phishing",
            vulnerability=(
                "Users may disclose credentials "
                "through fraudulent messages."
            ),
            likelihood=4,
            impact=5,
            risk_score=20,
            risk_level="Critical",
            recommendation="Use MFA and awareness training.",
        )

        db.session.add(risk)
        db.session.commit()

        loaded_organization = db.get_or_404(
            Organization,
            organization.id,
        )

        loaded_assessment = db.get_or_404(
            Assessment,
            assessment.id,
        )

        loaded_asset = db.get_or_404(
            Asset,
            asset.id,
        )

        assert (
            loaded_organization.assessments[0].id
            == assessment.id
        )

        assert (
            loaded_organization.assets[0].id
            == asset.id
        )

        assert (
            loaded_assessment.organization.id
            == organization.id
        )

        assert (
            loaded_assessment.assessor.id
            == user.id
        )

        assert (
            loaded_assessment.risk_items[0].id
            == risk.id
        )

        assert (
            loaded_asset.risk_items[0].id
            == risk.id
        )


def test_mitigation_relationship_is_many_to_many(app):
    with app.app_context():

        user = User(
            username="mitigation_tester",
            password_hash="test-hash",
            role="assessor",
        )

        organization = Organization(
            name="Mitigation Test Business",
            business_type="IT Services",
        )

        asset = Asset(
            organization=organization,
            name="Employee Workstation",
            asset_type="Endpoint",
        )

        assessment = Assessment(
            organization=organization,
            assessor=user,
        )

        risk = RiskItem(
            assessment=assessment,
            asset=asset,
            threat="Phishing",
            vulnerability=(
                "Users may click malicious links."
            ),
            likelihood=3,
            impact=4,
            risk_score=12,
            risk_level="High",
            recommendation="Use MFA and awareness training.",
        )

        mitigation_one = Mitigation(
            threat_type="Phishing",
            mitigation_name="MFA",
            description=(
                "Use multi-factor authentication."
            ),
            priority="High",
        )

        mitigation_two = Mitigation(
            threat_type="Phishing",
            mitigation_name="Awareness Training",
            description=(
                "Train staff to identify "
                "phishing attempts."
            ),
            priority="High",
        )

        risk.mitigations.extend(
            [
                mitigation_one,
                mitigation_two,
            ]
        )

        db.session.add_all(
            [
                user,
                organization,
                asset,
                assessment,
                risk,
            ]
        )

        db.session.commit()

        assert len(risk.mitigations) == 2

        assert (
            risk.mitigations[0]
            .risk_items[0]
            .id
            == risk.id
        )

        assert (
            risk.mitigations[1]
            .risk_items[0]
            .id
            == risk.id
        )
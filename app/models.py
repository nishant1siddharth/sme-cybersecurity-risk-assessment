from datetime import datetime, timezone

from sqlalchemy import CheckConstraint, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .extensions import db


risk_item_mitigations = db.Table(
    "risk_item_mitigations",
    db.Column(
        "risk_item_id",
        db.ForeignKey("risk_items.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    db.Column(
        "mitigation_id",
        db.ForeignKey("mitigations.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class User(db.Model):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    role: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="assessor",
    )

    assessments: Mapped[list["Assessment"]] = relationship(
        back_populates="assessor",
        foreign_keys="Assessment.assessor_id",
    )


class Organization(db.Model):
    __tablename__ = "organizations"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        unique=True,
    )
    business_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    assets: Mapped[list["Asset"]] = relationship(
        back_populates="organization",
        cascade="all, delete-orphan",
    )

    assessments: Mapped[list["Assessment"]] = relationship(
        back_populates="organization",
        cascade="all, delete-orphan",
    )


class Assessment(db.Model):
    __tablename__ = "assessments"

    id: Mapped[int] = mapped_column(primary_key=True)

    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )

    assessor_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )

    assessment_date: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    organization: Mapped["Organization"] = relationship(
        back_populates="assessments",
    )

    assessor: Mapped["User"] = relationship(
        back_populates="assessments",
        foreign_keys=[assessor_id],
    )

    risk_items: Mapped[list["RiskItem"]] = relationship(
        back_populates="assessment",
        cascade="all, delete-orphan",
    )


class Asset(db.Model):
    __tablename__ = "assets"

    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "name",
            name="uq_asset_organization_name",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    asset_type: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    organization: Mapped["Organization"] = relationship(
        back_populates="assets",
    )

    risk_items: Mapped[list["RiskItem"]] = relationship(
        back_populates="asset",
    )


class RiskItem(db.Model):
    __tablename__ = "risk_items"

    __table_args__ = (
        CheckConstraint(
            "likelihood BETWEEN 1 AND 5",
            name="ck_risk_likelihood_range",
        ),
        CheckConstraint(
            "impact BETWEEN 1 AND 5",
            name="ck_risk_impact_range",
        ),
        CheckConstraint(
            "risk_score BETWEEN 1 AND 25",
            name="ck_risk_score_range",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    assessment_id: Mapped[int] = mapped_column(
        ForeignKey("assessments.id", ondelete="CASCADE"),
        nullable=False,
    )

    asset_id: Mapped[int] = mapped_column(
        ForeignKey("assets.id", ondelete="RESTRICT"),
        nullable=False,
    )

    threat: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
    )

    vulnerability: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    likelihood: Mapped[int] = mapped_column(
        nullable=False,
    )

    impact: Mapped[int] = mapped_column(
        nullable=False,
    )

    risk_score: Mapped[int] = mapped_column(
        nullable=False,
    )

    risk_level: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    recommendation: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    assessment: Mapped["Assessment"] = relationship(
        back_populates="risk_items",
    )

    asset: Mapped["Asset"] = relationship(
        back_populates="risk_items",
    )

    mitigations: Mapped[list["Mitigation"]] = relationship(
        secondary=risk_item_mitigations,
        back_populates="risk_items",
    )


class Mitigation(db.Model):
    __tablename__ = "mitigations"

    __table_args__ = (
        UniqueConstraint(
            "threat_type",
            "mitigation_name",
            name="uq_mitigation_threat_name",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    threat_type: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
    )

    mitigation_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    priority: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    risk_items: Mapped[list["RiskItem"]] = relationship(
        secondary=risk_item_mitigations,
        back_populates="mitigations",
    )
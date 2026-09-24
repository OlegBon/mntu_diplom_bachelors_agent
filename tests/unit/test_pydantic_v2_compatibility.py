from datetime import datetime

from backend import models, schemas


def test_legacy_orm_response_schemas_use_pydantic_v2_from_attributes() -> None:
    expert = models.Expert(
        expert_id=7,
        username="schema-expert",
        first_name="Schema",
        last_name="Expert",
        middle_name=None,
        role="gemologist",
        is_active=True,
    )
    grade_mapping = models.GradeMapping(category="color", grade_value=1, grade_label="E")
    market_price = models.MarketPriceRef(
        id=3,
        price_index_value=1234.5,
        updated_at=datetime(2026, 9, 24, 12, 0),
        notes="compatibility check",
    )

    assert schemas.ExpertBase.model_validate(expert).model_dump()["username"] == "schema-expert"
    assert schemas.GradeMappingSchema.model_validate(grade_mapping).model_dump()["grade_label"] == "E"
    assert schemas.MarketPriceResponse.model_validate(market_price).model_dump()["id"] == 3

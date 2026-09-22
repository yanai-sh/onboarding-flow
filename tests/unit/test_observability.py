from onboarding_flow.observability import mask_plate


def test_mask_plate_hides_prefix() -> None:
    assert mask_plate("12345678") == "****5678"


def test_mask_plate_short_values() -> None:
    assert mask_plate("AB") == "****"

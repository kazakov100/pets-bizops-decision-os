from pets_bizops.analysis import evidence


def test_pet_growth_vs_loss_ratio_evidence_has_limitations():
    ev = evidence.pet_growth_vs_loss_ratio_evidence()
    assert ev.limitations
    assert len(ev.supporting_metrics["pet_loss_ratio_full_series"]) == 9


def test_pet_premium_per_customer_evidence_shows_gap():
    ev = evidence.pet_premium_per_customer_evidence()
    assert ev.supporting_metrics["pet_yoy_ifp_growth_pct"] > ev.supporting_metrics["pet_yoy_ppc_growth_pct"]


def test_pet_segment_share_evidence_shows_pet_as_second_largest():
    ev = evidence.pet_segment_share_evidence()
    assert "2nd-largest" in ev.finding
    assert ev.supporting_metrics["share_breakdown"][0]["segment"] == "Homeowners"


def test_company_growth_acceleration_evidence_is_monotonic():
    ev = evidence.company_growth_acceleration_evidence()
    assert ev.supporting_metrics["monotonic"] is True


def test_pet_loss_ratio_vs_other_segments_evidence_shows_pet_lagging():
    ev = evidence.pet_loss_ratio_vs_other_segments_evidence()
    assert abs(ev.supporting_metrics["pet_change_points"]) < abs(ev.supporting_metrics["car_change_points"])

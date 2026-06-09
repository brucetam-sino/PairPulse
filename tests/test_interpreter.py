from pairpulse.interpreter import interpret_rule


class TestInterpretRule:
    def test_bundle_lift_ge_3(self):
        result = interpret_rule({
            "antecedent": "A",
            "consequent": "B",
            "lift": 3.5,
            "confidence": 0.5,
            "support": 0.1,
        })
        types = [s["type"] for s in result["suggestions"]]
        assert "捆绑套餐" in types
        assert result["summary"] != ""

    def test_page_recommendation_lift_ge_2(self):
        result = interpret_rule({
            "antecedent": "A",
            "consequent": "B",
            "lift": 2.5,
            "confidence": 0.3,
            "support": 0.1,
        })
        types = [s["type"] for s in result["suggestions"]]
        assert "页面推荐" in types
        assert "捆绑套餐" not in types

    def test_display_adjustment_lift_ge_1_5_conf_ge_20(self):
        result = interpret_rule({
            "antecedent": "A",
            "consequent": "B",
            "lift": 1.6,
            "confidence": 0.25,
            "support": 0.1,
        })
        types = [s["type"] for s in result["suggestions"]]
        assert "陈列调整" in types

    def test_combo_discount_conf_ge_40_no_prior(self):
        result = interpret_rule({
            "antecedent": "A",
            "consequent": "B",
            "lift": 1.3,
            "confidence": 0.45,
            "support": 0.1,
        })
        types = [s["type"] for s in result["suggestions"]]
        assert "组合优惠" in types

    def test_upsell_lift_ge_2_few_suggestions(self):
        result = interpret_rule({
            "antecedent": "A",
            "consequent": "B",
            "lift": 2.1,
            "confidence": 0.1,
            "support": 0.1,
        })
        types = [s["type"] for s in result["suggestions"]]
        assert "加价购" in types
        assert "页面推荐" in types

    def test_no_suggestions_for_low_metrics(self):
        result = interpret_rule({
            "antecedent": "A",
            "consequent": "B",
            "lift": 1.1,
            "confidence": 0.1,
            "support": 0.01,
        })
        assert len(result["suggestions"]) == 0
        assert result["summary"] == ""

    def test_group_name_in_summary(self):
        result = interpret_rule({
            "antecedent": "A",
            "consequent": "B",
            "lift": 3.5,
            "confidence": 0.5,
            "support": 0.1,
        }, group_name="high_value")
        assert "[high_value]" in result["summary"]
